#!/usr/bin/env bash
# =============================================================================
# build-iso.sh — Bada VM Pro OS の起動可能 ISO を作る (Ubuntu 22.04 ベース)
#
#   ・debootstrap で最小 Ubuntu (jammy) の chroot を構築
#   ・w9wm を既定の X セッションに (lightdm 自動ログイン)
#   ・Bada アプリ (BadaVMPro / Laevateinn の .deb と単一 HTML) をプリインストール
#   ・Calamares を入れて「実ディスクへインストール」を可能に
#   ・NetworkManager で NAT/DHCP → apt がそのまま使える
#   ・あなたのリポジトリの apt リポジトリ (flat, [trusted=yes]) を登録
#   ・casper でライブ起動 (squashfs + overlay)
#   ・GRUB を BIOS + UEFI 両対応で書き、xorriso で isohybrid ISO を出力
#     → Rufus (dd / ISO モード) や `dd` でそのまま USB に書ける
#
# 必要権限: root (sudo)。GitHub Actions の ubuntu-latest で実行する前提。
#   使い方: sudo bash badaos-iso/build-iso.sh <version> <apt_base_url>
# =============================================================================
set -euo pipefail

VERSION="${1:-1.0.0}"
APT_BASE_URL="${2:-https://github.com/masaaki-avnturle/Bada/releases/download/badaos-v${VERSION}/}"
SUITE="jammy"
ARCH="amd64"
MIRROR="http://archive.ubuntu.com/ubuntu"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"

WORK="$(pwd)/badaos-build"
CHROOT="$WORK/chroot"
IMAGE="$WORK/image"
OUT="$(pwd)/out"
ISO_NAME="BadaVMPro-OS-${VERSION}-${ARCH}.iso"

echo "== Bada VM Pro OS ISO builder =="
echo "   version=$VERSION suite=$SUITE arch=$ARCH"
echo "   apt repo=$APT_BASE_URL"

# ---- 0. ホスト側ツール -------------------------------------------------------
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  debootstrap squashfs-tools xorriso isolinux syslinux-common \
  grub-pc-bin grub-efi-amd64-bin grub-common mtools dosfstools \
  ca-certificates wget rsync

rm -rf "$WORK"; mkdir -p "$CHROOT" "$IMAGE" "$OUT"

# ---- 1. 最小 Ubuntu を debootstrap ------------------------------------------
debootstrap --arch="$ARCH" --variant=minbase \
  --include=ca-certificates,gnupg "$SUITE" "$CHROOT" "$MIRROR"

# chroot 用マウント (proc/sys/devpts が無いと initramfs 更新等が失敗する)
mount --bind /dev       "$CHROOT/dev"
mount --bind /dev/pts   "$CHROOT/dev/pts"
mount -t proc  none     "$CHROOT/proc"
mount -t sysfs none     "$CHROOT/sys"
mount --bind /run       "$CHROOT/run"
# DNS 解決用 (apt がミラーへ到達できるように)
cp -f /etc/resolv.conf "$CHROOT/etc/resolv.conf" 2>/dev/null || true
cleanup() {
  for m in dev/pts proc sys run dev; do
    mountpoint -q "$CHROOT/$m" && umount -lf "$CHROOT/$m" || true
  done
}
trap cleanup EXIT

# ---- 2. chroot 内セットアップ用ファイルを配置 -------------------------------
mkdir -p "$CHROOT/opt/bada"
# 単一 HTML アプリ (Bada VM Pro / Laevateinn / ZoneBrowser 等) を同梱
for d in bada_vm_pro laevateinn; do
  if [ -f "$REPO_ROOT/$d/index.html" ]; then
    mkdir -p "$CHROOT/opt/bada/$d"
    cp "$REPO_ROOT/$d/index.html" "$CHROOT/opt/bada/$d/index.html"
  fi
done
[ -f "$REPO_ROOT/bada_gui_ide/dist/zone-browser.html" ] && \
  cp "$REPO_ROOT/bada_gui_ide/dist/zone-browser.html" "$CHROOT/opt/bada/zone-browser.html" || true

# あらかじめ取得済みの .deb (ワークフローが out_debs/ に置く) を同梱
mkdir -p "$CHROOT/opt/bada/debs"
if compgen -G "$(pwd)/out_debs/*.deb" > /dev/null; then
  cp "$(pwd)"/out_debs/*.deb "$CHROOT/opt/bada/debs/" || true
fi

# config 一式
install -Dm644 "$HERE/config/apt/bada.list.tmpl" "$CHROOT/tmp/bada.list.tmpl"
install -Dm644 "$HERE/config/xsessions/w9wm.desktop" "$CHROOT/usr/share/xsessions/w9wm.desktop"
install -Dm755 "$HERE/config/w9wm-session.sh" "$CHROOT/usr/local/bin/w9wm-session"
install -Dm755 "$HERE/config/bada-launcher.sh" "$CHROOT/usr/local/bin/bada-launcher"
mkdir -p "$CHROOT/etc/calamares"
cp -r "$HERE/config/calamares/." "$CHROOT/etc/calamares/"
cp "$HERE/config/setup-inside.sh" "$CHROOT/tmp/setup-inside.sh"
chmod +x "$CHROOT/tmp/setup-inside.sh"

# ---- 3. chroot 内でパッケージ導入・設定 -------------------------------------
chroot "$CHROOT" /bin/bash /tmp/setup-inside.sh "$VERSION" "$APT_BASE_URL"

# ---- 4. 後片付け → squashfs -------------------------------------------------
chroot "$CHROOT" apt-get clean
rm -f "$CHROOT/tmp/setup-inside.sh" "$CHROOT/tmp/bada.list.tmpl"
cleanup; trap - EXIT

mkdir -p "$IMAGE/casper" "$IMAGE/boot/grub" "$IMAGE/EFI/BOOT" "$IMAGE/isolinux"

# カーネル/initrd を取り出す
cp "$CHROOT"/boot/vmlinuz-*      "$IMAGE/casper/vmlinuz"
cp "$CHROOT"/boot/initrd.img-*   "$IMAGE/casper/initrd"

# filesystem.squashfs
mksquashfs "$CHROOT" "$IMAGE/casper/filesystem.squashfs" \
  -noappend -no-progress -e boot
printf "%s" "$(du -sx --block-size=1 "$CHROOT" | cut -f1)" > "$IMAGE/casper/filesystem.size"
echo "Bada VM Pro OS ${VERSION}" > "$IMAGE/casper/filesystem.manifest"

# ---- 5. ブートローダ設定 (BIOS: isolinux / UEFI: grub) ----------------------
CMDLINE="boot=casper username=bada hostname=badaos quiet splash ---"

cat > "$IMAGE/boot/grub/grub.cfg" <<EOF
set default=0
set timeout=10
menuentry "Bada VM Pro OS ${VERSION} (ライブ / インストール)" {
    linux /casper/vmlinuz $CMDLINE
    initrd /casper/initrd
}
menuentry "Bada VM Pro OS ${VERSION} (セーフグラフィック)" {
    linux /casper/vmlinuz boot=casper username=bada hostname=badaos nomodeset ---
    initrd /casper/initrd
}
EOF

# isolinux (BIOS)
cp /usr/lib/ISOLINUX/isolinux.bin "$IMAGE/isolinux/"
cp /usr/lib/syslinux/modules/bios/*.c32 "$IMAGE/isolinux/" 2>/dev/null || true
cat > "$IMAGE/isolinux/isolinux.cfg" <<EOF
UI menu.c32
PROMPT 0
TIMEOUT 100
DEFAULT bada
LABEL bada
  MENU LABEL Bada VM Pro OS ${VERSION}
  KERNEL /casper/vmlinuz
  APPEND initrd=/casper/initrd $CMDLINE
LABEL badasafe
  MENU LABEL Bada VM Pro OS (safe graphics)
  KERNEL /casper/vmlinuz
  APPEND initrd=/casper/initrd boot=casper username=bada hostname=badaos nomodeset ---
EOF

# UEFI: GRUB EFI アプリと FAT の efiboot.img
grub-mkstandalone \
  --format=x86_64-efi \
  --output="$IMAGE/EFI/BOOT/BOOTX64.EFI" \
  --locales="" --fonts="" \
  "boot/grub/grub.cfg=$IMAGE/boot/grub/grub.cfg"

( cd "$IMAGE" && \
  dd if=/dev/zero of=EFI/BOOT/efiboot.img bs=1M count=10 && \
  mkfs.vfat EFI/BOOT/efiboot.img && \
  mmd -i EFI/BOOT/efiboot.img ::/EFI ::/EFI/BOOT && \
  mcopy -i EFI/BOOT/efiboot.img EFI/BOOT/BOOTX64.EFI ::/EFI/BOOT/ )

# ---- 6. ISO 生成 (BIOS + UEFI ハイブリッド) --------------------------------
xorriso -as mkisofs \
  -iso-level 3 -full-iso9660-filenames -volid "BADAVMPRO_OS" \
  -eltorito-boot isolinux/isolinux.bin \
    -eltorito-catalog isolinux/boot.cat \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
  -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
  -eltorito-alt-boot -e EFI/BOOT/efiboot.img -no-emul-boot -isohybrid-gpt-basdat \
  -output "$OUT/$ISO_NAME" \
  "$IMAGE"

echo "== built: $OUT/$ISO_NAME =="
ls -lh "$OUT/$ISO_NAME"
sha256sum "$OUT/$ISO_NAME" | tee "$OUT/$ISO_NAME.sha256"
