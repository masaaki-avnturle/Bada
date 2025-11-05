#!/bin/sh
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
make
echo "Example: encrypt examples/trefoil.txt plain.txt cipher.bin"
