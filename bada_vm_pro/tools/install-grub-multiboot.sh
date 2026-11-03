#!/usr/bin/env bash
#
# install-grub-multiboot.sh — Bada VM Pro をレガシー GRUB デュアルブートで
#                             既存 OS (Windows) と共存インストールする
#
# 「裏表 (front/back)」3 パーティション構成 (先頭ヘッダを占有しない):
#
#   [ Windows           ] [ BOOT (専用)        ] [ Bada VM Pro       ]
#   [ 前方・表(おもて)   ] [ WIN属性/ブートフラグ ] [ 末尾・裏(うら)    ]
#   [ そのまま chainload ] [ GRUB 本体+grub.cfg  ] [ INDEX.HTM (OS本体) ]
#                     ↑ Windows と Bada の「間」に専用ブートローダー区画
#
#   ・Bada VM Pro 用パーティションを作るとき、その手前に「WIN 属性
#     (FAT・ブートフラグ付き) のブートローダー専用パーティション」も作る。
#   ・GRUB (i386-pc / レガシー BIOS) の本体・モジュール・grub.cfg はこの
#     専用 BOOT パーティションに置く (先頭ヘッダや Windows/Bada の中ではない)。
#     ※ レガシー BIOS では MBR 先頭 440B に GRUB の最小ブートストラップだけ
#       が入る (これは BIOS の仕様上避けられない)。設定・モジュール本体は
#       専用パーティション側。
#   ・起動時に GRUB メニューで Windows(表) / Bada VM Pro(裏) / 既存OS を選択。
#   ・VMware Workstation Pro 16 の仮想ディスクでも同じレイアウトでデュアル
#     ブートできる。
#
# 安全:
#   ・既定は *下見 (ドライラン)*。何も書き込まず計画のみ表示。
#   ・実際に書き込むのは --apply のときだけ (root 必須)。
#   ・末尾の空き領域にしか手を付けず、既存パーティションのデータは保持。
#
# 使い方:
#   sudo bash install-grub-multiboot.sh                 # 下見
#   sudo bash install-grub-multiboot.sh --apply         # 実行
#   オプション: --disk /dev/sdX  --size <MiB(既定512)>
#               --boot-size <MiB(既定128)>  --os-html <path>
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

APPLY=0
DISK=""
SIZE_MIB=512
BOOT_SIZE_MIB=128
OS_HTML=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --disk) DISK="$2"; shift ;;
    --size) SIZE_MIB="$2"; shift ;;
    --boot-size) BOOT_SIZE_MIB="$2"; shift ;;
    --os-html) OS_HTML="$2"; shift ;;
    -h|--help)
      sed -n '2,46p' "$0"; exit 0 ;;
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

# 末尾の空き領域を検出
DISK_END_MIB="$(parted -ms "$DISK" unit MiB print free 2>/dev/null | awk -F: '/^BYT;/{next} $1=="'"$DISK"'"||$1~/^\/dev/{gsub(/MiB/,"",$2); dend=$2} END{print dend}')"
read -r FREE_START FREE_END FREE_SIZE < <(
  parted -ms "$DISK" unit MiB print free 2>/dev/null | awk -F: '
    /free/ { gsub(/MiB/,"",$2); gsub(/MiB/,"",$3); gsub(/MiB/,"",$4); s=$2; e=$3; z=$4 }
    END { print s, e, z }')

say "ディスク末尾: ${DISK_END_MIB:-?} MiB / 末尾空き: start=${FREE_START:-?} end=${FREE_END:-?} size=${FREE_SIZE:-?} MiB"

# Windows (前方・表) パーティションの検出
WIN_PART="$(lsblk -rno NAME,FSTYPE "$DISK" 2>/dev/null | awk '$2=="ntfs"{print "/dev/"$1; exit}')" || WIN_PART=""
WIN_HINT="(未検出 — Windows が無い構成かもしれません)"
[ -n "$WIN_PART" ] && WIN_HINT="$WIN_PART (NTFS)"
say "Windows パーティション (前方・表・chainload 対象): $WIN_HINT"

# 計画: 末尾空きに BOOT(専用) → Bada の順で 2 区画
B_START="${FREE_START:-0}"
B_END="$(awk "BEGIN{print ${FREE_START:-0} + $BOOT_SIZE_MIB}")"
V_START="$B_END"
V_END="$(awk "BEGIN{print $V_START + $SIZE_MIB}")"
say ""
say "=== 実行計画 (裏表 3 パーティション / GRUB は専用 BOOT 区画へ) ==="
say "  Windows(表)  … 前方パーティションのまま (chainload)"
say "  1) BOOT 専用: parted mkpart primary fat16 ${B_START}MiB ${B_END}MiB + set boot on (WIN属性)"
say "     → GRUB 本体 (i386-pc) + grub.cfg をここへ。ラベル BADABOOT"
say "  2) Bada(裏) : parted mkpart primary fat32 ${V_START}MiB ${V_END}MiB  (ラベル BADAVMPRO)"
say "     → INDEX.HTM / BANNER.TXT をここへ"
say "  3) grub-install --target=i386-pc --boot-directory=<BOOT>/boot $DISK (MBR は最小ブートストラップのみ)"
say "  4) <BOOT>/boot/grub/grub.cfg 生成: Windows(表) / Bada VM Pro(裏) / 既存OS"
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
if [ -n "${DISK_END_MIB:-}" ]; then
  gap="$(awk "BEGIN{d=$DISK_END_MIB-$FREE_END; print (d<0?-d:d)}")"
  awk "BEGIN{exit !($gap <= 2)}" || die "検出した空き領域がディスク末尾ではありません。先頭側は触りません。中止します。"
fi
need_total="$(awk "BEGIN{print $BOOT_SIZE_MIB + $SIZE_MIB}")"
avail="$(awk "BEGIN{print $FREE_END-$FREE_START}")"
awk "BEGIN{exit !($avail >= $need_total)}" || die "末尾空きが不足 (${avail}MiB < ${need_total}MiB)。--size / --boot-size を小さくしてください。"

base="$(basename "$DISK")"
ensure_node(){
  local dev="$1" name; name="$(basename "$dev")"
  [ -b "$dev" ] && return 0
  local sysf="/sys/block/${base}/${name}/dev"
  if [ -f "$sysf" ]; then
    local mm; mm="$(cat "$sysf")"; mknod "$dev" b "${mm%%:*}" "${mm##*:}" 2>/dev/null || true
  fi
}
dev_for_no(){ local n="$1"; if [[ "$base" =~ [0-9]$ ]]; then echo "${DISK}p${n}"; else echo "${DISK}${n}"; fi; }

# 1) BOOT 専用パーティション (Windows と Bada の間・WIN属性)
say "BOOT 専用パーティション作成: ${B_START}MiB .. ${B_END}MiB (fat16 / boot flag)"
parted -s "$DISK" unit MiB mkpart primary fat16 "$B_START" "$B_END"
BOOTNO="$(parted -ms "$DISK" print | tail -1 | cut -d: -f1)"
parted -s "$DISK" set "$BOOTNO" boot on            # ← WIN 属性 (アクティブ/ブートフラグ)
parted -s "$DISK" set "$BOOTNO" lba on || true
# 2) Bada VM Pro パーティション (裏・末尾)
say "Bada VM Pro パーティション作成: ${V_START}MiB .. ${V_END}MiB (fat32 / BADAVMPRO)"
parted -s "$DISK" unit MiB mkpart primary fat32 "$V_START" "$V_END"
VNO="$(parted -ms "$DISK" print | tail -1 | cut -d: -f1)"
parted -s "$DISK" set "$VNO" lba on || true
partprobe "$DISK" 2>/dev/null || true; sleep 1

BOOTDEV="$(dev_for_no "$BOOTNO")"; ensure_node "$BOOTDEV"
VDEV="$(dev_for_no "$VNO")";       ensure_node "$VDEV"
[ -b "$BOOTDEV" ] || die "BOOT パーティションのデバイスが見つかりません: $BOOTDEV"
[ -b "$VDEV" ] || die "Bada パーティションのデバイスが見つかりません: $VDEV"
say "BOOT=$BOOTDEV  Bada=$VDEV"

# フォーマット
mkfs.vfat -F 16 -n BADABOOT "$BOOTDEV" >/dev/null
mkfs.vfat -F 32 -n BADAVMPRO "$VDEV" >/dev/null

# Bada(裏) に OS 本体を配置
VMNT="$(mktemp -d)"; mount "$VDEV" "$VMNT"
install -D "$OS_HTML" "$VMNT/INDEX.HTM"
cp "$HERE/grub/banner.txt" "$VMNT/BANNER.TXT" 2>/dev/null || cp "$HERE/BANNER.TXT" "$VMNT/BANNER.TXT" 2>/dev/null || true
sync; umount "$VMNT"; rmdir "$VMNT"

# BOOT(専用) に GRUB を配置。MBR には最小ブートストラップのみ、本体はここ。
BMNT="$(mktemp -d)"; mount "$BOOTDEV" "$BMNT"
grub-install --target=i386-pc --boot-directory="$BMNT/boot" --recheck "$DISK"
cp "$HERE/grub/banner.txt" "$BMNT/boot/BANNER.TXT" 2>/dev/null || true

# grub.cfg を BOOT 区画に生成
WIN_ENTRY=""
if [ -n "$WIN_PART" ]; then
  WIN_NO="$(echo "$WIN_PART" | grep -o '[0-9]*$')"
  WIN_ENTRY="menuentry \"Windows  (表 / front — chainload)\" --class windows {
  insmod part_msdos
  insmod ntfs
  insmod chain
  set root=(hd0,msdos${WIN_NO})
  drivemap -s (hd0) (hd0)
  chainloader +1
}"
fi
mkdir -p "$BMNT/boot/grub"
cat > "$BMNT/boot/grub/grub.cfg" <<CFG
# Bada VM Pro — 裏表デュアルブート (専用 BOOT パーティション上の GRUB)
set timeout=15
set default=0
insmod part_msdos
insmod fat
insmod ntfs
insmod chain
insmod search_label
insmod all_video
insmod gfxterm
if loadfont unicode ; then set gfxmode=auto; terminal_output gfxterm; fi
set menu_color_normal=cyan/black
set menu_color_highlight=black/cyan

menuentry "Bada VM Pro  (裏 / back — quantum Bada OS / w9wm desktop)" --class bada {
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
  set root=(hd0)
  chainloader +1
}

menuentry "System firmware setup" { fwsetup }
menuentry "Reboot" { reboot }
menuentry "Shut down" { halt }
CFG

sync; umount "$BMNT"; rmdir "$BMNT"
say "完了: 裏表 3 パーティション構成を作成しました。"
say "  Windows(表) = 前方パーティション (chainload)"
say "  BOOT(専用)  = $BOOTDEV  (WIN属性/boot flag, GRUB 本体+grub.cfg)"
say "  Bada(裏)    = $VDEV  (BADAVMPRO, INDEX.HTM)"
say "再起動 (VMware Pro 16 等) すると GRUB メニューで Windows / Bada VM Pro を選べます。"
