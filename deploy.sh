#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  Telegram Shop Bot - Deployment Script"
echo "=========================================="
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен!${NC}"
    echo "Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose не установлен!${NC}"
    echo "Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker установлен${NC}"
echo -e "${GREEN}✓ Docker Compose установлен${NC}"
echo ""

# Проверка .env файла
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env файл не найден${NC}"
    echo "Создайте .env файл с настройками"
    echo ""
    echo "Минимальные настройки:"
    echo "BOT_TOKEN=your_token"
    echo "ADMIN_IDS=your_id"
    echo "SOLANA_RPC_URL=https://api.devnet.solana.com"
    echo "MASTER_WALLET_PUBLIC_KEY=your_key"
    echo "MASTER_WALLET_PRIVATE_KEY=your_key"
    echo ""
    read -p "Создать .env сейчас? (y/n): " create_env
    
    if [ "$create_env" = "y" ]; then
        cat > .env << 'EOF'
# Telegram
BOT_TOKEN=
ADMIN_IDS=

# Database (для Docker с PostgreSQL)
DATABASE_URL=postgresql+asyncpg://botuser:changeme@db:5432/botdb

# Для PostgreSQL
POSTGRES_DB=botdb
POSTGRES_USER=botuser
POSTGRES_PASSWORD=changeme

# Solana
SOLANA_RPC_URL=https://api.devnet.solana.com
MASTER_WALLET_PUBLIC_KEY=
MASTER_WALLET_PRIVATE_KEY=

# Settings
MIN_DEPOSIT_SOL=0.01
IMAGE_PRICE_SOL=0.05
WITHDRAWAL_FEE_PERCENT=2
EOF
        echo -e "${GREEN}✓ .env файл создан${NC}"
        echo -e "${YELLOW}⚠️  Заполните .env файл своими данными и запустите скрипт снова${NC}"
        exit 0
    else
        exit 1
    fi
fi

echo -e "${GREEN}✓ .env файл найден${NC}"
echo ""

# Создание необходимых директорий
echo "Создание директорий..."
mkdir -p images data logs
echo -e "${GREEN}✓ Директории созданы${NC}"
echo ""

# Выбор режима
echo "Выберите режим развертывания:"
echo "1) Полное развертывание (PostgreSQL + Bot + Monitor)"
echo "2) Только бот (SQLite)"
echo "3) Пересобрать и перезапустить"
echo "4) Остановить все контейнеры"
echo "5) Просмотр логов"
read -p "Ваш выбор (1-5): " mode

case $mode in
    1)
        echo ""
        echo "Запуск полного развертывания..."
        echo ""
        
        # Сборка образов
        echo "Сборка Docker образов..."
        docker-compose build
        
        echo ""
        echo "Запуск контейнеров..."
        docker-compose up -d
        
        echo ""
        echo -e "${GREEN}✓ Контейнеры запущены!${NC}"
        echo ""
        echo "Подождите 10 секунд для инициализации БД..."
        sleep 10
        
        echo ""
        echo "Инициализация базы данных..."
        docker-compose exec bot python init_db.py
        
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}✓ Развертывание завершено!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "Полезные команды:"
        echo "  docker-compose logs -f bot      # Логи бота"
        echo "  docker-compose logs -f monitor  # Логи монитора"
        echo "  docker-compose ps               # Статус контейнеров"
        echo "  docker-compose down             # Остановить все"
        echo "  docker-compose restart          # Перезапустить"
        ;;
        
    2)
        echo ""
        echo "Запуск только бота (SQLite)..."
        
        # Изменение DATABASE_URL для SQLite
        export DATABASE_URL="sqlite+aiosqlite:///./data/bot.db"
        
        docker-compose up -d bot monitor
        
        echo ""
        echo -e "${GREEN}✓ Бот запущен!${NC}"
        ;;
        
    3)
        echo ""
        echo "Пересборка и перезапуск..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo -e "${GREEN}✓ Готово!${NC}"
        ;;
        
    4)
        echo ""
        echo "Остановка контейнеров..."
        docker-compose down
        echo -e "${GREEN}✓ Контейнеры остановлены${NC}"
        ;;
        
    5)
        echo ""
        echo "Выберите контейнер:"
        echo "1) Bot"
        echo "2) Monitor"
        echo "3) Database"
        echo "4) Все вместе"
        read -p "Ваш выбор (1-4): " log_choice
        
        case $log_choice in
            1) docker-compose logs -f bot ;;
            2) docker-compose logs -f monitor ;;
            3) docker-compose logs -f db ;;
            4) docker-compose logs -f ;;
        esac
        ;;
        
    *)
        echo -e "${RED}Неверный выбор${NC}"
        exit 1
        ;;
esac

echo ""
echo "Готово! 🚀"

