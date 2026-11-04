#!/bin/bash
# =============================================================================
# badaos-triboot-text — text-only triple-boot installer (no X / no GPU needed)
#
#   For PCs where the graphical screen stays black. Started automatically on
#   tty1 by the GRUB entry "Install (text mode)", or by hand:
#       sudo badaos-triboot-text
#   The Linux text console cannot draw Japanese, so this screen is English.
#   It runs the same core as the GUI wizard (badaos-triboot-core.sh):
#     [Windows][BADAVMBOOT (FAT, Bada VM Pro boot loader)][BADAVMPRO (OS)][Linux]
#   The disk's first sector (MBR / Windows' boot code) is not written.
# =============================================================================
CORE=/usr/local/lib/badaos/badaos-triboot-core.sh
LOG=/tmp/badaos-triboot.log
[ "$(id -u)" = 0 ] || exec sudo "$0" "$@"
export LANG=C.UTF-8

# Japanese plan text -> English (the console has no Japanese font)
tr_plan(){ sed -u \
  -e 's/=== Bada VM Pro トリプルブート計画 ===/=== Bada VM Pro triple-boot plan ===/' \
  -e 's/ディスク :/Disk    :/; s/起動方式:/boot mode:/; s/セクタ/sector/' \
  -e 's/(変更なし)/(unchanged)/; s/ → 縮小後 / -> shrink to /' \
  -e 's/^Windows の起動パーティション (ESP) \/ MBR: 変更しない/Windows ESP \/ MBR: not changed/' \
  -e 's/^Windows の MBR 起動コード: 変更しない (Bada VM Pro の起動コードは拡張区画の先頭 (EBR)、それをアクティブに)/MBR: not changed. Boot code goes to the extended partition (EBR), which is made active/' \
  -e 's/^Windows の MBR 起動コード: 変更しない (Bada VM Pro の起動コードは専用 FAT の先頭 (VBR)、それをアクティブに)/MBR: not changed. Boot code goes to the BADAVMBOOT FAT boot sector, which is made active/' \
  -e 's/^GPT + Legacy: 保護 MBR の起動コードと BIOS 起動区画を使用/GPT + Legacy: protective MBR boot code + BIOS boot partition/' \
  -e 's/--- 予定のレイアウト (ディスク先頭から) ---/--- planned layout (from the start of the disk) ---/' \
  -e 's/(新規)/(new) /; s/拡張区画/extended/; s/BIOS起動/BIOS-boot/; s/GRUB 埋め込み/GRUB-core/' \
  -e 's/★ Bada VM Pro 専用ブートローダ/<= Bada VM Pro boot loader (FAT)/' \
  -e 's/★ Bada VM Pro OS/<= Bada VM Pro OS/' \
  -e 's/★ 拡張区画 (中に論理区画 2 つ)/<= extended partition (2 logical inside)/' \
  -e 's/★ GRUB 本体 (未割り当て)/<= GRUB core (unallocated gap)/; s/★ GRUB 埋め込み用/<= GRUB core/' \
  -e 's/^PLAN_ONLY=1: ディスクは変更していません/(plan only - nothing written yet)/' \
  -e 's/^ERROR: Windows (NTFS) パーティションが見つかりません.*/ERROR: no Windows (NTFS) partition found on this disk/' \
  -e 's/^ERROR: Linux (ext4\/btrfs\/xfs) パーティションが見つかりません.*/ERROR: no Linux (ext4\/btrfs\/xfs) partition found on this disk/' \
  -e 's/^ERROR: Linux が Windows より前にあります.*/ERROR: Linux is before Windows. The disk must be: Windows, (free space), Linux/' \
  -e 's/^ERROR: Windows と Linux の間に \([0-9]*\)GiB 以上の空きがありません (現在 \([0-9]*\)GiB).*/ERROR: less than \1 GiB free between Windows and Linux (now \2 GiB)/' \
  -e 's/^ERROR: MBR の基本区画が 4 つとも使用中.*/ERROR: all 4 primary MBR partitions are used (1 free slot needed)/' \
  -e 's/^ERROR: MBR の拡張区画が既にある.*/ERROR: an extended partition already exists (not supported)/' \
  -e 's/^ERROR: 既に Bada VM Pro のパーティション.*/ERROR: Bada VM Pro partitions already exist on this disk/' \
  -e 's/^ERROR: OS 本体のパーティションが.*/ERROR: the OS partition would be smaller than 20 GiB/' \
  -e 's/^ERROR: Windows を縮小すると 30GiB を下回ります.*/ERROR: Windows would become smaller than 30 GiB; choose a smaller size/' \
  -e 's/^ERROR: \(.*\) のパーティション表を読めません.*/ERROR: cannot read the partition table of \1/' \
  -e 's/^注意: .*//' ; }

stage(){ case "$1" in
  3) echo "unmounting partitions";; 6|10) echo "shrinking Windows (NTFS)";;
  14) echo "creating partitions between Windows and Linux";; 18) echo "formatting FAT + ext4";;
  22) echo "copying the system (takes several minutes)";; 70) echo "writing settings";;
  80) echo "creating the user";; 86|88) echo "installing the Bada VM Pro boot loader";;
  93) echo "generating the boot menu";; 97) echo "cleaning up";; 100) echo "done";;
  *) echo "working";; esac; }

clear
echo "=================================================================="
echo " Bada VM Pro OS - triple boot installer (text mode)"
echo "   Windows | BADAVMBOOT (FAT, boot loader) | BADAVMPRO (OS) | Linux"
echo "   Existing Windows and Linux are kept. The MBR is not rewritten."
echo "=================================================================="
echo
echo "Disks:"
mapfile -t DISKS < <(lsblk -dn -o NAME -e 7,11)
i=1; for d in "${DISKS[@]}"; do printf '  %d) /dev/%s  %s  %s\n' "$i" "$d" "$(lsblk -dn -o SIZE /dev/$d)" "$(lsblk -dn -o MODEL /dev/$d)"; i=$((i+1)); done
echo
read -r -p "Disk with Windows and Linux (number): " n
DISK="/dev/${DISKS[$((n-1))]}"
[ -b "$DISK" ] || { echo "No disk selected."; read -r -p "Enter to exit" _; exit 1; }
read -r -p "Size for Bada VM Pro in GiB (Enter = all free space between them): " SIZE
SIZE="${SIZE//[^0-9]/}"; SIZE="${SIZE:-0}"

SHRINK=0
echo
if ! TARGET_DISK="$DISK" BADA_SIZE_GB="$SIZE" PLAN_ONLY=1 bash "$CORE" 2>&1 | tr_plan | tee /tmp/plan.txt | grep -v '^ERROR'; then :; fi
if grep -q '^ERROR' /tmp/plan.txt; then
  echo "Cannot plan: $(grep '^ERROR' /tmp/plan.txt | head -1)"
  if grep -q 'GiB free between' /tmp/plan.txt; then
    read -r -p "There is not enough free space. Shrink the end of Windows (NTFS) to make room? [y/N] " a
    [ "$a" = y ] || { read -r -p "Enter to exit" _; exit 1; }
    SHRINK=1
    TARGET_DISK="$DISK" BADA_SIZE_GB="$SIZE" SHRINK_WINDOWS=1 PLAN_ONLY=1 bash "$CORE" 2>&1 | tr_plan | tee /tmp/plan.txt
    grep -q '^ERROR' /tmp/plan.txt && { read -r -p "Enter to exit" _; exit 1; }
  else
    echo "(Windows must be before Linux, with free space between them. Use GParted if needed.)"
    read -r -p "Enter to exit" _; exit 1
  fi
fi
echo
read -r -p "Host name [badaos]: " HOST
read -r -p "User name [bada]: " USER_NAME
while :; do
  read -r -s -p "Password: " PASS; echo
  read -r -s -p "Password (again): " PASS2; echo
  [ "$PASS" = "$PASS2" ] && break; echo "Passwords differ, try again."
done
echo
read -r -p "Install with the plan above? Type yes to continue: " ok
[ "$ok" = yes ] || { echo "Cancelled."; read -r -p "Enter to exit" _; exit 1; }

: > "$LOG"
echo
TARGET_DISK="$DISK" BADA_SIZE_GB="$SIZE" SHRINK_WINDOWS="$SHRINK" \
NEW_HOST="${HOST:-badaos}" NEW_USER="${USER_NAME:-bada}" NEW_PASS="${PASS:-bada}" \
  bash "$CORE" 2>>"$LOG" | while read -r line; do
    case "$line" in [0-9]*) printf '[%3s%%] %s\n' "$line" "$(stage "$line")";; esac
  done
rc=${PIPESTATUS[0]}
echo
if [ "$rc" = 0 ]; then
  echo "Installation finished. Remove the USB stick and reboot."
  read -r -p "Reboot now? [Y/n] " a; [ "$a" = n ] || reboot
else
  echo "Installation FAILED (exit code $rc). Last lines of $LOG:"
  tail -n 15 "$LOG"
  read -r -p "Enter to exit" _
fi
exit "$rc"
