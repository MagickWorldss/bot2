@echo off
chcp 65001 >nul
REM Скрипт инициализации базы данных

set PYTHON=C:\Users\Smokier\AppData\Local\Programs\Python\Python312\python.exe

echo ==========================================
echo   Инициализация базы данных
echo ==========================================
echo.

%PYTHON% init_db.py

echo.
echo ==========================================
echo   ✓ База данных инициализирована!
echo ==========================================
echo.
echo Теперь можете запустить бота:
echo   run.bat             (основной бот)
echo   run_monitor.bat     (монитор транзакций)
echo.
pause

