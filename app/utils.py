"""Small async helpers used by the bot handlers."""

import asyncio
import io
import logging
from pathlib import Path

import aiohttp
from aiogram.types import Message
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)

# Keep strong references to background tasks so the garbage collector does not
# cancel them before they finish (recommended pattern from the asyncio docs).
_background_tasks: set[asyncio.Task] = set()


def fire_and_forget(coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


async def _delete_after(message: Message, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:  # already deleted, too old, or not deletable
        pass


def schedule_deletion(message: Message, delay: int | None = None) -> None:
    """Delete a message after ``delay`` seconds (default: settings.delete_delay_seconds)."""
    seconds = settings.delete_delay_seconds if delay is None else delay
    fire_and_forget(_delete_after(message, seconds))


async def prepare_thumbnail(thumb_url: str | None, video_id: str) -> Path | None:
    """Download and resize a thumbnail to Telegram's 320x320 limit. Returns None on failure."""
    if not thumb_url:
        return None

    settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = settings.downloads_dir / f"{video_id}_thumb.jpg"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.read()
        with Image.open(io.BytesIO(data)) as img:
            img = img.convert("RGB")
            img.thumbnail((320, 320))
            img.save(thumb_path, "JPEG")
        return thumb_path
    except Exception as exc:
        logger.warning("Thumbnail processing failed for %s: %s", video_id, exc)
        return None
