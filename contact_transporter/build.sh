#!/bin/sh
# build.sh — 設計図ソースを 1 本の Bada プログラムに結合し、C 版 Bada で実行する。
#   ./build.sh           : contact_blueprint.bada を生成して実行
#   ./build.sh --regen   : catalog/ から equations.bada を再生成してから実行
#   ./build.sh --native  : さらにネイティブ実行形式 contact_blueprint を生成
set -e
cd "$(dirname "$0")"
BADA=../bada_c/bada
[ -x "$BADA" ] || make -C ../bada_c >/dev/null
for a in "$@"; do
  [ "$a" = "--regen" ] && python3 tools/gen_equations.py catalog equations.bada
done
# bada_c には import が無いので、ライブラリ → 方程式レジストリ → 本体 の順に結合する
cat lib_core.bada lib_geom.bada lib_physics.bada lib_registry.bada equations.bada main_blueprint.bada > contact_blueprint.bada
"$BADA" run contact_blueprint.bada
for a in "$@"; do
  [ "$a" = "--native" ] && "$BADA" build contact_blueprint.bada -o contact_blueprint && echo "native: ./contact_blueprint"
done
exit 0
