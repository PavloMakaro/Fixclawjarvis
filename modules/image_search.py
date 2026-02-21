import os
import asyncio
import aiohttp
from tavily import TavilyClient
import config

def register_tools(registry):
    registry.register(
        name="search_and_download_images",
        func=search_and_download_images,
        description="Ищет и СКАЧИВАЕТ РЕАЛЬНЫЕ картинки через официальный TAVILY API. Аргументы: query (str), max_results (int), send_to_chat (bool).",
        requires_context=True
    )

async def search_and_download_images(query: str, max_results: int = 3, send_to_chat: bool = False, bot=None, chat_id=None, **kwargs) -> dict:
    try:
        api_key = getattr(config, 'TAVILY_API_KEY', os.environ.get('TAVILY_API_KEY'))
        if not api_key:
            return {"success": False, "error": "TAVILY_API_KEY не найден в config.py"}

        def fetch_urls():
            client = TavilyClient(api_key=api_key)
            # Включаем поиск картинок в Tavily
            response = client.search(query=query, search_depth="advanced", include_images=True)
            return response.get("images", [])[:max_results]

        try:
            image_urls = await asyncio.to_thread(fetch_urls)
        except Exception as e:
            return {"success": False, "error": f"Tavily search failed: {str(e)}"}

        if not image_urls:
            return {"success": True, "downloaded": 0, "sent_to_chat": 0, "local_paths": []}

        save_dir = os.path.join("downloads", "images", str(chat_id) if chat_id else "public")
        os.makedirs(save_dir, exist_ok=True)

        downloaded = []
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(image_urls):
                if not isinstance(url, str) or not url.startswith("http"): continue
                try:
                    ext = url.split(".")[-1].split("?")[0]
                    if len(ext) > 4 or not ext.isalnum(): ext = "jpg"
                    safe_query = "".join(c if c.isalnum() else "_" for c in query)[:15]
                    filepath = os.path.join(save_dir, f"{safe_query}_{i}.{ext}")

                    headers = {"User-Agent": "Mozilla/5.0"}

                    async with session.get(url, headers=headers, timeout=10) as img_resp:
                        if img_resp.status == 200:
                            with open(filepath, 'wb') as f:
                                async for chunk in img_resp.content.iter_chunked(8192):
                                    f.write(chunk)
                            downloaded.append({"path": filepath})
                except:
                    continue

        downloaded_files = downloaded

        sent_count = 0
        paths = []
        if send_to_chat and bot and chat_id:
            for file_info in downloaded_files:
                try:
                    with open(file_info["path"], 'rb') as photo_file:
                        await bot.send_photo(chat_id=chat_id, photo=photo_file)
                    sent_count += 1
                except Exception as e:
                    pass

        for f in downloaded_files: paths.append(f["path"])

        return {"success": True, "downloaded": len(paths), "sent_to_chat": sent_count, "local_paths": paths}

    except Exception as e:
        return {"success": False, "error": str(e)}
