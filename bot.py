import logging
import asyncio
import os
import time
import json
import datetime
import traceback
import mimetypes
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
import config
from core.agent import Agent
from core.tools import ToolRegistry
from core.watcher import ModuleWatcher
from core.display import AgentDisplay

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Initialize Tools
registry = ToolRegistry()
registry.load_modules()

# Initialize Watcher
watcher = ModuleWatcher(registry)
watcher.start()

# Initialize Agent
agent = Agent(registry)

# Persistence
SESSIONS_FILE = "data/sessions.json"
PROFILE_FILE = "data/profiles.json"
DOWNLOADS_DIR = "downloads"


def ensure_downloads_dir():
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR)


ensure_downloads_dir()


def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_sessions():
    if not os.path.exists("data"):
        os.makedirs("data")
    with open(SESSIONS_FILE, "w") as f:
        json.dump(user_sessions, f)


def load_profiles():
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


# In-memory session storage (loaded from file)
user_sessions = load_sessions()
user_profiles = load_profiles()
user_usage = {} # Session token usage
session_lock = asyncio.Lock()

# Token Encoder
def count_tokens(text):
    if not text: return 0
    return len(str(text)) // 4

# Task management for stopping
running_tasks = {}

async def summarize_history(history_slice):
    """Summarizes a slice of conversation history."""
    try:
        prompt = "Summarize the following conversation concisely in 2-3 sentences, preserving key facts and context:"
        msgs = [{"role": "system", "content": prompt}]
        for m in history_slice:
            role = m.get("role", "unknown")
            content = m.get("content", "")
            msgs.append({"role": "user", "content": f"{role}: {content}"})

        # Use agent's LLM non-streaming
        response_msg = await agent.llm.generate(msgs, stream=False)
        if response_msg and response_msg.content:
            return response_msg.content
    except Exception as e:
        logging.error(f"Summarization failed: {e}")
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    async with session_lock:
        user_sessions[chat_id] = []
        save_sessions()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello! I am your AI assistant. I can help you with tasks, manage your diary, and more.",
    )


async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    async with session_lock:
        user_sessions[chat_id] = []
        save_sessions()
    await context.bot.send_message(chat_id=chat_id, text="Memory cleared.")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in running_tasks:
        task = running_tasks[chat_id]
        if not task.done():
            task.cancel()
            await context.bot.send_message(chat_id=chat_id, text="Stopped.")
        else:
            await context.bot.send_message(chat_id=chat_id, text="Nothing is running.")
    else:
        await context.bot.send_message(chat_id=chat_id, text="Nothing is running.")


async def save_user_file(file_obj, chat_id, original_filename=None):
    """Downloads a file and returns the local path."""
    timestamp = int(time.time())

    # Create user-specific dir inside downloads
    user_dir = os.path.join(DOWNLOADS_DIR, str(chat_id))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    if original_filename:
        filename = f"{timestamp}_{original_filename}"
    else:
        # Generate generic name if not provided
        ext = ".bin"
        if hasattr(file_obj, "file_path") and file_obj.file_path:
            _, ext = os.path.splitext(file_obj.file_path)
        filename = f"{timestamp}_file{ext}"

    filepath = os.path.join(user_dir, filename)
    await file_obj.download_to_drive(filepath)
    return filepath


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    chat_id = str(update.effective_chat.id)

    # Cancel previous task if running
    if chat_id in running_tasks:
        task = running_tasks[chat_id]
        if not task.done():
            task.cancel()

    # Create new task
    task = asyncio.create_task(process_agent_loop(chat_id, user_input, context))
    running_tasks[chat_id] = task
    try:
        await task
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Task failed: {e}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    status_msg = await context.bot.send_message(
        chat_id=chat_id, text="Receiving voice message..."
    )

    try:
        file = await update.message.voice.get_file()
        filepath = await save_user_file(file, chat_id, f"voice.ogg")

        caption = update.message.caption or ""

        # Add file context to history immediately
        async with session_lock:
            if chat_id not in user_sessions:
                user_sessions[chat_id] = []
            user_sessions[chat_id].append(
                {
                    "role": "user",
                    "content": f"[Voice file uploaded to {filepath}]. Caption: {caption}",
                }
            )
            save_sessions()

        # Trigger Agent
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text="Voice received. Transcribing...",
        )

        prompt = "Please transcribe this voice message."
        if caption:
            prompt += f" Context: {caption}"

        if chat_id in running_tasks:
            task = running_tasks[chat_id]
            if not task.done():
                task.cancel()

        task = asyncio.create_task(process_agent_loop(chat_id, prompt, context))
        running_tasks[chat_id] = task
        try:
            await task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, text=f"Error processing voice: {str(e)}"
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    # Handle multiple photos (media groups) properly by just logging them and letting agent pick up
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        filepath = await save_user_file(file, chat_id, f"image.jpg")

        caption = update.message.caption or ""

        async with session_lock:
            if chat_id not in user_sessions:
                user_sessions[chat_id] = []
            user_sessions[chat_id].append(
                {
                    "role": "user",
                    "content": f"[Image uploaded to {filepath}]. Caption: {caption}",
                }
            )
            save_sessions()

        # Trigger Agent
        # If part of an album, subsequent triggers might cancel this one, but history is saved.
        # We rely on the last trigger to process all recent images.

        prompt = "Analyze this image."
        if caption:
            prompt = caption  # Use caption as the prompt if provided

        # Optional: Check if we are already processing (simple debounce)
        # But cancellation handles this. The last image in a burst will trigger the final analysis.

        if chat_id in running_tasks:
            task = running_tasks[chat_id]
            if not task.done():
                task.cancel()

        # Send status only if no recent status exists?
        # Actually, let's just send a temp message that gets edited by agent loop
        status_msg = await context.bot.send_message(
            chat_id=chat_id, text="Image received. Analyzing..."
        )

        # We need to pass the status_msg ID to process_agent_loop so it can edit it.
        # But process_agent_loop creates its own "Thinking..." message.
        # Let's delete our temp message to avoid clutter or let agent overwrite.
        # Better: Modify process_agent_loop to accept an existing message object to edit?
        # For simplicity, we just delete our temp message and let agent create its own.
        await context.bot.delete_message(
            chat_id=chat_id, message_id=status_msg.message_id
        )

        task = asyncio.create_task(process_agent_loop(chat_id, prompt, context))
        running_tasks[chat_id] = task
        try:
            await task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, text=f"Error processing image: {str(e)}"
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    try:
        doc = update.message.document
        file = await doc.get_file()
        filepath = await save_user_file(file, chat_id, doc.file_name)

        caption = update.message.caption or ""

        async with session_lock:
            if chat_id not in user_sessions:
                user_sessions[chat_id] = []
            user_sessions[chat_id].append(
                {
                    "role": "user",
                    "content": f"[File uploaded to {filepath}]. Caption: {caption}",
                }
            )
            save_sessions()

        prompt = "Analyze this file."
        if caption:
            prompt = caption

        if chat_id in running_tasks:
            task = running_tasks[chat_id]
            if not task.done():
                task.cancel()

        status_msg = await context.bot.send_message(
            chat_id=chat_id, text="File received. Processing..."
        )
        await context.bot.delete_message(
            chat_id=chat_id, message_id=status_msg.message_id
        )

        task = asyncio.create_task(process_agent_loop(chat_id, prompt, context))
        running_tasks[chat_id] = task
        try:
            await task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, text=f"Error processing file: {str(e)}"
        )


async def process_agent_loop(chat_id, user_input, context):
    chat_id_str = str(chat_id)

    # 1. Check Usage Quota
    current_usage = user_usage.get(chat_id_str, 0)
    if current_usage > 50000:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Session usage quota exceeded (50,000 tokens). Please use /clear to reset.")
        return

    async with session_lock:
        if chat_id_str not in user_sessions:
            user_sessions[chat_id_str] = []

        # 2. Smart Context Summarization
        hist = user_sessions[chat_id_str]
        # Calculate roughly
        total_tokens = sum(count_tokens(m.get("content", "")) for m in hist)

        # If history is too long ( > 15 messages OR > 4000 tokens)
        if len(hist) > 15 or total_tokens > 4000:
            # We want to keep the last 5 messages intact
            if len(hist) > 6:
                to_summarize = hist[:-6]
                kept_history = hist[-6:]

                # Send temporary status
                status_msg = await context.bot.send_message(chat_id=chat_id, text="🔄 Optimizing memory...")

                summary = await summarize_history(to_summarize)

                if summary:
                    # Replace old history with summary + recent
                    new_hist = [{"role": "system", "content": f"[Previous Conversation Summary]: {summary}"}] + kept_history
                    user_sessions[chat_id_str] = new_hist
                    save_sessions()
                    logging.info(f"Summarized history for {chat_id_str}")

                await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)

        # Shallow copy of CLEAN history
        session_history_start = list(user_sessions[chat_id_str])

    # Copy for agent to modify during this turn
    current_history = list(session_history_start)

    status_msg = await context.bot.send_message(chat_id=chat_id, text="Thinking...")

    # Initialize Display
    display = AgentDisplay(context, chat_id, status_msg.message_id)

    tool_ctx = {
        "bot": context.bot,
        "chat_id": chat_id,
        "job_queue": context.job_queue,
        "registry": registry,
        "agent_runner": scheduled_task_callback,  # Pass global callback
    }

    final_response = ""

    try:
        async for update_data in agent.run(
            user_input, history=current_history, tool_context=tool_ctx, plan_mode=True
        ):
            await display.update(update_data)

        # Ensure final render
        await display._try_render(force=True)
        final_response = "".join(display.final_response_parts)

    except asyncio.CancelledError:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=status_msg.message_id, text="Stopped."
        )
        return
    except Exception as e:
        final_response = f"Error in agent loop: {str(e)}"
        logging.error(f"Agent loop error: {e}")
        try:
            await context.bot.send_message(chat_id=chat_id, text=final_response)
        except:
            pass

    # GARBAGE COLLECTION & USAGE TRACKING:
    if final_response:
        # Update usage
        input_tokens = count_tokens(user_input)
        output_tokens = count_tokens(final_response)
        # Add rough estimate for system prompt and tools
        turn_usage = input_tokens + output_tokens + 500
        user_usage[chat_id_str] = user_usage.get(chat_id_str, 0) + turn_usage

        # Update history
        new_history = list(session_history_start)
        new_history.append({"role": "user", "content": user_input})
        new_history.append({"role": "assistant", "content": final_response})

        async with session_lock:
            user_sessions[chat_id_str] = new_history
            save_sessions()


async def scheduled_task_callback(context: ContextTypes.DEFAULT_TYPE):
    """Callback for scheduled recurring tasks."""
    job = context.job
    chat_id = job.chat_id
    prompt = job.data  # The prompt to run, e.g., "Check weather"

    await context.bot.send_message(chat_id=chat_id, text=f"⏰ Scheduled Task: {prompt}")

    # Run agent loop
    # Note: We need to ensure we don't block the job queue worker too long.
    # process_agent_loop creates user session history, sends messages, etc.
    # It requires 'context' to have .bot and .job_queue. The passed 'context' has it.
    await process_agent_loop(chat_id, prompt, context)


if __name__ == "__main__":
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear_memory))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Bot is running...")
    application.run_polling()
