#!/usr/bin/env python3
"""
Модуль для публикации статей на Telegra.ph
"""

import requests
import json
import os
from typing import Optional, Dict, Any

class TelegraphPublisher:
    """Класс для работы с Telegra.ph API"""

    BASE_URL = "https://api.telegra.ph"

    def __init__(self, access_token: Optional[str] = None):
        """
        Инициализация издателя Telegra.ph

        Args:
            access_token: Токен доступа Telegra.ph (можно получить через @Telegraph bot)
        """
        self.access_token = access_token
        self.session = requests.Session()

    def create_account(self, short_name: str, author_name: str = "", author_url: str = "") -> Dict[str, Any]:
        """
        Создание аккаунта Telegra.ph

        Args:
            short_name: Короткое имя аккаунта (обязательно)
            author_name: Имя автора (опционально)
            author_url: URL автора (опционально)

        Returns:
            Словарь с данными аккаунта, включая access_token
        """
        url = f"{self.BASE_URL}/createAccount"
        params = {
            "short_name": short_name,
            "author_name": author_name,
            "author_url": author_url
        }

        response = self.session.get(url, params=params)
        return response.json()

    def create_page(
        self,
        title: str,
        content: str,
        author_name: str = "",
        author_url: str = "",
        return_content: bool = False
    ) -> Dict[str, Any]:
        """
        Создание страницы (статьи) на Telegra.ph

        Args:
            title: Заголовок статьи
            content: Содержимое статьи в формате HTML
            author_name: Имя автора (опционально)
            author_url: URL автора (опционально)
            return_content: Возвращать ли содержимое в ответе

        Returns:
            Словарь с данными созданной страницы, включая URL
        """
        if not self.access_token:
            raise ValueError("Access token is required. Create account first or set access_token.")

        url = f"{self.BASE_URL}/createPage"
        params = {
            "access_token": self.access_token,
            "title": title,
            "author_name": author_name,
            "author_url": author_url,
            "content": content,
            "return_content": return_content
        }

        response = self.session.get(url, params=params)
        return response.json()

    def create_page_from_markdown(
        self,
        title: str,
        markdown_content: str,
        author_name: str = "",
        author_url: str = "",
        return_content: bool = False
    ) -> Dict[str, Any]:
        """
        Создание страницы из Markdown текста

        Args:
            title: Заголовок статьи
            markdown_content: Содержимое в формате Markdown
            author_name: Имя автора (опционально)
            author_url: URL автора (опционально)
            return_content: Возвращать ли содержимое в ответе

        Returns:
            Словарь с данными созданной страницы
        """
        # Преобразуем Markdown в HTML (простая реализация)
        html_content = self._markdown_to_html(markdown_content)
        return self.create_page(title, html_content, author_name, author_url, return_content)

    def _markdown_to_html(self, markdown: str) -> str:
        """
        Простое преобразование Markdown в HTML для Telegra.ph

        Args:
            markdown: Текст в формате Markdown

        Returns:
            HTML строка
        """
        # Преобразуем заголовки
        lines = markdown.split('\n')
        html_lines = []

        for line in lines:
            # Заголовки
            if line.startswith('# '):
                html_lines.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html_lines.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('#### '):
                html_lines.append(f'<h4>{line[5:]}</h4>')
            # Жирный текст
            elif '**' in line:
                line = line.replace('**', '<b>', 1)
                line = line.replace('**', '</b>', 1)
                html_lines.append(f'<p>{line}</p>')
            # Курсив
            elif '*' in line and not line.startswith('* '):
                line = line.replace('*', '<i>', 1)
                line = line.replace('*', '</i>', 1)
                html_lines.append(f'<p>{line}</p>')
            # Списки
            elif line.startswith('* '):
                html_lines.append(f'<li>{line[2:]}</li>')
            elif line.startswith('- '):
                html_lines.append(f'<li>{line[2:]}</li>')
            # Пустые строки
            elif line.strip() == '':
                html_lines.append('<br>')
            # Обычный текст
            else:
                html_lines.append(f'<p>{line}</p>')

        # Объединяем списки
        html = []
        in_list = False

        for line in html_lines:
            if line.startswith('<li>'):
                if not in_list:
                    html.append('<ul>')
                    in_list = True
                html.append(line)
            else:
                if in_list:
                    html.append('</ul>')
                    in_list = False
                html.append(line)

        if in_list:
            html.append('</ul>')

        return ''.join(html)

    def get_page(self, path: str, return_content: bool = True) -> Dict[str, Any]:
        """
        Получение информации о странице

        Args:
            path: Путь к странице (например, "Hello-12-31")
            return_content: Возвращать ли содержимое

        Returns:
            Словарь с данными страницы
        """
        url = f"{self.BASE_URL}/getPage"
        params = {
            "path": path,
            "return_content": return_content
        }

        response = self.session.get(url, params=params)
        return response.json()

    def edit_page(
        self,
        path: str,
        title: str,
        content: str,
        author_name: str = "",
        author_url: str = "",
        return_content: bool = False
    ) -> Dict[str, Any]:
        """
        Редактирование существующей страницы

        Args:
            path: Путь к странице
            title: Новый заголовок
            content: Новое содержимое в формате HTML
            author_name: Имя автора
            author_url: URL автора
            return_content: Возвращать ли содержимое

        Returns:
            Словарь с результатом редактирования
        """
        if not self.access_token:
            raise ValueError("Access token is required.")

        url = f"{self.BASE_URL}/editPage"
        params = {
            "access_token": self.access_token,
            "path": path,
            "title": title,
            "author_name": author_name,
            "author_url": author_url,
            "content": content,
            "return_content": return_content
        }

        response = self.session.get(url, params=params)
        return response.json()

    def get_account_info(self, fields: list = ["short_name", "author_name", "author_url", "auth_url", "page_count"]) -> Dict[str, Any]:
        """
        Получение информации об аккаунте

        Args:
            fields: Список полей для получения

        Returns:
            Словарь с информацией об аккаунте
        """
        if not self.access_token:
            raise ValueError("Access token is required.")

        url = f"{self.BASE_URL}/getAccountInfo"
        params = {
            "access_token": self.access_token,
            "fields": json.dumps(fields)
        }

        response = self.session.get(url, params=params)
        return response.json()

    def revoke_access_token(self) -> Dict[str, Any]:
        """
        Отзыв текущего токена доступа и создание нового

        Returns:
            Словарь с новым токеном
        """
        if not self.access_token:
            raise ValueError("Access token is required.")

        url = f"{self.BASE_URL}/revokeAccessToken"
        params = {
            "access_token": self.access_token
        }

        response = self.session.get(url, params=params)
        result = response.json()

        if result.get("ok") and "access_token" in result.get("result", {}):
            self.access_token = result["result"]["access_token"]

        return result


def publish_to_telegraph(
    title: str,
    content: str,
    access_token: Optional[str] = None,
    author_name: str = "",
    author_url: str = "",
    is_markdown: bool = False
) -> str:
    """
    Функция для быстрой публикации статьи на Telegra.ph

    Args:
        title: Заголовок статьи
        content: Содержимое статьи (HTML или Markdown)
        access_token: Токен доступа Telegra.ph
        author_name: Имя автора
        author_url: URL автора
        is_markdown: True если content в формате Markdown

    Returns:
        URL опубликованной статьи
    """
    publisher = TelegraphPublisher(access_token)

    if is_markdown:
        result = publisher.create_page_from_markdown(title, content, author_name, author_url)
    else:
        result = publisher.create_page(title, content, author_name, author_url)

    if result.get("ok"):
        return f"https://telegra.ph/{result['result']['path']}"
    else:
        raise Exception(f"Failed to publish: {result.get('error', 'Unknown error')}")


# Пример использования
if __name__ == "__main__":
    # Пример 1: Создание аккаунта
    publisher = TelegraphPublisher()
    account_info = publisher.create_account(
        short_name="TestBot",
        author_name="Test Author",
        author_url="https://example.com"
    )

    if account_info.get("ok"):
        access_token = account_info["result"]["access_token"]
        print(f"Access token: {access_token}")

        # Пример 2: Публикация статьи
        publisher.access_token = access_token

        # HTML контент
        html_content = "<p>Это тестовая статья.</p><p><b>Жирный текст</b> и <i>курсив</i>.</p>"

        result = publisher.create_page(
            title="Тестовая статья",
            content=html_content,
            author_name="Test Author"
        )

        if result.get("ok"):
            url = f"https://telegra.ph/{result['result']['path']}"
            print(f"Статья опубликована: {url}")
        else:
            print(f"Ошибка: {result.get('error')}")

    # Пример 3: Быстрая публикация через функцию
    try:
        url = publish_to_telegraph(
            title="Быстрая статья",
            content="## Заголовок\n\nЭто содержимое статьи.",
            author_name="Автор",
            is_markdown=True
        )
        print(f"Опубликовано: {url}")
    except Exception as e:
        print(f"Ошибка: {e}")