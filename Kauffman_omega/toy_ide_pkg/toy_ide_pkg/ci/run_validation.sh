#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)/.."
cd "$DIR"
python3 ci/harness_out33/validation_harness.py > validation_output.txt 2>&1 || true
echo "validation_output.txt written"
