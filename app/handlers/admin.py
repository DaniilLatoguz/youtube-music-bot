"""Admin-only handlers: statistics, database export, and full log export."""

import logging
from html import escape
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

from app.config import settings
from app.database import Database

logger = logging.getLogger(__name__)
router = Router(name="admin")


@router.message(Command("admin"), F.from_user.id == settings.admin_id)
async def admin_stats(message: Message, db: Database) -> None:
    total, users, rows = await db.get_stats()

    lines = [
        "📊 <b>BOT STATS</b>",
        "━━━━━━━━━━━━━━━━━━",
        f"👤 Unique users: <code>{users}</code>",
        f"🎵 Total downloads: <code>{total}</code>",
        "━━━━━━━━━━━━━━━━━━",
        "Recent requests:\n",
    ]
    for row in rows:
        username = (
            escape(row["username"])
            if row["username"] not in (None, "N/A")
            else "No username"
        )
        ts = (row["created_at"] or "Unknown").replace("T", " ")
        lines += [
            f"👤 {escape(row['full_name'] or 'Unknown')} (@{username})",
            f"🎶 <code>{escape(row['track_title'] or '')}</code>",
            f"🕒 {ts}",
            "──────────────────",
        ]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Download DB", callback_data="admin_get_db")],
            [InlineKeyboardButton(text="📄 Export full log", callback_data="admin_get_full_log")],
        ]
    )
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=keyboard)


@router.callback_query(F.data == "admin_get_db", F.from_user.id == settings.admin_id)
async def admin_get_db(callback: CallbackQuery) -> None:
    await callback.message.answer_document(
        FSInputFile(str(settings.db_path)), caption="📂 SQLite database file"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_get_full_log", F.from_user.id == settings.admin_id)
async def admin_get_full_log(callback: CallbackQuery, db: Database) -> None:
    rows = await db.get_all_downloads()
    report_path = Path(settings.db_path).parent / "full_report.txt"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("FULL DOWNLOAD REPORT\n")
        f.write("=" * 50 + "\n")
        for row in rows:
            f.write(
                f"Date:     {row['created_at']}\n"
                f"User:     {row['full_name']} (@{row['username']})\n"
                f"Track:    {row['track_title']}\n"
                f"Video ID: {row['video_id']}\n"
                + "-" * 30 + "\n"
            )

    await callback.message.answer_document(
        FSInputFile(str(report_path)), caption="📄 Full download log"
    )
    await callback.answer()
    try:
        report_path.unlink(missing_ok=True)
    except Exception:
        pass
