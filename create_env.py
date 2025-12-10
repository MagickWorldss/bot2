"""Создание .env файла."""
env_content = """# ===================================
# LOCAL DEVELOPMENT CONFIG
# ===================================
# Конфигурация для локальной разработки (SQLite)

# ===================================
# Telegram Bot
# ===================================
BOT_TOKEN=8466412706:AAFlGZRTg-DCGggf8NE8KDSoFPAAA-SX64c
ADMIN_IDS=8169477082

# ===================================
# Database - SQLite (для локальной разработки)
# ===================================
DATABASE_URL=sqlite+aiosqlite:///./bot.db

# ===================================
# Solana
# ===================================
SOLANA_RPC_URL=https://api.devnet.solana.com

MASTER_WALLET_PUBLIC_KEY=2Nx5XkW8cTQ392g61pR31C4iHQrhEXhQLmhp73ZmbaiC
MASTER_WALLET_PRIVATE_KEY=5oDZp4rxjuxEsmVhJbk9rJLaTh4amNj6NPDR4DGMiByy2HAFZG5wutMK9be3TTsybZ15Z2FRe9NNHuScjTApBKVA

# ===================================
# Application Settings
# ===================================
MIN_DEPOSIT_SOL=0.01
IMAGE_PRICE_SOL=0.05
WITHDRAWAL_FEE_PERCENT=2
"""

if __name__ == '__main__':
    import os
    if os.path.exists('.env'):
        response = input('Файл .env уже существует. Перезаписать? (y/n): ')
        if response.lower() != 'y':
            print('Отменено')
            exit(0)
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print('✅ .env файл создан!')
    print('\nСодержит:')
    print('  ✅ BOT_TOKEN')
    print('  ✅ ADMIN_IDS: 8169477082')
    print('  ✅ MASTER_WALLET ключи')
    print('  ✅ SOLANA_RPC_URL: devnet')
    print('  ✅ Все настройки')

