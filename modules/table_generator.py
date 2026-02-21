#!/usr/bin/env python3
"""
Модуль для создания красивых таблиц в терминале и Markdown
"""

from typing import List, Dict, Any, Optional, Union
import textwrap
from datetime import datetime

class TableGenerator:
    """Генератор красивых таблиц"""

    def __init__(self, title: str = ""):
        self.title = title
        self.headers = []
        self.rows = []
        self.column_widths = []
        self.styles = {
            'border': '─│┌┐└┘├┤┬┴┼',
            'header_separator': '═',
            'row_separator': '─',
            'corner': '╔╗╚╝╠╣╦╩╬',
            'simple': '┌─┐└─┘├─┤┬─┴┼'
        }
        self.style = 'border'

    def set_headers(self, headers: List[str]):
        """Установить заголовки таблицы"""
        self.headers = headers
        self._calculate_column_widths()

    def add_row(self, row: List[Any]):
        """Добавить строку данных"""
        self.rows.append(row)
        self._calculate_column_widths()

    def add_rows(self, rows: List[List[Any]]):
        """Добавить несколько строк"""
        self.rows.extend(rows)
        self._calculate_column_widths()

    def _calculate_column_widths(self):
        """Рассчитать ширину колонок"""
        all_data = []
        if self.headers:
            all_data.append(self.headers)
        all_data.extend(self.rows)

        if not all_data:
            return

        num_cols = len(all_data[0])
        self.column_widths = [0] * num_cols

        for row in all_data:
            for i, cell in enumerate(row):
                cell_str = str(cell)
                # Учитываем переносы строк
                lines = cell_str.split('\n')
                max_line_len = max(len(line) for line in lines) if lines else 0
                self.column_widths[i] = max(self.column_widths[i], max_line_len)

        # Минимальная ширина 3 символа
        self.column_widths = [max(w, 3) for w in self.column_widths]

    def _format_cell(self, cell: Any, width: int) -> str:
        """Форматировать ячейку"""
        cell_str = str(cell)
        lines = cell_str.split('\n')
        formatted_lines = []

        for line in lines:
            # Обрезать или дополнить пробелами
            if len(line) > width:
                line = line[:width-3] + '...'
            formatted_lines.append(line.ljust(width))

        return '\n'.join(formatted_lines)

    def generate_terminal_table(self) -> str:
        """Сгенерировать таблицу для терминала"""
        if not self.headers and not self.rows:
            return "Пустая таблица"

        # Определить символы границ
        if self.style == 'simple':
            chars = self.styles['simple']
            top_left, top_right, bottom_left, bottom_right = chars[0], chars[2], chars[3], chars[5]
            vertical, horizontal = chars[1], chars[1]
            cross = chars[8]
            t_down, t_up, t_right, t_left = chars[6], chars[7], chars[4], chars[7]
        else:
            chars = self.styles['border']
            top_left, top_right, bottom_left, bottom_right = chars[0], chars[1], chars[2], chars[3]
            vertical, horizontal = chars[4], chars[0]
            cross = chars[8]
            t_down, t_up, t_right, t_left = chars[6], chars[7], chars[5], chars[7]

        # Верхняя граница
        top_border = top_left + horizontal * (sum(self.column_widths) + len(self.column_widths) * 3 - 1) + top_right

        # Заголовки
        header_lines = []
        if self.headers:
            header_cells = []
            for i, header in enumerate(self.headers):
                header_cells.append(self._format_cell(header, self.column_widths[i]))

            # Определить максимальное количество строк в заголовках
            max_header_lines = max(len(cell.split('\n')) for cell in header_cells)

            for line_num in range(max_header_lines):
                line_parts = []
                for cell in header_cells:
                    cell_lines = cell.split('\n')
                    line_parts.append(cell_lines[line_num] if line_num < len(cell_lines) else ' ' * self.column_widths[i])
                header_lines.append(vertical + ' ' + ' ' + vertical + ' '.join(line_parts) + ' ' + vertical)

            # Разделитель заголовков
            if self.style == 'simple':
                header_separator = t_right + horizontal * (sum(self.column_widths) + len(self.column_widths) * 3 - 1) + t_left
            else:
                header_separator = t_down + horizontal * (sum(self.column_widths) + len(self.column_widths) * 3 - 1) + t_up
        else:
            header_lines = []
            header_separator = ""

        # Строки данных
        row_lines = []
        for row_idx, row in enumerate(self.rows):
            row_cells = []
            for i, cell in enumerate(row):
                row_cells.append(self._format_cell(cell, self.column_widths[i]))

            # Определить максимальное количество строк в строке
            max_row_lines = max(len(cell.split('\n')) for cell in row_cells)

            for line_num in range(max_row_lines):
                line_parts = []
                for cell in row_cells:
                    cell_lines = cell.split('\n')
                    line_parts.append(cell_lines[line_num] if line_num < len(cell_lines) else ' ' * self.column_widths[i])
                row_lines.append(vertical + ' ' + ' ' + vertical + ' '.join(line_parts) + ' ' + vertical)

            # Разделитель строк (кроме последней)
            if row_idx < len(self.rows) - 1:
                if self.style == 'simple':
                    row_separator = t_right + horizontal * (sum(self.column_widths) + len(self.column_widths) * 3 - 1) + t_left
                else:
                    row_separator = cross + horizontal * (sum(self.column_widths) + len(self.column_widths) * 3 - 1) + cross
                row_lines.append(row_separator)

        # Нижняя граница
        bottom_border = bottom_left + horizontal * (sum(self.column_widths) + len(self.column_widths) * 3 - 1) + bottom_right

        # Сборка таблицы
        table_parts = []
        if self.title:
            table_parts.append(f"╔{'═' * (len(self.title) + 4)}╗")
            table_parts.append(f"║  {self.title}  ║")
            table_parts.append(f"╚{'═' * (len(self.title) + 4)}╝")
            table_parts.append("")

        table_parts.append(top_border)
        if header_lines:
            table_parts.extend(header_lines)
            table_parts.append(header_separator)
        table_parts.extend(row_lines)
        table_parts.append(bottom_border)

        return '\n'.join(table_parts)

    def generate_markdown_table(self) -> str:
        """Сгенерировать таблицу в формате Markdown"""
        if not self.headers:
            return "Заголовки не установлены"

        # Заголовки
        header_line = '| ' + ' | '.join(self.headers) + ' |'
        separator_line = '|' + '|'.join(['---' for _ in self.headers]) + '|'

        # Строки данных
        rows_lines = []
        for row in self.rows:
            row_cells = []
            for i, cell in enumerate(row):
                cell_str = str(cell)
                # Экранировать символы Markdown
                cell_str = cell_str.replace('|', '\\|')
                row_cells.append(cell_str)
            rows_lines.append('| ' + ' | '.join(row_cells) + ' |')

        # Сборка таблицы
        table_parts = []
        if self.title:
            table_parts.append(f"## {self.title}")
            table_parts.append("")

        table_parts.append(header_line)
        table_parts.append(separator_line)
        table_parts.extend(rows_lines)

        return '\n'.join(table_parts)

    def generate_html_table(self, css_class: str = "") -> str:
        """Сгенерировать HTML таблицу"""
        if not self.headers:
            return "<p>Заголовки не установлены</p>"

        html_parts = []

        # Начало таблицы
        if css_class:
            html_parts.append(f'<table class="{css_class}">')
        else:
            html_parts.append('<table style="border-collapse: collapse; width: 100%;">')

        # Заголовки
        html_parts.append('<thead>')
        html_parts.append('<tr>')
        for header in self.headers:
            html_parts.append(f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;">{header}</th>')
        html_parts.append('</tr>')
        html_parts.append('</thead>')

        # Тело таблицы
        html_parts.append('<tbody>')
        for row in self.rows:
            html_parts.append('<tr>')
            for cell in row:
                cell_str = str(cell)
                html_parts.append(f'<td style="border: 1px solid #ddd; padding: 8px;">{cell_str}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')

        html_parts.append('</table>')

        return '\n'.join(html_parts)

    def save_to_file(self, filename: str, format: str = "terminal"):
        """Сохранить таблицу в файл"""
        if format == "markdown":
            content = self.generate_markdown_table()
        elif format == "html":
            content = self.generate_html_table()
        else:
            content = self.generate_terminal_table()

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Таблица сохранена в {filename}"


# Функции для быстрого создания таблиц
def create_simple_table(headers: List[str], rows: List[List[Any]], title: str = "") -> str:
    """Быстро создать простую таблицу"""
    table = TableGenerator(title)
    table.set_headers(headers)
    table.add_rows(rows)
    return table.generate_terminal_table()


def create_markdown_table(headers: List[str], rows: List[List[Any]], title: str = "") -> str:
    """Быстро создать Markdown таблицу"""
    table = TableGenerator(title)
    table.set_headers(headers)
    table.add_rows(rows)
    return table.generate_markdown_table()


def create_ai_models_table() -> str:
    """Создать таблицу с топовыми ИИ моделями"""
    headers = ["Ранг", "Модель", "Разработчик", "GPQA Diamond", "AIME 2025", "SWE Bench", "Цена (1M токенов)"]

    rows = [
        [1, "Claude Opus 4.6", "Anthropic", "89.6%", "N/A", "80.9%", "$5/$25"],
        [2, "Claude Sonnet 4.6", "Anthropic", "87.5%", "N/A", "82%", "$3/$15"],
        [3, "GPT-5.2", "OpenAI", "92.4%", "100%", "80%", "$10/$30"],
        [4, "Gemini 3 Pro", "Google", "91.9%", "100%", "76.2%", "$0.5/$1.5"],
        [5, "Kimi K2 Thinking", "Moonshot AI", "N/A", "99.1%", "N/A", "Бесплатно"],
        [6, "Grok 4", "xAI", "87.5%", "N/A", "N/A", "$20 (подписка)"],
        [7, "GPT-5", "OpenAI", "87.3%", "N/A", "76.3%", "$5/$15"],
        [8, "Gemini 2.5 Pro", "Google", "N/A", "N/A", "N/A", "$0.75/$2.25"],
        [9, "GPT oss 20b", "OpenAI", "N/A", "98.7%", "N/A", "Открытая"],
        [10, "OpenAI o3", "OpenAI", "N/A", "98.4%", "N/A", "$10/$30"]
    ]

    table = TableGenerator("🏆 ТОП-10 ИИ МОДЕЛЕЙ 2025")
    table.set_headers(headers)
    table.add_rows(rows)

    return table.generate_terminal_table()


def create_open_models_table() -> str:
    """Создать таблицу с открытыми моделями"""
    headers = ["Размер", "Модель", "Разработчик", "MMLU", "GSM8K", "HumanEval", "Лицензия"]

    rows = [
        ["0.8B", "flan-t5-large", "Google", "55.2%", "45.3%", "12.2%", "Apache 2.0"],
        ["3B", "Qwen2.5-3B", "Alibaba", "68.9%", "78.5%", "45.6%", "Apache 2.0"],
        ["7B", "Qwen2.5-7B", "Alibaba", "76.4%", "85.2%", "58.9%", "Apache 2.0"],
        ["14B", "Qwen2.5-14B", "Alibaba", "81.2%", "89.7%", "67.3%", "Apache 2.0"],
        ["32B", "Qwen2.5-32B", "Alibaba", "84.5%", "92.1%", "72.8%", "Apache 2.0"],
        ["72B", "Qwen2.5-72B", "Alibaba", "86.8%", "94.3%", "78.4%", "Apache 2.0"],
        ["111B", "Qwen1.5-110B", "Alibaba", "87.2%", "95.1%", "80.2%", "Apache 2.0"]
    ]

    table = TableGenerator("📊 ТОП ОТКРЫТЫХ ИИ МОДЕЛЕЙ")
    table.set_headers(headers)
    table.add_rows(rows)

    return table.generate_terminal_table()


if __name__ == "__main__":
    # Пример использования
    print("Пример таблицы с ИИ моделями:")
    print("=" * 60)
    print(create_ai_models_table())
    print("\n" + "=" * 60)
    print("\nПример таблицы с открытыми моделями:")
    print("=" * 60)
    print(create_open_models_table())