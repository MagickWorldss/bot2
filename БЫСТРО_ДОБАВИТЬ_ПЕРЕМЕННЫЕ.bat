@echo off
chcp 65001 >nul
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║      ⚠️ НУЖНО ДОБАВИТЬ ПЕРЕМЕННЫЕ В RAILWAY! ⚠️            ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo.
echo Бот не запускается потому что не заполнены переменные!
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo 📋 ЧТО НУЖНО:
echo.
echo  1. BOT_TOKEN                    - токен от @BotFather
echo  2. ADMIN_IDS                    - ваш Telegram ID
echo  3. MASTER_WALLET_PRIVATE_KEY    - приватный ключ SOL
echo  4. MASTER_WALLET_PUBLIC_KEY     - публичный адрес SOL
echo  5. DATABASE_URL                 - Railway создаст сам
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo 🚀 КАК ДОБАВИТЬ:
echo.
echo  ШАГ 1: Откройте https://railway.app
echo  ШАГ 2: Войдите в ваш проект
echo  ШАГ 3: Нажмите на блок бота
echo  ШАГ 4: Вкладка "Variables"
echo  ШАГ 5: "+ New Variable" для каждой переменной
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo 📖 Подробная инструкция:
echo.
echo    ДОБАВИТЬ_ПЕРЕМЕННЫЕ_RAILWAY.txt
echo.
echo ══════════════════════════════════════════════════════════════
echo.
pause
echo.
echo Открываю Railway Dashboard...
start https://railway.app/dashboard
echo.
echo Открываю инструкцию...
start ДОБАВИТЬ_ПЕРЕМЕННЫЕ_RAILWAY.txt
echo.
echo ✅ Готово!
echo.
pause

