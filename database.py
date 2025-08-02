import aiofiles
import os
from config import DB_FILE


async def add_user(user_id: int):
    """Добавить пользователя в базу подписчиков"""
    if not os.path.exists(os.path.dirname(DB_FILE)):
        os.makedirs(os.path.dirname(DB_FILE))

    # Проверяем, есть ли уже пользователь
    subscribers = await get_all_users()
    if user_id not in subscribers:
        async with aiofiles.open(DB_FILE, 'a') as f:
            await f.write(f"{user_id}\n")
        return True
    return False


async def remove_user(user_id: int):
    """Удалить пользователя из базы подписчиков"""
    subscribers = await get_all_users()
    if user_id in subscribers:
        subscribers.remove(user_id)
        async with aiofiles.open(DB_FILE, 'w') as f:
            for sub_id in subscribers:
                await f.write(f"{sub_id}\n")
        return True
    return False


async def get_all_users():
    """Получить всех подписчиков"""
    if not os.path.exists(DB_FILE):
        return []

    try:
        async with aiofiles.open(DB_FILE, 'r') as f:
            content = await f.read()
            return [int(line.strip()) for line in content.split('\n') if line.strip()]
    except:
        return []