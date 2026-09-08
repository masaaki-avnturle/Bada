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
    vim emacs-nox openssh-server curl wget less ca-certificates \
    bluez usbutils \
    mlterm screen tmux locales texlive texlive-lang-japanese \
    wmaker htop mc \
    xterm x11-apps x11-utils x11-xserver-utils \
    firefox-esr pcmanfm \
    udisks2 gvfs \
    network-manager
# xinetd is optional in newer Debian suites
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq xinetd || true
# the real w9wm (or its parent 9wm) as an alternative window manager --
# best effort, whichever the suite still ships
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq w9wm || \
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq 9wm || true
# AfterStep (NeXTSTEP style WM) -- best effort
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq afterstep || true
# Japanese input: fcitx-mozc + fcitx-configtool, falling back to fcitx5
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq fcitx-mozc fcitx-configtool || \
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq fcitx5-mozc fcitx5-config-qt || true
# common desktop applications -- best effort, one at a time so a renamed
# package never sinks the rest (calculator / text editor / image viewer /
# GNOME Files + the gvfs backends and pmount for USB sticks)
for app in galculator l3afpad gpicview nautilus gvfs-backends exfatprogs pmount; do
  chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$app" || true
done
# NAT / network settings GUI: NetworkManager's connection editor + tray applet
# (nm-connection-editor, nm-applet). Best effort so a rename never sinks the ISO.
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq network-manager-gnome || true

echo "==> Japanese locale (ja_JP.UTF-8)"
sed -i 's/^# *ja_JP.UTF-8 UTF-8/ja_JP.UTF-8 UTF-8/' "$CHROOT/etc/locale.gen" 2>/dev/null || true
grep -q '^ja_JP.UTF-8' "$CHROOT/etc/locale.gen" 2>/dev/null || echo 'ja_JP.UTF-8 UTF-8' >> "$CHROOT/etc/locale.gen"
grep -q '^en_US.UTF-8' "$CHROOT/etc/locale.gen" 2>/dev/null || echo 'en_US.UTF-8 UTF-8' >> "$CHROOT/etc/locale.gen"
chroot "$CHROOT" locale-gen
echo 'LANG=ja_JP.UTF-8' > "$CHROOT/etc/default/locale"

# AUTOMATIC internet: NetworkManager manages every wired/Wi-Fi NIC and
# auto-connects over DHCP at boot, so `apt`/firefox reach the FULL Debian
# archive (60,000+ packages) with no manual setup -- and it provides the
# NAT/connection SETTINGS GUI (nm-connection-editor) and tray applet
# (nm-applet). NetworkManager, not systemd-networkd, owns networking here;
# systemd-resolved still does DNS (NM feeds it), with a public fallback.
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq systemd-resolved || true
chroot "$CHROOT" systemctl enable NetworkManager systemd-resolved ssh 2>/dev/null || \
chroot "$CHROOT" systemctl enable NetworkManager ssh || true
# hand all interfaces to NetworkManager and route its DNS through resolved
mkdir -p "$CHROOT/etc/NetworkManager/conf.d"
cat > "$CHROOT/etc/NetworkManager/conf.d/10-badaos.conf" <<'EOF'
[main]
dns=systemd-resolved
# manage every device (nothing is left "unmanaged")
[keyfile]
unmanaged-devices=none
[device]
wifi.scan-rand-mac-address=no
EOF
# an explicit auto-connect DHCP profile that matches ANY ethernet NIC, so a
# fresh machine is online the moment it boots (belt-and-braces on top of
# NetworkManager's built-in wired auto-connect)
mkdir -p "$CHROOT/etc/NetworkManager/system-connections"
cat > "$CHROOT/etc/NetworkManager/system-connections/badaos-wired.nmconnection" <<'EOF'
[connection]
id=BadaOS Wired (auto)
type=ethernet
autoconnect=true
autoconnect-priority=10

[ipv4]
method=auto

[ipv6]
method=auto
EOF
chmod 600 "$CHROOT/etc/NetworkManager/system-connections/badaos-wired.nmconnection"
# a bare systemd-networkd would fight NetworkManager for the same NICs -- make
# sure only NetworkManager is driving them
chroot "$CHROOT" systemctl disable systemd-networkd 2>/dev/null || true
chroot "$CHROOT" systemctl mask systemd-networkd 2>/dev/null || true
rm -f "$CHROOT/etc/systemd/network/20-dhcp.network" 2>/dev/null || true
# fallback DNS so resolution works even when the DHCP server hands out none
mkdir -p "$CHROOT/etc/systemd/resolved.conf.d"
cat > "$CHROOT/etc/systemd/resolved.conf.d/10-badaos-fallback.conf" <<'EOF'
[Resolve]
FallbackDNS=9.9.9.9 1.1.1.1 8.8.8.8
EOF
# Bluetooth: bluetoothd starts when an adapter is present (bluetoothctl ready)
chroot "$CHROOT" systemctl enable bluetooth 2>/dev/null || true
rm -f "$CHROOT/etc/resolv.conf"
if [ -e "$CHROOT/lib/systemd/system/systemd-resolved.service" ] || \
   [ -e "$CHROOT/usr/lib/systemd/system/systemd-resolved.service" ]; then
  ln -sf /run/systemd/resolve/stub-resolv.conf "$CHROOT/etc/resolv.conf"
else
  printf 'nameserver 9.9.9.9\nnameserver 1.1.1.1\n' > "$CHROOT/etc/resolv.conf"
fi

cat > "$CHROOT/etc/motd" <<'EOF'
BadaOS GNU/Quantum 12.0 -- the real machine build

  * vim / emacs / sshd / xinetd / grub-install / update-grub preinstalled
  * bluetoothctl (bluez) + lsusb (usbutils) preinstalled; DHCP NAT networking
  * Japanese ready: ja_JP.UTF-8 / mlterm / fcitx-mozc + fcitx-configtool
    (Ctrl+Space), pLaTeX (texlive + texlive-lang-japanese; the FULL TeX
    Live is one `sudo apt install texlive-full` away), screen / tmux
  * window managers: w9wm / afterstep / wmaker / openbox. An INSTALLED
    BadaOS boots straight into the WM DESKTOP (w9wm + mlterm, no kiosk):
    drive Ubuntu-style apps from mlterm (apt, htop, mc, vim, tmux ...),
    `badavm &` opens the BadaVM Pro app as a window. Pick the WM with
    badaos.wm=... / badaos.session=kiosk restores the fullscreen app
  * desktop apps preinstalled: xterm + x11-apps (xeyes / xclock / xcalc),
    firefox-esr (web), pcmanfm + nautilus (files), galculator / l3afpad /
    gpicview
  * AUTOMATIC internet (NAT): NetworkManager auto-connects DHCP on every
    NIC at boot; DNS via systemd-resolved (9.9.9.9/1.1.1.1/8.8.8.8 fallback).
    Settings GUI: `badaos-network` (nm-connection-editor) or the nm-applet
    tray icon; console: nmtui / nmcli
  * USB sticks: plug in and open them from pcmanfm / nautilus (udisks2 +
    gvfs auto-mount), or `udisksctl mount -b /dev/sdb1` / `pmount sdb1`
  * apt uses the FULL Debian archive (60,000+ packages, Ubuntu-class):
        sudo apt update && sudo apt install <anything>   (nautilus included)
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

# Force a SOFTWARE mouse cursor. In a VM (QEMU/VMware/VirtualBox) the
# emulated GPU often does not render the X server's HARDWARE cursor, so the
# pointer is invisible even though the mouse works. SWcursor makes X draw
# the cursor into the framebuffer itself, so it always shows. Covers the
# common VM/basic video drivers; harmless on real hardware.
mkdir -p "$CHROOT/etc/X11/xorg.conf.d"
cat > "$CHROOT/etc/X11/xorg.conf.d/20-badaos-swcursor.conf" <<'EOF'
# BadaOS: always draw a visible mouse cursor (software cursor)
Section "Device"
    Identifier "BadaOS modesetting"
    Driver     "modesetting"
    Option     "SWcursor" "true"
EndSection
Section "Device"
    Identifier "BadaOS QXL"
    Driver     "qxl"
    Option     "SWcursor" "true"
EndSection
Section "Device"
    Identifier "BadaOS virtio"
    Driver     "virtio_gpu"
    Option     "SWcursor" "true"
EndSection
Section "Device"
    Identifier "BadaOS VMware"
    Driver     "vmware"
    Option     "SWcursor" "true"
EndSection
Section "Device"
    Identifier "BadaOS VESA"
    Driver     "vesa"
    Option     "SWcursor" "true"
EndSection
Section "Device"
    Identifier "BadaOS fbdev"
    Driver     "fbdev"
    Option     "SWcursor" "true"
EndSection
EOF

# start X on the autologin console (unless "textonly" is on the cmdline)
cat > "$CHROOT/home/bada/.bash_profile" <<'EOF'
if [ -z "$DISPLAY" ] && [ "$(tty)" = /dev/tty1 ] && ! grep -q textonly /proc/cmdline; then
  # NB: no -nocursor -- that flag disables the X pointer server-wide, which
  # is why the mouse cursor used to be invisible on the WM desktop.
  exec startx >/tmp/xorg.log 2>&1
fi
echo
echo "BadaOS GNU/Quantum 12.0 (live console)"
echo "  startx            -- launch the BadaOS environment"
echo "  sudo badaos-install -- install BadaOS to a REAL disk (GRUB into the MBR/ESP)"
echo "  (GUI install: reboot and pick 'Install BadaOS' in the GRUB menu)"
echo
EOF

cat > "$CHROOT/home/bada/.xinitrc" <<'EOF'
xset -dpms s off
# make the mouse cursor VISIBLE: modern Xorg keeps the root cursor hidden
# until some client sets one, and a bare WM session never does -- so set
# the classic left_ptr on the root window ourselves (x11-xserver-utils)
if command -v xsetroot >/dev/null 2>&1; then
  xsetroot -cursor_name left_ptr
  xsetroot -solid '#30363d'
fi
# Japanese environment: locale + fcitx-mozc input method (fcitx5 fallback)
export LANG=ja_JP.UTF-8
export GTK_IM_MODULE=fcitx QT_IM_MODULE=fcitx XMODIFIERS=@im=fcitx
if command -v fcitx >/dev/null 2>&1; then fcitx -d >/dev/null 2>&1
elif command -v fcitx5 >/dev/null 2>&1; then fcitx5 -d >/dev/null 2>&1
fi

# session model:
#   INSTALLED BadaOS -> a PLAIN WM DESKTOP: just the window manager (w9wm by
#     default; afterstep / wmaker / openbox selectable) with mlterm on it --
#     no kiosk. Ubuntu-style applications are driven from mlterm (apt, htop,
#     mc, vim, tmux, ...); `badavm &` opens the BadaVM Pro app as a normal
#     window when wanted.
#   LIVE boot -> the fullscreen BadaOS kiosk (the try-it/installer medium).
#   Overrides: badaos.session=desktop|kiosk, badaos.wm=w9wm|afterstep|wmaker|
#   openbox on the kernel cmdline; or `WM=wmaker startx` from a console.
pickwm() {
  case "$1" in
    w9wm)
      if command -v w9wm >/dev/null 2>&1; then echo w9wm; return; fi
      if command -v 9wm  >/dev/null 2>&1; then echo 9wm; return; fi ;;
    afterstep)
      if command -v afterstep >/dev/null 2>&1; then echo afterstep; return; fi ;;
    wmaker)
      if command -v wmaker >/dev/null 2>&1; then echo wmaker; return; fi ;;
  esac
  echo openbox
}
WMSEL=""
SESSION=""
for a in $(cat /proc/cmdline); do
  case "$a" in
    badaos.wm=*) WMSEL="${a#badaos.wm=}";;
    badaos.session=*) SESSION="${a#badaos.session=}";;
  esac
done
[ -n "${WM:-}" ] && { WMSEL="$WM"; SESSION=desktop; }
if [ -z "$SESSION" ]; then
  if grep -q boot=live /proc/cmdline; then SESSION=kiosk; else SESSION=desktop; fi
fi
if grep -q badaos.gui-installer /proc/cmdline; then SESSION=kiosk; fi

if [ "$SESSION" = "desktop" ]; then
  # the OS boots into the window manager alone: w9wm / afterstep / wmaker,
  # with mlterm (Japanese terminal) as the workbench for Ubuntu-style apps
  WMBIN="$(pickwm "${WMSEL:-w9wm}")"
  # NetworkManager tray applet: shows the connection and opens the settings
  # GUI (harmless if the WM has no system tray -- the editor still runs from
  # `badaos-network`)
  command -v nm-applet >/dev/null 2>&1 && nm-applet >/dev/null 2>&1 &
  if command -v mlterm >/dev/null 2>&1; then mlterm &
  elif command -v xterm >/dev/null 2>&1; then xterm & fi
  if [ "$WMBIN" = openbox ]; then exec openbox --sm-disable; fi
  sleep 1
  exec "$WMBIN"
fi

# kiosk session (live medium): the fullscreen BadaOS environment, or the
# Ubuntu-style GUI installer when the "Install BadaOS" GRUB entry was picked
WMBIN="$(pickwm "${WMSEL:-openbox}")"
URL="file:///opt/badaos/bada-vm-pro.html#autoboot"
if grep -q badaos.gui-installer /proc/cmdline; then
  URL="http://127.0.0.1:7788/"
  for i in $(seq 1 30); do
    if timeout 1 bash -c "exec 3<>/dev/tcp/127.0.0.1/7788" 2>/dev/null; then break; fi
    sleep 1
  done
fi
if [ "$WMBIN" = openbox ]; then
  openbox --sm-disable &
  exec chromium --kiosk --no-first-run --disable-infobars --noerrdialogs \
    --disable-session-crashed-bubble --password-store=basic "$URL"
fi
# non-openbox kiosk: map the kiosk window FIRST, then start the WM -- a
# window manager adopts already-mapped windows in place, so the kiosk never
# waits for an interactive 9wm-style sweep placement
chromium --kiosk --no-first-run --disable-infobars --noerrdialogs \
  --disable-session-crashed-bubble --password-store=basic "$URL" &
sleep 8
exec "$WMBIN"
EOF

# `badavm` opens the BadaVM Pro app as a normal window inside the WM desktop
cat > "$CHROOT/usr/local/bin/badavm" <<'EOF'
#!/bin/sh
exec chromium --app=file:///opt/badaos/bada-vm-pro.html#autoboot \
  --no-first-run --password-store=basic "$@"
EOF
chmod 0755 "$CHROOT/usr/local/bin/badavm"

# `badaos-network` opens the NAT / network SETTINGS GUI (nm-connection-editor);
# falls back to the nmtui text UI in a terminal if the GTK editor is absent
cat > "$CHROOT/usr/local/bin/badaos-network" <<'EOF'
#!/bin/sh
# BadaOS network / NAT settings
if command -v nm-connection-editor >/dev/null 2>&1; then
  exec nm-connection-editor "$@"
elif command -v nmtui >/dev/null 2>&1; then
  exec "${TERMINAL:-mlterm}" -e nmtui
else
  echo "NetworkManager tools not found." >&2; exit 1
fi
EOF
chmod 0755 "$CHROOT/usr/local/bin/badaos-network"
chroot "$CHROOT" chown -R bada:bada /home/bada

# the real-disk installer + branding for the installed system's GRUB
install -m 0755 "$HERE/badaos-install" "$CHROOT/usr/local/sbin/badaos-install"

# the Ubuntu-style GUI installer (wizard page + root backend on localhost)
mkdir -p "$CHROOT/usr/local/lib/badaos-installer"
install -m 0644 "$HERE/installer/index.html" "$CHROOT/usr/local/lib/badaos-installer/index.html"
install -m 0755 "$HERE/installer/badaos-installer-httpd.py" \
    "$CHROOT/usr/local/lib/badaos-installer/badaos-installer-httpd.py"
cat > "$CHROOT/etc/systemd/system/badaos-installer.service" <<'EOF'
[Unit]
Description=BadaOS GUI installer backend (Ubuntu-style wizard on localhost:7788)
ConditionKernelCommandLine=boot=live
After=basic.target

[Service]
ExecStart=/usr/bin/python3 /usr/local/lib/badaos-installer/badaos-installer-httpd.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
chroot "$CHROOT" systemctl enable badaos-installer.service

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
