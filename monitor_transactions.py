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
    Check for new deposits to user's wallet.
    
    Returns:
        Total amount of new deposits in SOL
    """
    try:
        # Get actual balance from blockchain
        actual_balance = await wallet_service.get_balance(user.wallet_address)
        
        # Calculate difference
        difference = actual_balance - user.balance_sol
        
        if difference > 0.0001:  # Ignore dust (< 0.0001 SOL)
            logger.info(
                f"New deposit detected for user {user.id}: "
                f"{difference} SOL (balance: {actual_balance})"
            )
            return difference
        
        return 0.0
        
    except Exception as e:
        logger.error(f"Error checking deposits for user {user.id}: {e}")
        return 0.0


async def process_deposits():
    """Process deposits for all users."""
    logger.info("Starting deposit monitoring...")
    
    while True:
        try:
            async for session in db.get_session():
                # Get all users
                result = await session.execute(select(User))
                users = result.scalars().all()
                
                logger.info(f"Checking deposits for {len(users)} users...")
                
                for user in users:
                    if user.is_blocked:
                        continue
                    
                    # Check for deposits
                    deposit_amount = await check_user_deposits(session, user)
                    
                    if deposit_amount > 0:
                        # Update user balance
                        await UserService.update_balance(
                            session,
                            user.id,
                            deposit_amount
                        )
                        
                        # Create transaction record
                        await TransactionService.create_transaction(
                            session=session,
                            user_id=user.id,
                            tx_type='deposit',
                            amount_sol=deposit_amount,
                            to_address=user.wallet_address,
                            description=f"Deposit to wallet",
                            status='completed'
                        )
                        
                        logger.info(
                            f"✅ Processed deposit for user {user.id}: "
                            f"{deposit_amount} SOL"
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

