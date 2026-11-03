#!/usr/bin/env bash
#
# install-grub-multiboot.sh — Bada VM Pro をレガシー GRUB マルチブートで
#                             既存 OS と共存インストールする
#
# 方針 (先頭ヘッダを占有しない・他 OS と共存):
#   1. ディスク *末尾* の空き領域に Bada VM Pro 用の新規パーティションを作る
#      (既存パーティションは一切消さない / FAT32・ラベル BADAVMPRO)。
#   2. そこへ OS 本体 (INDEX.HTM) と GRUB の /boot を置く。
#   3. GRUB (i386-pc / レガシー BIOS) を MBR に入れ、「マルチ OS セレクタ」
#      にする。Windows は前方パーティションのまま chainload。
#   4. 生成する grub.cfg で Windows / Bada VM Pro / 既存 OS を選べる。
#
# 安全:
#   ・既定は *下見 (ドライラン)*。何も書き込まず、実行予定の手順と、検出した
#     ディスク・パーティション・末尾空き領域・Windows パーティションを表示。
#   ・実際に書き込むのは --apply を付けたときだけ (root 必須)。
#   ・末尾の空き領域にしか手を付けず、既存パーティションのデータは保持。
#
# 使い方:
#   sudo bash install-grub-multiboot.sh                 # 下見
#   sudo bash install-grub-multiboot.sh --apply         # 実行
#   オプション: --disk /dev/sdX  --size <MiB(既定512)>  --os-html <path>
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

APPLY=0
DISK=""
SIZE_MIB=512
OS_HTML=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --disk) DISK="$2"; shift ;;
    --size) SIZE_MIB="$2"; shift ;;
    --os-html) OS_HTML="$2"; shift ;;
    -h|--help)
      sed -n '2,33p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

say(){ echo "[install] $*"; }
die(){ echo "[install] ERROR: $*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "需要コマンドがありません: $1 (apt install $2)"; }

# OS 本体 HTML の所在
if [ -z "$OS_HTML" ]; then
  for c in "$HERE/../index.html" "$HERE/INDEX.HTM" "$(dirname "$HERE")/INDEX.HTM" "./INDEX.HTM"; do
    [ -f "$c" ] && { OS_HTML="$c"; break; }
  done
fi
[ -n "$OS_HTML" ] && [ -f "$OS_HTML" ] || die "OS 本体 (INDEX.HTM / index.html) が見つかりません。--os-html で指定してください。"

need parted parted
need lsblk util-linux

# 対象ディスクの決定
if [ -z "$DISK" ]; then
  mapfile -t DISKS < <(lsblk -dn -o NAME,TYPE | awk '$2=="disk"{print "/dev/"$1}')
  if [ "${#DISKS[@]}" -eq 1 ]; then DISK="${DISKS[0]}"
  elif [ "${#DISKS[@]}" -eq 0 ]; then die "ディスクが見つかりません。"
  else
    say "複数のディスクがあります。--disk で指定してください:"; printf '  %s\n' "${DISKS[@]}"; exit 2
  fi
fi
[ -b "$DISK" ] || [ -f "$DISK" ] || die "ディスクがありません: $DISK"

say "対象ディスク: $DISK"
say "現在のパーティション:"
parted -s "$DISK" unit MiB print 2>/dev/null | sed 's/^/    /' || true

# 末尾の空き領域を検出 (parted の free リストで、ディスク末尾に接する最後の Free)
DISK_END_MIB="$(parted -ms "$DISK" unit MiB print free 2>/dev/null | awk -F: '/^BYT;/{next} $1=="'"$DISK"'"||$1~/^\/dev/{gsub(/MiB/,"",$2); dend=$2} END{print dend}')"
read -r FREE_START FREE_END FREE_SIZE < <(
  parted -ms "$DISK" unit MiB print free 2>/dev/null | awk -F: '
    /free/ { gsub(/MiB/,"",$2); gsub(/MiB/,"",$3); gsub(/MiB/,"",$4); s=$2; e=$3; z=$4 }
    END { print s, e, z }')

say "ディスク末尾: ${DISK_END_MIB:-?} MiB / 末尾空き: start=${FREE_START:-?} end=${FREE_END:-?} size=${FREE_SIZE:-?} MiB"

# Windows (前方) パーティションの検出: NTFS を優先 (ブロックデバイス時)。
# 画像ファイルを --disk に渡した下見では lsblk が使えないので非致命にする。
WIN_PART="$(lsblk -rno NAME,FSTYPE "$DISK" 2>/dev/null | awk '$2=="ntfs"{print "/dev/"$1; exit}')" || WIN_PART=""
WIN_HINT="(未検出 — Windows が無い構成かもしれません)"
[ -n "$WIN_PART" ] && WIN_HINT="$WIN_PART (NTFS)"
say "Windows パーティション (前方・chainload 対象): $WIN_HINT"

# 計画の提示
NEW_START="${FREE_START:-0}"
NEW_END_CALC=""
if [ -n "${FREE_START:-}" ]; then NEW_END_CALC="$(awk "BEGIN{print $NEW_START + $SIZE_MIB}")"; fi
say ""
say "=== 実行計画 (末尾パーティションに Bada VM Pro / GRUB を MBR へ) ==="
say "  1) parted $DISK mkpart primary fat32 ${NEW_START}MiB ${NEW_END_CALC:-+${SIZE_MIB}M}MiB  (末尾の空きのみ使用)"
say "  2) mkfs.vfat -n BADAVMPRO <新パーティション>"
say "  3) INDEX.HTM / BANNER.TXT を新パーティションへコピー"
say "  4) grub-install --target=i386-pc --boot-directory=<mnt>/boot --recheck $DISK   (GRUB を MBR へ)"
say "  5) <mnt>/boot/grub/grub.cfg を生成: Windows(chainload) / Bada VM Pro / 既存OS"
say ""

if [ "$APPLY" -ne 1 ]; then
  say "下見モードです。何も書き込んでいません。実行するには --apply を付けてください。"
  say "  sudo bash $(basename "$0") --apply --disk $DISK"
  exit 0
fi

# ---- ここから実書き込み (--apply) ----
[ "$(id -u)" -eq 0 ] || die "--apply には root 権限が必要です (sudo)。"
need mkfs.vfat dosfstools
need grub-install grub-pc-bin
[ -n "${FREE_START:-}" ] && [ -n "${FREE_END:-}" ] || die "末尾の空き領域を特定できませんでした。手動でパーティションを用意してください。"
# 末尾空きがディスク末尾に接しているか確認 (共存のため先頭側は触らない)
if [ -n "${DISK_END_MIB:-}" ]; then
  gap="$(awk "BEGIN{d=$DISK_END_MIB-$FREE_END; print (d<0?-d:d)}")"
  awk "BEGIN{exit !($gap <= 2)}" || die "検出した空き領域がディスク末尾ではありません。先頭側は触りません。中止します。"
fi
avail="$(awk "BEGIN{print $FREE_END-$FREE_START}")"
awk "BEGIN{exit !($avail >= $SIZE_MIB)}" || die "末尾空きが不足 (${avail}MiB < ${SIZE_MIB}MiB)。--size を小さくしてください。"

END_MIB="$(awk "BEGIN{print $FREE_START + $SIZE_MIB}")"
say "パーティション作成: ${FREE_START}MiB .. ${END_MIB}MiB"
parted -s "$DISK" unit MiB mkpart primary fat32 "$FREE_START" "$END_MIB"
NEWNO="$(parted -ms "$DISK" print | tail -1 | cut -d: -f1)"
parted -s "$DISK" set "$NEWNO" lba on || true
partprobe "$DISK" 2>/dev/null || true; sleep 1

# 子デバイス名 (loop/nvme/mmcblk は pN、sd/vd/hd は N)
base="$(basename "$DISK")"
if [[ "$base" =~ [0-9]$ ]]; then NEWDEV="${DISK}p${NEWNO}"; else NEWDEV="${DISK}${NEWNO}"; fi

# udev の無い最小環境向け: /sys からパーティションの /dev ノードを補完
ensure_node(){
  local dev="$1" name; name="$(basename "$dev")"
  [ -b "$dev" ] && return 0
  local sysf="/sys/block/${base}/${name}/dev"
  if [ -f "$sysf" ]; then
    local mm; mm="$(cat "$sysf")"; mknod "$dev" b "${mm%%:*}" "${mm##*:}" 2>/dev/null || true
  fi
}
ensure_node "$NEWDEV"
[ -b "$NEWDEV" ] || die "新パーティションのデバイスが見つかりません: $NEWDEV"
say "新パーティション: $NEWDEV"

mkfs.vfat -n BADAVMPRO "$NEWDEV" >/dev/null
MNT="$(mktemp -d)"
mount "$NEWDEV" "$MNT"
install -D "$OS_HTML" "$MNT/INDEX.HTM"
cp "$HERE/grub/banner.txt" "$MNT/BANNER.TXT" 2>/dev/null || cp "$HERE/BANNER.TXT" "$MNT/BANNER.TXT" 2>/dev/null || true

# GRUB (レガシー) を MBR へ。/boot は Bada パーティション上に置く。
grub-install --target=i386-pc --boot-directory="$MNT/boot" --recheck "$DISK"

# grub.cfg を具体的なパーティションで生成
WIN_ENTRY=""
if [ -n "$WIN_PART" ]; then
  WIN_NO="$(echo "$WIN_PART" | grep -o '[0-9]*$')"
  WIN_ENTRY="menuentry \"Windows  (chainload)\" --class windows {
  insmod part_msdos
  insmod ntfs
  insmod chain
  set root=(hd0,msdos${WIN_NO})
  drivemap -s (hd0) (hd0)
  chainloader +1
}"
fi
mkdir -p "$MNT/boot/grub"
cat > "$MNT/boot/grub/grub.cfg" <<CFG
set timeout=15
set default=0
insmod all_video
insmod gfxterm
if loadfont unicode ; then set gfxmode=auto; terminal_output gfxterm; fi
set menu_color_normal=cyan/black
set menu_color_highlight=black/cyan

menuentry "Bada VM Pro  (quantum Bada OS / w9wm desktop)" --class bada {
  insmod fat
  insmod search_label
  search --no-floppy --label --set=root BADAVMPRO
  echo ""
  if [ -f /BANNER.TXT ]; then cat /BANNER.TXT ; fi
  echo ""
  echo " OS 本体: (BADAVMPRO)/INDEX.HTM をブラウザで開くと起動します。"
  echo " 何かキーを押すとメニューへ戻ります。"
  read
}

${WIN_ENTRY}

menuentry "Boot from the first hard disk (existing OS)" {
  insmod chain
  set root=(hd0)
  chainloader +1
}

menuentry "System firmware setup" { fwsetup }
menuentry "Reboot" { reboot }
menuentry "Shut down" { halt }
CFG

sync
umount "$MNT"; rmdir "$MNT"
say "完了: GRUB (レガシー) を $DISK の MBR に導入し、Bada VM Pro を末尾パーティション $NEWDEV に配置しました。"
say "再起動すると GRUB メニューで Windows / Bada VM Pro / 既存 OS を選べます。"
