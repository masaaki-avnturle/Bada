#!/usr/bin/env bash
# 24 曲を最初から最後まで生成する: MP3 → 音サンプル → 作曲 → レンダリング → MP4
# usage: ./run_all.sh <dir with the 16 mp3s> <work dir>
set -euo pipefail
SRC=$1; WORK=${2:-./work}; HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$WORK/wav" "$WORK/wav44" "$WORK/audio" "$HERE/out" "$HERE/midi"
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null || echo ffmpeg)
for f in "$SRC"/*.mp3; do b=$(basename "${f%.mp3}")
  "$FF" -hide_banner -loglevel error -y -i "$f" -ac 1 -ar 22050 "$WORK/wav/$b.wav"
  "$FF" -hide_banner -loglevel error -y -i "$f" -ac 1 -ar 44100 "$WORK/wav44/$b.wav"; done
python3 "$HERE/segment.py" "$WORK/wav" "$WORK/segments.json"        # 安定音高の断片を切り出す
python3 "$HERE/compose.py" "$HERE/fugues.json"                         # 24 曲を作曲
python3 "$HERE/midi.py" "$HERE/fugues.json" "$HERE/midi"               # MIDI 書き出し
python3 "$HERE/render.py" "$HERE/fugues.json" "$WORK/wav44" "$WORK/segments.json" "$WORK/audio"   # 実音源で演奏
python3 "$HERE/video.py" "$HERE/fugues.json" "$WORK/audio" "$HERE/out"                            # MP4
