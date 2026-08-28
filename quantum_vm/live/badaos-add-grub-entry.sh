#!/bin/bash
# ============================================================================
# badaos-add-grub-entry.sh — add BadaOS to the GRUB menu of an EXISTING
# Linux PC without erasing anything (dual boot via ISO loopback).
#
# Usage (on the Linux machine that owns GRUB, as root):
#   sudo bash badaos-add-grub-entry.sh /path/to/BadaOS-12.0-live-amd64.iso
#
# The ISO is copied to /boot/badaos/ and a "BadaOS GNU/Quantum 12.0 (ISO)"
# entry is appended to /etc/grub.d/40_custom; from the next boot the PC's
# GRUB menu offers BadaOS next to the existing systems.
# Undo: remove the block from /etc/grub.d/40_custom and run update-grub.
# ============================================================================
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "run as root (sudo)"; exit 1; }
ISOSRC="${1:?usage: badaos-add-grub-entry.sh BadaOS-live.iso}"
[ -f "$ISOSRC" ] || { echo "no such file: $ISOSRC"; exit 1; }
command -v update-grub >/dev/null || { echo "update-grub not found (is this the GRUB host?)"; exit 1; }

mkdir -p /boot/badaos
cp "$ISOSRC" /boot/badaos/BadaOS-live.iso
BOOTDEV_UUID="$(findmnt -no UUID /boot 2>/dev/null || findmnt -no UUID /)"

cat >> /etc/grub.d/40_custom <<EOF

# --- BadaOS GNU/Quantum (added by badaos-add-grub-entry.sh) ---
menuentry "BadaOS GNU/Quantum 12.0 (ISO)" {
    search --no-floppy --fs-uuid --set=root $BOOTDEV_UUID
    set isofile=/badaos/BadaOS-live.iso
    if [ ! -e "\$isofile" ]; then set isofile=/boot/badaos/BadaOS-live.iso; fi
    loopback loop \$isofile
    linux (loop)/live/vmlinuz boot=live findiso=\$isofile toram quiet
    initrd (loop)/live/initrd
}
# --- end BadaOS ---
EOF

update-grub
echo "done: reboot and pick 'BadaOS GNU/Quantum 12.0 (ISO)' in the GRUB menu."
