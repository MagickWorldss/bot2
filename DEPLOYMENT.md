# Руководство по развертыванию

## Развертывание на Linux сервере (Ubuntu/Debian)

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Установка дополнительных пакетов
sudo apt install git nginx certbot python3-certbot-nginx -y
```

### 2. Создание пользователя для бота

```bash
# Создание пользователя
sudo useradd -m -s /bin/bash botuser

# Переключение на пользователя
sudo su - botuser
```

### 3. Клонирование и настройка

```bash
# Клонирование репозитория
git clone <your-repo-url> bot2
cd bot2

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Настройка .env

```bash
# Копирование примера
cp .env.example .env

# Редактирование (используйте nano, vim или любой другой редактор)
nano .env
```

Заполните все необходимые данные в `.env`.

### 5. Инициализация базы данных

```bash
# Создание таблиц и начальных данных
python init_db.py
```

### 6. Настройка systemd сервисов

```bash
# Выход из пользователя botuser
exit

# Создание директории для логов
sudo mkdir -p /var/log/telegram-bot
sudo chown botuser:botuser /var/log/telegram-bot

# Копирование service файлов
sudo cp /home/botuser/bot2/bot.service /etc/systemd/system/
sudo cp /home/botuser/bot2/monitor.service /etc/systemd/system/

# Редактирование service файлов
sudo nano /etc/systemd/system/bot.service
# Замените YOUR_USER на botuser
# Замените /path/to/bot2 на /home/botuser/bot2

sudo nano /etc/systemd/system/monitor.service
# Замените YOUR_USER на botuser
# Замените /path/to/bot2 на /home/botuser/bot2

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение и запуск сервисов
sudo systemctl enable bot.service
sudo systemctl enable monitor.service
sudo systemctl start bot.service
sudo systemctl start monitor.service

# Проверка статуса
sudo systemctl status bot.service
sudo systemctl status monitor.service
```

### 7. Просмотр логов

```bash
# Логи основного бота
sudo tail -f /var/log/telegram-bot/bot.log

# Логи монитора транзакций
sudo tail -f /var/log/telegram-bot/monitor.log

# Логи ошибок
sudo tail -f /var/log/telegram-bot/bot-error.log
sudo tail -f /var/log/telegram-bot/monitor-error.log

# Или через journalctl
sudo journalctl -u bot.service -f
sudo journalctl -u monitor.service -f
```

### 8. Управление сервисами

```bash
# Остановка
sudo systemctl stop bot.service
sudo systemctl stop monitor.service

# Запуск
sudo systemctl start bot.service
sudo systemctl start monitor.service

# Перезапуск
sudo systemctl restart bot.service
sudo systemctl restart monitor.service

# Отключение автозапуска
sudo systemctl disable bot.service
sudo systemctl disable monitor.service
```

## Развертывание с Docker

### 1. Создание Dockerfile

Создайте файл `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директории для изображений
RUN mkdir -p images

# Команда по умолчанию
CMD ["python", "main.py"]
```

### 2. Создание docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: telegram_bot
    restart: always
    volumes:
      - ./images:/app/images
      - ./bot.db:/app/bot.db
      - ./wallet_encryption.key:/app/wallet_encryption.key
    env_file:
      - .env
    depends_on:
      - db

  monitor:
    build: .
    container_name: telegram_monitor
    restart: always
    command: python monitor_transactions.py
    volumes:
      - ./images:/app/images
      - ./bot.db:/app/bot.db
      - ./wallet_encryption.key:/app/wallet_encryption.key
    env_file:
      - .env
    depends_on:
      - db

  db:
    image: postgres:15
    container_name: telegram_db
    restart: always
    environment:
      POSTGRES_DB: botdb
      POSTGRES_USER: botuser
      POSTGRES_PASSWORD: your_secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### 3. Запуск через Docker

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Перезапуск
docker-compose restart
```

## Использование PostgreSQL вместо SQLite

### 1. Установка PostgreSQL

```bash
sudo apt install postgresql postgresql-contrib -y
```

### 2. Создание базы данных

```bash
# Переключение на пользователя postgres
sudo -u postgres psql

# В psql:
CREATE DATABASE botdb;
CREATE USER botuser WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE botdb TO botuser;
\q
```

### 3. Обновление .env

```env
DATABASE_URL=postgresql+asyncpg://botuser:your_secure_password@localhost/botdb
```

### 4. Установка драйвера

```bash
pip install asyncpg
```

## Настройка Nginx (опционально, для webhook)

Если вы хотите использовать webhook вместо polling:

### 1. Создание конфигурации Nginx

```bash
sudo nano /etc/nginx/sites-available/telegram-bot
```

Содержимое:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /webhook {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Активация конфигурации

```bash
sudo ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Получение SSL сертификата

```bash
sudo certbot --nginx -d your-domain.com
```

## Мониторинг и обслуживание

### 1. Настройка автоматических бэкапов

Создайте скрипт `/home/botuser/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/botuser/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Бэкап базы данных
cp /home/botuser/bot2/bot.db $BACKUP_DIR/bot_$DATE.db

# Бэкап изображений
tar -czf $BACKUP_DIR/images_$DATE.tar.gz /home/botuser/bot2/images/

# Удаление старых бэкапов (старше 7 дней)
find $BACKUP_DIR -name "bot_*.db" -mtime +7 -delete
find $BACKUP_DIR -name "images_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Сделайте скрипт исполняемым:

```bash
chmod +x /home/botuser/backup.sh
```

Добавьте в crontab (выполнение каждый день в 3:00):

```bash
crontab -e

# Добавьте строку:
0 3 * * * /home/botuser/backup.sh >> /home/botuser/backup.log 2>&1
```

### 2. Мониторинг ресурсов

Установите htop для мониторинга:

```bash
sudo apt install htop -y
htop
```

### 3. Настройка алертов

Установите monit для мониторинга сервисов:

```bash
sudo apt install monit -y
```

Создайте конфигурацию `/etc/monit/conf.d/telegram-bot`:

```
check process telegram_bot with pidfile /run/telegram-bot.pid
    start program = "/bin/systemctl start bot.service"
    stop program = "/bin/systemctl stop bot.service"
    if failed host 127.0.0.1 port 8080 then restart
    if 5 restarts within 5 cycles then alert
```

## Обновление бота

```bash
# Переключение на пользователя botuser
sudo su - botuser
cd bot2

# Активация виртуального окружения
source venv/bin/activate

# Получение обновлений
git pull

# Обновление зависимостей
pip install -r requirements.txt --upgrade

# Выход из пользователя
exit

# Перезапуск сервисов
sudo systemctl restart bot.service
sudo systemctl restart monitor.service
```

## Безопасность

### 1. Настройка firewall

```bash
# Установка ufw
sudo apt install ufw -y

# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включение firewall
sudo ufw enable
```

### 2. Защита от DDoS (fail2ban)

```bash
# Установка
sudo apt install fail2ban -y

# Создание конфигурации
sudo nano /etc/fail2ban/jail.local
```

Содержимое:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
```

```bash
# Запуск
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Регулярные обновления

```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

## Troubleshooting

### Проблема: Сервис не запускается

```bash
# Проверка логов
sudo journalctl -u bot.service -n 50 --no-pager

# Проверка прав доступа
ls -la /home/botuser/bot2

# Проверка виртуального окружения
/home/botuser/bot2/venv/bin/python --version
```

### Проблема: База данных заблокирована (SQLite)

```bash
# Остановка всех сервисов
sudo systemctl stop bot.service
sudo systemctl stop monitor.service

# Проверка блокировок
lsof /home/botuser/bot2/bot.db

# Запуск сервисов
sudo systemctl start bot.service
sudo systemctl start monitor.service
```

### Проблема: Не хватает памяти

```bash
# Добавление swap файла
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Добавление в fstab для автозагрузки
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## Рекомендации по продакшену

1. **Используйте PostgreSQL** вместо SQLite для лучшей производительности
2. **Настройте мониторинг** (Prometheus + Grafana)
3. **Используйте load balancer** при высокой нагрузке
4. **Регулярно делайте бэкапы**
5. **Используйте отдельный RPC endpoint** для Solana (не публичный)
6. **Храните логи** в централизованной системе (ELK stack)
7. **Настройте алерты** для критичных событий
8. **Используйте Redis** для кэширования
9. **Оптимизируйте запросы** к базе данных
10. **Регулярно обновляйте** зависимости

## Полезные команды

```bash
# Проверка использования диска
df -h

# Проверка использования памяти
free -h

# Просмотр активных процессов
ps aux | grep python

# Проверка сетевых подключений
netstat -tulpn

# Очистка логов
sudo truncate -s 0 /var/log/telegram-bot/*.log
```

