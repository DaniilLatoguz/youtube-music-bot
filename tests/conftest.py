"""Shared test fixtures.

Environment defaults are set BEFORE any app module is imported, so that
app.config can build its Settings() without a real .env file.
"""

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

os.environ.setdefault("BOT_TOKEN", "123456:test-token-for-ci")
os.environ.setdefault("ADMIN_ID", "1")


@pytest_asyncio.fixture
async def db():
    # Imported lazily so the env defaults above are already in place.
    from app.database import Database

    database = Database(":memory:")
    await database.connect()
    try:
        yield database
    finally:
        await database.close()


def _make_message(text: str = ""):
    """Returns (incoming_message, status_message) mocks that mimic aiogram."""
    status = MagicMock(name="status_msg")
    status.edit_text = AsyncMock()
    status.delete = AsyncMock()

    message = MagicMock(name="message")
    message.text = text
    message.from_user = SimpleNamespace(id=1, username="tester", full_name="Test User")
    message.delete = AsyncMock()
    message.answer = AsyncMock(return_value=status)

    sent_audio = MagicMock()
    sent_audio.audio = SimpleNamespace(file_id="FILE_ID_123")
    message.answer_audio = AsyncMock(return_value=sent_audio)
    return message, status


def _make_callback(data: str):
    callback = MagicMock(name="callback")
    callback.data = data
    callback.from_user = SimpleNamespace(id=1, username="tester", full_name="Test User")
    callback.answer = AsyncMock()

    sent_audio = MagicMock()
    sent_audio.audio = SimpleNamespace(file_id="FILE_ID_123")
    callback.message = MagicMock()
    callback.message.answer_audio = AsyncMock(return_value=sent_audio)
    callback.message.delete = AsyncMock()
    return callback


@pytest.fixture
def message_factory():
    return _make_message


@pytest.fixture
def callback_factory():
    return _make_callback
