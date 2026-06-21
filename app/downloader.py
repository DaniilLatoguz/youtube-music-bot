"""YouTube download logic — a thin wrapper around yt-dlp."""

import logging

import yt_dlp

from app.config import settings

logger = logging.getLogger(__name__)


def _is_url(text: str) -> bool:
    return text.strip().lower().startswith(("http://", "https://"))


def _base_opts() -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "bestaudio/best",
    }
    # Only override ffmpeg location when a custom path is set; otherwise let
    # yt-dlp find ffmpeg on the system PATH.
    if settings.ffmpeg_path and settings.ffmpeg_path != "ffmpeg":
        opts["ffmpeg_location"] = settings.ffmpeg_path
    return opts


def get_video_info(query: str) -> dict | None:
    """Resolve a URL or search string to a single track's metadata (no download)."""
    target = query.strip() if _is_url(query) else f"ytsearch1:{query.strip()}"

    opts = _base_opts()
    opts["skip_download"] = True
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(target, download=False)
    except Exception as exc:
        logger.warning("get_video_info failed for %r: %s", query, exc)
        return None

    # A search returns a playlist-like dict with an "entries" list.
    if info and "entries" in info:
        entries = [e for e in info["entries"] if e]
        if not entries:
            return None
        info = entries[0]
    return info


def download_audio_by_id(video_id: str) -> tuple[str | None, dict]:
    """Download a track by id, convert to MP3 (192 kbps) and embed cover art.

    Returns (file_path, info_dict). file_path is None if the download failed.
    """
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    output_template = str(settings.downloads_dir / f"{video_id}.%(ext)s")

    opts = _base_opts()
    opts.update(
        {
            "outtmpl": output_template,
            "writethumbnail": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
        }
    )
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as exc:
        logger.error("download_audio_by_id failed for %s: %s", video_id, exc)
        return None, {}

    file_path = settings.downloads_dir / f"{video_id}.mp3"
    if not file_path.exists():
        return None, info or {}
    return str(file_path), info or {}
