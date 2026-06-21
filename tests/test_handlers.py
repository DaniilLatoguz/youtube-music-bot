"""Tests for the user handlers (aiogram objects and the downloader are mocked)."""

import pytest

from app import downloader
from app.handlers import user as user_handlers


@pytest.fixture(autouse=True)
def patch_deletion(monkeypatch):
    """Replace schedule_deletion with a recorder so no real background tasks run."""
    calls = []
    monkeypatch.setattr(user_handlers, "schedule_deletion", lambda *a, **k: calls.append((a, k)))
    return calls


async def test_start_sends_welcome(message_factory):
    message, _ = message_factory()
    await user_handlers.start(message)
    message.answer.assert_awaited_once()
    assert "MUSIC DOWNLOADER" in message.answer.call_args.args[0]


async def test_handle_link_unknown(message_factory, monkeypatch, db):
    monkeypatch.setattr(downloader, "get_video_info", lambda q: None)
    message, status = message_factory("bad link")

    await user_handlers.handle_link(message, db)

    status.edit_text.assert_awaited()
    assert "Could not retrieve" in status.edit_text.call_args.args[0]


async def test_handle_link_cached_schedules_deletion(
    message_factory, monkeypatch, db, patch_deletion
):
    # Arrange: the track is already cached.
    await db.save_track_to_cache("vid1", "file_abc", "Cached Song")
    monkeypatch.setattr(
        downloader,
        "get_video_info",
        lambda q: {"id": "vid1", "title": "Cached Song", "filesize_approx": 1000},
    )

    message, status = message_factory("https://youtu.be/vid1")
    await user_handlers.handle_link(message, db)

    # The "already in library" prompt is shown with a button...
    args, kwargs = status.edit_text.call_args
    assert "already in the library" in args[0]
    assert kwargs.get("reply_markup") is not None
    # ...and it is scheduled for auto-deletion.
    assert patch_deletion, "expected the cached prompt to be scheduled for deletion"


async def test_handle_link_rejects_oversized_file(message_factory, monkeypatch, db):
    huge = 999 * 1024 * 1024  # 999 MB
    monkeypatch.setattr(
        downloader,
        "get_video_info",
        lambda q: {"id": "big", "title": "Huge", "filesize": huge},
    )
    message, status = message_factory("https://youtu.be/big")

    await user_handlers.handle_link(message, db)

    assert "too large" in status.edit_text.call_args.args[0]
    # nothing should have been cached
    assert await db.get_cached_track("big") is None


async def test_restore_sends_cached_audio(callback_factory, db):
    await db.save_track_to_cache("vid1", "file_abc", "Cached Song")
    callback = callback_factory("restore_vid1")

    await user_handlers.restore(callback, db)

    callback.message.answer_audio.assert_awaited_once()
    assert callback.message.answer_audio.call_args.kwargs.get("audio") == "file_abc"
    # the re-download was logged
    rows = await db.get_all_downloads()
    assert len(rows) == 1
    assert rows[0]["video_id"] == "vid1"


async def test_restore_missing_track_alerts(callback_factory, db):
    callback = callback_factory("restore_does_not_exist")
    await user_handlers.restore(callback, db)
    callback.answer.assert_awaited_once()
    assert callback.answer.call_args.kwargs.get("show_alert") is True
