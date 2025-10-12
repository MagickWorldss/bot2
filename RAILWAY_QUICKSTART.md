# ⚡ Railway.app - Быстрый старт

## 🎯 Запуск бота за 5 минут!

### Шаг 1: Подготовка (2 минуты)

```bash
# 1. Создайте кошелек
python create_wallet.py
# Сохраните ключи!

# 2. Получите BOT_TOKEN от @BotFather
# 3. Получите ваш ID от @userinfobot
```

### Шаг 2: GitHub (1 минута)

```bash
git init
git add .
git commit -m "Deploy to Railway"

# Создайте репо на github.com/new
git remote add origin https://github.com/ваш_username/bot2.git
git push -u origin main
```

### Шаг 3: Railway (2 минуты)

1. **Зайдите**: [railway.app](https://railway.app)

2. **New Project** → **Deploy from GitHub repo**

3. **Выберите** ваш репозиторий `bot2`

4. **Добавьте PostgreSQL**:
   - New → Database → Add PostgreSQL

5. **Добавьте переменные**:
   Settings → Variables → вставьте:

```env
BOT_TOKEN=ваш_токен
ADMIN_IDS=ваш_id
SOLANA_RPC_URL=https://api.devnet.solana.com
MASTER_WALLET_PUBLIC_KEY=ваш_ключ
MASTER_WALLET_PRIVATE_KEY=ваш_ключ
MIN_DEPOSIT_SOL=0.01
IMAGE_PRICE_SOL=0.05
WITHDRAWAL_FEE_PERCENT=2
```

6. **Deploy!** - Railway автоматически задеплоит

### Шаг 4: Worker (30 секунд)

1. **New** → **Empty Service**
2. **Settings** → **Source** → выберите тот же репо
3. **Start Command**: `python monitor_transactions.py`
4. **Variables** → скопируйте все из основного сервиса

### Шаг 5: Инициализация (30 секунд)

```bash
# Установите Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link проекта
railway link

# Инициализация БД
railway run python init_db.py
```

### Шаг 6: Проверка

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте `/start`

## ✅ ГОТОВО! 🎉

Ваш бот работает 24/7!

---

## 📋 Что дальше?

1. **Получите тестовые SOL**:
   - https://faucet.solana.com/
   - Вставьте ваш MASTER_WALLET_PUBLIC_KEY

2. **Добавьте товары**:
   - `/admin` → ➕ Добавить товар

3. **Мониторьте**:
   - Railway Dashboard → Logs

---

## 🔗 Полная документация

- 📖 **RAILWAY_DEPLOY.md** - детальная инструкция
- 📖 **START_HERE.md** - общее руководство
- 📖 **ADMIN_GUIDE.md** - функции администратора

---

## 💰 Стоимость

- **$5** бесплатных кредитов при регистрации
- **$5/месяц** Hobby Plan
- Достаточно для одного бота

---

## 🆘 Проблемы?

```bash
# Логи
railway logs

# Перезапуск
railway restart

# Переменные
railway variables
```

Или смотрите **RAILWAY_DEPLOY.md** → Решение проблем

---

**🚂 Railway.app - Самый простой способ!** 🚀

