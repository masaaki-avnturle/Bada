#!/usr/bin/env bash
#
# build-iso.sh — Bada VM Pro ライブ CD/USB (BadaVMPro-live.iso) を生成
#
#   本物の isolinux (syslinux) を用いた El Torito ブータブル ISO を作る。
#   これにより Rufus はディスクを「ISO イメージモード」で認識し、USB
#   ブートディスクを作成できる (自作 MBR による DD モード強制ではない)。
#   isohybrid MBR (isohdpfx.bin) も埋め込むので CD/USB どちらでもブート可。
#
# 必要パッケージ (CI では apt で導入): xorriso, isolinux, syslinux-common
#   Ubuntu: sudo apt-get install -y xorriso isolinux syslinux-common
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
OUT="$ROOT/dist/BadaVMPro-live.iso"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# --- isolinux バイナリの所在 (ディストリで揺れるため候補から探す) ---
find_first() { for p in "$@"; do [ -f "$p" ] && { echo "$p"; return 0; }; done; return 1; }
ISOLINUX_BIN="$(find_first /usr/lib/ISOLINUX/isolinux.bin /usr/share/syslinux/isolinux.bin)"
LDLINUX_C32="$(find_first /usr/lib/syslinux/modules/bios/ldlinux.c32 /usr/share/syslinux/ldlinux.c32)"
ISOHDPFX="$(find_first /usr/lib/ISOLINUX/isohdpfx.bin /usr/share/syslinux/isohdpfx.bin || true)"

echo "isolinux.bin : $ISOLINUX_BIN"
echo "ldlinux.c32  : $LDLINUX_C32"
echo "isohdpfx.bin : ${ISOHDPFX:-(なし: isohybrid をスキップ)}"

# --- ステージング (ISO のルートに置くファイル) ---
mkdir -p "$STAGE/isolinux"
cp "$ROOT/index.html" "$STAGE/INDEX.HTM"
cp "$ISOLINUX_BIN" "$STAGE/isolinux/isolinux.bin"
cp "$LDLINUX_C32"  "$STAGE/isolinux/ldlinux.c32"
cp "$HERE/isolinux/isolinux.cfg" "$STAGE/isolinux/isolinux.cfg"

# 起動バナー (isolinux が DISPLAY で表示)
cat > "$STAGE/isolinux/boot.msg" <<'MSG'

  ================================================================
   Bada VM Pro  --  Live CD / USB  (w9wm desktop, quantum Bada OS)
  ================================================================

  This medium carries the Bada VM Pro operating system as data.
  Open  INDEX.HTM  from this disc/USB in any web browser to boot
  the w9wm desktop OS (bash/apt/vim/emacs/ssh/screen/latex/mozc
  preinstalled).

  Built with isolinux -- create a bootable USB with Rufus in
  "ISO Image mode".  Native apps: github.com/masaaki-avnturle/Bada

MSG

# README / AUTORUN / LICENSE
cat > "$STAGE/README.TXT" <<'MSG'
Bada VM Pro Live CD/USB
=======================
INDEX.HTM をウェブブラウザで開くと OS (w9wm デスクトップ) が起動します。
Rufus では「ISO イメージモード」で USB ブートディスクを作成できます。
ネイティブ版: https://github.com/masaaki-avnturle/Bada
MSG
cat > "$STAGE/AUTORUN.INF" <<'MSG'
[autorun]
label=Bada VM Pro Live CD
action=Open INDEX.HTM in your browser to boot the OS
MSG
if [ -f "$ROOT/../LICENSE" ]; then cp "$ROOT/../LICENSE" "$STAGE/LICENSE.TXT"; else
  echo "MIT License - see https://github.com/masaaki-avnturle/Bada" > "$STAGE/LICENSE.TXT"
fi

mkdir -p "$ROOT/dist"

# --- xorriso で isolinux El Torito ISO を生成 (+ isohybrid) ---
ISOHYBRID_OPT=()
[ -n "${ISOHDPFX:-}" ] && ISOHYBRID_OPT=(-isohybrid-mbr "$ISOHDPFX")

xorriso -as mkisofs \
  -o "$OUT" \
  -V BADAVMPRO_LIVE \
  -J -joliet-long -r \
  -b isolinux/isolinux.bin \
  -c isolinux/boot.cat \
  -no-emul-boot -boot-load-size 4 -boot-info-table \
  "${ISOHYBRID_OPT[@]}" \
  "$STAGE"

echo
echo "wrote $OUT"
ls -la "$OUT"
file "$OUT"
