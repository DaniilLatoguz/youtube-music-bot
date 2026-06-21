#!/usr/bin/env bash
# One-step setup. Run once from the project root:  ./install.sh
set -e
cd "$(dirname "$0")"

echo "=== YouTube Music Bot — setup ==="

if command -v python3 >/dev/null 2>&1; then PY=python3; elif command -v python >/dev/null 2>&1; then PY=python; else
  echo "ERROR: Python is not installed."; exit 1; fi
echo "[1/4] Python: $($PY --version)"

if command -v ffmpeg >/dev/null 2>&1; then
  echo "[2/4] ffmpeg: found"
else
  echo "[2/4] ffmpeg: NOT FOUND — install it before running:"
  echo "        Ubuntu/Debian: sudo apt update && sudo apt install -y ffmpeg"
  echo "        macOS:         brew install ffmpeg"
fi

if [ ! -d ".venv" ]; then echo "[3/4] Creating virtualenv (.venv)..."; $PY -m venv .venv; else echo "[3/4] .venv exists."; fi
echo "      Installing dependencies..."
./.venv/bin/python -m pip install --upgrade pip >/dev/null
./.venv/bin/python -m pip install -r requirements.txt

if [ ! -f ".env" ]; then cp .env.example .env; echo "[4/4] Created .env from template."; else echo "[4/4] .env exists — left unchanged."; fi

echo ""
echo "Done. Next:"
echo "  1) Open .env and set BOT_TOKEN and ADMIN_ID"
echo "  2) Start the bot:  ./run.sh"
