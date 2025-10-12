#!/bin/bash

# Скрипт для загрузки бота на сервер

echo "=========================================="
echo "  Загрузка бота на сервер"
echo "=========================================="
echo ""

# Запрос данных сервера
read -p "IP адрес сервера: " SERVER_IP
read -p "SSH пользователь (по умолчанию root): " SSH_USER
SSH_USER=${SSH_USER:-root}
read -p "Директория на сервере (по умолчанию /root/bot2): " SERVER_DIR
SERVER_DIR=${SERVER_DIR:-/root/bot2}

echo ""
echo "Загружаем на: $SSH_USER@$SERVER_IP:$SERVER_DIR"
echo ""

# Создание директории на сервере
echo "Создание директории на сервере..."
ssh $SSH_USER@$SERVER_IP "mkdir -p $SERVER_DIR"

# Исключаем ненужные файлы
echo "Создание архива..."
tar --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='*.db' \
    --exclude='*.log' \
    --exclude='images' \
    --exclude='.env' \
    -czf bot2.tar.gz .

# Загрузка на сервер
echo "Загрузка на сервер..."
scp bot2.tar.gz $SSH_USER@$SERVER_IP:$SERVER_DIR/

# Распаковка на сервере
echo "Распаковка на сервере..."
ssh $SSH_USER@$SERVER_IP "cd $SERVER_DIR && tar -xzf bot2.tar.gz && rm bot2.tar.gz"

# Удаление локального архива
rm bot2.tar.gz

echo ""
echo "✓ Файлы загружены!"
echo ""
echo "Следующие шаги:"
echo "1. Подключитесь к серверу: ssh $SSH_USER@$SERVER_IP"
echo "2. Перейдите в директорию: cd $SERVER_DIR"
echo "3. Создайте .env файл: nano .env"
echo "4. Запустите развертывание: ./deploy.sh"
echo ""
echo "Или выполните все команды сразу:"
echo "ssh $SSH_USER@$SERVER_IP 'cd $SERVER_DIR && nano .env && ./deploy.sh'"

