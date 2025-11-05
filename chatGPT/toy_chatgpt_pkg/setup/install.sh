#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/src"
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install torch
echo "Setup complete. Run: $ROOT/bin/run.sh"
