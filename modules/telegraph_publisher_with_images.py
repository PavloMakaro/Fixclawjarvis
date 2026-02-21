import requests
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
                files = {'file': f}
                response = requests.post(f'{self.base_url}/upload', files=files)

            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result['result'][0]['src']
            return None
        except Exception as e:
            print(f"Ошибка при загрузке изображения: {e}")
            return None

    def create_page_with_images(self, title, content_nodes, author_name="Sandbox", author_url=""):
        """Создает страницу с изображениями"""
        url = f"{self.base_url}/createPage"

        params = {
            "access_token": self.access_token,
            "title": title,
            "author_name": author_name,
            "author_url": author_url,
            "content": json.dumps(content_nodes)
        }

        response = requests.post(url, data=params)
        return response.json()

    def create_cobrazera_article(self):
        """Создает статью о Cobrazera с изображениями"""
        # Загружаем изображения
        image_paths = [
            "downloads/images/5193621219/Cobrazera_CS2_p_0.jpg",
            "downloads/images/5193621219/Cobrazera_CS2_p_1.jpg"
        ]

        image_urls = []
        for img_path in image_paths:
            if os.path.exists(img_path):
                img_url = self.upload_image(img_path)
                if img_url:
                    image_urls.append(img_url)
                    print(f"Изображение загружено: {img_url}")

        # Создаем контент с изображениями
        content = []

        # Заголовок
        content.append({"tag": "h3", "children": ["🎮 Анарбилег 'Cobrazera' Ууганбаяр"]})
        content.append({"tag": "p", "children": ["Будущее монгольского CS2"]})

        # Изображения
        if image_urls:
            content.append({"tag": "img", "attrs": {"src": image_urls[0]}})
            content.append({"tag": "p", "children": ["Фото: Cobrazera в составе The MongolZ"]})

        # Основная информация
        content.append({"tag": "h4", "children": ["ℹ️ Основная информация"]})
        content.append({"tag": "ul", "children": [
            {"tag": "li", "children": ["Полное имя: Анарбилег Ууганбаяр"]},
            {"tag": "li", "children": ["Никнейм: Cobrazera"]},
            {"tag": "li", "children": ["Дата рождения: 3 августа 2005 года"]},
            {"tag": "li", "children": ["Национальность: Монголия"]},
            {"tag": "li", "children": ["Текущая команда: The MongolZ"]},
            {"tag": "li", "children": ["Позиция: Rifler"]},
            {"tag": "li", "children": ["Игра: Counter-Strike 2"]}
        ]})

        # Второе изображение
        if len(image_urls) > 1:
            content.append({"tag": "img", "attrs": {"src": image_urls[1]}})
            content.append({"tag": "p", "children": ["Cobrazera на турнире"]})

        # Достижения
        content.append({"tag": "h4", "children": ["🏆 Достижения"]})
        content.append({"tag": "ul", "children": [
            {"tag": "li", "children": ["MESA Pro Series Spring 2025 — 1 место ($1,100)"]},
            {"tag": "li", "children": ["ESL Challenger League Season 49: Asia — 3 место ($1,000)"]},
            {"tag": "li", "children": ["IESF World Championship 2024 — 5-8 место ($2,500)"]},
            {"tag": "li", "children": ["Asian Champions League 2025 — 5-6 место ($2,400)"]}
        ]})

        # Статистика
        content.append({"tag": "h4", "children": ["📊 Статистика"]})
        content.append({"tag": "ul", "children": [
            {"tag": "li", "children": ["Общий заработок: $8,290"]},
            {"tag": "li", "children": ["Количество турниров: 6"]},
            {"tag": "li", "children": ["Рейтинг в Монголии: #81"]},
            {"tag": "li", "children": ["Заработок в 2024: $2,790"]},
            {"tag": "li", "children": ["Заработок в 2025: $5,500"]}
        ]})

        # Заключение
        content.append({"tag": "h4", "children": ["✨ Заключение"]})
        content.append({"tag": "p", "children": [
            "Анарбилег 'Cobrazera' Ууганбаяр — восходящая звезда монгольского CS2. ",
            "В возрасте 19 лет он уже показывает стабильные результаты на международной арене в составе The MongolZ. ",
            "Его переход в топовую монгольскую команду и регулярные выступления на турнирах различного уровня ",
            "свидетельствуют о серьезном подходе к карьере. Cobrazera представляет новое поколение монгольских ",
            "киберспортсменов, которые укрепляют позиции региона на мировой арене."
        ]})

        # Хештеги
        content.append({"tag": "p", "children": [
            {"tag": "strong", "children": ["#Cobrazera #CS2 #TheMongolZ #Монголия #Киберспорт #CounterStrike"]}
        ]})

        # Создаем страницу
        result = self.create_page_with_images(
            title="Анарбилег 'Cobrazera' Ууганбаяр",
            content_nodes=content,
            author_name="Sandbox"
        )

        return result

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
    result = publisher.create_cobrazera_article()

    if result.get('ok'):
        print(f"✅ Статья создана: https://telegra.ph/{result['result']['path']}")
    else:
        print(f"❌ Ошибка: {result}")