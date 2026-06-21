"""Application settings, loaded from environment variables / the .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor paths to the project root so the bot works regardless of the current
# working directory it is launched from.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required (no defaults) — the app refuses to start without them.
    bot_token: str
    admin_id: int

    # Optional, with sensible defaults.
    ffmpeg_path: str = "ffmpeg"
    delete_delay_seconds: int = 35
    max_file_size_mb: int = 50
    db_path: Path = _DATA_DIR / "bot_data.db"
    downloads_dir: Path = _DATA_DIR / "downloads"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


# Instantiated once at import. Raises pydantic.ValidationError if BOT_TOKEN or
# ADMIN_ID are missing; __main__.py turns that into a friendly message.
settings = Settings()
