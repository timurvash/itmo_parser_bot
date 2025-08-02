import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
from config import ITMO_URL, HEADERS, CSV_FILE, YOUR_ID


class ITMOParser:
    def __init__(self):
        self.url = ITMO_URL
        self.headers = HEADERS
        self.your_id = YOUR_ID

    def parse_rating(self):
        """Парсинг рейтинга"""
        try:
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Находим все элементы рейтинга
            rating_items = soup.find_all('div', class_='RatingPage_table__item__qMY0F')

            total_people = len(rating_items)
            contract_count = 0
            your_position = None
            your_contract_position = None
            contract_position_counter = 0

            for i, item in enumerate(rating_items, 1):
                # Извлекаем номер заявления
                position_element = item.find('p', class_='RatingPage_table__position__uYWvi')
                if position_element:
                    span = position_element.find('span')
                    if span:
                        application_id = span.text.strip()

                        # Проверяем договор
                        contract_text = item.get_text()
                        has_contract = 'Договор: да' in contract_text

                        if has_contract:
                            contract_count += 1
                            contract_position_counter += 1

                        # Проверяем ваш ID
                        if application_id == self.your_id:
                            your_position = i
                            if has_contract:
                                your_contract_position = contract_position_counter

            return {
                'total_people': total_people,
                'contract_count': contract_count,
                'your_position': your_position,
                'your_contract_position': your_contract_position,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            print(f"Ошибка парсинга: {e}")
            return None

    def save_to_csv(self, data):
        """Сохранение данных в CSV"""
        if not os.path.exists(os.path.dirname(CSV_FILE)):
            os.makedirs(os.path.dirname(CSV_FILE))

        file_exists = os.path.exists(CSV_FILE)

        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'total_people', 'contract_count', 'your_position', 'your_contract_position']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(data)

    def get_last_contract_count(self):
        """Получить последнее количество договоров из CSV"""
        if not os.path.exists(CSV_FILE):
            return None

        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                if rows:
                    return int(rows[-1]['contract_count'])
        except:
            pass
        return None