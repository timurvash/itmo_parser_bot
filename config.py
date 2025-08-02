import os

# Bot token from BotFather - вставьте свой токен сюда
BOT_TOKEN = "7229928084:AAFeSaAbV8RSM0CSe6R_zuR4MNSJKiGtZs0"

# URL for parsing
ITMO_URL = "https://abit.itmo.ru/ranking/bachelor/contract/2196"

# Your ID for tracking
YOUR_ID = "4154668"

# Database file
DB_FILE = "data/users.txt"
CSV_FILE = "data/ranking_history.csv"

# Headers for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Проверяем наличие токена
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("❌ ВНИМАНИЕ: Необходимо заменить YOUR_BOT_TOKEN_HERE на реальный токен бота!")
    print("📱 Получите токен у @BotFather в Telegram")
    print("🔧 Замените YOUR_BOT_TOKEN_HERE в файле config.py")
else:
    print(f"✅ Конфигурация загружена")
    print(f"📱 BOT_TOKEN: установлен ({BOT_TOKEN[:10]}...)")
    print(f"🔗 ITMO_URL: {ITMO_URL}")
    print(f"👤 YOUR_ID: {YOUR_ID}")