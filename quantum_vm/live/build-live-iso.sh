#!/bin/bash
# ============================================================================
# build-live-iso.sh — build "BadaOS Live", a REAL bootable ISO for real PCs.
#
# What it produces: BadaOS-12.0-live-amd64.iso — a hybrid BIOS+UEFI image
# whose boot loader is the REAL GRUB 2: power the PC on, and the GRUB menu
# shows "BadaOS GNU/Quantum 12.0". Booting it starts a minimal Debian live
# system (kernel + squashfs) that autologins and launches the BadaOS
# environment (quantum_vm/dist/bada-vm-pro.html, the Bada-language hypervisor
# + BadaOS + BadaX Server) fullscreen in a Chromium kiosk — standalone, no
# Windows, no network needed.
#
# The live system also ships:
#   * /usr/local/sbin/badaos-install — the REAL-DISK installer: partitions a
#     chosen disk, copies the system onto it, and runs grub-install so the
#     machine's own boot loader menu shows BadaOS from then on. (Run inside
#     the live boot; it ERASES the chosen disk and asks for confirmation.)
#   * fonts-noto-cjk so the Japanese UI renders.
#
# Usage (Debian/Ubuntu host or CI, as root):
#   sudo bash quantum_vm/live/build-live-iso.sh [OUTPUT.iso]
# Requires: debootstrap squashfs-tools xorriso mtools grub-pc-bin
#           grub-efi-amd64-bin grub-common
# ============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
QVM="$(dirname "$HERE")"
OUT="${1:-$QVM/dist/BadaOS-12.0-live-amd64.iso}"
WORK="${BADAOS_LIVE_WORK:-/tmp/badaos-live}"
CHROOT="$WORK/chroot"
ISO="$WORK/iso"
MIRROR="${BADAOS_DEB_MIRROR:-https://deb.debian.org/debian}"
SUITE=bookworm

[ -f "$QVM/dist/bada-vm-pro.html" ] || { echo "run tools/build-vm.js first"; exit 1; }
[ "$(id -u)" = 0 ] || { echo "run as root (sudo)"; exit 1; }

echo "==> [1/6] debootstrap $SUITE ($MIRROR)"
rm -rf "$WORK"; mkdir -p "$CHROOT" "$ISO/live" "$ISO/boot/grub"
debootstrap --arch=amd64 --variant=minbase "$SUITE" "$CHROOT" "$MIRROR"

echo "==> [2/6] install kernel + live-boot + X + chromium kiosk"
# keep daemons quiet inside the chroot
printf '#!/bin/sh\nexit 101\n' > "$CHROOT/usr/sbin/policy-rc.d"
chmod +x "$CHROOT/usr/sbin/policy-rc.d"
mount -t proc proc "$CHROOT/proc"
mount -t sysfs sys "$CHROOT/sys"
mount -o bind /dev "$CHROOT/dev"
mount -o bind /dev/pts "$CHROOT/dev/pts"
trap 'umount -lf "$CHROOT/dev/pts" "$CHROOT/dev" "$CHROOT/sys" "$CHROOT/proc" 2>/dev/null || true' EXIT

cat > "$CHROOT/etc/apt/sources.list" <<EOF
deb $MIRROR $SUITE main contrib non-free-firmware
EOF
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get update -qq
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    linux-image-amd64 live-boot systemd-sysv \
    xserver-xorg xinit openbox chromium fonts-noto-cjk \
    kbd sudo rsync parted dosfstools e2fsprogs \
    grub2-common grub-pc-bin grub-efi-amd64-bin os-prober ntfs-3g \
    vim emacs-nox openssh-server curl wget less ca-certificates
# xinetd is optional in newer Debian suites
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq xinetd || true

# real networking (DHCP on every ethernet NIC) so `apt` reaches the FULL
# Debian archive -- 60,000+ packages, the same class as Ubuntu.
mkdir -p "$CHROOT/etc/systemd/network"
cat > "$CHROOT/etc/systemd/network/20-dhcp.network" <<'EOF'
[Match]
Name=en* eth*

[Network]
DHCP=yes
EOF
chroot "$CHROOT" systemctl enable systemd-networkd systemd-resolved ssh 2>/dev/null || \
chroot "$CHROOT" systemctl enable systemd-networkd ssh || true
ln -sf /run/systemd/resolve/resolv.conf "$CHROOT/etc/resolv.conf" || true

cat > "$CHROOT/etc/motd" <<'EOF'
BadaOS GNU/Quantum 12.0 -- the real machine build

  * vim / emacs / sshd / xinetd / grub-install / update-grub preinstalled
  * apt uses the FULL Debian archive (60,000+ packages, Ubuntu-class):
        sudo apt update && sudo apt install <anything>
  * install to the real disk:  sudo badaos-install
    (default mode installs into the FREE SPACE of the disk -- existing
     partitions and OSes are kept and stay in the GRUB menu)
EOF

echo "==> [3/6] configure the BadaOS kiosk (autologin -> X -> fullscreen)"
echo badaos > "$CHROOT/etc/hostname"
cat > "$CHROOT/etc/issue" <<'EOF'
BadaOS GNU/Quantum 12.0 (live) \n \l
EOF

mkdir -p "$CHROOT/opt/badaos"
cp "$QVM/dist/bada-vm-pro.html" "$CHROOT/opt/badaos/bada-vm-pro.html"

chroot "$CHROOT" useradd -m -s /bin/bash bada || true
echo 'bada:badaos' | chroot "$CHROOT" chpasswd
echo 'root:badaos' | chroot "$CHROOT" chpasswd
echo 'bada ALL=(ALL) NOPASSWD: ALL' > "$CHROOT/etc/sudoers.d/badaos-live"

# autologin on tty1
mkdir -p "$CHROOT/etc/systemd/system/getty@tty1.service.d"
cat > "$CHROOT/etc/systemd/system/getty@tty1.service.d/autologin.conf" <<'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin bada --noclear %I $TERM
EOF

# start X on the autologin console (unless "textonly" is on the cmdline)
cat > "$CHROOT/home/bada/.bash_profile" <<'EOF'
if [ -z "$DISPLAY" ] && [ "$(tty)" = /dev/tty1 ] && ! grep -q textonly /proc/cmdline; then
  exec startx -- -nocursor >/tmp/xorg.log 2>&1
fi
echo
echo "BadaOS GNU/Quantum 12.0 (live console)"
echo "  startx            -- launch the BadaOS environment"
echo "  sudo badaos-install -- install BadaOS to a REAL disk (GRUB into the MBR/ESP)"
echo
EOF

cat > "$CHROOT/home/bada/.xinitrc" <<'EOF'
xset -dpms s off
openbox --sm-disable &
exec chromium --kiosk --no-first-run --disable-infobars --noerrdialogs \
  --disable-session-crashed-bubble --password-store=basic \
  "file:///opt/badaos/bada-vm-pro.html#autoboot"
EOF
chroot "$CHROOT" chown -R bada:bada /home/bada

# the real-disk installer + branding for the installed system's GRUB
install -m 0755 "$HERE/badaos-install" "$CHROOT/usr/local/sbin/badaos-install"

# BadaOS Commander: System Commander-style OS chooser in the installed GRUB
# (colored menu + a chainload entry per other bootable partition; runs on
# every update-grub next to os-prober)
install -m 0755 "$HERE/25_badaos_commander" "$CHROOT/etc/grub.d/25_badaos_commander"

# unattended VM install: kernel arg badaos.autoinstall=/dev/XXX (whole disk)
# or badaos.autoinstall-free=/dev/XXX (into the free space, keeping the
# existing partitions) runs the installer non-interactively at boot (used by
# the "Install to /dev/vda" GRUB entries -- vda only exists on virtio VMs,
# never on real hardware).
cat > "$CHROOT/etc/systemd/system/badaos-autoinstall.service" <<'EOF'
[Unit]
Description=BadaOS unattended real-disk install (VM)
ConditionKernelCommandLine=|badaos.autoinstall
ConditionKernelCommandLine=|badaos.autoinstall-free
After=basic.target systemd-udev-settle.service

[Service]
Type=oneshot
StandardOutput=journal+console
StandardError=journal+console
ExecStart=/bin/sh -c 'C=$(cat /proc/cmdline); DEV=$(echo "$C" | sed -n "s/.*badaos\.autoinstall-free=\([^ ]*\).*/\1/p"); if [ -n "$DEV" ]; then exec /usr/local/sbin/badaos-install --auto-free "$DEV"; fi; DEV=$(echo "$C" | sed -n "s/.*badaos\.autoinstall=\([^ ]*\).*/\1/p"); exec /usr/local/sbin/badaos-install --auto "$DEV"'

[Install]
WantedBy=multi-user.target
EOF
chroot "$CHROOT" systemctl enable badaos-autoinstall.service
sed -i 's/^GRUB_DISTRIBUTOR=.*/GRUB_DISTRIBUTOR="BadaOS GNU\/Quantum"/' \
    "$CHROOT/etc/default/grub" 2>/dev/null || \
    echo 'GRUB_DISTRIBUTOR="BadaOS GNU/Quantum"' >> "$CHROOT/etc/default/grub"
# free-space installs keep the machine's other OSes: os-prober puts them
# into the GRUB menu next to BadaOS on every update-grub
grep -q '^GRUB_DISABLE_OS_PROBER=' "$CHROOT/etc/default/grub" 2>/dev/null || \
    echo 'GRUB_DISABLE_OS_PROBER=false' >> "$CHROOT/etc/default/grub"

echo "==> [4/6] squashfs"
chroot "$CHROOT" apt-get clean
rm -rf "$CHROOT/var/lib/apt/lists"/* "$CHROOT/usr/sbin/policy-rc.d"
umount -lf "$CHROOT/dev/pts" "$CHROOT/dev" "$CHROOT/sys" "$CHROOT/proc" 2>/dev/null || true
trap - EXIT
cp "$CHROOT"/boot/vmlinuz-*   "$ISO/live/vmlinuz"
cp "$CHROOT"/boot/initrd.img-* "$ISO/live/initrd"
# /boot stays INSIDE the squashfs so badaos-install can copy a bootable
# system (kernel + initrd) onto the real disk.
mksquashfs "$CHROOT" "$ISO/live/filesystem.squashfs" \
    -comp xz -noappend -quiet

echo "==> [5/6] GRUB menu (this IS the boot menu the real PC shows)"
sed "s/@VOLID@/BADAOS/g" "$HERE/grub-live.cfg" > "$ISO/boot/grub/grub.cfg"

echo "==> [6/6] grub-mkrescue (hybrid BIOS+UEFI ISO)"
grub-mkrescue -o "$OUT" "$ISO" -- -volid BADAOS
xorriso -indev "$OUT" -report_el_torito plain | sed -n '1,8p'
ls -lh "$OUT"
echo "BadaOS live ISO built: $OUT"
echo "  * USB へ書き込み: Rufus / balenaEtcher / dd"
echo "  * PC を USB から起動 -> GRUB メニューに 'BadaOS GNU/Quantum 12.0'"
echo "  * 実ディスクへ本インストール: ライブ起動後 'sudo badaos-install'"
