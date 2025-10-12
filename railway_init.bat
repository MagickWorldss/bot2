@echo off
chcp 65001 >nul
echo ==========================================
echo   Инициализация БД на Railway
echo ==========================================
echo.

echo Выполнение команды...
echo.

npx @railway/cli login

echo.
echo Теперь подключаемся к проекту...
npx @railway/cli link

echo.
echo Инициализация базы данных...
npx @railway/cli run python init_db.py

echo.
echo ==========================================
echo   ✅ Готово!
echo ==========================================
echo.
echo Теперь проверьте бота в Telegram:
echo 1. Найдите: @astra_shop_bot
echo 2. Отправьте: /start
echo.
pause

