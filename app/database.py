"""Async SQLite access layer.

A single connection is opened at startup and reused for every query (aiosqlite
serialises operations on one connection), instead of opening a new connection
per call.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, path: str | Path) -> None:
        self._path = str(path)
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._create_tables()
        logger.info("Database connected: %s", self._path)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected — call connect() first.")
        return self._conn

    async def _create_tables(self) -> None:
        await self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                video_id TEXT PRIMARY KEY,
                file_id  TEXT NOT NULL,
                title    TEXT
            )
            """
        )
        await self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS download_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                username    TEXT,
                full_name   TEXT,
                track_title TEXT,
                video_id    TEXT,
                created_at  TEXT NOT NULL
            )
            """
        )
        await self.conn.commit()

    # ---------------------------------------------------------------- cache

    async def get_cached_track(self, video_id: str) -> dict | None:
        async with self.conn.execute(
            "SELECT file_id, title FROM cache WHERE video_id = ?", (video_id,)
        ) as cur:
            row = await cur.fetchone()
        return {"file_id": row["file_id"], "title": row["title"]} if row else None

    async def save_track_to_cache(self, video_id: str, file_id: str, title: str) -> None:
        await self.conn.execute(
            "INSERT OR REPLACE INTO cache (video_id, file_id, title) VALUES (?, ?, ?)",
            (video_id, file_id, title),
        )
        await self.conn.commit()

    # -------------------------------------------------------------- history

    async def log_download(
        self,
        user_id: int,
        username: str,
        full_name: str,
        track_title: str,
        video_id: str,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO download_history
                (user_id, username, full_name, track_title, video_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                full_name,
                track_title,
                video_id,
                datetime.now(UTC).isoformat(timespec="seconds"),
            ),
        )
        await self.conn.commit()

    async def get_stats(
        self, recent_limit: int = 15
    ) -> tuple[int, int, list[aiosqlite.Row]]:
        """Returns (total_downloads, unique_users, recent_rows)."""
        async with self.conn.execute(
            "SELECT COUNT(*) AS c FROM download_history"
        ) as cur:
            total = (await cur.fetchone())["c"]
        async with self.conn.execute(
            "SELECT COUNT(DISTINCT user_id) AS c FROM download_history"
        ) as cur:
            users = (await cur.fetchone())["c"]
        async with self.conn.execute(
            """
            SELECT username, full_name, track_title, created_at
            FROM download_history ORDER BY id DESC LIMIT ?
            """,
            (recent_limit,),
        ) as cur:
            recent = await cur.fetchall()
        return total, users, recent

    async def get_all_downloads(self) -> list[aiosqlite.Row]:
        async with self.conn.execute(
            """
            SELECT user_id, username, full_name, track_title, video_id, created_at
            FROM download_history ORDER BY created_at ASC
            """
        ) as cur:
            return await cur.fetchall()
