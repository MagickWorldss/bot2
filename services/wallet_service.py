"""Solana wallet service."""
import base58
from typing import Optional, Tuple
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction as SoldersTransaction
from cryptography.fernet import Fernet
import os
from config import settings


class WalletService:
    """Service for managing Solana wallets."""
    
    def __init__(self):
        self.rpc_client = AsyncClient(settings.solana_rpc_url)
        self.master_keypair = Keypair.from_base58_string(settings.master_wallet_private_key)
        
        # Generate or load encryption key for wallet private keys
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for wallet storage."""
        key_file = 'wallet_encryption.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def create_wallet(self) -> Tuple[str, str]:
        """
        Create a new Solana wallet.
        
        Returns:
            Tuple of (public_key, encrypted_private_key)
        """
        keypair = Keypair()
        public_key = str(keypair.pubkey())
        private_key = base58.b58encode(bytes(keypair)).decode()
        
        # Encrypt private key
        encrypted_private_key = self.cipher.encrypt(private_key.encode()).decode()
        
        return public_key, encrypted_private_key
    
    def decrypt_private_key(self, encrypted_private_key: str) -> str:
        """Decrypt wallet private key."""
        return self.cipher.decrypt(encrypted_private_key.encode()).decode()
    
    def get_keypair(self, encrypted_private_key: str) -> Keypair:
        """Get keypair from encrypted private key."""
        private_key = self.decrypt_private_key(encrypted_private_key)
        return Keypair.from_base58_string(private_key)
    
    async def get_balance(self, public_key: str) -> float:
        """
        Get wallet balance in SOL.
        
        Args:
            public_key: Wallet public key
            
        Returns:
            Balance in SOL
        """
        try:
            pubkey = Pubkey.from_string(public_key)
            response = await self.rpc_client.get_balance(pubkey)
            
            if response.value is not None:
                # Convert lamports to SOL (1 SOL = 1_000_000_000 lamports)
                return response.value / 1_000_000_000
            return 0.0
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0.0
    
    async def transfer_sol(
        self,
        from_keypair: Keypair,
        to_public_key: str,
        amount_sol: float
    ) -> Optional[str]:
        """
        Transfer SOL from one wallet to another.
        
        Args:
            from_keypair: Sender's keypair
            to_public_key: Recipient's public key
            amount_sol: Amount in SOL
            
        Returns:
            Transaction hash if successful, None otherwise
        """
        try:
            # Convert SOL to lamports
            amount_lamports = int(amount_sol * 1_000_000_000)
            
            # Create transfer instruction
            to_pubkey = Pubkey.from_string(to_public_key)
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=from_keypair.pubkey(),
                    to_pubkey=to_pubkey,
                    lamports=amount_lamports
                )
            )
            
            # Get recent blockhash
            recent_blockhash_resp = await self.rpc_client.get_latest_blockhash()
            recent_blockhash = recent_blockhash_resp.value.blockhash
            
            # Create and sign transaction
            transaction = SoldersTransaction.new_with_payer(
                [transfer_ix],
                from_keypair.pubkey()
            )
            transaction.partial_sign([from_keypair], recent_blockhash)
            
            # Send transaction
            response = await self.rpc_client.send_transaction(transaction)
            
            return str(response.value)
        except Exception as e:
            print(f"Error transferring SOL: {e}")
            return None
    
    async def check_incoming_transactions(
        self,
        wallet_public_key: str,
        last_signature: Optional[str] = None
    ) -> list:
        """
        Check for incoming transactions to a wallet.
        
        Args:
            wallet_public_key: Wallet to check
            last_signature: Last processed signature
            
        Returns:
            List of new transactions
        """
        try:
            pubkey = Pubkey.from_string(wallet_public_key)
            
            # Get transaction signatures
            signatures_resp = await self.rpc_client.get_signatures_for_address(
                pubkey,
                limit=10
            )
            
            if not signatures_resp.value:
                return []
            
            new_transactions = []
            for sig_info in signatures_resp.value:
                signature = str(sig_info.signature)
                
                # Stop if we reach the last processed signature
                if last_signature and signature == last_signature:
                    break
                
                # Get transaction details
                tx_resp = await self.rpc_client.get_transaction(
                    sig_info.signature,
                    max_supported_transaction_version=0
                )
                
                if tx_resp.value:
                    new_transactions.append({
                        'signature': signature,
                        'slot': sig_info.slot,
                        'block_time': sig_info.block_time,
                        'transaction': tx_resp.value
                    })
            
            return new_transactions
        except Exception as e:
            print(f"Error checking transactions: {e}")
            return []
    
    async def close(self):
        """Close RPC client."""
        await self.rpc_client.close()


# Global wallet service instance
wallet_service = WalletService()

