#!/bin/sh
# install.sh — install the portable tarball build of Ω-Vim.
#   sudo ./install.sh                    # -> /usr/local
#   PREFIX=$HOME/.local ./install.sh     # user-local, no sudo
set -e
APP=omega-vim
PREFIX="${PREFIX:-/usr/local}"
HERE="$(cd "$(dirname "$0")" && pwd)"
SHARE="$PREFIX/share/$APP"

command -v ruby >/dev/null 2>&1 || { echo "ruby (>=3.0) is required"; exit 1; }

install -d "$PREFIX/bin" "$SHARE"
cp -r "$HERE/lib" "$HERE/src" "$HERE/bin" "$HERE/vendor" "$SHARE/"
cp -r "$HERE/examples" "$SHARE/" 2>/dev/null || true
cp "$HERE/README.md" "$SHARE/" 2>/dev/null || true

cat > "$PREFIX/bin/$APP" <<EOF
#!/bin/sh
exec ruby "$SHARE/bin/omega-vim" "\$@"
EOF
chmod 0755 "$PREFIX/bin/$APP"

echo "Installed $APP to $PREFIX/bin/$APP"
echo "Try:  $APP demo      # headless demo"
echo "      $APP FILE      # edit a file (= or :fix corrects any language)"
