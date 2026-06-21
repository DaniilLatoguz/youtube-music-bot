#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

REPO_URL="https://github.com/DaniilLatoguz/youtube-music-bot.git"

rm -rf .git          # чистим любую прошлую историю git (файлы и .env НЕ трогаются)
git init -q
git branch -M main

# Личность для коммитов (только для этого репозитория)
git config user.name  "Daniil Latoguz"
git config user.email "danila.latoghuz@gmail.com"

git add .gitignore .dockerignore .env.example requirements.txt requirements-dev.txt pyproject.toml LICENSE install.sh run.sh
git commit -q -m "Add project scaffolding, tooling, and setup scripts"

git add app/__init__.py app/config.py app/logging_setup.py
git commit -q -m "Add typed configuration (pydantic-settings) and logging"

git add app/database.py
git commit -q -m "Add async SQLite database layer with a reused connection"

git add app/downloader.py
git commit -q -m "Add YouTube downloader service (yt-dlp wrapper)"

git add app/utils.py
git commit -q -m "Add async helpers: background tasks, auto-deletion, thumbnails"

git add app/handlers/__init__.py app/handlers/user.py
git commit -q -m "Add user handlers: download flow, caching, auto-deleting prompt"

git add app/handlers/admin.py
git commit -q -m "Add admin panel: stats, database and log export"

git add app/bot.py app/__main__.py
git commit -q -m "Wire the bot together and add the entry point"

git add tests
git commit -q -m "Add test suite: database, downloader, handlers"

git add Dockerfile docker-compose.yml
git commit -q -m "Add Docker support"

git add .github
git commit -q -m "Add GitHub Actions CI (ruff + pytest)"

git add README.md
git commit -q -m "Add README and documentation"

if [ -n "$(git status --porcelain)" ]; then
  git add -A && git commit -q -m "Add remaining project files"
fi

git remote add origin "$REPO_URL"
git push -f origin main

echo ""
echo "Готово — обнови страницу репозитория на GitHub."