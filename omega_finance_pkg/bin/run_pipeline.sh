#!/bin/sh
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
make
# Example pipeline: ingest sample, analyze day, predict
./bin/launcher ingest examples/prices_sample.csv
./bin/launcher analyze_day 2025-09-24
./bin/launcher predict AAPL 1
