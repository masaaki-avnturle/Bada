#!/usr/bin/env bash
# Build a standalone Ubuntu/Linux CLI executable for the Bada language
# (compiler + interpreter + quantum) using Node's Single-Executable-Application
# feature — no Node install required on the target machine.
#
# Output: cli/build/bada-cli-linux-x64   (run: ./bada-cli-linux-x64 run prog.bada)
#     and cli/build/bada_<ver>_amd64.deb  (installs /usr/bin/bada)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
app="$(cd "$here/.." && pwd)"
ver="$(node -p "require('$app/electron/package.json').version" 2>/dev/null || echo 1.0.0)"
build="$here/build"
rm -rf "$build"; mkdir -p "$build"

# 1) bundle the engine + the CLI into a single self-contained CommonJS file.
cat "$app/www/bada.js" "$here/cli.js" > "$build/bada-bundle.js"
# portable CLI: runs anywhere Node is present (incl. Android/Termux: `node bada-cli.js run x.bada`)
cp "$build/bada-bundle.js" "$build/bada-cli.js"

# 2) generate the SEA blob.
cat > "$build/sea-config.json" <<JSON
{ "main": "bada-bundle.js", "output": "bada-prep.blob", "disableExperimentalSEAWarning": true }
JSON
( cd "$build" && node --experimental-sea-config sea-config.json )

# 3) inject the blob into a copy of the node binary.
cp "$(command -v node)" "$build/bada-cli-linux-x64"
npx --yes postject "$build/bada-cli-linux-x64" NODE_SEA_BLOB "$build/bada-prep.blob" \
  --sentinel-fuse NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2
chmod +x "$build/bada-cli-linux-x64"

# 4) smoke-test the binary.
echo 'print "bada cli " + (2+2)' | "$build/bada-cli-linux-x64" run - >/dev/null
"$build/bada-cli-linux-x64" version

# 5) build a .deb that installs the binary as /usr/bin/bada.
pkg="$build/deb/bada-cli_${ver}_amd64"
mkdir -p "$pkg/DEBIAN" "$pkg/usr/bin" "$pkg/usr/share/doc/bada"
cp "$build/bada-cli-linux-x64" "$pkg/usr/bin/bada"
cp "$app/README.md" "$pkg/usr/share/doc/bada/README.md" 2>/dev/null || true
cat > "$pkg/DEBIAN/control" <<CTRL
Package: bada
Version: ${ver}
Section: devel
Priority: optional
Architecture: amd64
Maintainer: Masaaki Yamaguchi <masaaki.tabu4@gmail.com>
Homepage: https://github.com/masaaki-avnturle/Bada
Description: Bada language — command-line compiler and interpreter (+ quantum)
 Lexer, parser, tree-walking interpreter and a bytecode compiler + stack VM for
 the Bada language, plus a quantum backend (state-vector simulator + OpenQASM).
 Self-contained (Node SEA); no runtime dependencies. Commands: run vm dis qasm check.
CTRL
dpkg-deb --build --root-owner-group "$pkg" >/dev/null
mv "$build/deb/bada-cli_${ver}_amd64.deb" "$build/bada-cli_${ver}_amd64.deb"

echo "== built =="
ls -la "$build/bada-cli-linux-x64" "$build/bada-cli_${ver}_amd64.deb"
