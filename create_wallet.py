"""Script to create a new Solana wallet for the bot."""
from solders.keypair import Keypair
import base58
import json


def create_wallet():
    """Create a new Solana wallet and display credentials."""
    # Create new keypair
    keypair = Keypair()
    
    # Get public key
    public_key = str(keypair.pubkey())
    
    # Get private key in base58 format
    private_key = base58.b58encode(bytes(keypair)).decode()
    
    print("=" * 80)
    print(" " * 25 + "НОВЫЙ SOLANA КОШЕЛЕК")
    print("=" * 80)
    print()
    print("📍 Public Key (Адрес кошелька):")
    print(f"   {public_key}")
    print()
    print("🔑 Private Key (Приватный ключ в base58):")
    print(f"   {private_key}")
    print()
    print("=" * 80)
    print()
    print("⚠️  ВАЖНО!")
    print("   • Сохраните эти данные в безопасном месте")
    print("   • НИКОГДА не делитесь приватным ключом с кем-либо")
    print("   • Потеря приватного ключа = потеря доступа к средствам")
    print()
    print("=" * 80)
    print()
    print("📝 Добавьте следующие строки в ваш .env файл:")
    print()
    print(f"MASTER_WALLET_PUBLIC_KEY={public_key}")
    print(f"MASTER_WALLET_PRIVATE_KEY={private_key}")
    print()
    print("=" * 80)
    
    # Ask if user wants to save to JSON file
    save = input("\nСохранить кошелек в файл wallet.json? (y/n): ").lower().strip()
    
    if save == 'y':
        keypair_bytes = bytes(keypair)
        with open('wallet.json', 'w') as f:
            json.dump(list(keypair_bytes), f)
        
        print("\n✓ Кошелек сохранен в wallet.json (формат Solana CLI)")
        print("  Вы можете использовать этот файл с Solana CLI:")
        print(f"  solana-keygen pubkey wallet.json")
        print()
        print("⚠️  НЕ загружайте wallet.json в git/github!")
    
    print()
    print("=" * 80)
    print()
    print("🚀 Следующие шаги:")
    print()
    print("1. Скопируйте ключи в .env файл")
    print("2. Для тестирования используйте Devnet:")
    print("   SOLANA_RPC_URL=https://api.devnet.solana.com")
    print()
    print("3. Получите тестовые SOL на Devnet:")
    print(f"   https://faucet.solana.com/")
    print(f"   Адрес: {public_key}")
    print()
    print("4. Для продакшена используйте Mainnet:")
    print("   SOLANA_RPC_URL=https://api.mainnet-beta.solana.com")
    print("   И купите реальные SOL на бирже")
    print()
    print("5. Проверьте баланс на Solana Explorer:")
    print(f"   https://explorer.solana.com/address/{public_key}?cluster=devnet")
    print()
    print("=" * 80)


if __name__ == '__main__':
    try:
        create_wallet()
    except Exception as e:
        print(f"\n❌ Ошибка при создании кошелька: {e}")
        import traceback
        traceback.print_exc()

