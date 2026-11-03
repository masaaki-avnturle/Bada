#!/usr/bin/env bash
#
# build-iso.sh — Bada VM Pro レガシー GRUB マルチブート ライブ ISO を生成
#
#   grub-mkrescue (BIOS / i386-pc) で、GRUB を MBR のマルチ OS セレクタと
#   する前提のライブ ISO を作る。ISO には次を同梱:
#     boot/grub/grub.cfg  … レガシー GRUB マルチブート メニュー
#     INDEX.HTM           … Bada VM Pro OS 本体 (ブラウザで開くと起動)
#     install-grub-multiboot.sh … 実機インストーラ (末尾パーティション + GRUB)
#   grub-mkrescue は isohybrid MBR も付けるので Rufus / USB からも起動でき、
#   ブート後は GRUB メニュー (レガシー) が出る。
#
# 必要パッケージ (CI では apt): grub-pc-bin grub2-common xorriso
#   Ubuntu: sudo apt-get install -y grub-pc-bin grub2-common xorriso
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
OUT="$ROOT/dist/BadaVMPro-live.iso"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/boot/grub"
cp "$HERE/grub/grub.cfg"             "$STAGE/boot/grub/grub.cfg"
cp "$ROOT/index.html"                "$STAGE/INDEX.HTM"
cp "$HERE/install-grub-multiboot.sh" "$STAGE/install-grub-multiboot.sh"
cp "$HERE/grub/banner.txt"           "$STAGE/BANNER.TXT"
if [ -f "$ROOT/../LICENSE" ]; then cp "$ROOT/../LICENSE" "$STAGE/LICENSE.TXT"; else
  echo "MIT License - see https://github.com/masaaki-avnturle/Bada" > "$STAGE/LICENSE.TXT"
fi

cat > "$STAGE/README.TXT" <<'MSG'
Bada VM Pro — legacy GRUB multiboot live ISO
============================================
このディスクは BIOS/レガシー用の GRUB マルチブート ライブ ISO です。
ブートすると GRUB メニューが出て、複数の OS を選択できます。

他の OS と共存させるインストール (先頭ヘッダを占有しない):
  ・Bada VM Pro は *ディスク末尾* の新規パーティションに入ります。
  ・Windows は前方パーティションのまま残り、GRUB が chainload します。
  ・GRUB は MBR のマルチ OS セレクタになります。

既存の Ubuntu などから:
  sudo bash install-grub-multiboot.sh            # 下見 (非破壊・既定)
  sudo bash install-grub-multiboot.sh --apply    # 実行

OS 本体は INDEX.HTM です。どの PC のブラウザでも開けば w9wm デスクトップが
起動します (bash/apt/vim/emacs/ssh/screen/latex/mozc プリインストール)。
MSG

mkdir -p "$ROOT/dist"

# grub-mkrescue: BIOS(i386-pc) レガシー ブータブル ISO。
# --modules で chainloader/part/fs を core に埋め込み、メニューが確実に動くように。
grub-mkrescue \
  --modules="biosdisk part_msdos part_gpt fat ntfs ntldr chain configfile normal echo ls search search_label test all_video gfxterm" \
  -o "$OUT" "$STAGE" \
  -- -volid BADAVMPRO_LIVE

echo
echo "wrote $OUT"
ls -la "$OUT"
file "$OUT"
