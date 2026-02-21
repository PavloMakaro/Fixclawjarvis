"""
Diary module - ASYNC VERSION (legacy wrapper for Telegram job_queue)
"""

import asyncio
import os
import datetime
from typing import Optional

DIARY_FILE = "data/diary.txt"


async def add_entry(text: str) -> str:
    """Add a diary entry"""
    try:
        os.makedirs("data", exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {text}\n"

        def _write():
            with open(DIARY_FILE, "a", encoding="utf-8") as f:
                f.write(entry)

        await asyncio.to_thread(_write)
        return "Diary entry added."
    except Exception as e:
        return f"Error writing to diary: {str(e)}"


async def read_entries(date: Optional[str] = None) -> str:
    """Read diary entries"""
    try:
        if not os.path.exists(DIARY_FILE):
            return "Diary is empty."

        def _read():
            with open(DIARY_FILE, "r", encoding="utf-8") as f:
                return f.read()

        content = await asyncio.to_thread(_read)

        if date:
            filtered = [
                line for line in content.splitlines() if line.startswith(f"[{date}")
            ]
            return "\n".join(filtered) if filtered else f"No entries found for {date}."

        return (
            content[-2000:] + "\n...(showing last 2000 chars)"
            if len(content) > 2000
            else content
        )
    except Exception as e:
        return f"Error reading diary: {str(e)}"


async def diary_alarm(context):
    """Callback function for the diary alarm job"""
    job = context.job
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    has_entry = False
    if os.path.exists(DIARY_FILE):

        def _check():
            with open(DIARY_FILE, "r", encoding="utf-8") as f:
                return today in f.read()

        has_entry = await asyncio.to_thread(_check)

    if not has_entry:
        await context.bot.send_message(
            job.chat_id,
            text="📓 DIARY PROMPT: You haven't written in your diary today. How was your day? (Reply with voice or text)",
        )


async def setup_reminder(
    time_str: str = "20:00", job_queue=None, chat_id=None, **kwargs
) -> str:
    """Set up a daily diary reminder"""
    if not job_queue or not chat_id:
        return "Error: JobQueue or ChatID missing."

    try:
        hour, minute = map(int, time_str.split(":"))
        t = datetime.time(hour=hour, minute=minute)

        job_queue.run_daily(diary_alarm, t, chat_id=chat_id, name=f"diary_{chat_id}")
        return f"Daily diary reminder set for {time_str}."
    except Exception as e:
        return f"Error setting reminder: {str(e)}"


def register_tools(registry):
    """Register diary tools"""
    registry.register(
        "add_diary_entry", add_entry, "Add entry to diary. Arguments: text (str)"
    )
    registry.register(
        "read_diary",
        read_entries,
        "Read diary entries. Arguments: date (str, optional)",
    )
    registry.register(
        "setup_diary_reminder",
        setup_reminder,
        "Setup daily diary reminder. Arguments: time (str)",
        requires_context=True,
    )
