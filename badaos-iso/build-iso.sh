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
# grub-mkrescue は grub-common、BIOS/UEFI コアは grub-pc-bin/grub-efi-amd64-bin、
# ESP 作成に mtools が要る。xorriso で ISO を焼く。
apt-get install -y --no-install-recommends \
  debootstrap squashfs-tools xorriso \
  grub-common grub-pc-bin grub-efi-amd64-bin mtools dosfstools \
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

mkdir -p "$IMAGE/casper" "$IMAGE/boot/grub"

# カーネル/initrd を取り出す (ライブ起動用)。存在しなければビルドを止める。
KVER="$(chroot "$CHROOT" bash -c 'ls -1 /boot/vmlinuz-* 2>/dev/null | sed "s#.*/vmlinuz-##" | sort -V | tail -1')"
if [ -z "$KVER" ]; then
  echo "FATAL: chroot にカーネル (/boot/vmlinuz-*) がありません。linux-generic の導入に失敗しています。"
  exit 1
fi
echo "kernel version in image: $KVER"
cp "$CHROOT/boot/vmlinuz-$KVER"    "$IMAGE/casper/vmlinuz"
cp "$CHROOT/boot/initrd.img-$KVER" "$IMAGE/casper/initrd"
test -s "$IMAGE/casper/vmlinuz" || { echo "FATAL: vmlinuz が空/欠落"; exit 1; }
test -s "$IMAGE/casper/initrd"  || { echo "FATAL: initrd が空/欠落";  exit 1; }
ls -lh "$IMAGE/casper/vmlinuz" "$IMAGE/casper/initrd"

# filesystem.squashfs
#   /boot は「除外しない」。除外するとインストール後のシステムにカーネルが
#   入らず、実ディスクへ入れても起動できなくなるため。
mksquashfs "$CHROOT" "$IMAGE/casper/filesystem.squashfs" \
  -noappend -no-progress -wildcards \
  -e "boot/grub" "proc/*" "sys/*" "run/*" "tmp/*"
printf "%s" "$(du -sx --block-size=1 "$CHROOT" | cut -f1)" > "$IMAGE/casper/filesystem.size"
echo "Bada VM Pro OS ${VERSION}" > "$IMAGE/casper/filesystem.manifest"
# casper が起動メディアを識別しやすいよう .disk/info を置く
mkdir -p "$IMAGE/.disk"
echo "Bada VM Pro OS ${VERSION} - Release amd64" > "$IMAGE/.disk/info"
: > "$IMAGE/.disk/base_installable"

# ---- 5. GRUB 設定 (BIOS+UEFI 共通)。search で ISO を必ず見つける ----------
CMDLINE="boot=casper username=bada hostname=badaos quiet splash ---"
cat > "$IMAGE/boot/grub/grub.cfg" <<EOF
if loadfont /boot/grub/fonts/unicode.pf2 ; then set gfxmode=auto; insmod gfxterm; terminal_output gfxterm; fi
insmod all_video
insmod part_gpt
insmod part_msdos
insmod iso9660
set default=0
set timeout=15
# GRUB がどのデバイスから起動しても、カーネルのある ISO ボリュームを
# 探して root に設定する (これが無いと「kernel が無い」エラーになる)
search --no-floppy --set=root --file /casper/vmlinuz
menuentry "Bada VM Pro OS ${VERSION} (ライブ / インストール)" {
    linux /casper/vmlinuz $CMDLINE
    initrd /casper/initrd
}
menuentry "Bada VM Pro OS ${VERSION} (セーフグラフィック)" {
    linux /casper/vmlinuz boot=casper username=bada hostname=badaos nomodeset ---
    initrd /casper/initrd
}
EOF

# ---- 6. ISO 生成: grub-mkrescue が BIOS(El Torito)+UEFI(ESP)+isohybrid を
#         すべて面倒みる。Rufus / dd でそのまま USB に書ける ----------------
grub-mkrescue -o "$OUT/$ISO_NAME" "$IMAGE" \
  --product-name "Bada VM Pro OS" --product-version "$VERSION" \
  -- -volid "BADAVMPRO_OS"

test -s "$OUT/$ISO_NAME" || { echo "FATAL: ISO 生成に失敗"; exit 1; }
echo "== built: $OUT/$ISO_NAME =="
ls -lh "$OUT/$ISO_NAME"
sha256sum "$OUT/$ISO_NAME" | tee "$OUT/$ISO_NAME.sha256"
