@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   Проверка проекта Telegram Bot
echo ==========================================
echo.

set ERRORS=0

REM 1. Проверка Python
echo 1. Проверка Python...
python --version >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo ✓ Python установлен: !PYTHON_VERSION!
) else (
    echo ✗ Python не найден
    set /a ERRORS+=1
)
echo.

REM 2. Проверка структуры проекта
echo 2. Проверка структуры проекта...
set FILES=main.py config.py requirements.txt Dockerfile docker-compose.yml
for %%f in (%FILES%) do (
    if exist %%f (
        echo ✓ %%f
    ) else (
        echo ✗ %%f не найден
        set /a ERRORS+=1
    )
)

set DIRS=database services handlers middleware utils
for %%d in (%DIRS%) do (
    if exist %%d\ (
        echo ✓ %%d\
    ) else (
        echo ✗ %%d\ не найдена
        set /a ERRORS+=1
    )
)
echo.

REM 3. Проверка .env файла
echo 3. Проверка .env файла...
if exist .env (
    echo ✓ .env файл найден
    
    findstr /C:"BOT_TOKEN=" .env >nul
    if %errorlevel%==0 (
        echo ✓ BOT_TOKEN присутствует
    ) else (
        echo ✗ BOT_TOKEN отсутствует
        set /a ERRORS+=1
    )
    
    findstr /C:"ADMIN_IDS=" .env >nul
    if %errorlevel%==0 (
        echo ✓ ADMIN_IDS присутствует
    ) else (
        echo ✗ ADMIN_IDS отсутствует
        set /a ERRORS+=1
    )
) else (
    echo ⚠ .env файл не найден (создайте из .env.example)
)
echo.

REM 4. Проверка зависимостей
echo 4. Проверка requirements.txt...
if exist requirements.txt (
    echo ✓ requirements.txt найден
) else (
    echo ✗ requirements.txt не найден
    set /a ERRORS+=1
)
echo.

REM 5. Проверка Docker
echo 5. Проверка Docker (опционально)...
docker --version >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('docker --version') do set DOCKER_VERSION=%%i
    echo ✓ Docker установлен: !DOCKER_VERSION!
    
    docker-compose --version >nul 2>&1
    if %errorlevel%==0 (
        for /f "tokens=*" %%i in ('docker-compose --version') do set COMPOSE_VERSION=%%i
        echo ✓ Docker Compose установлен: !COMPOSE_VERSION!
    ) else (
        echo ⚠ Docker Compose не установлен
    )
) else (
    echo ⚠ Docker не установлен (опционально для разработки)
)
echo.

REM 6. Компиляция Python файлов
echo 6. Проверка синтаксиса Python...
set COMPILE_ERRORS=0
set TEST_FILES=main.py config.py init_db.py create_wallet.py

for %%f in (%TEST_FILES%) do (
    if exist %%f (
        python -m py_compile %%f 2>nul
        if !errorlevel!==0 (
            echo ✓ %%f
        ) else (
            echo ✗ %%f имеет синтаксические ошибки
            set /a COMPILE_ERRORS+=1
        )
    )
)

if !COMPILE_ERRORS!==0 (
    echo ✓ Все файлы компилируются без ошибок
) else (
    echo ✗ Найдено ошибок компиляции: !COMPILE_ERRORS!
    set /a ERRORS+=!COMPILE_ERRORS!
)
echo.

REM 7. Проверка документации
echo 7. Проверка документации...
set DOC_FILES=README.md START_HERE.md QUICKSTART.md START_ON_HOSTING.md
for %%f in (%DOC_FILES%) do (
    if exist %%f (
        echo ✓ %%f
    ) else (
        echo ⚠ %%f не найден
    )
)
echo.

REM Итоговый отчет
echo ==========================================
if !ERRORS!==0 (
    echo ✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!
    echo.
    echo Проект готов к использованию! 🚀
    echo.
    echo Следующие шаги:
    echo 1. Создайте .env файл (если еще нет^)
    echo 2. Запустите: python create_wallet.py
    echo 3. Заполните .env своими данными
    echo 4. Запустите: python init_db.py
    echo 5. Запустите: python main.py
    echo.
    echo Или для Docker:
    echo 1. Создайте .env
    echo 2. Запустите: deploy.bat
) else (
    echo ⚠ НАЙДЕНО ПРОБЛЕМ: !ERRORS!
    echo.
    echo Исправьте ошибки и запустите проверку снова
)
echo ==========================================

pause

