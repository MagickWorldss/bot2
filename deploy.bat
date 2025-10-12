@echo off
chcp 65001 >nul
echo ==========================================
echo   Telegram Shop Bot - Deployment Script
echo ==========================================
echo.

REM Проверка Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не установлен!
    echo Установите Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose не установлен!
    pause
    exit /b 1
)

echo ✓ Docker установлен
echo ✓ Docker Compose установлен
echo.

REM Проверка .env файла
if not exist .env (
    echo ⚠️  .env файл не найден
    echo.
    set /p create_env="Создать .env файл? (y/n): "
    if /i "%create_env%"=="y" (
        (
            echo # Telegram
            echo BOT_TOKEN=
            echo ADMIN_IDS=
            echo.
            echo # Database
            echo DATABASE_URL=postgresql+asyncpg://botuser:changeme@db:5432/botdb
            echo.
            echo # PostgreSQL
            echo POSTGRES_DB=botdb
            echo POSTGRES_USER=botuser
            echo POSTGRES_PASSWORD=changeme
            echo.
            echo # Solana
            echo SOLANA_RPC_URL=https://api.devnet.solana.com
            echo MASTER_WALLET_PUBLIC_KEY=
            echo MASTER_WALLET_PRIVATE_KEY=
            echo.
            echo # Settings
            echo MIN_DEPOSIT_SOL=0.01
            echo IMAGE_PRICE_SOL=0.05
            echo WITHDRAWAL_FEE_PERCENT=2
        ) > .env
        echo ✓ .env файл создан
        echo ⚠️  Заполните .env файл своими данными и запустите скрипт снова
        pause
        exit /b 0
    )
    exit /b 1
)

echo ✓ .env файл найден
echo.

REM Создание директорий
echo Создание директорий...
if not exist images mkdir images
if not exist data mkdir data
if not exist logs mkdir logs
echo ✓ Директории созданы
echo.

REM Меню
echo Выберите режим развертывания:
echo 1) Полное развертывание (PostgreSQL + Bot + Monitor)
echo 2) Только бот (SQLite)
echo 3) Пересобрать и перезапустить
echo 4) Остановить все контейнеры
echo 5) Просмотр логов
echo.
set /p mode="Ваш выбор (1-5): "

if "%mode%"=="1" (
    echo.
    echo Запуск полного развертывания...
    echo.
    
    echo Сборка Docker образов...
    docker-compose build
    
    echo.
    echo Запуск контейнеров...
    docker-compose up -d
    
    echo.
    echo ✓ Контейнеры запущены!
    echo.
    echo Подождите 10 секунд для инициализации БД...
    timeout /t 10 /nobreak >nul
    
    echo.
    echo Инициализация базы данных...
    docker-compose exec bot python init_db.py
    
    echo.
    echo ==========================================
    echo ✓ Развертывание завершено!
    echo ==========================================
    echo.
    echo Полезные команды:
    echo   docker-compose logs -f bot      # Логи бота
    echo   docker-compose logs -f monitor  # Логи монитора
    echo   docker-compose ps               # Статус контейнеров
    echo   docker-compose down             # Остановить все
    echo   docker-compose restart          # Перезапустить
    
) else if "%mode%"=="2" (
    echo.
    echo Запуск только бота (SQLite)...
    docker-compose up -d bot monitor
    echo.
    echo ✓ Бот запущен!
    
) else if "%mode%"=="3" (
    echo.
    echo Пересборка и перезапуск...
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    echo ✓ Готово!
    
) else if "%mode%"=="4" (
    echo.
    echo Остановка контейнеров...
    docker-compose down
    echo ✓ Контейнеры остановлены
    
) else if "%mode%"=="5" (
    echo.
    echo Выберите контейнер:
    echo 1) Bot
    echo 2) Monitor
    echo 3) Database
    echo 4) Все вместе
    echo.
    set /p log_choice="Ваш выбор (1-4): "
    
    if "%log_choice%"=="1" docker-compose logs -f bot
    if "%log_choice%"=="2" docker-compose logs -f monitor
    if "%log_choice%"=="3" docker-compose logs -f db
    if "%log_choice%"=="4" docker-compose logs -f
    
) else (
    echo Неверный выбор
    pause
    exit /b 1
)

echo.
echo Готово! 🚀
pause

