"""Tests for the Database layer (in-memory SQLite)."""


async def test_cache_roundtrip(db):
    assert await db.get_cached_track("vid1") is None
    await db.save_track_to_cache("vid1", "file_abc", "Song One")
    assert await db.get_cached_track("vid1") == {"file_id": "file_abc", "title": "Song One"}


async def test_cache_replace(db):
    await db.save_track_to_cache("vid1", "old", "Old")
    await db.save_track_to_cache("vid1", "new", "New")
    cached = await db.get_cached_track("vid1")
    assert cached["file_id"] == "new"
    assert cached["title"] == "New"


async def test_log_and_stats(db):
    await db.log_download(1, "alice", "Alice A", "Track 1", "v1")
    await db.log_download(1, "alice", "Alice A", "Track 2", "v2")
    await db.log_download(2, "bob", "Bob B", "Track 3", "v3")

    total, users, recent = await db.get_stats()
    assert total == 3
    assert users == 2
    assert len(recent) == 3
    assert recent[0]["track_title"] == "Track 3"  # most recent first


async def test_get_all_downloads(db):
    await db.log_download(1, "alice", "Alice A", "Track 1", "v1")
    rows = await db.get_all_downloads()
    assert len(rows) == 1
    assert rows[0]["video_id"] == "v1"
