"""
Audio transcription tool using Groq Whisper API
"""

import os
import asyncio
from groq import Groq
import config


async def transcribe_audio_async(filepath: str) -> str:
    """Transcribe audio file using Groq Whisper API"""
    try:
        if not os.path.exists(filepath):
            return "Error: File not found."

        client = Groq(api_key=config.GROQ_API_KEY)

        with open(filepath, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(filepath), file.read()),
                model="whisper-large-v3",
                response_format="text",
            )

        return str(transcription) if transcription else "No transcription returned"
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"


def transcribe_audio(filepath: str) -> str:
    """Synchronous wrapper for audio transcription"""
    try:
        return asyncio.run(transcribe_audio_async(filepath))
    except Exception as e:
        return f"Error running transcription: {str(e)}"