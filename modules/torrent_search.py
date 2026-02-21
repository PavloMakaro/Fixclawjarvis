import requests
from bs4 import BeautifulSoup
import re

def search_rutracker(query):
    """Поиск на rutracker.org"""
    try:
        url = f"https://rutracker.org/forum/tracker.php?nm={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # Поиск результатов
        for row in soup.find_all('tr', class_='tCenter hl-tr'):
            title_elem = row.find('a', class_='torTopic')
            if title_elem:
                title = title_elem.text.strip()
                link = "https://rutracker.org/forum/" + title_elem['href']
                results.append({
                    'title': title,
                    'url': link
                })

        return {
            'success': True,
            'query': query,
            'results': results[:10],  # первые 10 результатов
            'source': 'rutracker.org'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'query': query,
            'source': 'rutracker.org'
        }

def search_1337x(query):
    """Поиск на 1337x.to"""
    try:
        url = f"https://1337x.to/search/{requests.utils.quote(query)}/1/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # Поиск результатов в таблице
        table = soup.find('table', class_='table-list')
        if table:
            for row in table.find_all('tr')[1:]:  # пропускаем заголовок
                cells = row.find_all('td')
                if len(cells) >= 1:
                    title_elem = cells[0].find('a', href=re.compile(r'/torrent/'))
                    if title_elem:
                        title = title_elem.text.strip()
                        link = "https://1337x.to" + title_elem['href']
                        results.append({
                            'title': title,
                            'url': link
                        })

        return {
            'success': True,
            'query': query,
            'results': results[:10],
            'source': '1337x.to'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'query': query,
            'source': '1337x.to'
        }

if __name__ == "__main__":
    # Тестирование
    print("Поиск Garry's Mod на rutracker:")
    result1 = search_rutracker("Garry's Mod")
    print(result1)

    print("\nПоиск Garry's Mod на 1337x:")
    result2 = search_1337x("Garry's Mod")
    print(result2)