import aiosqlite
import os
from datetime import datetime
import pytz
from config import DB_FILE

# Московская временная зона
MOSCOW_TZ = pytz.timezone('Europe/Moscow')


async def init_database():
    """Инициализация базы данных"""
    if not os.path.exists(os.path.dirname(DB_FILE)):
        os.makedirs(os.path.dirname(DB_FILE))

    async with aiosqlite.connect(DB_FILE) as db:
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                your_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0
            )
        ''')

        # Таблица подписок
        await db.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица истории рейтинга
        await db.execute('''
            CREATE TABLE IF NOT EXISTS rating_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_people INTEGER,
                contract_count INTEGER,
                contract_paid_count INTEGER,
                contract_unpaid_count INTEGER
            )
        ''')

        await db.commit()


async def add_or_update_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Добавить или обновить пользователя"""
    moscow_time = datetime.now(MOSCOW_TZ)

    async with aiosqlite.connect(DB_FILE) as db:
        # Проверяем, существует ли пользователь
        cursor = await db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        user_exists = await cursor.fetchone()

        if user_exists:
            # Обновляем существующего пользователя
            await db.execute('''
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?, 
                    last_activity = ?, message_count = message_count + 1
                WHERE user_id = ?
            ''', (username, first_name, last_name, moscow_time, user_id))
        else:
            # Добавляем нового пользователя
            await db.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, created_at, last_activity, message_count)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (user_id, username, first_name, last_name, moscow_time, moscow_time))

        await db.commit()


async def set_user_id(user_id: int, your_id: str):
    """Установить ID абитуриента для пользователя"""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('UPDATE users SET your_id = ? WHERE user_id = ?', (your_id, user_id))
        await db.commit()


async def get_user_id(user_id: int):
    """Получить ID абитуриента пользователя"""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('SELECT your_id FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        return result[0] if result and result[0] else None


async def subscribe_user(user_id: int):
    """Подписать пользователя на уведомления"""
    async with aiosqlite.connect(DB_FILE) as db:
        try:
            await db.execute('INSERT INTO subscriptions (user_id) VALUES (?)', (user_id,))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def unsubscribe_user(user_id: int):
    """Отписать пользователя от уведомлений"""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
        await db.commit()
        return cursor.rowcount > 0


async def get_all_subscribers():
    """Получить всех подписчиков"""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('SELECT user_id FROM subscriptions')
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def save_rating_data(data):
    """Сохранить данные рейтинга"""
    moscow_time = datetime.now(MOSCOW_TZ)

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            INSERT INTO rating_history 
            (timestamp, total_people, contract_count, contract_paid_count, contract_unpaid_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (moscow_time, data['total_people'], data['contract_count'],
              data['contract_paid_count'], data['contract_unpaid_count']))
        await db.commit()


async def get_last_contract_count():
    """Получить последнее количество договоров"""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('''
            SELECT contract_count FROM rating_history 
            ORDER BY timestamp DESC LIMIT 1
        ''')
        result = await cursor.fetchone()
        return result[0] if result else None


async def get_user_stats():
    """Получить статистику пользователей (для админа)"""
    async with aiosqlite.connect(DB_FILE) as db:
        # Общая статистика
        cursor = await db.execute('SELECT COUNT(*) FROM users')
        total_users = (await cursor.fetchone())[0]

        cursor = await db.execute('SELECT COUNT(*) FROM subscriptions')
        total_subscribers = (await cursor.fetchone())[0]

        cursor = await db.execute('SELECT SUM(message_count) FROM users')
        total_messages = (await cursor.fetchone())[0] or 0

        # Топ активных пользователей
        cursor = await db.execute('''
            SELECT user_id, username, first_name, last_name, message_count, last_activity
            FROM users 
            ORDER BY message_count DESC 
            LIMIT 10
        ''')
        top_users = await cursor.fetchall()

        return {
            'total_users': total_users,
            'total_subscribers': total_subscribers,
            'total_messages': total_messages,
            'top_users': top_users
        }


async def get_rating_stats():
    """Получить статистику рейтинга (для админа)"""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('''
            SELECT timestamp, total_people, contract_count, contract_paid_count, contract_unpaid_count
            FROM rating_history 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_data = await cursor.fetchall()

        return recent_data