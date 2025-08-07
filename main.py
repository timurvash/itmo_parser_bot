import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import threading
import time
import pytz

from config import BOT_TOKEN, ADMIN_ID
from database import (init_database, add_or_update_user, set_user_id, get_user_id,
                      subscribe_user, unsubscribe_user, get_all_subscribers,
                      save_rating_data, get_last_contract_count, get_user_stats, get_rating_stats)
from parser import ITMOParser

# Московская временная зона
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Отключаем избыточные логи
logging.getLogger('aiogram.dispatcher').setLevel(logging.WARNING)
logging.getLogger('aiogram.bot').setLevel(logging.WARNING)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Глобальная переменная для event loop
main_loop = None


def get_moscow_time():
    """Получить текущее московское время"""
    return datetime.now(MOSCOW_TZ)


def format_moscow_time(dt=None):
    """Форматировать московское время"""
    if dt is None:
        dt = get_moscow_time()
    return dt.strftime('%Y-%m-%d %H:%M:%S')


# Создаем клавиатуры
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Проверить рейтинг")],
            [KeyboardButton(text="🔔 Подписаться на уведомления")],
            [KeyboardButton(text="🔕 Отписаться от уведомлений")],
            [KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Статистика пользователей", callback_data="admin_users")],
            [InlineKeyboardButton(text="📈 Статистика рейтинга", callback_data="admin_rating")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")]
        ]
    )
    return keyboard


def get_settings_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆔 Установить ID", callback_data="set_id")],
            [InlineKeyboardButton(text="👁️ Мой ID", callback_data="show_id")]
        ]
    )
    return keyboard


# Middleware для учета сообщений
@dp.message.middleware()
async def message_counter_middleware(handler, event, data):
    """Middleware для подсчета сообщений пользователей"""
    if isinstance(event, types.Message) and event.from_user:
        await add_or_update_user(
            event.from_user.id,
            event.from_user.username,
            event.from_user.first_name,
            event.from_user.last_name
        )
    return await handler(event, data)


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    moscow_time = format_moscow_time()
    await message.answer(
        f"👋 Привет! Я бот для отслеживания рейтинга ИТМО.\n\n"
        f"🕐 Текущее время: {moscow_time} (МСК)\n\n"
        f"Доступные команды:\n"
        f"📊 Проверить рейтинг - текущая статистика\n"
        f"🔔 Подписаться на уведомления - получать уведомления об изменениях\n"
        f"🔕 Отписаться от уведомлений - отключить уведомления\n"
        f"⚙️ Настройки - установить свой ID абитуриента\n\n"
        f"💡 Для отслеживания вашей позиции установите свой ID абитуриента в настройках!",
        reply_markup=get_main_keyboard()
    )


# Обработчик команды /admin (только для админа)
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not ADMIN_ID or message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав доступа к админ панели.")
        return

    await message.answer("👑 Админ панель:", reply_markup=get_admin_keyboard())


# Обработчик команды /set_id
@dp.message(Command("set_id"))
async def cmd_set_id(message: types.Message):
    args = message.text.split()[1:]
    if not args:
        await message.answer("Использование: /set_id <ваш_id>\nПример: /set_id 4154668")
        return

    your_id = args[0]
    await set_user_id(message.from_user.id, your_id)
    await message.answer(f"✅ Ваш ID установлен: {your_id}")


# Обработчик команды /my_id
@dp.message(Command("my_id"))
async def cmd_my_id(message: types.Message):
    your_id = await get_user_id(message.from_user.id)
    if your_id:
        await message.answer(f"🆔 Ваш текущий ID: {your_id}")
    else:
        await message.answer("❌ ID не установлен. Используйте /set_id <ваш_id> для установки.")


# Обработчик проверки рейтинга
@dp.message(F.text == "📊 Проверить рейтинг")
async def check_rating(message: types.Message):
    await message.answer("🔄 Парсинг данных, подождите...")

    user_your_id = await get_user_id(message.from_user.id)

    parser = ITMOParser()
    data = parser.parse_rating(user_your_id)

    if data:
        # Формируем текст о позиции пользователя
        if user_your_id:
            if data['your_position']:
                your_pos_text = f"🎯 Ваша позиция: {data['your_position']}"
                if data['your_contract_position']:
                    your_pos_text += f"\n💼 Позиция среди договоров: {data['your_contract_position']}"
                    if data['your_paid_position']:
                        your_pos_text += f"\n💰 Позиция среди оплаченных: {data['your_paid_position']}"
                    elif data['your_unpaid_position']:
                        your_pos_text += f"\n⏳ Позиция среди неоплаченных: {data['your_unpaid_position']}"
                else:
                    your_pos_text += f"\n💼 У вас нет договора"
            else:
                your_pos_text = f"❌ Ваш ID ({user_your_id}) не найден в списке"
        else:
            your_pos_text = "ℹ️ Установите свой ID в настройках для отслеживания позиции"

        result_text = (
            f"📈 **Статистика рейтинга ИТМО**\n\n"
            f"👥 Всего человек в списке: {data['total_people']}\n"
            f"📝 Человек с договорами: {data['contract_count']}\n"
            f"💰 Договоры оплачены: {data['contract_paid_count']}\n"
            f"⏳ Договоры не оплачены: {data['contract_unpaid_count']}\n\n"
            f"{your_pos_text}\n\n"
            f"🕐 Обновлено: {data['timestamp']} (МСК)"
        )

        # Сохраняем данные
        await save_rating_data(data)

        await message.answer(result_text, parse_mode='Markdown')
    else:
        await message.answer("❌ Ошибка при парсинге данных. Попробуйте позже.")


# Обработчик настроек
@dp.message(F.text == "⚙️ Настройки")
async def settings_menu(message: types.Message):
    await message.answer("⚙️ Настройки:", reply_markup=get_settings_keyboard())


# Обработчик подписки
@dp.message(F.text == "🔔 Подписаться на уведомления")
async def subscribe(message: types.Message):
    if await subscribe_user(message.from_user.id):
        await message.answer("✅ Вы подписались на уведомления!")
    else:
        await message.answer("ℹ️ Вы уже подписаны на уведомления.")


# Обработчик отписки
@dp.message(F.text == "🔕 Отписаться от уведомлений")
async def unsubscribe(message: types.Message):
    if await unsubscribe_user(message.from_user.id):
        await message.answer("✅ Вы отписались от уведомлений.")
    else:
        await message.answer("ℹ️ Вы не подписаны на уведомления.")


# Обработчики callback кнопок
@dp.callback_query(F.data == "set_id")
async def callback_set_id(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🆔 Для установки вашего ID абитуриента используйте команду:\n"
        "/set_id <ваш_id>\n\n"
        "Пример: /set_id 4154668"
    )


@dp.callback_query(F.data == "show_id")
async def callback_show_id(callback: types.CallbackQuery):
    await callback.answer()
    your_id = await get_user_id(callback.from_user.id)
    if your_id:
        await callback.message.answer(f"🆔 Ваш текущий ID: {your_id}")
    else:
        await callback.message.answer("❌ ID не установлен. Используйте /set_id <ваш_id> для установки.")


@dp.callback_query(F.data == "admin_users")
async def callback_admin_users(callback: types.CallbackQuery):
    if not ADMIN_ID or callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.answer()
    stats = await get_user_stats()

    text = (
        f"👥 **Статистика пользователей**\n\n"
        f"Всего пользователей: {stats['total_users']}\n"
        f"Подписчиков: {stats['total_subscribers']}\n"
        f"Всего сообщений: {stats['total_messages']}\n\n"
        f"**Топ активных пользователей:**\n"
    )

    for i, user in enumerate(stats['top_users'], 1):
        user_id, username, first_name, last_name, msg_count, last_activity = user
        name = first_name or username or f"ID:{user_id}"
        text += f"{i}. {name} - {msg_count} сообщений\n"

    await callback.message.answer(text, parse_mode='Markdown')


@dp.callback_query(F.data == "admin_rating")
async def callback_admin_rating(callback: types.CallbackQuery):
    if not ADMIN_ID or callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.answer()
    stats = await get_rating_stats()

    text = "📈 **Последние записи рейтинга:**\n\n"

    for record in stats:
        timestamp, total, contracts, paid, unpaid = record
        text += (
            f"🕐 {timestamp}\n"
            f"Всего: {total}, Договоры: {contracts}\n"
            f"Оплачено: {paid}, Не оплачено: {unpaid}\n\n"
        )

    await callback.message.answer(text, parse_mode='Markdown')


@dp.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: types.CallbackQuery):
    if not ADMIN_ID or callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer(
        "📢 Для рассылки сообщения всем пользователям используйте команду:\n"
        "/broadcast <текст сообщения>"
    )


# Команда рассылки (только для админа)
@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if not ADMIN_ID or message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для рассылки.")
        return

    text = message.text[len("/broadcast"):].strip()
    if not text:
        await message.answer("❌ Укажите текст для рассылки.")
        return

    subscribers = await get_all_subscribers()
    sent = 0

    for user_id in subscribers:
        try:
            await bot.send_message(user_id, f"📢 **Сообщение от администратора:**\n\n{text}", parse_mode='Markdown')
            sent += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Ошибка отправки пользователю {user_id}: {e}")

    await message.answer(f"✅ Рассылка завершена. Отправлено: {sent}/{len(subscribers)}")


# Функция уведомления пользователей
async def notify_users(old_data, new_data):
    """Уведомить всех подписчиков об изменении"""
    try:
        users = await get_all_subscribers()
        moscow_time = format_moscow_time()

        # Формируем сообщение об изменениях
        changes = []
        if old_data.get('contract_count', 0) != new_data['contract_count']:
            changes.append(f"Договоры: {old_data.get('contract_count', 0)} → {new_data['contract_count']}")
        if old_data.get('contract_paid_count', 0) != new_data['contract_paid_count']:
            changes.append(f"Оплачено: {old_data.get('contract_paid_count', 0)} → {new_data['contract_paid_count']}")
        if old_data.get('contract_unpaid_count', 0) != new_data['contract_unpaid_count']:
            changes.append(
                f"Не оплачено: {old_data.get('contract_unpaid_count', 0)} → {new_data['contract_unpaid_count']}")

        if not changes:
            return

        message_text = (
                f"🚨 **!!!ОБНОВЛЕНИЕ РЕЙТИНГА!!!**\n\n"
                f"📊 Изменения:\n" + "\n".join(changes) + "\n\n"
                                                         f"📈 Текущая статистика:\n"
                                                         f"👥 Всего людей: {new_data['total_people']}\n"
                                                         f"📝 Договоры: {new_data['contract_count']}\n"
                                                         f"💰 Оплачено: {new_data['contract_paid_count']}\n"
                                                         f"⏳ Не оплачено: {new_data['contract_unpaid_count']}\n\n"
                                                         f"🕐 {moscow_time} (МСК)"
        )

        successful_sends = 0
        for user_id in users:
            try:
                await bot.send_message(user_id, message_text, parse_mode='Markdown')
                successful_sends += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"❌ Ошибка отправки пользователю {user_id}: {e}")

        print(f"✅ Уведомления отправлены {successful_sends}/{len(users)} пользователям")

    except Exception as e:
        print(f"❌ Ошибка в notify_users: {e}")


# Функция парсинга по расписанию
def scheduled_parsing():
    """Функция для выполнения парсинга по расписанию"""
    try:
        parser = ITMOParser()

        # Получаем последние данные
        old_count = asyncio.run(get_last_contract_count())

        # Парсим новые данные
        data = parser.parse_rating()

        if data:
            # Сохраняем данные
            asyncio.run(save_rating_data(data))

            # Если количество изменилось, отправляем уведомления
            if old_count is not None and old_count != data['contract_count']:
                moscow_time = format_moscow_time()
                print(f"🔄 Изменение обнаружено: {old_count} -> {data['contract_count']} в {moscow_time}")

                # Запускаем уведомления в основном event loop
                if main_loop and not main_loop.is_closed():
                    old_data = {'contract_count': old_count}
                    asyncio.run_coroutine_threadsafe(
                        notify_users(old_data, data),
                        main_loop
                    )

            moscow_time = format_moscow_time()
            print(f"✅ Парсинг выполнен: {moscow_time}, договоров: {data['contract_count']}")
        else:
            moscow_time = format_moscow_time()
            print(f"❌ Ошибка при парсинге в {moscow_time}")

    except Exception as e:
        moscow_time = format_moscow_time()
        print(f"❌ Ошибка в scheduled_parsing в {moscow_time}: {e}")


# Функция для запуска планировщика в отдельном потоке
def run_scheduler():
    import schedule

    # Настраиваем расписание
    schedule.every(2).hours.do(scheduled_parsing)

    moscow_time = format_moscow_time()
    print(f"📅 Планировщик запущен (каждые 2 часа) в {moscow_time}")

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Проверяем каждую минуту
        except Exception as e:
            moscow_time = format_moscow_time()
            print(f"❌ Ошибка в планировщике в {moscow_time}: {e}")
            time.sleep(60)


# Основная функция
async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()

    # Инициализируем базу данных
    await init_database()

    moscow_time = format_moscow_time()
    print(f"🚀 Бот запущен в {moscow_time}!")

    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Выполняем первоначальный парсинг
    print("🔄 Выполняем первоначальный парсинг...")
    scheduled_parsing()

    # Запускаем бота с обработкой ошибок
    try:
        await dp.start_polling(
            bot,
            polling_timeout=20,
            request_timeout=15,
            retry_after=3
        )
    except KeyboardInterrupt:
        moscow_time = format_moscow_time()
        print(f"🛑 Бот остановлен пользователем в {moscow_time}")
    except Exception as e:
        moscow_time = format_moscow_time()
        print(f"❌ Критическая ошибка в {moscow_time}: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        moscow_time = format_moscow_time()
        print(f"🛑 Программа завершена в {moscow_time}")
    except Exception as e:
        moscow_time = format_moscow_time()
        print(f"❌ Фатальная ошибка в {moscow_time}: {e}")