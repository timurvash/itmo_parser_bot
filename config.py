import os

# Bot token from BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# URL for parsing
ITMO_URL = os.getenv("ITMO_URL", "https://abit.itmo.ru/ranking/bachelor/contract/2196")

# Your ID for tracking
YOUR_ID = os.getenv("YOUR_ID", "4154668")

# Database file
DB_FILE = "data/users.txt"
CSV_FILE = "data/ranking_history.csv"

# Headers for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Проверяем наличие обязательных переменных
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    raise ValueError("Необходимо установить переменную окружения BOT_TOKEN")