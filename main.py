import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import schedule
import threading
import time

from config import BOT_TOKEN
from database import add_user, remove_user, get_all_users
from parser import ITMOParser

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Создаем клавиатуру
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Проверить рейтинг")],
            [KeyboardButton(text="🔔 Подписаться на уведомления")],
            [KeyboardButton(text="🔕 Отписаться от уведомлений")]
        ],
        resize_keyboard=True
    )
    return keyboard


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для отслеживания рейтинга ИТМО.\n\n"
        "Доступные команды:\n"
        "📊 Проверить рейтинг - текущая статистика\n"
        "🔔 Подписаться на уведомления - получать уведомления об изменениях\n"
        "🔕 Отписаться от уведомлений - отключить уведомления",
        reply_markup=get_main_keyboard()
    )


# Обработчик проверки рейтинга
@dp.message(F.text == "📊 Проверить рейтинг")
async def check_rating(message: types.Message):
    await message.answer("🔄 Парсинг данных, подождите...")

    parser = ITMOParser()
    data = parser.parse_rating()

    if data:
        your_pos_text = f"🎯 Ваша позиция: {data['your_position']}" if data['your_position'] else "❌ Ваш ID не найден"
        your_contract_pos_text = f"💼 Ваша позиция среди договоров: {data['your_contract_position']}" if data[
            'your_contract_position'] else "💼 У вас нет договора или ID не найден"

        result_text = (
            f"📈 **Статистика рейтинга ИТМО**\n\n"
            f"👥 Всего человек в списке: {data['total_people']}\n"
            f"📝 Человек с договорами: {data['contract_count']}\n\n"
            f"{your_pos_text}\n"
            f"{your_contract_pos_text}\n\n"
            f"🕐 Обновлено: {data['timestamp']}"
        )

        # Сохраняем данные
        parser.save_to_csv(data)

        await message.answer(result_text, parse_mode='Markdown')
    else:
        await message.answer("❌ Ошибка при парсинге данных. Попробуйте позже.")


# Обработчик подписки
@dp.message(F.text == "🔔 Подписаться на уведомления")
async def subscribe(message: types.Message):
    user_id = message.from_user.id
    if await add_user(user_id):
        await message.answer("✅ Вы подписались на уведомления!")
    else:
        await message.answer("ℹ️ Вы уже подписаны на уведомления.")


# Обработчик отписки
@dp.message(F.text == "🔕 Отписаться от уведомлений")
async def unsubscribe(message: types.Message):
    user_id = message.from_user.id
    if await remove_user(user_id):
        await message.answer("✅ Вы отписались от уведомлений.")
    else:
        await message.answer("ℹ️ Вы не подписаны на уведомления.")


# Функция уведомления пользователей
async def notify_users(old_count, new_count):
    """Уведомить всех подписчиков об изменении"""
    users = await get_all_users()

    message_text = (
        f"🚨 **!!!ОБНОВЛЕНИЕ!!!**\n\n"
        f"📝 Новое количество человек с подписанными договорами: **{new_count}**\n"
        f"📊 Было: {old_count}\n"
        f"📈 Изменение: {'+' if new_count > old_count else ''}{new_count - old_count}\n\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    for user_id in users:
        try:
            await bot.send_message(user_id, message_text, parse_mode='Markdown')
            await asyncio.sleep(0.1)  # Небольшая задержка между отправками
        except Exception as e:
            print(f"Ошибка отправки пользователю {user_id}: {e}")


# Функция парсинга по расписанию
def scheduled_parsing():
    """Функция для выполнения парсинга по расписанию"""
    try:
        parser = ITMOParser()

        # Получаем последнее количество договоров
        old_count = parser.get_last_contract_count()

        # Парсим новые данные
        data = parser.parse_rating()

        if data:
            new_count = data['contract_count']

            # Сохраняем данные
            parser.save_to_csv(data)

            # Если количество изменилось, отправляем уведомления
            if old_count is not None and old_count != new_count:
                print(f"Изменение обнаружено: {old_count} -> {new_count}")
                # Запускаем уведомления в event loop
                asyncio.create_task(notify_users(old_count, new_count))

            print(f"Парсинг выполнен: {data['timestamp']}, договоров: {new_count}")
        else:
            print("Ошибка при парсинге")

    except Exception as e:
        print(f"Ошибка в scheduled_parsing: {e}")


# Функция для запуска планировщика в отдельном потоке
def run_scheduler():
    schedule.every(2).hours.do(scheduled_parsing)

    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту


# Основная функция
async def main():
    print("🚀 Бот запущен!")

    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Выполняем первоначальный парсинг
    print("🔄 Выполняем первоначальный парсинг...")
    scheduled_parsing()

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())