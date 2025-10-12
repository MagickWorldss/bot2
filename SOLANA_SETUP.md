# Настройка Solana кошелька

## Введение

Для работы бота необходим мастер-кошелек Solana, который будет использоваться для:
- Создания дочерних кошельков для пользователей
- Обработки транзакций
- Хранения средств

## Метод 1: Использование Solana CLI (Рекомендуется для продакшена)

### 1. Установка Solana CLI

**Linux/Mac:**
```bash
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
```

**Windows (PowerShell):**
```powershell
cmd /c "curl https://release.solana.com/stable/solana-install-init-x86_64-pc-windows-msvc.exe --output C:\solana-install-tmp\solana-install-init.exe --create-dirs"
C:\solana-install-tmp\solana-install-init.exe
```

### 2. Добавление Solana в PATH

**Linux/Mac:**
```bash
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
```

Добавьте эту строку в `~/.bashrc` или `~/.zshrc` для постоянного эффекта.

**Windows:**
Solana installer автоматически добавит в PATH.

### 3. Проверка установки

```bash
solana --version
```

### 4. Настройка сети

**Для тестирования (Devnet):**
```bash
solana config set --url https://api.devnet.solana.com
```

**Для продакшена (Mainnet):**
```bash
solana config set --url https://api.mainnet-beta.solana.com
```

### 5. Создание кошелька

```bash
# Создание нового кошелька
solana-keygen new --outfile ~/solana-wallet.json

# Система попросит ввести passphrase (можно оставить пустым для тестирования)
# ВАЖНО: Сохраните seed phrase в безопасном месте!
```

### 6. Получение публичного адреса

```bash
solana-keygen pubkey ~/solana-wallet.json
```

Это ваш `MASTER_WALLET_PUBLIC_KEY`.

### 7. Получение приватного ключа в base58

```bash
cat ~/solana-wallet.json
```

Вы увидите массив чисел, например: `[1,2,3,4,...]`

Для конвертации в base58 используйте Python:

```bash
python3 << EOF
import base58
import json

with open('solana-wallet.json', 'r') as f:
    keypair = json.load(f)

private_key = base58.b58encode(bytes(keypair)).decode()
print(f"Private Key (base58): {private_key}")
EOF
```

Это ваш `MASTER_WALLET_PRIVATE_KEY`.

### 8. Получение тестовых SOL (только для Devnet)

```bash
solana airdrop 2
```

Это зачислит 2 SOL на ваш кошелек в devnet.

### 9. Проверка баланса

```bash
solana balance
```

## Метод 2: Использование Phantom Wallet (Проще для начинающих)

### 1. Установка Phantom

Скачайте расширение для браузера: [https://phantom.app/](https://phantom.app/)

### 2. Создание кошелька

1. Откройте расширение Phantom
2. Выберите "Create New Wallet"
3. Сохраните seed phrase (12 слов) в безопасном месте
4. Установите пароль

### 3. Переключение на Devnet (для тестирования)

1. Откройте Phantom
2. Нажмите на иконку настроек (шестеренка)
3. Внизу нажмите несколько раз до появления "Change Network"
4. Выберите "Devnet"

### 4. Получение публичного адреса

1. Откройте Phantom
2. Нажмите на адрес кошелька в верхней части
3. Скопируйте адрес

Это ваш `MASTER_WALLET_PUBLIC_KEY`.

### 5. Экспорт приватного ключа

⚠️ **ОПАСНО**: Никогда не делитесь приватным ключом!

1. Откройте Phantom
2. Настройки → Security & Privacy
3. Export Private Key
4. Введите пароль
5. Скопируйте приватный ключ

Это ваш `MASTER_WALLET_PRIVATE_KEY`.

### 6. Получение тестовых SOL (Devnet)

В Phantom на devnet нажмите "Airdrop" для получения тестовых SOL.

## Метод 3: Использование Python скрипта

Создайте файл `create_wallet.py`:

```python
from solders.keypair import Keypair
import base58
import json

# Создание нового keypair
keypair = Keypair()

# Получение публичного ключа
public_key = str(keypair.pubkey())

# Получение приватного ключа в base58
private_key = base58.b58encode(bytes(keypair)).decode()

print("=" * 60)
print("НОВЫЙ SOLANA КОШЕЛЕК")
print("=" * 60)
print(f"\nPublic Key (Адрес):")
print(public_key)
print(f"\nPrivate Key (Base58):")
print(private_key)
print("\n⚠️  ВАЖНО: Сохраните эти данные в безопасном месте!")
print("⚠️  Никогда не делитесь приватным ключом!")
print("\nДобавьте в .env:")
print(f"MASTER_WALLET_PUBLIC_KEY={public_key}")
print(f"MASTER_WALLET_PRIVATE_KEY={private_key}")
print("=" * 60)

# Опционально: сохранение в файл JSON (формат Solana CLI)
keypair_bytes = bytes(keypair)
with open('wallet.json', 'w') as f:
    json.dump(list(keypair_bytes), f)
print("\n✓ Кошелек также сохранен в wallet.json")
```

Запустите:

```bash
python create_wallet.py
```

## Настройка .env файла

После создания кошелька, добавьте следующие строки в файл `.env`:

```env
# Solana Configuration
SOLANA_RPC_URL=https://api.devnet.solana.com
MASTER_WALLET_PUBLIC_KEY=ваш_публичный_ключ_здесь
MASTER_WALLET_PRIVATE_KEY=ваш_приватный_ключ_здесь
```

### Для тестирования (Devnet):
```env
SOLANA_RPC_URL=https://api.devnet.solana.com
```

### Для продакшена (Mainnet):
```env
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

## Получение SOL на кошелек

### Devnet (Тестовая сеть):

**Через Solana CLI:**
```bash
solana airdrop 2
```

**Через веб-фаucet:**
- [https://faucet.solana.com/](https://faucet.solana.com/)
- [https://solfaucet.com/](https://solfaucet.com/)

### Mainnet (Реальная сеть):

Купите SOL на бирже и переведите на свой кошелек:
- **Binance**: [https://www.binance.com/](https://www.binance.com/)
- **Coinbase**: [https://www.coinbase.com/](https://www.coinbase.com/)
- **Kraken**: [https://www.kraken.com/](https://www.kraken.com/)
- **FTX**: [https://ftx.com/](https://ftx.com/)

⚠️ **Важно**: Убедитесь, что переводите именно SOL (Solana), а не токены на другой сети!

## RPC Endpoints

### Публичные RPC (бесплатные):

**Devnet:**
- `https://api.devnet.solana.com`

**Mainnet:**
- `https://api.mainnet-beta.solana.com`

⚠️ **Ограничения**: Публичные RPC имеют rate limits (ограничения на количество запросов).

### Приватные RPC (рекомендуется для продакшена):

**QuickNode:**
- [https://www.quicknode.com/](https://www.quicknode.com/)
- Цена: от $9/месяц
- До 100M запросов/месяц

**Alchemy:**
- [https://www.alchemy.com/solana](https://www.alchemy.com/solana)
- Бесплатный план: 300M compute units/месяц

**Helius:**
- [https://www.helius.dev/](https://www.helius.dev/)
- Бесплатный план: 100K запросов/день

**GetBlock:**
- [https://getblock.io/](https://getblock.io/)
- Цена: от $49/месяц

### Пример настройки с QuickNode:

1. Зарегистрируйтесь на [QuickNode](https://www.quicknode.com/)
2. Создайте endpoint для Solana (Mainnet или Devnet)
3. Скопируйте HTTP Provider URL
4. Добавьте в `.env`:

```env
SOLANA_RPC_URL=https://your-endpoint.solana-mainnet.quiknode.pro/your-token/
```

## Безопасность

### ✅ Рекомендации:

1. **Никогда не делитесь приватным ключом** с кем-либо
2. **Храните seed phrase** в безопасном месте (офлайн)
3. **Используйте разные кошельки** для тестирования и продакшена
4. **Регулярно делайте бэкапы** файла `wallet_encryption.key`
5. **Используйте hardware wallet** для больших сумм (Ledger, Trezor)
6. **Ограничьте доступ** к серверу с ботом
7. **Используйте .gitignore** для исключения `.env` из git
8. **Зашифруйте диск** на сервере
9. **Используйте 2FA** на всех биржах и сервисах
10. **Мониторьте транзакции** на блокчейне

### ❌ Что НЕ делать:

1. ❌ Не публикуйте приватный ключ в git/github
2. ❌ Не храните приватный ключ в открытом виде
3. ❌ Не используйте один кошелек для всего
4. ❌ Не игнорируйте обновления безопасности
5. ❌ Не используйте публичные WiFi для транзакций

## Проверка настройки

После настройки кошелька, проверьте подключение:

```python
import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

async def test_connection():
    # Замените на ваш RPC URL
    rpc_url = "https://api.devnet.solana.com"
    client = AsyncClient(rpc_url)
    
    # Замените на ваш публичный ключ
    public_key = "ваш_публичный_ключ"
    
    try:
        # Проверка баланса
        pubkey = Pubkey.from_string(public_key)
        response = await client.get_balance(pubkey)
        
        if response.value is not None:
            balance_sol = response.value / 1_000_000_000
            print(f"✓ Подключение успешно!")
            print(f"✓ Публичный ключ: {public_key}")
            print(f"✓ Баланс: {balance_sol} SOL")
        else:
            print("✗ Не удалось получить баланс")
    
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
    
    finally:
        await client.close()

if __name__ == '__main__':
    asyncio.run(test_connection())
```

## Мониторинг кошелька

### Через Solana Explorer:

**Devnet:**
```
https://explorer.solana.com/address/ваш_адрес?cluster=devnet
```

**Mainnet:**
```
https://explorer.solana.com/address/ваш_адрес
```

### Через Solscan:

**Mainnet:**
```
https://solscan.io/account/ваш_адрес
```

## Часто задаваемые вопросы

**Q: Сколько SOL нужно для работы бота?**
A: Минимум ~0.01 SOL для тестирования. Для продакшена рекомендуется иметь 1-5 SOL для покрытия комиссий.

**Q: Какая комиссия за транзакцию в Solana?**
A: ~0.000005 SOL (0.5 цента при цене SOL = $100)

**Q: Можно ли изменить мастер-кошелек после запуска?**
A: Да, но все пользовательские кошельки останутся привязаны к старому ключу шифрования.

**Q: Что делать, если потерял приватный ключ?**
A: Без приватного ключа доступ к кошельку невозможен. Всегда храните бэкапы!

**Q: Безопасно ли хранить приватные ключи в .env?**
A: Для продакшена рекомендуется использовать менеджеры секретов (HashiCorp Vault, AWS Secrets Manager).

**Q: Как перенести бота на другой сервер?**
A: Скопируйте `.env`, `wallet_encryption.key` и базу данных. Убедитесь, что файлы защищены.

## Дополнительные ресурсы

- **Документация Solana**: [https://docs.solana.com/](https://docs.solana.com/)
- **Solana Cookbook**: [https://solanacookbook.com/](https://solanacookbook.com/)
- **Web3.py документация**: [https://michaelhly.github.io/solana-py/](https://michaelhly.github.io/solana-py/)
- **Solana Discord**: [https://discord.gg/solana](https://discord.gg/solana)
- **Solana StackExchange**: [https://solana.stackexchange.com/](https://solana.stackexchange.com/)

