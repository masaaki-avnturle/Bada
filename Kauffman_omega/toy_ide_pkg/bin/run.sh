#!/usr/bin/env bash
set -e
PKGROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PKGROOT"
if [ ! -d ".venv" ]; then python3 -m venv .venv || true; fi
. .venv/bin/activate || true
python3 -m pip install --upgrade pip setuptools || true
python3 -m pip install requests beautifulsoup4 numpy scipy sympy pypandoc || true
python3 usr/bin/toy_hypothesis_engine.py "$@"
