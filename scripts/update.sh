#!/bin/bash

echo "🔄 Обновляем бота..."

# Останавливаем текущий контейнер
docker-compose down

# Получаем обновления (если используется git)
if [ -d ".git" ]; then
    echo "📥 Получаем обновления из git..."
    git pull
fi

# Пересобираем и запускаем
echo "🔨 Пересобираем контейнер..."
docker-compose up --build -d

echo "✅ Обновление завершено"
echo "📋 Проверить статус: docker-compose ps"
echo "📄 Посмотреть логи: docker-compose logs -f"