# YouTube Music Telegram Bot

A Telegram bot that downloads tracks from **YouTube** and **YouTube Music** as
MP3 (192 kbps) with embedded cover art. Built with **aiogram 3** and **yt-dlp**.

> Replace `USERNAME/REPO` below with your GitHub path to activate the badge.

![CI](https://github.com/USERNAME/REPO/actions/workflows/ci.yml/badge.svg)

## Features

- 🎵 Download audio from a YouTube / YouTube Music link, or a plain text search query
- 🖼️ Embedded cover art and track metadata (title, performer, duration)
- ⚡ **Caching** — a track sent once is re-sent instantly via Telegram's `file_id`, with no re-download
- 🧹 The "already in library" prompt **auto-deletes** after a configurable delay so it doesn't clutter the chat
- 📊 Admin panel — usage stats, database export, and full log export
- 🐳 Docker support and a CI pipeline (ruff + pytest)

## Requirements

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/) on your `PATH` (or set `FFMPEG_PATH`)
- A bot token from [@BotFather](https://t.me/BotFather)
- Your numeric Telegram id from [@userinfobot](https://t.me/userinfobot)

## Quick start

### Option A — scripts (Linux / macOS)

```bash
./install.sh        # creates a venv, installs deps, copies .env.example -> .env
# open .env and fill in BOT_TOKEN and ADMIN_ID
./run.sh
```

### Option B — manual

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit BOT_TOKEN and ADMIN_ID
python -m app
```

### Option C — Docker

```bash
cp .env.example .env          # then edit BOT_TOKEN and ADMIN_ID
docker compose up --build
```

## Configuration

All settings are read from environment variables / the `.env` file.

| Variable               | Required | Default    | Description                                            |
| ---------------------- | -------- | ---------- | ------------------------------------------------------ |
| `BOT_TOKEN`            | yes      | —          | Bot token from @BotFather                              |
| `ADMIN_ID`             | yes      | —          | Your numeric Telegram id (unlocks the admin panel)     |
| `FFMPEG_PATH`          | no       | `ffmpeg`   | Path to ffmpeg if it is not on your `PATH`             |
| `DELETE_DELAY_SECONDS` | no       | `35`       | Seconds before the "already in library" prompt deletes |
| `MAX_FILE_SIZE_MB`     | no       | `50`       | Largest file to accept (Telegram bot limit is 50 MB)   |

## Usage

1. Send `/start` to the bot.
2. Send a YouTube / YouTube Music link (or just type a song name).
3. The bot replies with the track as an audio file.

If a track is already cached, you get a **Download again** button instead of a
re-download. That prompt removes itself automatically after `DELETE_DELAY_SECONDS`.

### Admin

Send `/admin` (only works for `ADMIN_ID`) to see usage statistics and to export
the database or the full download log.

## Project structure

```
app/
├── __main__.py        # entry point: python -m app
├── config.py          # typed settings (pydantic-settings)
├── logging_setup.py   # logging configuration
├── database.py        # async SQLite layer (one reused connection)
├── downloader.py      # yt-dlp wrapper
├── bot.py             # Bot / Dispatcher wiring
├── utils.py           # background tasks, auto-deletion, thumbnails
└── handlers/
    ├── user.py        # /start, link handling, "download again"
    └── admin.py       # /admin, exports
tests/                 # pytest suite (database, downloader, handlers)
```

## Running tests

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q
```

## Troubleshooting

- **`Configuration error: required settings are missing`** — `BOT_TOKEN` or
  `ADMIN_ID` is not set. Check your `.env`.
- **ffmpeg / audio conversion errors** — ffmpeg is not installed or not on your
  `PATH`. Install it, or set `FFMPEG_PATH`.
- **YouTube returns "Sign in to confirm you're not a bot" / extraction fails** —
  YouTube periodically tightens access. First update yt-dlp:
  `pip install -U yt-dlp`.

## Notes

This project is for educational and personal use. Downloading copyrighted
content may be restricted in your country and may violate YouTube's Terms of
Service — please respect the rights of content owners.
