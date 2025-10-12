# 🌐 Руководство по размещению на хостинге

Это руководство покажет как разместить бота на различных хостингах для работы 24/7.

## 🚀 Быстрый старт (Docker)

### Вариант 1: Один клик (Windows)

```bash
deploy.bat
```

### Вариант 2: Один клик (Linux/Mac)

```bash
chmod +x deploy.sh
./deploy.sh
```

Скрипт автоматически:
- Проверит Docker
- Создаст .env если нужно
- Соберет образы
- Запустит контейнеры
- Инициализирует БД

## 📋 Подготовка

### 1. Создайте .env файл

```env
# Telegram
BOT_TOKEN=ваш_токен
ADMIN_IDS=ваш_id

# Database (для Docker с PostgreSQL)
DATABASE_URL=postgresql+asyncpg://botuser:changeme@db:5432/botdb
POSTGRES_DB=botdb
POSTGRES_USER=botuser
POSTGRES_PASSWORD=changeme

# Solana
SOLANA_RPC_URL=https://api.devnet.solana.com
MASTER_WALLET_PUBLIC_KEY=ваш_ключ
MASTER_WALLET_PRIVATE_KEY=ваш_ключ

# Settings
MIN_DEPOSIT_SOL=0.01
IMAGE_PRICE_SOL=0.05
WITHDRAWAL_FEE_PERCENT=2
```

### 2. Создайте кошелек (если еще нет)

```bash
python create_wallet.py
```

## 🐳 Docker развертывание

### Локальное тестирование

```bash
# Сборка
docker-compose build

# Запуск
docker-compose up -d

# Инициализация БД
docker-compose exec bot python init_db.py

# Логи
docker-compose logs -f

# Остановка
docker-compose down
```

### Продакшен с PostgreSQL

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Логи бота
docker-compose logs -f bot

# Логи монитора
docker-compose logs -f monitor
```

## 🌍 Популярные хостинги

### 1. DigitalOcean (Рекомендуется)

**Цена**: от $6/месяц (Droplet 1GB RAM)

**Шаги:**

1. **Создайте Droplet**
   - OS: Ubuntu 22.04 LTS
   - План: Basic ($6)
   - Регион: ближайший к вам

2. **Подключитесь по SSH**
   ```bash
   ssh root@ваш_ip
   ```

3. **Установите Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   chmod +x /usr/local/bin/docker-compose
   ```

4. **Клонируйте проект**
   ```bash
   git clone ваш_репозиторий
   cd bot2
   ```

5. **Настройте .env**
   ```bash
   nano .env
   # Вставьте настройки, Ctrl+X для сохранения
   ```

6. **Запустите**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

**Готово!** Бот работает 24/7

### 2. Hetzner Cloud

**Цена**: от €4.15/месяц (CX11)

Аналогично DigitalOcean, но дешевле:

```bash
# После создания сервера
ssh root@ваш_ip

# Установка Docker (см. выше)

# Клонирование и запуск
git clone ваш_репозиторий
cd bot2
nano .env  # настройте
chmod +x deploy.sh
./deploy.sh
```

### 3. AWS EC2

**Цена**: Free Tier (первый год) или от $5/месяц

1. Создайте EC2 инстанс (t2.micro)
2. OS: Ubuntu 22.04
3. Security Group: открыть порт 22 (SSH)
4. Подключитесь и установите Docker
5. Клонируйте, настройте, запустите

### 4. Google Cloud Platform

**Цена**: $300 бесплатных кредитов или от $5/месяц

1. Создайте Compute Engine VM
2. Ubuntu 22.04, e2-micro
3. SSH подключение
4. Установите Docker
5. Разверните бота

### 5. Railway.app (Самый простой)

**Цена**: от $5/месяц

1. Зарегистрируйтесь на [Railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Выберите ваш репозиторий
4. Railway автоматически определит Dockerfile
5. Добавьте переменные окружения в настройках
6. Deploy!

**Плюсы**: автоматическое развертывание, логи, мониторинг
**Минусы**: дороже чем VPS

### 6. Render.com

**Цена**: от $7/месяц

Аналогично Railway:

1. [Render.com](https://render.com) → New Web Service
2. Подключите GitHub
3. Выберите Docker
4. Добавьте environment variables
5. Deploy

### 7. Fly.io

**Цена**: Free tier 256MB RAM или от $2/месяц

```bash
# Установите flyctl
curl -L https://fly.io/install.sh | sh

# Войдите
flyctl auth login

# В папке проекта
flyctl launch

# Deploy
flyctl deploy
```

## 🔧 VPS настройка (детально)

### Пошаговая инструкция для Ubuntu 22.04

#### 1. Первоначальная настройка

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка необходимых пакетов
apt install -y curl wget git nano

# Создание пользователя (опционально)
adduser botuser
usermod -aG sudo botuser
su - botuser
```

#### 2. Установка Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверка
docker --version
docker-compose --version

# Перелогиньтесь для применения изменений
exit
ssh user@server
```

#### 3. Клонирование проекта

```bash
# Через Git (если есть репозиторий)
git clone https://github.com/ваш_username/bot2.git
cd bot2

# Или загрузка через SCP/SFTP
# На локальной машине:
scp -r bot2/ user@server:/home/user/
```

#### 4. Настройка

```bash
# Создание .env
nano .env

# Вставьте настройки:
BOT_TOKEN=...
ADMIN_IDS=...
# и т.д.

# Сохраните: Ctrl+X, Y, Enter
```

#### 5. Запуск

```bash
# Сделайте скрипт исполняемым
chmod +x deploy.sh

# Запустите
./deploy.sh

# Выберите режим 1 (полное развертывание)
```

#### 6. Проверка

```bash
# Статус контейнеров
docker-compose ps

# Логи
docker-compose logs -f bot

# Проверка в Telegram
# Найдите бота и отправьте /start
```

## 📊 Мониторинг и управление

### Полезные команды Docker

```bash
# Просмотр логов
docker-compose logs -f              # Все сервисы
docker-compose logs -f bot          # Только бот
docker-compose logs -f monitor      # Только монитор
docker-compose logs --tail=100 bot  # Последние 100 строк

# Статус контейнеров
docker-compose ps

# Перезапуск
docker-compose restart
docker-compose restart bot          # Только бот

# Остановка
docker-compose stop
docker-compose down                 # С удалением контейнеров

# Обновление
git pull                            # Получить изменения
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Использование ресурсов
docker stats

# Вход в контейнер
docker-compose exec bot /bin/bash
```

### Автоматический перезапуск

Docker Compose автоматически перезапускает контейнеры при падении благодаря `restart: always`.

### Бэкапы

```bash
# Создайте скрипт backup.sh
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
tar -czf backups/backup_$DATE.tar.gz data/ images/ .env
echo "Backup created: backup_$DATE.tar.gz"
EOF

chmod +x backup.sh

# Добавьте в crontab (ежедневно в 3:00)
crontab -e
# Добавьте строку:
0 3 * * * /home/user/bot2/backup.sh
```

## 🔒 Безопасность

### 1. Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw enable
sudo ufw status
```

### 2. Fail2Ban

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Регулярные обновления

```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 4. SSH ключи

```bash
# На локальной машине
ssh-keygen -t rsa -b 4096

# Копирование ключа
ssh-copy-id user@server

# Отключите парольную аутентификацию
sudo nano /etc/ssh/sshd_config
# Установите: PasswordAuthentication no
sudo systemctl restart sshd
```

## 📈 Масштабирование

### Несколько инстансов бота

Для высокой нагрузки можно запустить несколько копий:

```yaml
# docker-compose.yml
services:
  bot1:
    build: .
    # ... настройки
  
  bot2:
    build: .
    # ... настройки
  
  # Load balancer (nginx)
  nginx:
    image: nginx:alpine
    # ... настройки
```

## 🆘 Troubleshooting

### Бот не запускается

```bash
# Проверьте логи
docker-compose logs bot

# Проверьте .env
cat .env

# Проверьте что контейнер запущен
docker-compose ps

# Перезапустите
docker-compose restart bot
```

### База данных не подключается

```bash
# Проверьте что PostgreSQL запущен
docker-compose ps db

# Логи БД
docker-compose logs db

# Проверьте DATABASE_URL в .env
```

### Нехватка памяти

```bash
# Проверьте использование
free -h
docker stats

# Добавьте swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Проблемы с Solana RPC

```bash
# Используйте приватный RPC
# В .env измените на:
SOLANA_RPC_URL=https://your-endpoint.quiknode.pro/...
```

## 💰 Сравнение хостингов

| Хостинг | Цена/месяц | Сложность | Гибкость | Рекомендация |
|---------|------------|-----------|----------|--------------|
| **Railway** | $5 | ⭐ | ⭐⭐ | Новички |
| **Render** | $7 | ⭐ | ⭐⭐ | Новички |
| **DigitalOcean** | $6 | ⭐⭐ | ⭐⭐⭐ | **Лучший выбор** |
| **Hetzner** | €4 | ⭐⭐ | ⭐⭐⭐ | Экономия |
| **AWS EC2** | $5+ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Энтерпрайз |
| **GCP** | $5+ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Энтерпрайз |
| **Fly.io** | $2+ | ⭐⭐ | ⭐⭐⭐ | Микросервисы |

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker-compose logs -f`
2. Смотрите раздел Troubleshooting
3. Создайте Issue на GitHub
4. Спросите в Telegram чате

## ✅ Чеклист развертывания

- [ ] VPS/хостинг выбран и оплачен
- [ ] Docker и Docker Compose установлены
- [ ] Проект скопирован на сервер
- [ ] .env файл создан и заполнен
- [ ] Solana кошелек создан
- [ ] `deploy.sh` запущен
- [ ] Логи проверены
- [ ] Бот отвечает в Telegram
- [ ] Мониторинг транзакций работает
- [ ] Настроены бэкапы
- [ ] Firewall настроен

## 🎉 Готово!

Ваш бот теперь работает 24/7 на хостинге! 🚀

**Не забудьте:**
- Регулярно делать бэкапы
- Следить за логами
- Обновлять зависимости
- Мониторить ресурсы

Удачи! 💪

