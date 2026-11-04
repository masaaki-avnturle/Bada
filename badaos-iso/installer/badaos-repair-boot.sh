#!/bin/bash
# =============================================================================
# badaos-repair-boot — インストール済み Bada VM Pro の「起動」を直す (再インストール不要)
#   「grub rescue>」で止まる / 起動メニューが出ない時に、USB のライブ環境から実行:
#       sudo badaos-repair-boot          (デスクトップの「起動の修復」からも可)
#   BADAVMPRO / BADAVMBOOT のラベルでパーティションを探し、ブートローダを
#   専用 FAT (BADAVMBOOT) 側に入れ直す。ディスク先頭 (MBR) は書き換えない。
# =============================================================================
set -uo pipefail
[ "$(id -u)" = 0 ] || exec sudo "$0" "$@"
LOG=/tmp/badaos-repair.log
if [ -n "${DISPLAY:-}" ] && [ -z "${BADA_IN_XTERM:-}" ] && command -v xterm >/dev/null 2>&1; then
  command -v zenity >/dev/null && ! zenity --question --width=520 --title="Bada VM Pro 起動の修復" \
    --text="インストール済みの Bada VM Pro のブートローダを入れ直します。\n(専用 FAT パーティション BADAVMBOOT 側。sda の先頭 MBR は書き換えません)\n\n実行しますか?" && exit 0
  exec env BADA_IN_XTERM=1 xterm -fa "DejaVu Sans Mono" -fd "Noto Sans Mono CJK JP" -fs 12 -geometry 100x30+40+40 \
    -T "Bada VM Pro 起動の修復" -e bash -c "'$0'; echo; read -r -p 'Enter で閉じる' _"
fi
fail(){ echo "ERROR: $*"; exit 1; }
exec > >(tee "$LOG") 2>&1

ROOT_DEV="$(blkid -L BADAVMPRO || true)"; BOOT_DEV="$(blkid -L BADAVMBOOT || true)"
[ -b "$ROOT_DEV" ] && [ -b "$BOOT_DEV" ] || fail "BADAVMPRO / BADAVMBOOT partitions not found (is Bada VM Pro installed?)"
DISK="/dev/$(lsblk -no PKNAME "$BOOT_DEV" | head -1)"
echo "Bada VM Pro: OS=$ROOT_DEV  boot(FAT32)=$BOOT_DEV  disk=$DISK"
LABEL="$(sfdisk -J "$DISK" | python3 -c 'import json,sys; print(json.load(sys.stdin)["partitiontable"]["label"])')"

MNT=/mnt/badarepair; mkdir -p "$MNT"
umount -R "$MNT" 2>/dev/null || true
mount "$ROOT_DEV" "$MNT" || fail "cannot mount BADAVMPRO"
mkdir -p "$MNT/boot/efi"; mount "$BOOT_DEV" "$MNT/boot/efi" || fail "cannot mount BADAVMBOOT"
for m in dev dev/pts proc sys run; do mkdir -p "$MNT/$m"; done
mount --bind /dev "$MNT/dev"; mount --bind /dev/pts "$MNT/dev/pts"
mount -t proc none "$MNT/proc"; mount -t sysfs none "$MNT/sys"; mount --bind /run "$MNT/run"
[ -d /sys/firmware/efi/efivars ] && mount -t efivarfs efivarfs "$MNT/sys/firmware/efi/efivars" 2>/dev/null || true
cleanup(){ sync; umount -R "$MNT" 2>/dev/null || umount -lR "$MNT" 2>/dev/null || true; }
trap cleanup EXIT

[ -L "$MNT/boot/grub" ] || { rm -rf "$MNT/boot/grub"; ln -s efi/grub "$MNT/boot/grub"; }
BOOT_UUID="$(blkid -s UUID -o value "$BOOT_DEV")"

if [ -d /sys/firmware/efi ]; then
  echo "== UEFI: reinstalling \\EFI\\BadaVMPro\\ on BADAVMBOOT"
  chroot "$MNT" grub-install --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot/efi \
    --bootloader-id=BadaVMPro --no-nvram --recheck || fail "grub-install (UEFI) failed"
  chroot "$MNT" grub-install --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot/efi \
    --removable --no-nvram --recheck || true
  for d in "$MNT/boot/efi/EFI/BadaVMPro" "$MNT/boot/efi/EFI/BOOT"; do
    [ -d "$d" ] && printf 'search --no-floppy --fs-uuid --set=root %s\nset prefix=($root)/grub\nconfigfile $prefix/grub.cfg\n' "$BOOT_UUID" > "$d/grub.cfg"
  done
  L='\EFI\BadaVMPro\grubx64.efi'; [ -f "$MNT/boot/efi/EFI/BadaVMPro/shimx64.efi" ] && L='\EFI\BadaVMPro\shimx64.efi'
  for n in $(efibootmgr | grep -E "^Boot[0-9A-Fa-f]{4}\*? Bada VM Pro([[:space:]]|\$)" | cut -c5-8); do efibootmgr -q -b "$n" -B || true; done
  efibootmgr -q -c -d "$DISK" -p "$(echo "$BOOT_DEV" | grep -o '[0-9]*$')" -L "Bada VM Pro" -l "$L" || echo "note: could not add the UEFI boot entry"
elif [ "$LABEL" = dos ]; then
  echo "== Legacy + MBR: reinstalling GRUB on the BADAVMBOOT FAT side (MBR not changed)"
  bash /usr/local/lib/badaos/badaos-legacy-boot "$DISK" "$MNT" || fail "Legacy boot setup failed"
else
  echo "== Legacy + GPT: reinstalling GRUB to the BIOS boot partition"
  chroot "$MNT" grub-install --target=i386-pc --boot-directory=/boot/efi --recheck "$DISK" || fail "grub-install (i386-pc) failed"
fi
echo "== regenerating the boot menu (detects Windows / Linux)"
chroot "$MNT" grub-mkconfig -o /boot/efi/grub/grub.cfg || fail "grub-mkconfig failed"
echo
echo "Repair finished. Remove the USB stick and reboot."
