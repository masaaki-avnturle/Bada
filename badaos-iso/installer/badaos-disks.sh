#!/bin/bash
# badaos-disks — インストール先の候補になる「実ディスク」を一覧する (NAME SIZE MODEL)
#   ・起動に使っている USB / DVD (ライブメディア) は除く
#   ・フロッピー (2)・ループ (7)・CD/DVD (11)・zram は除く
#   ・sda を先頭に並べる (インストーラの既定値)
BOOTDEV=""
for m in /cdrom /run/live/medium /isodevice; do
  src="$(findmnt -no SOURCE "$m" 2>/dev/null | head -1)"
  [ -n "$src" ] && { BOOTDEV="$(lsblk -no PKNAME "$src" 2>/dev/null | head -1)"; [ -n "$BOOTDEV" ] || BOOTDEV="$(basename "$src")"; break; }
done
lsblk -dn -o NAME,SIZE,MODEL -e 2,7,11 2>/dev/null \
  | awk -v boot="$BOOTDEV" '$1 != boot && $1 !~ /^zram/' \
  | sort -k1,1 | awk '$1=="sda"{print; next} {rest=rest $0 "\n"} END{printf "%s", rest}'
