import requests
import base64
import json
import os
from pathlib import Path

class TelegraphPublisher:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.telegra.ph"

    def upload_image(self, image_path):
        """Загружает изображение на сервер Telegra.ph"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Кодируем в base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')

            # Создаем payload
            payload = {
                'access_token': self.access_token,
                'file': encoded_image
            }

            response = requests.post(f"{self.base_url}/upload", data=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result['result'][0]['src']
                else:
                    print(f"Ошибка загрузки: {result}")
                    return None
            else:
                print(f"HTTP ошибка: {response.status_code}")
                return None

        except Exception as e:
            print(f"Ошибка при загрузке изображения: {e}")
            return None

    def create_article_with_images(self, title, content_nodes, author_name="Sandbox", author_url=""):
        """Создает статью с изображениями"""
        try:
            # Подготавливаем контент
            content_json = json.dumps(content_nodes)

            payload = {
                'access_token': self.access_token,
                'title': title,
                'author_name': author_name,
                'author_url': author_url,
                'content': content_json,
                'return_content': True
            }

            response = requests.post(f"{self.base_url}/createPage", data=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result['result']['url']
                else:
                    print(f"Ошибка создания статьи: {result}")
                    return None
            else:
                print(f"HTTP ошибка: {response.status_code}")
                return None

        except Exception as e:
            print(f"Ошибка при создании статьи: {e}")
            return None

    def create_cobrazera_article(self, image_paths=None):
        """Создает статью о Cobrazera"""

        # Основной контент статьи
        content = [
            # Заголовок
            {"tag": "h3", "children": ["🎮 Анарбилег 'Cobrazera' Ууганбаяр: Будущее монгольского CS2"]},

            # Изображение 1
            {"tag": "img", "attrs": {"src": "/file/936f5b8d90b8876cf9bc1.jpg"}},

            # Основная информация
            {"tag": "h4", "children": ["📋 Основная информация"]},
            {"tag": "ul", "children": [
                {"tag": "li", "children": ["Полное имя: Анарбилег Ууганбаяр"]},
                {"tag": "li", "children": ["Никнейм: Cobrazera"]},
                {"tag": "li", "children": ["Дата рождения: 3 августа 2005 года"]},
                {"tag": "li", "children": ["Национальность: Монголия"]},
                {"tag": "li", "children": ["Текущая команда: The MongolZ"]},
                {"tag": "li", "children": ["Позиция: Rifler"]},
                {"tag": "li", "children": ["Игра: Counter-Strike 2"]},
                {"tag": "li", "children": ["Общий заработок: $8,290"]},
                {"tag": "li", "children": ["Количество турниров: 6"]},
                {"tag": "li", "children": ["Рейтинг в Монголии: #81"]}
            ]},

            # Карьерный путь
            {"tag": "h4", "children": ["🚀 Карьерный путь"]},
            {"tag": "p", "children": ["Cobrazera начал свою профессиональную карьеру в 2024 году. До прихода в The MongolZ он играл за команду The Huns, где проявил себя как перспективный молодой игрок."]},
            {"tag": "p", "children": ["В 2025 году состоялся его переход в The MongolZ — ведущую монгольскую киберспортивную организацию. Этот переход стал важным этапом в его карьере, открыв доступ к более серьезным турнирам и международной арене."]},

            # Достижения
            {"tag": "h4", "children": ["🏆 Достижения"]},
            {"tag": "ul", "children": [
                {"tag": "li", "children": ["MESA Pro Series Spring 2025 — 1 место ($1,100)"]},
                {"tag": "li", "children": ["ESL Challenger League Season 49: Asia — 3 место ($1,000)"]},
                {"tag": "li", "children": ["IESF World Championship 2024 — 5-8 место ($2,500)"]},
                {"tag": "li", "children": ["Asian Champions League 2025 — 5-6 место ($2,400)"]},
                {"tag": "li", "children": ["BLAST Open Spring 2025 — 13-16 место ($1,000)"]},
                {"tag": "li", "children": ["The MongolZ Esports Club Championship #1 — 1 место ($290)"]}
            ]},

            # Статистика по годам
            {"tag": "h4", "children": ["📊 Статистика по годам"]},
            {"tag": "table", "children": [
                {"tag": "tr", "children": [
                    {"tag": "th", "children": ["Год"]},
                    {"tag": "th", "children": ["Заработок"]},
                    {"tag": "th", "children": ["Турниры"]}
                ]},
                {"tag": "tr", "children": [
                    {"tag": "td", "children": ["2024"]},
                    {"tag": "td", "children": ["$2,790"]},
                    {"tag": "td", "children": ["2"]}
                ]},
                {"tag": "tr", "children": [
                    {"tag": "td", "children": ["2025"]},
                    {"tag": "td", "children": ["$5,500"]},
                    {"tag": "td", "children": ["4"]}
                ]}
            ]},

            # Игровой стиль
            {"tag": "h4", "children": ["🎯 Игровой стиль"]},
            {"tag": "p", "children": ["Cobrazera играет на позиции rifler, что означает его специализацию на использовании винтовок (AK-47, M4A4). Эта позиция требует отличной точности, позиционирования и принятия быстрых решений."]},
            {"tag": "p", "children": ["В возрасте 19 лет он демонстрирует зрелость и стабильность, нехарактерные для большинства молодых игроков. Его переход в The MongolZ прошел гладко, что свидетельствует о хорошей адаптивности и командной работе."]},

            # Значение для монгольской сцены
            {"tag": "h4", "children": ["🇲🇳 Значение для монгольской сцены"]},
            {"tag": "p", "children": ["Cobrazera является частью нового поколения монгольских киберспортсменов, которые поднимают уровень региона на международной арене. The MongolZ уже доказали свою конкурентоспособность на азиатской сцене, и такие игроки как Cobrazera укрепляют позиции команды."]},
            {"tag": "p", "children": ["Монгольская сцена CS2 активно развивается, демонстрируя впечатляющие результаты на международных турнирах. Игроки из Монголии показывают уникальный стиль игры, сочетающий агрессивность и тактическую дисциплину."]},

            # Перспективы
            {"tag": "h4", "children": ["🔮 Перспективы"]},
            {"tag": "p", "children": ["С учетом его возраста и текущего прогресса, Cobrazera имеет все шансы стать одним из ключевых игроков не только монгольской, но и азиатской сцены CS2 в ближайшие годы."]},
            {"tag": "p", "children": ["Его стабильные выступления на турнирах различного уровня показывают серьезный подход к карьере. В ближайшие 2-3 года мы можем ожидать от него прорыва на крупных международных турнирах."]},

            # Изображение 2
            {"tag": "img", "attrs": {"src": "/file/936f5b8d90b8876cf9bc1.jpg"}},

            # Источники
            {"tag": "h4", "children": ["📚 Источники"]},
            {"tag": "ul", "children": [
                {"tag": "li", "children": ["Liquipedia Counter-Strike Wiki"]},
                {"tag": "li", "children": ["Esports Earnings"]},
                {"tag": "li", "children": ["HLTV.org"]},
                {"tag": "li", "children": ["EGamersWorld"]}
            ]},

            # Хештеги
            {"tag": "p", "children": ["#Cobrazera #CS2 #TheMongolZ #Монголия #Киберспорт #CounterStrike #Rifler #МолодойТалант"]}
        ]

        # Создаем статью
        title = "Анарбилег 'Cobrazera' Ууганбаяр: Будущее монгольского CS2"
        url = self.create_article_with_images(title, content)

        return url

# Пример использования
if __name__ == "__main__":
    import sys
    # Add root directory to path to import config
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        import config
        ACCESS_TOKEN = config.TELEGRAPH_ACCESS_TOKEN
    except ImportError:
        ACCESS_TOKEN = "YOUR_TOKEN_HERE"

    publisher = TelegraphPublisher(ACCESS_TOKEN)

    # Создаем статью
    article_url = publisher.create_cobrazera_article()

    if article_url:
        print(f"Статья создана: {article_url}")
    else:
        print("Ошибка при создании статьи")