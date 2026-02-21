from tavily import TavilyClient
import config

def register_tools(registry):
    """Регистрирует инструменты для глубокого исследования с помощью Tavily API"""
    registry.register(
        "tavily_deep_research",
        tavily_deep_research,
        "Uses Tavily API to autonomously research the web, gather context from multiple sites, "
        "and return a highly accurate synthesized answer with source URLs. Use this for complex "
        "questions, deep research, or when you need a ready-made summarized answer. Arguments: query (str)."
    )

def tavily_deep_research(query):
    """
    Выполняет глубокое исследование с использованием Tavily API.
    Tavily самостоятельно ищет информацию на нескольких сайтах, читает их
    и возвращает готовый синтезированный ответ вместе со ссылками на источники.

    Args:
        query (str): Поисковый запрос для исследования

    Returns:
        str: Синтезированный ответ с источниками или сообщение об ошибке
    """
    try:
        # Инициализация клиента Tavily
        client = TavilyClient(api_key=config.TAVILY_API_KEY)

        # Выполнение поиска с расширенными параметрами
        response = client.search(
            query=query,
            search_depth="advanced",  # Глубокий поиск
            include_answer=True,      # Включить сгенерированный ответ
            max_results=5             # Максимальное количество результатов
        )

        # Извлечение сгенерированного ответа
        answer = response.get('answer', 'No answer generated.')

        # Извлечение списка источников
        sources = response.get('results', [])

        # Формирование итоговой строки
        result = f"🔍 **Результат исследования:**\n\n{answer}\n\n"

        if sources:
            result += "📚 **Источники:**\n"
            for i, source in enumerate(sources, 1):
                title = source.get('title', 'Без названия')
                url = source.get('url', '#')
                result += f"{i}. **{title}**\n   {url}\n"
        else:
            result += "\n⚠️ **Источники не найдены**"

        return result

    except ImportError:
        return "❌ Ошибка: Библиотека 'tavily' не установлена. Установите её с помощью 'pip install tavily-python'"
    except Exception as e:
        return f"❌ Ошибка при выполнении исследования: {str(e)}"
