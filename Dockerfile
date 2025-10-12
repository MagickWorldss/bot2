FROM python:3.11-slim

# Метаданные
LABEL maintainer="Telegram Shop Bot"
LABEL description="Telegram bot for selling digital products with Solana payments"

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование всех файлов проекта
COPY . .

# Создание необходимых директорий
RUN mkdir -p images data logs

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Telegram bot не нуждается в healthcheck
# Railway автоматически мониторит процесс

# Команда по умолчанию (использует start.py для автоинициализации)
CMD ["python", "start.py"]

