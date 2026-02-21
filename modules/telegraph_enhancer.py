#!/usr/bin/env python3
"""
Модуль для создания улучшенных статей на Telegra.ph с картинками
"""

import base64
import requests
from typing import List, Dict, Any
from pathlib import Path

class TelegraphEnhancer:
    """Класс для создания статей с картинками для Telegra.ph"""

    def __init__(self, telegraph_publisher):
        """
        Инициализация улучшителя статей

        Args:
            telegraph_publisher: Экземпляр TelegraphPublisher
        """
        self.publisher = telegraph_publisher

    def upload_image(self, image_path: str) -> str:
        """
        Загружает изображение на Telegra.ph и возвращает URL

        Args:
            image_path: Путь к локальному файлу изображения

        Returns:
            URL загруженного изображения
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Кодируем в base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')

            # Загружаем на Telegra.ph
            url = "https://telegra.ph/upload"
            files = {'file': ('image.jpg', image_data, 'image/jpeg')}

            response = requests.post(url, files=files)

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    image_info = result[0]
                    if 'src' in image_info:
                        return f"https://telegra.ph{image_info['src']}"

            return ""

        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")
            return ""

    def create_enhanced_article(
        self,
        title: str,
        content_parts: List[Dict[str, str]],  # Список частей: {'type': 'text'/'image', 'content': '...'}
        author_name: str = "",
        author_url: str = ""
    ) -> Dict[str, Any]:
        """
        Создает статью с текстом и изображениями

        Args:
            title: Заголовок статьи
            content_parts: Список частей контента
            author_name: Имя автора
            author_url: URL автора

        Returns:
            Результат создания страницы
        """
        html_content = []

        for part in content_parts:
            if part['type'] == 'text':
                # Оборачиваем текст в параграфы
                paragraphs = part['content'].split('\n\n')
                for p in paragraphs:
                    if p.strip():
                        html_content.append(f"<p>{p.strip()}</p>")

            elif part['type'] == 'image':
                image_url = part['content']
                if image_url:
                    html_content.append(f'<img src="{image_url}" alt="{title}"/>')
                    if 'caption' in part:
                        html_content.append(f'<p><em>{part["caption"]}</em></p>')

            elif part['type'] == 'header':
                level = part.get('level', 2)
                html_content.append(f"<h{level}>{part['content']}</h{level}>")

            elif part['type'] == 'list':
                items = part['content']
                html_content.append("<ul>")
                for item in items:
                    html_content.append(f"<li>{item}</li>")
                html_content.append("</ul>")

        # Объединяем весь HTML
        full_html = "\n".join(html_content)

        # Создаем страницу
        return self.publisher.create_page(
            title=title,
            content=full_html,
            author_name=author_name,
            author_url=author_url,
            return_content=True
        )

    def create_cobrazera_article(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Создает улучшенную статью о Cobrazera

        Args:
            image_paths: Список путей к изображениям

        Returns:
            Результат создания статьи
        """
        # Загружаем изображения
        image_urls = []
        for img_path in image_paths:
            if Path(img_path).exists():
                url = self.upload_image(img_path)
                if url:
                    image_urls.append(url)
                    print(f"Изображение загружено: {url}")

        # Создаем части контента
        content_parts = [
            {
                'type': 'header',
                'content': 'Анарбилег "Cobrazera" Ууганбаяр: Будущее монгольского CS2',
                'level': 1
            },
            {
                'type': 'text',
                'content': 'Молодой монгольский киберспортсмен, который ворвался в профессиональную сцену Counter-Strike 2 и уже показывает впечатляющие результаты в составе команды The MongolZ.'
            }
        ]

        # Добавляем первое изображение
        if image_urls:
            content_parts.append({
                'type': 'image',
                'content': image_urls[0],
                'caption': 'Анарбилег "Cobrazera" Ууганбаяр'
            })

        # Основная информация
        content_parts.extend([
            {
                'type': 'header',
                'content': '📊 Основная информация',
                'level': 2
            },
            {
                'type': 'list',
                'content': [
                    'Полное имя: Анарбилег Ууганбаяр',
                    'Никнейм: Cobrazera',
                    'Дата рождения: 3 августа 2005 года',
                    'Национальность: Монголия',
                    'Текущая команда: The MongolZ',
                    'Позиция: Rifler',
                    'Игра: Counter-Strike 2'
                ]
            }
        ])

        # Карьерный путь
        content_parts.extend([
            {
                'type': 'header',
                'content': '🚀 Карьерный путь',
                'level': 2
            },
            {
                'type': 'text',
                'content': 'Cobrazera начал свою профессиональную карьеру в 2024 году, играя за команду The Huns. В декабре 2025 года состоялся его переход в The MongolZ — ведущую монгольскую киберспортивную организацию, что стало важным этапом в его карьере.'
            }
        ])

        # Добавляем второе изображение
        if len(image_urls) > 1:
            content_parts.append({
                'type': 'image',
                'content': image_urls[1],
                'caption': 'Cobrazera в составе The MongolZ'
            })

        # Достижения
        content_parts.extend([
            {
                'type': 'header',
                'content': '🏆 Достижения и статистика',
                'level': 2
            },
            {
                'type': 'text',
                'content': 'По данным Esports Earnings, общий заработок Cobrazera составляет $15,700. Он участвовал в 6 турнирах и занимает 81 место в рейтинге монгольских игроков.'
            },
            {
                'type': 'header',
                'content': 'Ключевые турниры',
                'level': 3
            },
            {
                'type': 'list',
                'content': [
                    'MESA Pro Series Spring 2025 — 1 место ($1,100)',
                    'ESL Challenger League Season 49: Asia — 3 место ($1,000)',
                    'IESF World Championship 2024 — 5-8 место ($2,500)',
                    'Asian Champions League 2025 — 5-6 место ($2,400)',
                    'BLAST Open Spring 2025 — 13-16 место ($1,000)'
                ]
            }
        ])

        # Игровой стиль
        content_parts.extend([
            {
                'type': 'header',
                'content': '🎯 Игровой стиль',
                'level': 2
            },
            {
                'type': 'text',
                'content': 'Как rifler, Cobrazera специализируется на использовании винтовок (AK-47, M4A4). Эта позиция требует отличной точности, позиционирования и принятия быстрых решений. В возрасте 19 лет он показывает быструю адаптацию к новой команде и стабильные выступления на турнирах.'
            }
        ])

        # Значение для монгольской сцены
        content_parts.extend([
            {
                'type': 'header',
                'content': '🇲🇳 Значение для монгольской сцены',
                'level': 2
            },
            {
                'type': 'text',
                'content': 'Cobrazera является частью нового поколения монгольских киберспортсменов, которые поднимают уровень региона на международной арене. The MongolZ уже доказали свою конкурентоспособность на азиатской сцене, и такие игроки как Cobrazera укрепляют позиции команды.'
            }
        ])

        # Перспективы
        content_parts.extend([
            {
                'type': 'header',
                'content': '✨ Перспективы',
                'level': 2
            },
            {
                'type': 'text',
                'content': 'С учетом его возраста и текущего прогресса, Cobrazera имеет все шансы стать одним из ключевых игроков не только монгольской, но и азиатской сцены CS2 в ближайшие годы. Его карьера только начинается, и мы можем ожидать от него более значительных достижений на мировой арене.'
            }
        ])

        # Источники
        content_parts.extend([
            {
                'type': 'header',
                'content': '📚 Источники',
                'level': 2
            },
            {
                'type': 'list',
                'content': [
                    'Liquipedia Counter-Strike Wiki',
                    'HLTV.org',
                    'Esports Earnings',
                    'Prosettings.net'
                ]
            }
        ])

        # Создаем статью
        return self.create_enhanced_article(
            title="Анарбилег 'Cobrazera' Ууганбаяр: Будущее монгольского CS2",
            content_parts=content_parts,
            author_name="Sandbox",
            author_url=""
        )