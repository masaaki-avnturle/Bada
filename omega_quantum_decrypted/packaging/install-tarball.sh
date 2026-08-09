#!/bin/sh
# install.sh — install the portable tarball build of omega_quantum_decrypted.
# Usage:  sudo ./install.sh            (installs to /usr/local)
#         PREFIX=$HOME/.local ./install.sh   (user-local, no sudo)
set -e
APP=omega_quantum_decrypted
PREFIX="${PREFIX:-/usr/local}"
HERE="$(cd "$(dirname "$0")" && pwd)"

install -d "$PREFIX/bin" "$PREFIX/share/$APP/examples" "$PREFIX/share/doc/$APP"
install -m 0755 "$HERE/$APP" "$PREFIX/bin/$APP"
cp "$HERE"/examples/* "$PREFIX/share/$APP/examples/" 2>/dev/null || true
cp "$HERE/README.md" "$PREFIX/share/doc/$APP/README.md" 2>/dev/null || true

echo "Installed $APP to $PREFIX/bin/$APP"
echo "Try:  $APP selftest"
