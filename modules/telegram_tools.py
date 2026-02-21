import os

def register_tools(registry):
    registry.register("send_file", send_file, "Sends a file to the user. Arguments: filepath (str). Context (bot, chat_id) is injected automatically.", requires_context=True)
    registry.register("send_message", send_message, "Sends a separate message to the user. Arguments: text (str). Context (bot, chat_id) is injected automatically.", requires_context=True)

async def send_file(filepath, bot=None, chat_id=None, **kwargs):
    """Sends a file to the user via Telegram."""
    if not bot or not chat_id:
        return "Error: Telegram context missing. This tool can only be used within the bot."
    if not os.path.exists(filepath):
        return f"Error: File '{filepath}' not found."

    try:
        await bot.send_document(chat_id=chat_id, document=filepath)
        return f"File '{filepath}' sent successfully."
    except Exception as e:
        return f"Error sending file: {str(e)}"

async def send_message(text, bot=None, chat_id=None, **kwargs):
    """Sends a message to the user via Telegram."""
    if not bot or not chat_id:
        return "Error: Telegram context missing."
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        return "Message sent."
    except Exception as e:
        return f"Error sending message: {str(e)}"
