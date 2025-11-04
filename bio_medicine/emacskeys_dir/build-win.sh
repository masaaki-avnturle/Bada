#!/bin/sh
# build-win.sh - cross-build Windows remapper (x86_64 by default)
TARGET=${1:-x86_64}
case "$TARGET" in
  x86_64) CC=x86_64-w64-mingw32-gcc ;; i686) CC=i686-w64-mingw32-gcc ;; *) echo "Unknown target"; exit 2 ;;
esac
command -v "$CC" >/dev/null 2>&1 || (echo "$CC not found. Install mingw-w64." && exit 3)
mkdir -p bin lib include usr || true
SRC_DIR=src
OUT=remapper.exe
if [ ! -f "$SRC_DIR/remapper.c" ]; then echo "Source not found: $SRC_DIR/remapper.c"; exit 4; fi
$CC -O2 -municode $SRC_DIR/remapper.c $SRC_DIR/emacs_bindings.c $SRC_DIR/vim_bindings.c -o $OUT -luser32 -lpsapi || exit $?
echo "Built $OUT"
