import os

# Bot token from BotFather - ТОЛЬКО через переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin ID for statistics and management
ADMIN_ID = os.getenv("ADMIN_ID")

# URL for parsing
ITMO_URL = os.getenv("ITMO_URL", "https://abit.itmo.ru/ranking/bachelor/contract/2196")

# Database file
DB_FILE = "data/database.db"

# Headers for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Проверяем наличие обязательных переменных
if not BOT_TOKEN:
    raise ValueError("❌ КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения BOT_TOKEN не установлена!")

if not BOT_TOKEN.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
    raise ValueError("❌ ОШИБКА: BOT_TOKEN должен начинаться с цифры")

if ':' not in BOT_TOKEN:
    raise ValueError("❌ ОШИБКА: BOT_TOKEN должен содержать символ ':'")

# Конвертируем ADMIN_ID в int если он установлен
if ADMIN_ID:
    try:
        ADMIN_ID = int(ADMIN_ID)
    except ValueError:
        raise ValueError("❌ ОШИБКА: ADMIN_ID должен быть числом")

# Логи для отладки (БЕЗ отображения токена!)
print(f"✅ Конфигурация загружена:")
print(f"📱 BOT_TOKEN: {'✅ Установлен' if BOT_TOKEN else '❌ Не установлен'}")
print(f"👑 ADMIN_ID: {'✅ Установлен' if ADMIN_ID else '❌ Не установлен'}")
print(f"🔗 ITMO_URL: {ITMO_URL}")
print(f"📁 DB_FILE: {DB_FILE}")