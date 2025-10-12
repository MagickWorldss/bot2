@echo off
chcp 65001 >nul
REM Скрипт настройки проекта для Windows

set PYTHON=C:\Users\Smokier\AppData\Local\Programs\Python\Python312\python.exe

echo ==========================================
echo   Настройка Telegram Shop Bot
echo ==========================================
echo.

echo 1. Установка зависимостей...
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install -r requirements.txt

echo.
echo ✓ Зависимости установлены!
echo.

echo 2. Создание Solana кошелька...
%PYTHON% create_wallet.py

echo.
echo ==========================================
echo   ✓ Настройка завершена!
echo ==========================================
echo.
echo Следующие шаги:
echo 1. Создайте .env файл
echo 2. Добавьте BOT_TOKEN и ADMIN_IDS
echo 3. Добавьте ключи кошелька
echo 4. Запустите: init.bat
echo.
pause

