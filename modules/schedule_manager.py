import sys
sys.path.append('modules')

from schedule_reminder import get_today_schedule, get_tomorrow_schedule, format_schedule_message, set_week_type, get_current_week_type
from auto_schedule_reminders import send_evening_reminder, send_morning_reminder, setup_daily_reminders, get_reminder_status, check_and_send_reminders
from irkutsk_time import get_irkutsk_time

def show_today_schedule():
    """Показывает расписание на сегодня"""
    schedule = get_today_schedule()
    return format_schedule_message(schedule, "📅 Расписание на сегодня")

def show_tomorrow_schedule():
    """Показывает расписание на завтра"""
    schedule = get_tomorrow_schedule()
    return format_schedule_message(schedule, "📅 Расписание на завтра")

def change_week_type(new_type):
    """Меняет тип недели"""
    if new_type in ['числитель', 'знаменатель']:
        result = set_week_type(new_type)
        return f"{result}\n{show_today_schedule()}"
    else:
        return "Ошибка: тип недели должен быть 'числитель' или 'знаменатель'"

def get_schedule_info():
    """Возвращает полную информацию о расписании"""
    irkutsk_time = get_irkutsk_time()
    week_type = get_current_week_type()

    # Получаем день недели на русском
    days_map = {
        'Monday': 'ПН', 'Tuesday': 'ВТ', 'Wednesday': 'СР',
        'Thursday': 'ЧТ', 'Friday': 'ПТ', 'Saturday': 'СБ', 'Sunday': 'ВС'
    }
    day_ru = days_map.get(irkutsk_time['day_of_week'], 'ПН')

    info = [
        f"📊 Информация о расписании:",
        f"• Текущее время: {irkutsk_time['time']}",
        f"• День недели: {day_ru}",
        f"• Тип недели: {week_type}",
        f"",
        f"{show_today_schedule()}",
        f"",
        f"{show_tomorrow_schedule()}",
        f"",
        f"{get_reminder_status()}"
    ]

    return "\n".join(info)

def manual_reminder_test():
    """Тестовая отправка напоминаний"""
    messages = []

    # Вечернее напоминание
    evening = send_evening_reminder()
    if evening:
        messages.append(evening)

    # Утреннее напоминание
    morning = send_morning_reminder()
    if morning:
        messages.append(morning)

    if messages:
        return "\n\n---\n\n".join(messages)
    else:
        return "Напоминания не требуются в текущее время"

def process_user_command(command):
    """Обрабатывает команды пользователя"""
    command = command.lower().strip()

    if command in ['сегодня', 'пары сегодня', 'расписание сегодня']:
        return show_today_schedule()

    elif command in ['завтра', 'пары завтра', 'расписание завтра']:
        return show_tomorrow_schedule()

    elif command in ['числитель', 'знаменатель']:
        return change_week_type(command)

    elif command in ['статус', 'инфо', 'информация']:
        return get_schedule_info()

    elif command in ['напоминания', 'ремнинд']:
        return get_reminder_status()

    elif command in ['тест напоминаний', 'тест']:
        return manual_reminder_test()

    elif command in ['помощь', 'help']:
        return get_help()

    else:
        return f"Неизвестная команда: {command}\n{get_help()}"

def get_help():
    """Возвращает справку по командам"""
    return """
📚 Команды управления расписанием:

• "сегодня" - расписание на сегодня
• "завтра" - расписание на завтра
• "числитель" - переключить на неделю числитель
• "знаменатель" - переключить на неделю знаменатель
• "статус" - полная информация о расписании
• "напоминания" - статус системы напоминаний
• "тест" - тестовая отправка напоминаний
• "помощь" - эта справка

💡 Система автоматически напоминает:
   - Вечером в 20:00 о парах на завтра
   - Утром за 2 часа до первой пары
"""