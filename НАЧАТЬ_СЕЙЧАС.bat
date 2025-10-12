@echo off
chcp 65001 >nul
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║            🚀 ФИНАЛЬНЫЙ ЗАПУСК БОТА 🚀                      ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo.
echo ✅ Все ошибки исправлены!
echo ✅ Все функции готовы!
echo ✅ Документация создана!
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo 🔥 14 ФУНКЦИЙ:
echo.
echo  • Реферальная система
echo  • Промокоды
echo  • Корзина
echo  • Достижения
echo  • Ежедневные бонусы
echo  • Квесты
echo  • Аукцион
echo  • Тикет-система
echo  • Уведомления
echo  • Сезонные события
echo  • Квизы
echo  • Таймер
echo  • Предзаказ
echo  • Рейтинг
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo 👑 СИСТЕМА РОЛЕЙ:
echo.
echo  • User (пользователь)
echo  • Seller (продавец)
echo  • Moderator (модератор)
echo  • Admin (администратор)
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo ⚠️ ВАЖНО! СНАЧАЛА СДЕЛАЙТЕ:
echo.
echo  1️⃣  Откройте Railway Dashboard
echo     https://railway.app/dashboard
echo.
echo  2️⃣  Добавьте переменные:
echo     • BOT_TOKEN (от @BotFather)
echo     • ADMIN_IDS (от @userinfobot)
echo     • MASTER_WALLET_PUBLIC_KEY
echo     • MASTER_WALLET_PRIVATE_KEY
echo     • Добавьте PostgreSQL (+New → Database → PostgreSQL)
echo.
echo  3️⃣  После этого вернитесь сюда!
echo.
echo ══════════════════════════════════════════════════════════════
echo.
pause
echo.
echo Открываю Railway Dashboard...
start https://railway.app/dashboard
echo.
echo ✅ После добавления переменных нажмите любую кнопку...
pause
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo 🚀 Загружаю код на Railway...
echo.
call update_railway.bat
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo ✅ ГОТОВО!
echo.
echo 📱 Проверьте бота через 5 минут:
echo    Telegram → @astra_shop_bot → /start
echo.
echo 📖 Документация:
echo    ВСЕ_ИСПРАВЛЕНИЯ_ГОТОВЫ.txt
echo.
pause

