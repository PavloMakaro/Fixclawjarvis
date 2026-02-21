import time
import asyncio
from telegram.constants import ParseMode
import logging

logger = logging.getLogger(__name__)

class AgentDisplay:
    def __init__(self, context, chat_id, message_id):
        self.context = context
        self.chat_id = chat_id
        self.message_id = message_id

        self.logs = [] # List of (type, content) tuples
        # Types: 'thinking', 'tool_call', 'tool_result'

        self.final_response_parts = []

        self.last_render_time = 0
        self.render_interval = 2.0 # Update every 2 seconds to avoid flood limits
        self.lock = asyncio.Lock()

        self.current_thinking_buffer = []

    async def update(self, state_update):
        status = state_update.get("status")
        content = state_update.get("content")

        should_render = False

        if status == "thinking":
            if content:
                self.current_thinking_buffer.append(content)
                should_render = True

        elif status == "tool_use":
            # Flush thinking buffer if any
            if self.current_thinking_buffer:
                self.logs.append(('thinking', "".join(self.current_thinking_buffer)))
                self.current_thinking_buffer = []

            tool_name = state_update.get("tool")
            args = state_update.get("args")
            self.logs.append(('tool_call', f"{tool_name}({args})"))
            should_render = True

        elif status == "observation":
            result = state_update.get("result")
            self.logs.append(('tool_result', result))
            should_render = True

        elif status == "final_stream":
            # Flush thinking buffer if any
            if self.current_thinking_buffer:
                self.logs.append(('thinking', "".join(self.current_thinking_buffer)))
                self.current_thinking_buffer = []

            if content:
                self.final_response_parts.append(content)
                should_render = True

        elif status == "final":
             # Flush thinking buffer
            if self.current_thinking_buffer:
                self.logs.append(('thinking', "".join(self.current_thinking_buffer)))
                self.current_thinking_buffer = []

            self.final_response_parts = [content] if content else []
            should_render = True

        if should_render:
            await self._try_render()

    async def _try_render(self, force=False):
        now = time.time()
        if not force and (now - self.last_render_time < self.render_interval):
            return

        async with self.lock:
            try:
                text = self._build_text()
                # If text hasn't changed effectively (logic handled by Telegram usually, but we can check hash)
                # Just send
                await self.context.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self.message_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                self.last_render_time = time.time()
            except Exception as e:
                # Often fails due to "Message is not modified" or rate limits
                # logger.warning(f"Display render error: {e}")
                pass

    def _build_text(self):
        # Build the log string
        lines = []

        # Add current thinking buffer to view implicitly
        current_think = "".join(self.current_thinking_buffer)

        # We want to show the last few log entries to avoid hitting message length limits
        # Strategy:
        # 1. Show all Thinking/Tools in a blockquote (simulating CLI)
        # 2. Show Final Answer outside

        log_text = ""
        for type_, content in self.logs:
            if type_ == 'thinking':
                # Sanitize HTML
                safe_content = self._sanitize_html(content)
                log_text += f"🧠 <i>Thought:</i> {safe_content}\n\n"
            elif type_ == 'tool_call':
                safe_content = self._sanitize_html(content)
                log_text += f"🛠 <b>Exec:</b> <code>{safe_content}</code>\n"
            elif type_ == 'tool_result':
                # Truncate result
                safe_content = self._sanitize_html(str(content)[:200] + ("..." if len(str(content)) > 200 else ""))
                log_text += f"✅ <b>Result:</b> {safe_content}\n\n"

        if current_think:
            safe_think = self._sanitize_html(current_think)
            log_text += f"🧠 <i>Thinking...</i> {safe_think}\n"

        # Limit log text length to keep message valid (Telegram limit 4096)
        # We reserve 2000 chars for final answer
        max_log_len = 2000
        if len(log_text) > max_log_len:
            log_text = "...(earlier logs)...\n" + log_text[-(max_log_len):]

        final_text = "".join(self.final_response_parts)

        # Combine
        full_text = ""
        if log_text:
            full_text += f"<blockquote>{log_text}</blockquote>\n\n"

        full_text += self._sanitize_html(final_text)

        if not full_text:
            full_text = "..."

        return full_text

    def _sanitize_html(self, text):
        # Basic replacement of < > &
        if not text: return ""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
