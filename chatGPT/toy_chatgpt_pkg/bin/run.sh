#!/usr/bin/env bash
set -e
PKGROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PKGROOT/src"
if [ -z "$VIRTUAL_ENV" ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install torch --quiet || true
fi
python3 toy_chatbot.py
