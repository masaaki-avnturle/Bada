#!/usr/bin/env bash
# make-apt-repo.sh — .deb を集めて flat な apt リポジトリの索引を作る
#   使い方: make-apt-repo.sh <debs_dir> <out_dir>
#   出力: <out_dir>/ に .deb 群 + Packages + Packages.gz + Release
#   ISO 側は `deb [trusted=yes] <base_url>/ ./` で参照する (署名なし)。
set -euo pipefail
DEBS_DIR="${1:?debs dir}"
OUT="${2:?out dir}"

command -v dpkg-scanpackages >/dev/null 2>&1 || sudo apt-get install -y dpkg-dev
command -v apt-ftparchive   >/dev/null 2>&1 || sudo apt-get install -y apt-utils

mkdir -p "$OUT"
cp "$DEBS_DIR"/*.deb "$OUT"/ 2>/dev/null || { echo "no .deb in $DEBS_DIR"; exit 0; }

cd "$OUT"
# Filename をベア名にする (GitHub Releases はフラットな URL のため)
dpkg-scanpackages --multiversion . /dev/null > Packages
sed -i 's#^Filename: \./#Filename: #' Packages
gzip -kf Packages

apt-ftparchive release . > Release

echo "== apt repo index =="
ls -l "$OUT"
echo "--- Packages ---"; sed -n '1,40p' Packages
