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
    git build-essential make pkg-config \
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
for app in galculator l3afpad gpicview nautilus gvfs-backends exfatprogs pmount apache2; do
  chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$app" || true
done
# NAT / network settings GUI: NetworkManager's connection editor + tray applet
# (nm-connection-editor, nm-applet). Best effort so a rename never sinks the ISO.
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq network-manager-gnome || true

# EXTERNAL router / USB Wi-Fi / USB LTE dongles: when one is plugged in it is
# auto-recognized (usb-modeswitch flips CD-mode dongles to their modem/NIC
# interface; ModemManager drives LTE/3G; wpasupplicant + iw drive Wi-Fi), and
# NetworkManager offers it as a connection you unlock with the router password.
# firmware for the common USB Wi-Fi/LTE chipsets is baked in (non-free-firmware).
for p in wpasupplicant iw wireless-tools rfkill usb-modeswitch modemmanager \
         firmware-realtek firmware-atheros firmware-iwlwifi firmware-brcm80211 \
         firmware-misc-nonfree; do
  chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$p" || true
done
chroot "$CHROOT" systemctl enable ModemManager 2>/dev/null || true

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
# (nm-applet). NetworkManager, not systemd-networkd, owns networking here.
#
# DNS is handled by NetworkManager ITSELF (dns=default: NM writes a real
# /etc/resolv.conf from the DHCP-provided servers). We deliberately do NOT
# route DNS through systemd-resolved + a stub symlink: on real hardware that
# chain is the #1 reason "the internet doesn't work" -- routing comes up but
# name resolution silently fails when resolved is slow/not-ready. Public
# resolvers are appended to every profile as a fallback so names resolve even
# when the DHCP server hands out no DNS at all.
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq isc-dhcp-client || true
chroot "$CHROOT" systemctl enable NetworkManager ssh 2>/dev/null || \
chroot "$CHROOT" systemctl enable NetworkManager || true
# systemd-resolved, if present, must NOT own resolv.conf here (we use NM's own
# resolver). Disable it so there is exactly one DNS path.
chroot "$CHROOT" systemctl disable systemd-resolved 2>/dev/null || true
# make NetworkManager manage ALL devices, including any listed in
# /etc/network/interfaces (ifupdown managed=true), and write resolv.conf itself
mkdir -p "$CHROOT/etc/NetworkManager/conf.d"
cat > "$CHROOT/etc/NetworkManager/conf.d/10-badaos.conf" <<'EOF'
[main]
# NetworkManager writes /etc/resolv.conf directly from DHCP (no resolved stub)
dns=default
plugins=keyfile,ifupdown
# auto-create a DHCP connection for EVERY wired/USB device with no config, so
# a USB router / Ethernet / tethering adapter goes online the instant it is
# plugged in -- no command, no password (empty = auto-default for all).
no-auto-default=

[ifupdown]
# even NICs mentioned in /etc/network/interfaces are handed to NetworkManager
managed=true

[keyfile]
unmanaged-devices=none

[device]
wifi.scan-rand-mac-address=no
EOF
# /etc/network/interfaces must define ONLY loopback, otherwise ifupdown claims
# the ethernet NIC and NetworkManager marks it unmanaged -> no auto internet.
mkdir -p "$CHROOT/etc/network"
cat > "$CHROOT/etc/network/interfaces" <<'EOF'
# BadaOS: NetworkManager manages all real interfaces. Only loopback here.
source /etc/network/interfaces.d/*
auto lo
iface lo inet loopback
EOF
mkdir -p "$CHROOT/etc/network/interfaces.d"
# an explicit auto-connect DHCP profile that matches ANY ethernet NIC, so a
# fresh machine is online the moment it boots (belt-and-braces on top of
# NetworkManager's built-in wired auto-connect). Public DNS is appended as a
# fallback (ignore-auto-dns=false => DHCP DNS first, then these).
mkdir -p "$CHROOT/etc/NetworkManager/system-connections"
cat > "$CHROOT/etc/NetworkManager/system-connections/badaos-wired.nmconnection" <<'EOF'
[connection]
id=BadaOS Wired (auto)
type=ethernet
autoconnect=true
autoconnect-priority=10
autoconnect-retries=0

[ipv4]
method=auto
dns=9.9.9.9;1.1.1.1;8.8.8.8;
ignore-auto-dns=false
may-fail=true

[ipv6]
method=auto
may-fail=true
EOF
chmod 600 "$CHROOT/etc/NetworkManager/system-connections/badaos-wired.nmconnection"

# HOT-PLUG AUTO-CONNECT: the moment a USB router / Ethernet / tethering / LTE
# adapter is inserted, bring its interface up and let NetworkManager DHCP it
# automatically (usb-modeswitch flips CD-mode dongles first). No command,
# no password -- the machine is simply online over the new uplink (NAT).
cat > "$CHROOT/usr/local/sbin/badaos-usbnet-up" <<'EOF'
#!/bin/sh
# arg1 = kernel iface name (usb0 / enx.. / eth.. / wwan0)
IF="$1"
[ -n "$IF" ] || exit 0
command -v usb_modeswitch >/dev/null 2>&1 && usb_modeswitch -W >/dev/null 2>&1 || true
nmcli device set "$IF" managed yes >/dev/null 2>&1 || true
# a wired/tethering NIC just needs DHCP; NetworkManager auto-default handles it
nmcli device connect "$IF" >/dev/null 2>&1 || true
EOF
chmod 0755 "$CHROOT/usr/local/sbin/badaos-usbnet-up"
mkdir -p "$CHROOT/etc/udev/rules.d"
cat > "$CHROOT/etc/udev/rules.d/70-badaos-usbnet.rules" <<'EOF'
# BadaOS: auto-bring-up + DHCP any newly plugged USB network adapter
ACTION=="add", SUBSYSTEM=="net", SUBSYSTEMS=="usb", \
  RUN+="/usr/local/sbin/badaos-usbnet-up %k"
EOF

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
# clock sync: systemd-timesyncd keeps the BadaOS / Ubuntu / Windows clocks in
# step over NTP (through the NAT). `timedatectl` shows and drives it;
# `timedatectl set-local-rtc 1` keeps the shared hardware RTC in LOCAL time so
# a Windows dual boot reads the same wall-clock time.
chroot "$CHROOT" env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq systemd-timesyncd || true
chroot "$CHROOT" systemctl enable systemd-timesyncd 2>/dev/null || true
mkdir -p "$CHROOT/etc/systemd/timesyncd.conf.d"
cat > "$CHROOT/etc/systemd/timesyncd.conf.d/10-badaos.conf" <<'EOF'
[Time]
NTP=ntp.nict.jp pool.ntp.org
FallbackNTP=time.cloudflare.com time.windows.com
EOF
# Bluetooth: bluetoothd starts when an adapter is present (bluetoothctl ready)
chroot "$CHROOT" systemctl enable bluetooth 2>/dev/null || true
# resolv.conf: a PLAIN file (NOT a symlink to the resolved stub). NetworkManager
# (dns=default) rewrites it from DHCP once online; until then these public
# resolvers make name resolution work, so DNS never blocks the first boot.
rm -f "$CHROOT/etc/resolv.conf"
printf '# BadaOS: NetworkManager rewrites this from DHCP. Fallback resolvers:\nnameserver 9.9.9.9\nnameserver 1.1.1.1\nnameserver 8.8.8.8\n' > "$CHROOT/etc/resolv.conf"

# ---------------------------------------------------------------------------
# Boot-time network self-heal: a oneshot that, after NetworkManager is up,
# forces networking on, connects the first available wired/USB NIC over DHCP,
# and -- if DNS still looks broken -- drops the public resolvers into
# /etc/resolv.conf. This guarantees the machine reaches the internet even if
# the auto-connect profile did not fire (odd NIC name, late-probing driver).
cat > "$CHROOT/usr/local/sbin/badaos-net-up" <<'EOF'
#!/bin/sh
# BadaOS network self-heal (run at boot by badaos-net.service)
nmcli networking on >/dev/null 2>&1 || true
# give slow NIC drivers a moment to register
i=0; while [ "$i" -lt 10 ]; do
  nmcli -t -f DEVICE,TYPE,STATE device 2>/dev/null | grep -qE ':(ethernet|wifi):' && break
  i=$((i+1)); sleep 1
done
# connect every managed wired/tethering device that is not already up
nmcli -t -f DEVICE,TYPE,STATE device 2>/dev/null | while IFS=: read -r dev typ state; do
  [ -n "$dev" ] || continue
  case "$typ" in
    ethernet|wifi)
      case "$state" in
        connected) : ;;
        *) nmcli device connect "$dev" >/dev/null 2>&1 || true ;;
      esac ;;
  esac
done
# DNS backstop: if we cannot resolve a name, ensure public resolvers are present
if command -v getent >/dev/null 2>&1 && ! getent hosts deb.debian.org >/dev/null 2>&1; then
  if ! grep -q '^nameserver' /etc/resolv.conf 2>/dev/null; then
    printf 'nameserver 9.9.9.9\nnameserver 1.1.1.1\nnameserver 8.8.8.8\n' > /etc/resolv.conf 2>/dev/null || true
  fi
fi
exit 0
EOF
chmod 0755 "$CHROOT/usr/local/sbin/badaos-net-up"
mkdir -p "$CHROOT/etc/systemd/system"
cat > "$CHROOT/etc/systemd/system/badaos-net.service" <<'EOF'
[Unit]
Description=BadaOS network self-heal (auto DHCP + DNS backstop)
Wants=NetworkManager.service
After=NetworkManager.service
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/badaos-net-up
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
EOF
chroot "$CHROOT" systemctl enable badaos-net.service 2>/dev/null || \
  ln -sf /etc/systemd/system/badaos-net.service \
    "$CHROOT/etc/systemd/system/multi-user.target.wants/badaos-net.service" 2>/dev/null || true

# ---------------------------------------------------------------------------
# `badaos-net-fix` -- the user-facing one-command repair/diagnose tool. If the
# internet is ever down, run it: it restarts NetworkManager, brings the NICs up
# on DHCP, fixes DNS, and prints exactly which step (link / IP / DNS / route)
# failed so the problem is obvious.
cat > "$CHROOT/usr/local/bin/badaos-net-fix" <<'EOF'
#!/bin/sh
# BadaOS internet repair + diagnosis
[ "$(id -u)" = 0 ] && S="" || S="sudo"
echo "== BadaOS network fix =="
$S systemctl unmask systemd-networkd 2>/dev/null; $S systemctl mask systemd-networkd 2>/dev/null || true
echo "-> restarting NetworkManager ..."
$S systemctl restart NetworkManager 2>/dev/null || $S service network-manager restart 2>/dev/null || true
nmcli networking on 2>/dev/null || true
sleep 2
echo "-> devices:"; nmcli -f DEVICE,TYPE,STATE device status 2>/dev/null || true
# bring up every wired/wifi device
nmcli -t -f DEVICE,TYPE device 2>/dev/null | while IFS=: read -r dev typ; do
  case "$typ" in ethernet|wifi) nmcli device connect "$dev" 2>/dev/null || true ;; esac
done
sleep 3
IP=$(ip -4 -o addr show scope global 2>/dev/null | awk '{print $4}' | head -n1)
if [ -z "$IP" ]; then
  echo "!! no IPv4 address yet -- check the cable / Wi-Fi (badaos-router connect \"SSID\")."
else
  echo "-> address: $IP"
fi
# DNS backstop
if ! getent hosts deb.debian.org >/dev/null 2>&1; then
  echo "-> DNS was failing; writing public resolvers to /etc/resolv.conf"
  printf 'nameserver 9.9.9.9\nnameserver 1.1.1.1\nnameserver 8.8.8.8\n' | $S tee /etc/resolv.conf >/dev/null 2>&1 || true
fi
# verdict
if ping -c1 -W3 1.1.1.1 >/dev/null 2>&1; then
  if getent hosts deb.debian.org >/dev/null 2>&1 && ping -c1 -W3 deb.debian.org >/dev/null 2>&1; then
    echo "OK: internet reachable (routing + DNS). Try: sudo apt update"
  else
    echo "Routing OK but DNS still failing -- resolv.conf: "; cat /etc/resolv.conf 2>/dev/null
  fi
else
  echo "No route to the internet yet. If this is Wi-Fi, run: badaos-router connect \"<SSID>\""
  echo "For a wired/USB router, replug it (auto-DHCP) or check the upstream router."
fi
EOF
chmod 0755 "$CHROOT/usr/local/bin/badaos-net-fix"

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
  * AUTOMATIC internet (NAT): NetworkManager auto-connects DHCP on every NIC
    at boot and writes /etc/resolv.conf itself (public 9.9.9.9/1.1.1.1/8.8.8.8
    fallback baked in), and a boot self-heal (badaos-net.service) reconnects
    any NIC that did not come up. IF THE INTERNET IS EVER DOWN, run:
        badaos-net-fix          # restart NM, DHCP the NICs, fix DNS, diagnose
    Settings GUI: `badaos-network` (nm-connection-editor) or the nm-applet
    tray icon; console: nmtui / nmcli
  * EXTERNAL router / USB Ethernet / tethering / LTE adapter: JUST PLUG IT
    into a USB port -- it is auto-recognized and NetworkManager DHCPs it
    automatically, so you are online over the new uplink (NAT) with no
    command and no password. (Wi-Fi APs that need a key: run
    `badaos-router connect "SSID"` and enter the passcode when prompted --
    it validates the 8-63 char key, retries, and verifies link+DNS+ping
    before saying Connected; scan/status: badaos-router)
  * clock sync: `timedatectl` -- systemd-timesyncd keeps BadaOS / Ubuntu /
    Windows in step over NTP (via the NAT). `timedatectl set-local-rtc 1`
    keeps the shared RTC in local time for a Windows dual boot
  * USB sticks: plug in and open them from pcmanfm / nautilus (udisks2 +
    gvfs auto-mount), or `udisksctl mount -b /dev/sdb1` / `pmount sdb1`
  * developer tools preinstalled: git, curl, a C/C++ compiler (gcc/g++/make,
    build-essential) -- the Debian equivalent of Xcode Command Line Tools.
    screen / tmux / texlive (+ Japanese) are baked in too.
  * big optionals over the NAT (too large to bake under the 2 GB image):
        badaos-extras clang          # clang / llvm / lld
        badaos-extras texlive-full   # the full TeX Live
        badaos-extras dev | media | all
    `xcode-select --install` also adds clang/llvm/cmake; `brew` installs
    Homebrew (Linuxbrew) on first run over the internet
  * BadaApache -- the Apache HTTP Server written in Bada -- serves the zone://
    ultra network: inside BadaVM Pro run `apachectl start` to publish the
    DocumentRoot onto zone://url.or.jp, then `zone zone://url.or.jp/apache`.
    The real apache2 is installed too (best effort); source in /opt/badaos
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

# `badaos-router` -- plug an external router / USB Wi-Fi / USB LTE dongle in,
# then connect to the internet by entering the ROUTER PASSWORD, in one step.
# It auto-detects the newly plugged adapter (NetworkManager/ModemManager),
# scans, and joins with the password you give.
cat > "$CHROOT/usr/local/bin/badaos-router" <<'EOF'
#!/bin/sh
# BadaOS external-router / Wi-Fi connect helper (wraps nmcli)
set -e
if ! command -v nmcli >/dev/null 2>&1; then
  echo "NetworkManager (nmcli) not found." >&2; exit 1
fi
# make sure a freshly plugged USB dongle is switched and radios are on
command -v usb_modeswitch >/dev/null 2>&1 && sudo usb_modeswitch -W >/dev/null 2>&1 || true
sudo rfkill unblock all 2>/dev/null || true
nmcli radio wifi on 2>/dev/null || true

case "${1:-}" in
  ""|list|scan)
    echo "Detected network adapters (external routers / USB Wi-Fi / LTE):"
    nmcli -f DEVICE,TYPE,STATE device status || true
    echo
    echo "Wi-Fi / router networks in range:"
    nmcli device wifi rescan 2>/dev/null || true
    nmcli -f SSID,SIGNAL,SECURITY device wifi list || true
    echo
    echo "Connect by entering the router passcode:  badaos-router connect \"<SSID>\" [passcode]"
    ;;
  connect|join|reconnect)
    SSID="${2:?usage: badaos-router connect \"<SSID>\" [passcode]}"
    PW="${3:-}"
    # If no passcode was given on the command line, prompt for it (hidden).
    if [ -z "$PW" ]; then
      printf 'Enter the passcode for "%s" (as printed on the router): ' "$SSID" >&2
      stty -echo 2>/dev/null || true
      read -r PW || true
      stty echo 2>/dev/null || true
      echo >&2
    fi
    # WPA/WPA2/WPA3-PSK passcodes are 8-63 chars: the usual reason a connect
    # "fails" is a mistyped/too-short key, so check it before we even try.
    LEN=$(printf %s "$PW" | wc -c)
    if [ "$LEN" -lt 8 ] || [ "$LEN" -gt 63 ]; then
      echo "badaos-router: passcode is $LEN characters -- a Wi-Fi passcode must be 8-63." >&2
      echo "  Re-enter it exactly as printed on the router (KEY / PASSWORD). Not connected." >&2
      exit 1
    fi
    # Reliable connect: retry the association a few times so a momentary
    # handshake timeout or slow DHCP does not leave you disconnected.
    OK=0
    i=1
    while [ "$i" -le 3 ]; do
      echo "Joining \"$SSID\" with the passcode (attempt $i/3) ..."
      if nmcli device wifi connect "$SSID" password "$PW"; then OK=1; break; fi
      echo "  attempt $i failed; rescanning and retrying ..." >&2
      nmcli device wifi rescan 2>/dev/null || true
      sleep 2
      i=$((i+1))
    done
    if [ "$OK" != 1 ]; then
      echo "Could not join \"$SSID\" -- the passcode was rejected or the AP is out of range." >&2
      echo "  Double-check the passcode and signal, then re-run badaos-router connect." >&2
      exit 1
    fi
    # Verify the connection is really up: carrier, DNS, then a ping.
    echo "Verifying the connection ..."
    for t in 1 2 3 4 5; do
      if ping -c1 -W3 deb.debian.org >/dev/null 2>&1; then
        echo "  link + DNS + ping OK -- internet reachable via \"$SSID\". Connected."
        echo "  NetworkManager saved the profile (autoconnect on); it reconnects next boot."
        exit 0
      fi
      sleep 2
    done
    echo "  Associated with \"$SSID\" but no internet route yet." >&2
    echo "  DHCP/DNS may still be settling -- check the router, then retry." >&2
    exit 1
    ;;
  *)
    echo "usage: badaos-router [list] | connect \"<SSID>\" [passcode]" ;;
esac
EOF
chmod 0755 "$CHROOT/usr/local/bin/badaos-router"

# ------------------------------------------------------------------------
# developer toolchain: git + curl + a C/C++ compiler (build-essential) are
# baked in -- that is the Debian equivalent of the Xcode Command Line Tools.
# `brew` (Homebrew / Linuxbrew) and `xcode-select` are provided as launchers
# so the familiar macOS-style commands work here too.
# ------------------------------------------------------------------------
# `brew`: on first use, install Homebrew on Linux over the NAT (it must NOT
# run as root and lives in /home/linuxbrew/.linuxbrew); afterwards exec the
# real brew. Needs the internet the first time (NetworkManager provides it).
cat > "$CHROOT/usr/local/bin/brew" <<'EOF'
#!/bin/sh
# BadaOS Homebrew (Linuxbrew) launcher
BREW=/home/linuxbrew/.linuxbrew/bin/brew
[ -x "$BREW" ] || { for h in "$HOME/.linuxbrew/bin/brew" /home/linuxbrew/.linuxbrew/bin/brew; do [ -x "$h" ] && BREW="$h" && break; done; }
if [ -x "$BREW" ]; then exec "$BREW" "$@"; fi
if [ "$(id -u)" = 0 ]; then
  echo "Homebrew must not be run as root. Run 'brew' as the 'bada' user." >&2
  exit 1
fi
echo "Homebrew is not installed yet -- installing it now (needs the internet)..."
export NONINTERACTIVE=1
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || {
  echo "Homebrew install failed (offline?). Connect to the internet and retry 'brew'." >&2
  exit 1
}
[ -x "$BREW" ] && exec "$BREW" "$@"
echo "Homebrew installed. Open a new shell (or: eval \"\$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)\")." >&2
EOF
chmod 0755 "$CHROOT/usr/local/bin/brew"

# `xcode-select` / `xcodebuild`: Xcode itself is macOS-only, but map the
# familiar Command Line Tools commands to the Debian developer toolchain.
cat > "$CHROOT/usr/local/bin/xcode-select" <<'EOF'
#!/bin/sh
# BadaOS shim: the Xcode Command Line Tools == git + build-essential + clang
case "$1" in
  -p|--print-path) echo "/usr" ;;
  --install)
    echo "Installing the developer command line tools (git + compilers)..."
    if [ "$(id -u)" = 0 ]; then S=""; else S="sudo"; fi
    $S apt-get update -qq
    $S env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
        git build-essential clang llvm make cmake pkg-config || {
        echo "install failed (offline?). Connect to the internet and retry." >&2; exit 1; }
    echo "Done. git / gcc / g++ / clang / make / cmake are ready." ;;
  -v|--version) echo "xcode-select version 2409 (BadaOS shim -> Debian toolchain)" ;;
  *) echo "usage: xcode-select [-p|--print-path] [--install] [--version]"
     echo "  (BadaOS: the CLT map to git + build-essential + clang on Debian)" ;;
esac
EOF
chmod 0755 "$CHROOT/usr/local/bin/xcode-select"
cat > "$CHROOT/usr/local/bin/xcodebuild" <<'EOF'
#!/bin/sh
echo "xcodebuild: Xcode itself is macOS-only. On BadaOS use the installed"
echo "toolchain directly: make / cmake / gcc / g++ / clang (git + curl too),"
echo "or 'xcode-select --install' to add clang/llvm. Homebrew: 'brew'."
EOF
chmod 0755 "$CHROOT/usr/local/bin/xcodebuild"

# BadaApache: the Apache HTTP Server written in Bada, which publishes its
# DocumentRoot onto the zone:// ultra network at zone://url.or.jp. Its Bada
# source ships under /opt/badaos; `badapache` runs it inside BadaVM Pro (the
# Bada runtime), and also drives the real apache2 if it is installed.
mkdir -p "$CHROOT/opt/badaos"
install -m 0644 "$QVM/bada/badapache.bada" "$CHROOT/opt/badaos/badapache.bada" 2>/dev/null || \
  cp "$QVM/bada/badapache.bada" "$CHROOT/opt/badaos/badapache.bada" 2>/dev/null || true
cat > "$CHROOT/usr/local/bin/badapache" <<'EOF'
#!/bin/sh
# BadaApache -- Apache in the Bada language, bound to zone://url.or.jp.
# The Bada implementation lives in BadaVM Pro; inside it run:
#     apachectl start        # publishes DocumentRoot onto zone://url.or.jp
#     zone zone://url.or.jp/apache
echo "BadaApache 2.4.58 (Quantum/Bada) -- Apache that serves the zone:// ultra network."
echo "Bada source: /opt/badaos/badapache.bada"
echo "Run it inside BadaVM Pro (badavm):  apachectl start  ->  zone zone://url.or.jp/apache"
if command -v apache2ctl >/dev/null 2>&1; then
  echo
  echo "The real apache2 is also installed here; controlling it now:"
  exec sudo apache2ctl "${@:-status}"
fi
EOF
chmod 0755 "$CHROOT/usr/local/bin/badapache"

# `badaos-extras` -- install the HEAVY optional packages over the NAT with one
# command. screen/tmux/texlive and a C/C++ compiler ship on the ISO already;
# clang, the FULL TeX Live, and other big bundles are too large to bake under
# the 2 GB image limit, so they are fetched from the Debian archive on demand.
cat > "$CHROOT/usr/local/bin/badaos-extras" <<'EOF'
#!/bin/sh
# BadaOS extras -- one-command installer (over the NAT) for the big optionals.
set -e
if [ "$(id -u)" = 0 ]; then S=""; else S="sudo"; fi

bundle() {
  case "$1" in
    clang)        echo "clang llvm lld lldb" ;;
    texlive-full|tex) echo "texlive-full" ;;
    dev)          echo "build-essential clang llvm cmake git pkg-config gdb valgrind" ;;
    media)        echo "vlc gimp ffmpeg" ;;
    screen)       echo "screen" ;;
    tmux)         echo "tmux" ;;
    all)          echo "clang llvm lld texlive-full build-essential cmake gdb vlc gimp ffmpeg" ;;
    *)            echo "$1" ;;   # any other name -> apt package(s) verbatim
  esac
}

if [ $# -eq 0 ]; then
  cat <<USAGE
badaos-extras -- install big optional software over the internet (NAT).
Baked into the ISO already: screen, tmux, texlive (+ Japanese), git, curl,
a C/C++ compiler (build-essential).  Fetch the rest on demand:

  badaos-extras clang          clang / llvm / lld / lldb
  badaos-extras texlive-full   the FULL TeX Live distribution
  badaos-extras dev            build-essential clang llvm cmake gdb valgrind
  badaos-extras media          vlc gimp ffmpeg
  badaos-extras all            clang + texlive-full + dev + media
  badaos-extras <pkg> ...      any Debian package name(s)

Needs the internet (NetworkManager provides it automatically).
USAGE
  exit 0
fi

PKGS=""
for name in "$@"; do PKGS="$PKGS $(bundle "$name")"; done
echo "==> installing over the NAT:$PKGS"
$S apt-get update -qq
# shellcheck disable=SC2086
$S env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $PKGS || {
  echo "install failed -- are you online?  Check: nmcli / ping deb.debian.org" >&2
  exit 1
}
echo "done: $PKGS"
EOF
chmod 0755 "$CHROOT/usr/local/bin/badaos-extras"

# put Homebrew on PATH for interactive shells (harmless before it is installed)
cat > "$CHROOT/etc/profile.d/10-badaos-brew.sh" <<'EOF'
if [ -x /home/linuxbrew/.linuxbrew/bin/brew ]; then
  eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi
EOF

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
# xz with a big dictionary + 1 MiB blocks packs the rootfs tighter, keeping
# the ISO well under the 2 GB release-asset limit (leaving room for the
# baked userland; the heavy extras go on over the NAT via `badaos-extras`).
mksquashfs "$CHROOT" "$ISO/live/filesystem.squashfs" \
    -comp xz -b 1M -Xdict-size 100% -noappend -quiet

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
