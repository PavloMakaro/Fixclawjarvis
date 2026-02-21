"""
Permanent memory module - ASYNC VERSION
"""

import asyncio
import os
from typing import Optional
from core.memory_rag import memory_instance

MEMORY_FILE = os.path.join("Permanent memory", "Permanent-memory")


async def update_memory(info: str) -> str:
    """Append important facts to permanent memory"""
    try:
        # Try Vector Memory first
        if memory_instance.enabled:

            def _add():
                return memory_instance.add(info)

            result = await asyncio.to_thread(_add)
            return f"Memory updated (Vector): {result}"

        # Fallback to file
        await _ensure_memory_file()

        def _append():
            with open(MEMORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n{info}")

        await asyncio.to_thread(_append)
        return f"Memory updated (File): {info}"
    except Exception as e:
        return f"Error updating memory: {str(e)}"


async def read_memory(query: str = None) -> str:
    """Retrieve facts from memory"""
    try:
        # If query provided, use vector search
        if query and memory_instance.enabled:

            def _search():
                return memory_instance.search(query, n_results=3)

            results = await asyncio.to_thread(_search)

            if results:
                formatted = "\n".join([f"- {r}" for r in results])
                return f"Relevant Memory:\n{formatted}"
            else:
                return "No relevant memory found."

        # Fallback: Read full file
        await _ensure_memory_file()

        def _read():
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return f.read()

        content = await asyncio.to_thread(_read)
        return content if content else "Memory is empty."
    except Exception as e:
        return f"Error reading memory: {str(e)}"


async def _ensure_memory_file():
    """Ensure memory file exists"""
    directory = os.path.dirname(MEMORY_FILE)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    if not os.path.exists(MEMORY_FILE):

        def _create():
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                f.write("")

        await asyncio.to_thread(_create)


async def clear_memory() -> str:
    """Clear all memory"""
    try:
        if memory_instance.enabled:

            def _clear():
                # Note: ChromaDB clear implementation depends on version
                return "Vector memory clear not implemented"

            result = await asyncio.to_thread(_clear)
            return result

        await _ensure_memory_file()

        def _write():
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                f.write("")

        await asyncio.to_thread(_write)
        return "Memory cleared"
    except Exception as e:
        return f"Error clearing memory: {str(e)}"


def register_tools(registry):
    """Register memory tools"""
    registry.register(
        "update_memory",
        update_memory,
        "Save fact to permanent memory. Arguments: info (str)",
    )
    registry.register(
        "read_memory", read_memory, "Read from memory. Arguments: query (str, optional)"
    )
    registry.register("clear_memory", clear_memory, "Clear all memory")
