#!/bin/bash

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Создайте файл .env на основе .env.example"
    echo "💡 Скопируйте .env.example в .env и заполните переменные:"
    echo "   cp .env.example .env"
    exit 1
fi

# Проверяем основные переменные
source .env

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN не установлен в .env файле!"
    exit 1
fi

if [ -z "$ADMIN_ID" ]; then
    echo "❌ ADMIN_ID не установлен в .env файле!"
    exit 1
fi

echo "✅ Переменные окружения проверены"
echo "🚀 Запускаем бота..."

# Создаем директорию для данных
mkdir -p data

# Запускаем Docker Compose
docker-compose up -d --build