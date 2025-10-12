# ⚡ Windows → Railway - СУПЕР-БЫСТРАЯ ИНСТРУКЦИЯ

## 🎯 За 15 минут - Бот в облаке!

---

## 1️⃣ УСТАНОВКА (5 минут)

### Скачайте и установите:

1. **Git**: https://git-scm.com/download/win
   - Качаем → Устанавливаем → Next везде

2. **Node.js**: https://nodejs.org/
   - Качаем LTS → Устанавливаем → Next везде

3. **Перезапустите PowerShell** (обязательно!)

---

## 2️⃣ ПОДГОТОВКА (5 минут)

### В PowerShell (в папке `C:\dev\tg\bot2`):

```powershell
# 1. Создать кошелек
python create_wallet.py
# ⚠️ СОХРАНИТЕ КЛЮЧИ В БЛОКНОТ!

# 2. Настроить Git
git config --global user.name "Ваше Имя"
git config --global user.email "ваш_email@mail.com"

# 3. Загрузить на GitHub
git init
git add .
git commit -m "Deploy"
```

### Telegram:

1. **@BotFather** → `/newbot` → Создать бота → **Скопировать TOKEN**
2. **@userinfobot** → `/start` → **Скопировать ID**

### GitHub:

1. **github.com** → Sign up → Создать аккаунт
2. **New repository** → Название: `bot2` → Create
3. **Скопировать** команду `git remote add origin ...`

### В PowerShell:

```powershell
# Вставьте скопированную команду:
git remote add origin https://github.com/ваш_username/bot2.git

# Загрузите код:
git branch -M main
git push -u origin main
```

---

## 3️⃣ RAILWAY (5 минут)

### 1. Создать проект:

1. **railway.app** → Login with GitHub
2. **New Project** → Deploy from GitHub repo → Выбрать `bot2`
3. Подождать сборку (2-3 минуты)

### 2. Добавить базу:

1. **New** → **Database** → **Add PostgreSQL**

### 3. Добавить переменные:

1. Нажать на блок бота
2. **Settings** → **Variables** → **Raw Editor**
3. Вставить (свои данные!):

```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_IDS=ваш_id
SOLANA_RPC_URL=https://api.devnet.solana.com
MASTER_WALLET_PUBLIC_KEY=ваш_публичный_ключ
MASTER_WALLET_PRIVATE_KEY=ваш_приватный_ключ
MIN_DEPOSIT_SOL=0.01
IMAGE_PRICE_SOL=0.05
WITHDRAWAL_FEE_PERCENT=2
```

4. **Update Variables**

### 4. Создать Worker:

1. **New** → **Empty Service**
2. **Settings** → **Source** → выбрать `bot2`
3. **Start Command**: `python monitor_transactions.py`
4. **Variables** → скопировать все из основного бота

### 5. Инициализация:

```powershell
# Установить Railway CLI
npm install -g @railway/cli

# Войти
railway login

# Подключиться
railway link

# Инициализировать БД
railway run python init_db.py
```

---

## ✅ ПРОВЕРКА

**Telegram** → Найти бота → `/start` → Должно прийти приветствие!

---

## 🎉 ГОТОВО!

Бот работает 24/7! 🚀

**Полная инструкция**: `WINDOWS_RAILWAY_GUIDE.md`

---

## 🆘 НЕ РАБОТАЕТ?

```powershell
# Логи
railway logs

# Перезапуск
railway restart
```

Или смотрите: **WINDOWS_RAILWAY_GUIDE.md** (там все подробно!)

