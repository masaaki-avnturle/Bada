#!/bin/sh
# Usage: pdftotext-wrapper.sh in.pdf out.txt
if [ $# -lt 2 ]; then
  echo "usage: $0 in.pdf out.txt" >&2
  exit 2
fi
IN="$1"
OUT="$2"
if command -v pdftotext >/dev/null 2>&1; then
  pdftotext "$IN" "$OUT"
  exit $?
else
  echo "pdftotext not found" >&2
  exit 127
fi
