#!/usr/bin/env bash
# Start the bot. Run:  ./run.sh
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then echo "Run ./install.sh first."; exit 1; fi
if [ ! -f ".env" ]; then echo "No .env found. Run ./install.sh, then fill it in."; exit 1; fi

set -a; . ./.env; set +a
if [ -z "$BOT_TOKEN" ]; then echo "BOT_TOKEN is empty in .env."; exit 1; fi
if ! printf '%s' "$ADMIN_ID" | grep -Eq '^[0-9]+$'; then echo "ADMIN_ID must be your numeric Telegram id in .env."; exit 1; fi

echo "Starting bot...  (Ctrl+C to stop)"
exec ./.venv/bin/python -m app
