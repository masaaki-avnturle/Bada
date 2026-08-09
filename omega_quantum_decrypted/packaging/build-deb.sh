#!/bin/sh
# build-deb.sh — build a downloadable Ubuntu/Debian .deb and a portable .tar.gz.
# Requires only: cc, make, dpkg-deb (present on every Ubuntu). No other deps.
set -e

APP=omega_quantum_decrypted
DEBNAME=omega-quantum-decrypted     # Debian package names: no underscores allowed
VERSION="${VERSION:-1.0.0}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v dpkg >/dev/null 2>&1; then
    ARCH="$(dpkg --print-architecture)"
else
    ARCH=amd64
fi

echo ">> building binary"
make clean >/dev/null 2>&1 || true
make all

DIST="$ROOT/dist"
STAGE="$DIST/${DEBNAME}_${VERSION}_${ARCH}"
rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN"
mkdir -p "$STAGE/usr/bin"
mkdir -p "$STAGE/usr/share/$APP/examples"
mkdir -p "$STAGE/usr/share/doc/$APP"

install -m 0755 "build/$APP" "$STAGE/usr/bin/$APP"
cp examples/*.knot examples/*.txt "$STAGE/usr/share/$APP/examples/" 2>/dev/null || true
cp README.md "$STAGE/usr/share/doc/$APP/README.md"
cp LICENSE   "$STAGE/usr/share/doc/$APP/LICENSE" 2>/dev/null || true

SIZE_KB=$(du -ks "$STAGE/usr" | cut -f1)

cat > "$STAGE/DEBIAN/control" <<EOF
Package: $DEBNAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Masaaki Yamaguchi <masaaki.tabu4@gmail.com>
Installed-Size: $SIZE_KB
Depends: libc6
Homepage: https://masaaki-avnturle.github.io/Bada/
Description: Omega-Quantum-Decrypted — Jones-polynomial quantum cryptography
 Decryption (kaidoku / 解読) tool whose key is derived from the Kauffman
 bracket and writhe-normalised Jones polynomial of a knot diagram, folded
 through the Unknown-Prior Engine phase core (psi_i = sqrt(a_i) exp(i theta_i)).
 Self-contained: needs only libc, no OpenSSL or other libraries.
 Part of the Bada / Yamaguchi framework.
EOF

echo ">> building .deb"
DEB="$DIST/${DEBNAME}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$DEB" >/dev/null 2>&1 \
    || dpkg-deb --build "$STAGE" "$DEB"
echo "   -> $DEB"

echo ">> building portable .tar.gz"
TARSTAGE="$DIST/${APP}-${VERSION}-linux-${ARCH}"
rm -rf "$TARSTAGE"
mkdir -p "$TARSTAGE/examples"
install -m 0755 "build/$APP" "$TARSTAGE/$APP"
cp examples/*.knot examples/*.txt "$TARSTAGE/examples/" 2>/dev/null || true
cp README.md "$TARSTAGE/README.md"
cp LICENSE   "$TARSTAGE/LICENSE" 2>/dev/null || true
cp packaging/install-tarball.sh "$TARSTAGE/install.sh"
chmod +x "$TARSTAGE/install.sh"
TARBALL="$DIST/${APP}-${VERSION}-linux-${ARCH}.tar.gz"
tar -C "$DIST" -czf "$TARBALL" "$(basename "$TARSTAGE")"
echo "   -> $TARBALL"

echo ">> done. Artifacts in dist/:"
ls -la "$DIST" | sed 's/^/   /'
