#!/usr/bin/env bash
# Build a standalone Ubuntu/Linux CLI application that revives a contact-faulty
# USB memory stick, using Node's Single-Executable-Application feature — no Node
# install required on the target machine.
#
# Output: cli/build/usb-resume-linux-x64        (run: ./usb-resume-linux-x64)
#     and cli/build/usb-resume-cli_<ver>_amd64.deb  (installs /usr/bin/usb-resume)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
ver="1.0.0"
build="$here/build"
rm -rf "$build"; mkdir -p "$build"

# 1) the CLI is a single self-contained file — copy it in as the SEA main.
cp "$here/usb-resume.js" "$build/usb-resume.js"

# 2) generate the SEA blob.
cat > "$build/sea-config.json" <<JSON
{ "main": "usb-resume.js", "output": "usb-resume.blob", "disableExperimentalSEAWarning": true }
JSON
( cd "$build" && node --experimental-sea-config sea-config.json )

# 3) inject the blob into a copy of the node binary.
cp "$(command -v node)" "$build/usb-resume-linux-x64"
npx --yes postject "$build/usb-resume-linux-x64" NODE_SEA_BLOB "$build/usb-resume.blob" \
  --sentinel-fuse NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2
chmod +x "$build/usb-resume-linux-x64"

# 4) smoke-test.
"$build/usb-resume-linux-x64" --version
"$build/usb-resume-linux-x64" scan >/dev/null

# 5) build a .deb that installs the binary as /usr/bin/usb-resume.
pkg="$build/deb/usb-resume-cli_${ver}_amd64"
mkdir -p "$pkg/DEBIAN" "$pkg/usr/bin" "$pkg/usr/share/doc/usb-resume"
cp "$build/usb-resume-linux-x64" "$pkg/usr/bin/usb-resume"
cp "$here/../README.md" "$pkg/usr/share/doc/usb-resume/README.md" 2>/dev/null || true
cat > "$pkg/DEBIAN/control" <<CTRL
Package: usb-resume
Version: ${ver}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Masaaki Yamaguchi <masaaki.tabu4@gmail.com>
Homepage: https://github.com/masaaki-avnturle/Bada
Description: Revive a contact-faulty USB memory stick (re-authorize / power / re-enumerate)
 Corrects the machine-language descriptor's n-ary (base-n) digit drift on the
 complex rotational body (integrable error corrector), then re-authorizes,
 powers on and re-binds the device via sysfs. Self-contained (Node SEA); no
 runtime dependencies. Simulation by default; --apply writes real sysfs (root).
CTRL
dpkg-deb --build --root-owner-group "$pkg" >/dev/null
mv "$build/deb/usb-resume-cli_${ver}_amd64.deb" "$build/usb-resume-cli_${ver}_amd64.deb"

echo "== built =="
ls -la "$build/usb-resume-linux-x64" "$build/usb-resume-cli_${ver}_amd64.deb"
