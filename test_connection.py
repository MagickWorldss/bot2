"""Test script to verify Solana connection and wallet setup."""
import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
import base58
from dotenv import load_dotenv
import os


async def test_solana_connection():
    """Test connection to Solana RPC."""
    # Load environment variables
    load_dotenv()
    
    rpc_url = os.getenv('SOLANA_RPC_URL', 'https://api.devnet.solana.com')
    public_key = os.getenv('MASTER_WALLET_PUBLIC_KEY')
    private_key = os.getenv('MASTER_WALLET_PRIVATE_KEY')
    
    print("=" * 80)
    print(" " * 25 + "ТЕСТ ПОДКЛЮЧЕНИЯ К SOLANA")
    print("=" * 80)
    print()
    
    # Test 1: Check environment variables
    print("📋 Тест 1: Проверка переменных окружения")
    if not public_key:
        print("   ❌ MASTER_WALLET_PUBLIC_KEY не найден в .env")
        return
    else:
        print(f"   ✓ Public Key: {public_key[:20]}...{public_key[-10:]}")
    
    if not private_key:
        print("   ❌ MASTER_WALLET_PRIVATE_KEY не найден в .env")
        return
    else:
        print(f"   ✓ Private Key: {'*' * 40}")
    
    print(f"   ✓ RPC URL: {rpc_url}")
    print()
    
    # Test 2: Validate keys
    print("🔑 Тест 2: Валидация ключей")
    try:
        pubkey = Pubkey.from_string(public_key)
        print(f"   ✓ Public key валиден")
    except Exception as e:
        print(f"   ❌ Невалидный public key: {e}")
        return
    
    try:
        keypair = Keypair.from_base58_string(private_key)
        print(f"   ✓ Private key валиден")
        
        # Check if keys match
        if str(keypair.pubkey()) == public_key:
            print(f"   ✓ Ключи совпадают")
        else:
            print(f"   ❌ Public и private ключи не совпадают!")
            print(f"      Public key из .env: {public_key}")
            print(f"      Public key из private key: {keypair.pubkey()}")
            return
    except Exception as e:
        print(f"   ❌ Невалидный private key: {e}")
        return
    print()
    
    # Test 3: Connect to RPC
    print("🌐 Тест 3: Подключение к Solana RPC")
    client = AsyncClient(rpc_url)
    
    try:
        # Get cluster version
        version_response = await client.get_version()
        print(f"   ✓ Подключение успешно")
        print(f"   ✓ Solana версия: {version_response.value.solana_core}")
        
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        await client.close()
        return
    print()
    
    # Test 4: Get balance
    print("💰 Тест 4: Проверка баланса кошелька")
    try:
        balance_response = await client.get_balance(pubkey)
        
        if balance_response.value is not None:
            balance_lamports = balance_response.value
            balance_sol = balance_lamports / 1_000_000_000
            
            print(f"   ✓ Баланс успешно получен")
            print(f"   💵 Баланс: {balance_sol:.9f} SOL")
            print(f"   💵 Баланс: {balance_lamports:,} lamports")
            
            if balance_sol < 0.001:
                print()
                print("   ⚠️  Низкий баланс!")
                if 'devnet' in rpc_url.lower():
                    print(f"   Получите тестовые SOL на:")
                    print(f"   https://faucet.solana.com/")
                else:
                    print(f"   Пополните кошелек реальными SOL")
        else:
            print(f"   ❌ Не удалось получить баланс")
            
    except Exception as e:
        print(f"   ❌ Ошибка получения баланса: {e}")
    print()
    
    # Test 5: Get recent blockhash
    print("⛓️  Тест 5: Получение recent blockhash")
    try:
        blockhash_response = await client.get_latest_blockhash()
        blockhash = blockhash_response.value.blockhash
        print(f"   ✓ Blockhash получен: {str(blockhash)[:20]}...")
    except Exception as e:
        print(f"   ❌ Ошибка получения blockhash: {e}")
    print()
    
    # Close client
    await client.close()
    
    # Summary
    print("=" * 80)
    print()
    print("✅ Все тесты пройдены успешно!")
    print()
    print("🎉 Ваш бот готов к работе с Solana!")
    print()
    print("📝 Следующие шаги:")
    print("   1. Инициализируйте базу данных: python init_db.py")
    print("   2. Запустите бота: python main.py")
    print("   3. Запустите монитор транзакций: python monitor_transactions.py")
    print()
    print("🔍 Отслеживайте ваш кошелек на:")
    network = 'devnet' if 'devnet' in rpc_url.lower() else 'mainnet'
    cluster_param = '?cluster=devnet' if network == 'devnet' else ''
    print(f"   https://explorer.solana.com/address/{public_key}{cluster_param}")
    print()
    print("=" * 80)


async def main():
    """Main function."""
    try:
        await test_solana_connection()
    except KeyboardInterrupt:
        print("\n\n⚠️  Тест прерван пользователем")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())

