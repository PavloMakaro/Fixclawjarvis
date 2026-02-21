"""
Media processing module - ASYNC VERSION
Handles video downloads, audio transcription, image recognition
"""

import asyncio
import os
import base64
from typing import Optional
import aiohttp
import yt_dlp
from groq import Groq
import config


async def download_video(url: str) -> str:
    """Download video using yt-dlp (async wrapper)"""
    try:
        os.makedirs("downloads", exist_ok=True)

        ydl_opts = {
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "format": "best",
            "noplaylist": True,
            "quiet": True,
        }

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filename = await asyncio.to_thread(_download)
        return f"Video downloaded to: {filename}"
    except Exception as e:
        return f"Error downloading video: {str(e)}"


async def transcribe_audio(filepath: str) -> str:
    """Transcribe audio using Groq Whisper"""
    try:
        if not os.path.exists(filepath):
            return "Error: File not found."

        client = Groq(api_key=config.GROQ_API_KEY)

        def _transcribe():
            with open(filepath, "rb") as file:
                result = client.audio.transcriptions.create(
                    file=(os.path.basename(filepath), file.read()),
                    model="whisper-large-v3",
                    response_format="text",
                )
                return str(result) if result else ""

        transcription = await asyncio.to_thread(_transcribe)
        return transcription
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"


async def recognize_image(filepath: str) -> str:
    """Recognize text in image using OCR.Space"""
    try:
        if not os.path.exists(filepath):
            return "Error: File not found."

        url = "https://api.ocr.space/parse/image"

        async with aiohttp.ClientSession() as session:
            with open(filepath, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("file", f, filename=os.path.basename(filepath))
                data.add_field("apikey", config.OCR_API_KEY)
                data.add_field("language", "eng")
                data.add_field("isOverlayRequired", "false")

                async with session.post(url, data=data, timeout=20) as response:
                    result = await response.json()

                    if result.get("IsErroredOnProcessing"):
                        return f"OCR Error: {result.get('ErrorMessage')}"

                    parsed_results = result.get("ParsedResults", [])
                    if not parsed_results:
                        return "No text found."

                    return (
                        parsed_results[0].get("ParsedText", "No text found")
                        or "No text found"
                    )
    except Exception as e:
        return f"Error recognizing image: {str(e)}"


async def recognize_image_groq(filepath: str) -> str:
    """Recognize content in image using Groq Vision"""
    try:
        if not os.path.exists(filepath):
            return "Error: File not found."

        client = Groq(api_key=config.GROQ_API_KEY)

        with open(filepath, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        def _recognize():
            return client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this image in detail and extract any text found.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0.7,
                max_tokens=1024,
            )

        completion = await asyncio.to_thread(_recognize)
        return completion.choices[0].message.content or ""
    except Exception as e:
        return f"Error with Groq Vision: {str(e)}"


def register_tools(registry):
    """Register media tools"""
    registry.register(
        "download_video", download_video, "Download video. Arguments: url (str)"
    )
    registry.register(
        "transcribe_audio",
        transcribe_audio,
        "Transcribe audio file. Arguments: filepath (str)",
    )
    registry.register(
        "recognize_image",
        recognize_image,
        "Recognize text in image (OCR). Arguments: filepath (str)",
    )
    registry.register(
        "recognize_image_groq",
        recognize_image_groq,
        "Recognize image content with Groq Vision. Arguments: filepath (str)",
    )
