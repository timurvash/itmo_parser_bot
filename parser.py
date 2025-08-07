import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from config import ITMO_URL, HEADERS

# Московская временная зона
MOSCOW_TZ = pytz.timezone('Europe/Moscow')


class ITMOParser:
    def __init__(self):
        self.url = ITMO_URL
        self.headers = HEADERS

    def get_moscow_time(self):
        """Получить текущее московское время"""
        return datetime.now(MOSCOW_TZ)

    def format_moscow_time(self, dt=None):
        """Форматировать московское время"""
        if dt is None:
            dt = self.get_moscow_time()
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def parse_rating(self, user_your_id=None):
        """Парсинг рейтинга с учетом новых типов договоров"""
        try:
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Находим все элементы рейтинга
            rating_items = soup.find_all('div', class_='RatingPage_table__item__qMY0F')

            total_people = len(rating_items)
            contract_count = 0
            contract_paid_count = 0  # Зеленые элементы (оплачено)
            contract_unpaid_count = 0  # Желтые элементы (не оплачено)

            your_position = None
            your_contract_position = None
            your_paid_position = None
            your_unpaid_position = None

            contract_position_counter = 0
            paid_position_counter = 0
            unpaid_position_counter = 0

            for i, item in enumerate(rating_items, 1):
                # Извлекаем номер заявления
                position_element = item.find('p', class_='RatingPage_table__position__uYWvi')
                if position_element:
                    span = position_element.find('span')
                    if span:
                        application_id = span.text.strip()

                        # Проверяем наличие договора
                        contract_text = item.get_text()
                        has_contract = 'Договор: да' in contract_text

                        if has_contract:
                            contract_count += 1
                            contract_position_counter += 1

                            # Определяем тип договора по CSS классам
                            is_paid = 'RatingPage_table__item_green__InEVk' in str(item)
                            is_unpaid = 'RatingPage_table__item_yellow__lbs7n' in str(item)

                            if is_paid:
                                contract_paid_count += 1
                                paid_position_counter += 1
                            elif is_unpaid:
                                contract_unpaid_count += 1
                                unpaid_position_counter += 1

                        # Проверяем пользовательский ID
                        if user_your_id and application_id == user_your_id:
                            your_position = i
                            if has_contract:
                                your_contract_position = contract_position_counter
                                if 'RatingPage_table__item_green__InEVk' in str(item):
                                    your_paid_position = paid_position_counter
                                elif 'RatingPage_table__item_yellow__lbs7n' in str(item):
                                    your_unpaid_position = unpaid_position_counter

            # Используем московское время
            moscow_time = self.format_moscow_time()

            return {
                'total_people': total_people,
                'contract_count': contract_count,
                'contract_paid_count': contract_paid_count,
                'contract_unpaid_count': contract_unpaid_count,
                'your_position': your_position,
                'your_contract_position': your_contract_position,
                'your_paid_position': your_paid_position,
                'your_unpaid_position': your_unpaid_position,
                'timestamp': moscow_time
            }

        except Exception as e:
            moscow_time = self.format_moscow_time()
            print(f"Ошибка парсинга в {moscow_time}: {e}")
            return None