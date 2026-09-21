#!/bin/sh
# グランドピアノ 88 鍵ぶんのサンプル(FluidR3_GM, MIT ライセンスの midi-js-soundfonts)を取得して WAV に変換する。
# 使い方: sh fetch_piano_samples.sh <出力フォルダ> [ffmpeg のパス]
set -e
OUT=${1:-piano}; FF=${2:-ffmpeg}
mkdir -p "$OUT"
BASE=https://raw.githubusercontent.com/gleitz/midi-js-soundfonts/gh-pages/FluidR3_GM/acoustic_grand_piano-mp3
for m in $(seq 21 108); do
  n=$(python3 -c "n='C Db D Eb E F Gb G Ab A Bb B'.split(); m=$m; print('%s%d'%(n[m%12], m//12-1))")
  [ -f "$OUT/$n.wav" ] && continue
  curl -sS -o "$OUT/$n.mp3" "$BASE/$n.mp3"
  "$FF" -y -loglevel error -i "$OUT/$n.mp3" -ac 1 -ar 44100 "$OUT/$n.wav"
  rm -f "$OUT/$n.mp3"
done
echo "done: $(ls "$OUT"/*.wav | wc -l) samples in $OUT"
