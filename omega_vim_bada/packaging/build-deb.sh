#!/bin/sh
# build-deb.sh — build a downloadable Ubuntu/Debian .deb and a portable .tar.gz
# for Ω-Vim (the Bada-language Vim editor). Pure Ruby: depends only on `ruby`.
set -e

APP=omega-vim
VERSION="${VERSION:-1.0.0}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v dpkg >/dev/null 2>&1; then ARCH="all"; else ARCH="all"; fi

# locate the Bada host library to vendor
BADA_LIB=""
for c in "$ROOT/../bada_ruby/lib" "$ROOT/vendor/bada_ruby/lib"; do
  [ -d "$c" ] && BADA_LIB="$c" && break
done
[ -n "$BADA_LIB" ] || { echo "ERROR: bada_ruby/lib not found to vendor"; exit 1; }

echo ">> syntax check + tests"
ruby -Ilib -I"$BADA_LIB" tests/test_omega_vim.rb >/dev/null && echo "   tests OK"

DIST="$ROOT/dist"
SHARE="usr/share/$APP"
STAGE="$DIST/${APP}_${VERSION}_${ARCH}"
rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN" "$STAGE/usr/bin" \
         "$STAGE/$SHARE/lib" "$STAGE/$SHARE/src" "$STAGE/$SHARE/examples" \
         "$STAGE/$SHARE/bin" "$STAGE/$SHARE/vendor/bada_ruby/lib" \
         "$STAGE/usr/share/doc/$APP"

cp -r lib/*        "$STAGE/$SHARE/lib/"
cp -r src/*        "$STAGE/$SHARE/src/"
cp -r examples/*   "$STAGE/$SHARE/examples/" 2>/dev/null || true
cp bin/omega-vim   "$STAGE/$SHARE/bin/omega-vim"
cp -r "$BADA_LIB"/* "$STAGE/$SHARE/vendor/bada_ruby/lib/"
cp README.md       "$STAGE/usr/share/doc/$APP/README.md"
cp LICENSE         "$STAGE/usr/share/doc/$APP/LICENSE" 2>/dev/null || true

# launcher on PATH
cat > "$STAGE/usr/bin/$APP" <<EOF
#!/bin/sh
exec ruby "/$SHARE/bin/omega-vim" "\$@"
EOF
chmod 0755 "$STAGE/usr/bin/$APP"

SIZE_KB=$(du -ks "$STAGE/usr" | cut -f1)
cat > "$STAGE/DEBIAN/control" <<EOF
Package: $APP
Version: $VERSION
Section: editors
Priority: optional
Architecture: $ARCH
Maintainer: Masaaki Yamaguchi <masaaki.tabu4@gmail.com>
Installed-Size: $SIZE_KB
Depends: ruby (>= 3.0)
Homepage: https://masaaki-avnturle.github.io/Bada/
Description: Ω-Vim — a Vim editor written in the Bada language
 A modal (vi/vim) text editor written from scratch in the Bada language
 (Yamaguchi framework). Its error-correction command '=' / ':fix' repairs
 source code in ANY programming language using the complex-rotation
 spinning-top (koma) integrable system of special relativity: delimiter
 nesting is a rotation orbit, correct code is a closed orbit, and the fixer
 closes an open orbit with minimum defect while conserving the entropy
 invariant Xi.
EOF

echo ">> building .deb"
DEB="$DIST/${APP}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$DEB" >/dev/null 2>&1 \
  || dpkg-deb --build "$STAGE" "$DEB"
echo "   -> $DEB"

echo ">> building portable .tar.gz"
TARSTAGE="$DIST/${APP}-${VERSION}"
rm -rf "$TARSTAGE"; mkdir -p "$TARSTAGE"
cp -r lib src examples bin README.md "$TARSTAGE/"
cp LICENSE "$TARSTAGE/" 2>/dev/null || true
mkdir -p "$TARSTAGE/vendor/bada_ruby/lib"
cp -r "$BADA_LIB"/* "$TARSTAGE/vendor/bada_ruby/lib/"
cp packaging/install-tarball.sh "$TARSTAGE/install.sh"; chmod +x "$TARSTAGE/install.sh"
TARBALL="$DIST/${APP}-${VERSION}-linux.tar.gz"
tar -C "$DIST" -czf "$TARBALL" "$(basename "$TARSTAGE")"
echo "   -> $TARBALL"

echo ">> artifacts:"; ls -la "$DIST" | sed 's/^/   /'
