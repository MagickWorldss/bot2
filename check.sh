#!/bin/bash

# Скрипт быстрой проверки проекта

echo "=========================================="
echo "  Проверка проекта Telegram Bot"
echo "=========================================="
echo ""

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# 1. Проверка Python
echo "1. Проверка Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python установлен: $PYTHON_VERSION${NC}"
    
    # Проверка версии
    VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$VERSION >= 3.11" | bc -l) )); then
        echo -e "${GREEN}✓ Версия Python подходит (требуется 3.11+)${NC}"
    else
        echo -e "${YELLOW}⚠ Версия Python $VERSION (рекомендуется 3.11+)${NC}"
    fi
else
    echo -e "${RED}✗ Python не найден${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 2. Проверка структуры проекта
echo "2. Проверка структуры проекта..."
REQUIRED_FILES=("main.py" "config.py" "requirements.txt" "Dockerfile" "docker-compose.yml")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file не найден${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

REQUIRED_DIRS=("database" "services" "handlers" "middleware" "utils")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ $dir/${NC}"
    else
        echo -e "${RED}✗ $dir/ не найдена${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# 3. Проверка .env файла
echo "3. Проверка .env файла..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env файл найден${NC}"
    
    # Проверка обязательных переменных
    REQUIRED_VARS=("BOT_TOKEN" "ADMIN_IDS" "MASTER_WALLET_PUBLIC_KEY" "MASTER_WALLET_PRIVATE_KEY")
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^$var=" .env; then
            VALUE=$(grep "^$var=" .env | cut -d '=' -f2)
            if [ -z "$VALUE" ] || [ "$VALUE" = "your_" ] || [[ "$VALUE" == your_* ]]; then
                echo -e "${YELLOW}⚠ $var не заполнен${NC}"
            else
                echo -e "${GREEN}✓ $var заполнен${NC}"
            fi
        else
            echo -e "${RED}✗ $var отсутствует${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    done
else
    echo -e "${YELLOW}⚠ .env файл не найден (создайте из .env.example)${NC}"
fi
echo ""

# 4. Проверка зависимостей
echo "4. Проверка зависимостей Python..."
if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✓ requirements.txt найден${NC}"
    
    # Попытка проверить установку (если venv активен)
    if command -v pip &> /dev/null; then
        echo "  Проверка установленных пакетов..."
        
        # Ключевые пакеты
        KEY_PACKAGES=("aiogram" "sqlalchemy" "solana" "cryptography")
        for pkg in "${KEY_PACKAGES[@]}"; do
            if pip show $pkg &> /dev/null; then
                VERSION=$(pip show $pkg | grep Version | cut -d ' ' -f2)
                echo -e "  ${GREEN}✓ $pkg ($VERSION)${NC}"
            else
                echo -e "  ${YELLOW}⚠ $pkg не установлен${NC}"
            fi
        done
    fi
else
    echo -e "${RED}✗ requirements.txt не найден${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 5. Проверка Docker
echo "5. Проверка Docker (опционально)..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker установлен: $DOCKER_VERSION${NC}"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        echo -e "${GREEN}✓ Docker Compose установлен: $COMPOSE_VERSION${NC}"
    else
        echo -e "${YELLOW}⚠ Docker Compose не установлен${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Docker не установлен (опционально для разработки)${NC}"
fi
echo ""

# 6. Компиляция Python файлов
echo "6. Проверка синтаксиса Python..."
if command -v python3 &> /dev/null; then
    PYTHON_FILES=("main.py" "config.py" "init_db.py" "create_wallet.py")
    COMPILE_ERRORS=0
    
    for file in "${PYTHON_FILES[@]}"; do
        if [ -f "$file" ]; then
            if python3 -m py_compile "$file" 2>/dev/null; then
                echo -e "${GREEN}✓ $file${NC}"
            else
                echo -e "${RED}✗ $file имеет синтаксические ошибки${NC}"
                COMPILE_ERRORS=$((COMPILE_ERRORS + 1))
            fi
        fi
    done
    
    if [ $COMPILE_ERRORS -eq 0 ]; then
        echo -e "${GREEN}✓ Все файлы компилируются без ошибок${NC}"
    else
        echo -e "${RED}✗ Найдено ошибок компиляции: $COMPILE_ERRORS${NC}"
        ERRORS=$((ERRORS + COMPILE_ERRORS))
    fi
fi
echo ""

# 7. Проверка документации
echo "7. Проверка документации..."
DOC_FILES=("README.md" "START_HERE.md" "QUICKSTART.md" "START_ON_HOSTING.md")
for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${YELLOW}⚠ $file не найден${NC}"
    fi
done
echo ""

# Итоговый отчет
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!${NC}"
    echo ""
    echo "Проект готов к использованию! 🚀"
    echo ""
    echo "Следующие шаги:"
    echo "1. Создайте .env файл (если еще нет)"
    echo "2. Запустите: python3 create_wallet.py"
    echo "3. Заполните .env своими данными"
    echo "4. Запустите: python3 init_db.py"
    echo "5. Запустите: python3 main.py"
    echo ""
    echo "Или для Docker:"
    echo "1. Создайте .env"
    echo "2. Запустите: ./deploy.sh"
else
    echo -e "${RED}⚠ НАЙДЕНО ПРОБЛЕМ: $ERRORS${NC}"
    echo ""
    echo "Исправьте ошибки и запустите проверку снова"
fi
echo "=========================================="

