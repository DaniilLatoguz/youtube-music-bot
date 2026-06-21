"""User-facing handlers: /start, link handling, and the 'download again' button."""

import asyncio
import logging
import os
from pathlib import Path

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app import downloader
from app.config import settings
from app.database import Database
from app.utils import prepare_thumbnail, schedule_deletion

logger = logging.getLogger(__name__)
router = Router(name="user")

START_TEXT = (
    "✨ ——— <b>MUSIC DOWNLOADER</b> ——— ✨\n\n"
    "👋 <b>Hi! I'm ready to help.</b>\n"
    "Send me a link and I'll download it in high quality.\n\n"
    "📥 <b>Supported sources:</b>\n"
    "🔹 YouTube\n"
    "🔹 YouTube Music\n\n"
    "<i>Waiting for your link... 🎧</i>"
)


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(START_TEXT, parse_mode=ParseMode.HTML)


# F.text & ~F.text.startswith("/") so unknown commands are not sent to yt-dlp
# as search queries.
@router.message(F.text & ~F.text.startswith("/"))
async def handle_link(message: Message, db: Database) -> None:
    query = message.text
    user = message.from_user

    try:
        await message.delete()
    except Exception:
        pass

    status_msg = await message.answer("🔍 Fetching info...")

    try:
        # Step 1: metadata only — avoids downloading oversized files.
        info = await asyncio.wait_for(
            asyncio.to_thread(downloader.get_video_info, query), timeout=60.0
        )
        if not info:
            await status_msg.edit_text("❌ Could not retrieve info for this link.")
            schedule_deletion(status_msg, 10)
            return

        video_id = info.get("id")
        title = info.get("title", "Unknown track")

        # Step 2: size check before any download.
        filesize = info.get("filesize") or info.get("filesize_approx") or 0
        if filesize > settings.max_file_size_bytes:
            await status_msg.edit_text(
                f"❌ File is over {settings.max_file_size_mb} MB — too large for Telegram."
            )
            schedule_deletion(status_msg, 10)
            return

        # Step 3: cache check — serve from Telegram servers if already uploaded.
        cached = await db.get_cached_track(video_id)
        if cached:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Download again ⬇️",
                            callback_data=f"restore_{video_id}",
                        )
                    ]
                ]
            )
            await status_msg.edit_text(
                "🎵 This track is already in the library.", reply_markup=keyboard
            )
            # Auto-remove this prompt so it does not clutter the chat.
            schedule_deletion(status_msg)
            return

        # Step 4: download audio.
        await status_msg.edit_text("📥 Downloading audio...")
        file_path, dl_info = await asyncio.wait_for(
            asyncio.to_thread(downloader.download_audio_by_id, video_id), timeout=300.0
        )
        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text("❌ Download failed.")
            schedule_deletion(status_msg, 10)
            return

        # Step 5: upload to Telegram.
        await status_msg.edit_text("📤 Uploading to Telegram...")
        thumb_path = await prepare_thumbnail(dl_info.get("thumbnail"), video_id)
        performer = dl_info.get("artist") or dl_info.get("uploader") or "Unknown Artist"

        sent = await message.answer_audio(
            audio=FSInputFile(file_path),
            title=title,
            performer=performer,
            duration=int(float(dl_info.get("duration", 0))),
            thumbnail=(
                FSInputFile(str(thumb_path))
                if thumb_path and thumb_path.exists()
                else None
            ),
        )

        # Step 6: persist records.
        await db.log_download(
            user.id, user.username or "N/A", user.full_name, title, video_id
        )
        await db.save_track_to_cache(video_id, sent.audio.file_id, title)
        await status_msg.delete()

        # Step 7: clean up local files — the bot is stateless after upload.
        for path in filter(None, [Path(file_path), thumb_path]):
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass

    except TimeoutError:
        await status_msg.edit_text("⏳ Request timed out. Please try again.")
        schedule_deletion(status_msg, 10)
    except Exception as exc:
        logger.exception("Error while handling %r: %s", query, exc)
        await status_msg.edit_text("❌ An unexpected error occurred.")
        schedule_deletion(status_msg, 10)


@router.callback_query(F.data.startswith("restore_"))
async def restore(callback: CallbackQuery, db: Database) -> None:
    video_id = callback.data.removeprefix("restore_")
    cached = await db.get_cached_track(video_id)
    if not cached:
        await callback.answer("❌ Track not found in cache.", show_alert=True)
        return

    await callback.message.answer_audio(audio=cached["file_id"])
    await db.log_download(
        callback.from_user.id,
        callback.from_user.username or "N/A",
        callback.from_user.full_name,
        cached["title"],
        video_id,
    )
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
