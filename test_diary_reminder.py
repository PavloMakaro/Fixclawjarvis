import sys
sys.path.append('modules')

from auto_diary_reminder import setup_diary_reminder, check_diary_reminder_status, get_diary_stats

print('📓 НАСТРОЙКА НАПОМИНАНИЯ ДЛЯ ДНЕВНИКА:')

result = setup_diary_reminder()
print(f"✅ {result['message']}")
print()

status = check_diary_reminder_status()
print(f"⏰ Текущее время: {status['current_time']}")
print(f"🔔 Напоминание: {status['reminder_time']}")
print(f"📅 Следующее: {status['next_reminder_in']}")
print()

stats = get_diary_stats()
if stats['exists']:
    print(f"📊 Статистика дневника: {stats['entry_count']} записей")
    print(f"📅 Последняя запись: {stats['last_entry']}")
else:
    print(f"📊 {stats['message']}")