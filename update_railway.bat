@echo off
chcp 65001 >nul
echo ==========================================
echo   Обновление бота на Railway
echo ==========================================
echo.

echo 1. Добавление изменений в Git...
git add .

echo.
echo 2. Создание коммита...
git commit -m "Add delete regions and cities functionality"

echo.
echo 3. Загрузка на GitHub...
git push

echo.
echo ==========================================
echo   ✅ Готово!
echo ==========================================
echo.
echo Railway автоматически обновит бота (2-3 минуты)
echo.
echo Изменения:
echo • Баланс отображается в ЕВРО
echo • Резервация курса на 30 минут
echo • Автоматическое истечение заявок
echo • Полное управление пользователями
echo • Удаление регионов и городов
echo • Автоматическая инициализация БД
echo.
echo Через 3 минуты проверьте:
echo   Telegram → @astra_shop_bot → /admin
echo.
pause

