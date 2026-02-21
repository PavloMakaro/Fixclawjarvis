def register_tools(registry):
    registry.register("set_reminder", set_reminder, "Sets a one-time reminder. Arguments: seconds (int), message (str).", requires_context=True)
    registry.register("schedule_recurring_task", schedule_recurring_task, "Schedules a recurring task (e.g. daily weather). Arguments: time (str, 'HH:MM'), prompt (str).", requires_context=True)

async def alarm(context):
    """Callback function for the alarm job."""
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"🔔 REMINDER: {job.data}")

async def set_reminder(seconds, message, job_queue=None, chat_id=None, **kwargs):
    """Sets a one-time reminder."""
    if not job_queue or not chat_id:
        return "Error: JobQueue or ChatID missing from context."

    try:
        job_queue.run_once(alarm, seconds, chat_id=chat_id, data=message)
        return f"Reminder set for {seconds} seconds from now."
    except Exception as e:
        return f"Error setting reminder: {str(e)}"

async def schedule_recurring_task(time="08:00", prompt="Check weather", job_queue=None, chat_id=None, agent_runner=None, **kwargs):
    """Schedules a daily recurring task that runs the agent with a prompt."""
    if not job_queue or not chat_id:
        return "Error: JobQueue or ChatID missing."
    if not agent_runner:
        return "Error: Agent runner callback not found in context. Cannot schedule task."

    try:
        import datetime

        hour, minute = map(int, time.split(":"))
        t = datetime.time(hour=hour, minute=minute)

        job_name = f"recurring_{chat_id}_{int(datetime.datetime.now().timestamp())}"
        job_queue.run_daily(agent_runner, t, chat_id=chat_id, data=prompt, name=job_name)

        return f"Scheduled daily task '{prompt}' at {time}."
    except Exception as e:
        return f"Error scheduling task: {str(e)}"
