"""Monitor incoming Solana transactions and update user balances."""
import asyncio
import logging
from datetime import datetime
from database.database import db
from database.models import User
from services.wallet_service import wallet_service
from services.user_service import UserService
from services.transaction_service import TransactionService
from sqlalchemy import select


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_user_deposits(session, user: User) -> float:
    """
    Check for new deposits to user's wallet with EUR rate reservation.
    
    Returns:
        Amount in EUR to credit (not SOL!)
    """
    try:
        from services.deposit_service import deposit_service
        from services.price_service import price_service
        
        # Get actual balance from blockchain (in SOL)
        actual_balance = await wallet_service.get_balance(user.wallet_address)
        
        # Calculate difference in SOL (compare with wallet_balance_sol, NOT balance_sol!)
        # balance_sol = EUR balance
        # wallet_balance_sol = last known SOL balance on blockchain
        sol_difference = actual_balance - user.wallet_balance_sol
        
        if sol_difference > 0.0001:  # Ignore dust (< 0.0001 SOL)
            logger.info(
                f"New deposit detected for user {user.id}: "
                f"{sol_difference} SOL (balance: {actual_balance})"
            )
            
            # Check for active deposit request with reserved rate
            active_deposit = await deposit_service.get_active_deposit(session, user.id)
            
            if active_deposit and abs(sol_difference - active_deposit.sol_amount) < 0.001:
                # Deposit matches active request - use reserved rate!
                logger.info(
                    f"Deposit matches request #{active_deposit.id} "
                    f"with reserved rate {active_deposit.reserved_rate}"
                )
                
                # Complete deposit request
                await deposit_service.complete_deposit(session, active_deposit.id)
                
                # Return EUR amount (using reserved rate!)
                return active_deposit.eur_amount
            else:
                # No matching request - use current rate
                rate = await price_service.get_sol_eur_rate()
                eur_amount = sol_difference * rate
                
                logger.info(
                    f"Deposit without request, using current rate {rate}: "
                    f"{sol_difference} SOL = {eur_amount} EUR"
                )
                
                return eur_amount
        
        return 0.0
        
    except Exception as e:
        logger.error(f"Error checking deposits for user {user.id}: {e}")
        return 0.0


async def process_deposits():
    """Process deposits for all users with EUR conversion."""
    logger.info("Starting deposit monitoring...")
    
    while True:
        try:
            async for session in db.get_session():
                from services.deposit_service import deposit_service
                
                # Expire old deposit requests
                expired_count = await deposit_service.expire_old_deposits(session)
                if expired_count > 0:
                    logger.info(f"Expired {expired_count} old deposit requests")
                
                # Get all users
                result = await session.execute(select(User))
                users = result.scalars().all()
                
                logger.info(f"Checking deposits for {len(users)} users...")
                
                for user in users:
                    if user.is_blocked:
                        continue
                    
                    # Check for deposits (returns EUR amount!)
                    eur_amount = await check_user_deposits(session, user)
                    
                    if eur_amount > 0:
                        # Get actual SOL amount for logging
                        actual_balance = await wallet_service.get_balance(user.wallet_address)
                        sol_received = actual_balance - user.wallet_balance_sol
                        
                        # Update user balance in EUR!
                        await UserService.update_balance(
                            session,
                            user.id,
                            eur_amount  # Add EUR, not SOL!
                        )
                        
                        # Update wallet SOL balance tracker
                        user.wallet_balance_sol = actual_balance
                        await session.commit()
                        
                        # Create transaction record
                        await TransactionService.create_transaction(
                            session=session,
                            user_id=user.id,
                            tx_type='deposit',
                            amount_sol=eur_amount,  # Store EUR amount in transaction
                            description=f"Deposit: {sol_received:.6f} SOL = {eur_amount:.2f} EUR (rate reserved)",
                            status='completed'
                        )
                        
                        logger.info(
                            f"✅ Processed deposit for user {user.id}: "
                            f"{sol_received:.6f} SOL = {eur_amount:.2f} EUR"
                        )
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            logger.error(f"Error in deposit monitoring: {e}", exc_info=True)
            await asyncio.sleep(60)  # Wait 1 minute on error


async def process_withdrawals():
    """Process pending withdrawals."""
    logger.info("Starting withdrawal monitoring...")
    
    while True:
        try:
            async for session in db.get_session():
                # Get pending withdrawals
                pending = await TransactionService.get_pending_transactions(session)
                withdrawals = [tx for tx in pending if tx.tx_type == 'withdrawal']
                
                if withdrawals:
                    logger.info(f"Processing {len(withdrawals)} pending withdrawals...")
                
                for tx in withdrawals:
                    try:
                        # Get user's keypair
                        user = await UserService.get_user(session, tx.user_id)
                        if not user:
                            logger.error(f"User {tx.user_id} not found for withdrawal {tx.id}")
                            continue
                        
                        keypair = wallet_service.get_keypair(user.wallet_private_key)
                        
                        # Send transaction
                        tx_hash = await wallet_service.transfer_sol(
                            from_keypair=keypair,
                            to_public_key=tx.to_address,
                            amount_sol=tx.amount_sol
                        )
                        
                        if tx_hash:
                            # Update transaction status
                            await TransactionService.update_transaction_status(
                                session,
                                tx.id,
                                'completed',
                                tx_hash
                            )
                            
                            logger.info(
                                f"✅ Processed withdrawal {tx.id}: "
                                f"{tx.amount_sol} SOL to {tx.to_address}"
                            )
                        else:
                            logger.error(f"Failed to process withdrawal {tx.id}")
                        
                    except Exception as e:
                        logger.error(f"Error processing withdrawal {tx.id}: {e}")
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every 1 minute
                
        except Exception as e:
            logger.error(f"Error in withdrawal monitoring: {e}", exc_info=True)
            await asyncio.sleep(60)


async def main():
    """Main function to run both monitoring tasks."""
    logger.info("=== Starting transaction monitor ===")
    
    # Create database tables if not exist
    await db.create_tables()
    
    # Run both tasks concurrently
    await asyncio.gather(
        process_deposits(),
        process_withdrawals()
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Transaction monitor stopped by user")
    except Exception as e:
        logger.error(f"Transaction monitor crashed: {e}", exc_info=True)

