#!/usr/bin/env bash
# Build a standalone Windows 10/11 CLI executable for the Bada language
# (compiler + interpreter + quantum) using Node's Single-Executable-Application
# feature. Runs on windows-latest with `shell: bash` (Git Bash).
#
# Output: cli/build/bada-cli-win-x64.exe
#   Usage on Windows:  bada-cli-win-x64.exe run prog.bada
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
app="$(cd "$here/.." && pwd)"
build="$here/build"
rm -rf "$build"; mkdir -p "$build"

# 1) bundle engine + CLI into one self-contained file.
cat "$app/www/bada.js" "$here/usb.js" "$here/cli.js" > "$build/bada-bundle.js"

# 2) generate the SEA blob.
cat > "$build/sea-config.json" <<JSON
{ "main": "bada-bundle.js", "output": "bada-prep.blob", "disableExperimentalSEAWarning": true }
JSON
( cd "$build" && node --experimental-sea-config sea-config.json )

# 3) copy node.exe and inject the blob.
node -e "require('fs').copyFileSync(process.execPath, process.argv[1])" "$build/bada-cli-win-x64.exe"
npx --yes postject "$build/bada-cli-win-x64.exe" NODE_SEA_BLOB "$build/bada-prep.blob" \
  --sentinel-fuse NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2

# 4) smoke-test.
echo 'print "bada win cli " + (2+2)' | "$build/bada-cli-win-x64.exe" run -
"$build/bada-cli-win-x64.exe" version
echo "== built =="
ls -la "$build/bada-cli-win-x64.exe"
