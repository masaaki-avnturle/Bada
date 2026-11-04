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
#   ミラーの一時的なダウンロード失敗に備えて最大 4 回やり直す
for try in 1 2 3 4; do
  debootstrap --arch="$ARCH" --variant=minbase \
    --include=ca-certificates,gnupg "$SUITE" "$CHROOT" "$MIRROR" && break
  [ "$try" = 4 ] && { echo "FATAL: debootstrap に失敗"; exit 1; }
  echo "debootstrap 失敗 (試行 $try) — やり直します"; sleep $(( try * 10 ))
  rm -rf "$CHROOT"; mkdir -p "$CHROOT"
done

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
# パッケージ w9wm の w9wm.desktop (Exec=/usr/bin/w9wm) に上書きされないよう別名にする
install -Dm644 "$HERE/config/xsessions/badaos-w9wm.desktop" "$CHROOT/usr/share/xsessions/badaos-w9wm.desktop"
install -Dm755 "$HERE/config/w9wm-session.sh" "$CHROOT/usr/local/bin/w9wm-session"
install -Dm755 "$HERE/config/bada-launcher.sh" "$CHROOT/usr/local/bin/bada-launcher"
install -Dm755 "$HERE/config/install-badaos.sh"        "$CHROOT/usr/local/bin/install-badaos"
install -Dm755 "$HERE/config/install-badaos-simple.sh" "$CHROOT/usr/local/bin/install-badaos-simple"
install -Dm755 "$HERE/config/badaos-partition.sh"      "$CHROOT/usr/local/bin/badaos-partition"
install -Dm755 "$HERE/config/badaos-apps.sh"           "$CHROOT/usr/local/bin/badaos-apps"
install -Dm755 "$HERE/config/badaos-extras.sh"         "$CHROOT/usr/local/bin/badaos-extras"
# w9wm の自動配置パッチ (setup-inside.sh がソースからビルドする時に当てる)
install -Dm644 "$HERE/w9wm/30_badaos_autoplace.diff"   "$CHROOT/tmp/w9wm-patches/30_badaos_autoplace.diff"
# 自作 GUI インストーラ (zenity ウィザード + 実インストール本体, Calamares 代替)
install -Dm755 "$HERE/installer/badaos-installer.sh"    "$CHROOT/usr/local/bin/badaos-installer"
install -Dm755 "$HERE/installer/badaos-install-core.sh" "$CHROOT/usr/local/lib/badaos/badaos-install-core.sh"
# トリプルブート: Windows の下に Bada VM Pro 専用ブート FAT + OS 区画 (UEFI / Legacy)
install -Dm755 "$HERE/config/install-badaos-triboot.sh"          "$CHROOT/usr/local/bin/install-badaos-triboot"
install -Dm755 "$HERE/installer/badaos-triboot-installer.sh"     "$CHROOT/usr/local/bin/badaos-triboot-installer"
install -Dm755 "$HERE/installer/badaos-triboot-core.sh"          "$CHROOT/usr/local/lib/badaos/badaos-triboot-core.sh"
install -Dm755 "$HERE/installer/badaos-triboot-text.sh"          "$CHROOT/usr/local/bin/badaos-triboot-text"
install -Dm755 "$HERE/installer/badaos-disks.sh"                 "$CHROOT/usr/local/lib/badaos/badaos-disks"
install -Dm755 "$HERE/installer/35_badavmpro_triboot"            "$CHROOT/usr/local/lib/badaos/35_badavmpro_triboot"
# Calamares の日本語インストール設定
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

# ---- squashfs を「4GiB 未満の複数レイヤ」に分けて作る -------------------------
#   Rufus の「ISO イメージモード」は ISO の中身を FAT32 の USB にコピーするため、
#   1 ファイル 4GiB 以上は書けない。texlive-full 入りでも各ファイルが 4GiB 未満に
#   なるよう、casper の多層起動 (casper/*.squashfs をすべて overlay で重ねる) を使う:
#     filesystem.squashfs        … ベース (TeX 本体とフォント以外すべて)
#     filesystem-tex.squashfs    … /usr/share/texlive (フォント以外), texmf
#     filesystem-fonts.squashfs  … TeX のフォント, /usr/share/fonts
#   /boot は「除外しない」(インストール後のシステムにカーネルを入れるため)。
printf "%s" "$(du -sx --block-size=1 "$CHROOT" | cut -f1)" > "$IMAGE/casper/filesystem.size"
LAYERS="$WORK/layers"; rm -rf "$LAYERS"; mkdir -p "$LAYERS"
split_out(){ # $1=レイヤ名  $2...=chroot からの相対パス (同じ FS 内で mv するので一瞬)
  local name="$1"; shift; mkdir -p "$LAYERS/$name"
  for p in "$@"; do
    [ -e "$CHROOT/$p" ] || continue
    mkdir -p "$LAYERS/$name/$(dirname "$p")"
    mv "$CHROOT/$p" "$LAYERS/$name/$p"
    mkdir -p "$CHROOT/$p"            # 空の置き場所 (overlay で上のレイヤが見える)
  done; }
split_out fonts usr/share/texlive/texmf-dist/fonts usr/share/fonts
split_out tex   usr/share/texlive usr/share/texmf var/lib/texmf
SQ_OPTS="-noappend -no-progress -comp xz -b 1M"
mksquashfs "$CHROOT" "$IMAGE/casper/filesystem.squashfs" $SQ_OPTS \
  -wildcards -e "boot/grub" "proc/*" "sys/*" "run/*" "tmp/*"
mksquashfs "$LAYERS/tex"   "$IMAGE/casper/filesystem-tex.squashfs"   $SQ_OPTS
mksquashfs "$LAYERS/fonts" "$IMAGE/casper/filesystem-fonts.squashfs" $SQ_OPTS
# FAT32 (Rufus ISO モード) の上限: 1 ファイル 4GiB 未満
for f in "$IMAGE"/casper/*.squashfs; do
  sz=$(stat -c %s "$f"); echo "layer $(basename "$f"): $(( sz / 1048576 )) MiB"
  [ "$sz" -lt 4294967295 ] || { echo "FATAL: $f が 4GiB 以上です (FAT32 に入りません)。レイヤを分けてください"; exit 1; }
done
echo "Bada VM Pro OS ${VERSION}" > "$IMAGE/casper/filesystem.manifest"
# casper が起動メディアを識別しやすいよう .disk/info を置く
mkdir -p "$IMAGE/.disk"
echo "Bada VM Pro OS ${VERSION} - Release amd64" > "$IMAGE/.disk/info"
: > "$IMAGE/.disk/base_installable"

# ---- 5. GRUB 設定 (BIOS+UEFI 共通)。search で ISO を必ず見つける ----------
CMDLINE="boot=casper username=bada hostname=badaos quiet splash ---"
cat > "$IMAGE/boot/grub/grub.cfg" <<EOF
# 日本語メニューを Legacy BIOS / UEFI どちらでも表示するため、ビデオ → フォント → gfxterm の順に
insmod all_video
insmod gfxterm
insmod font
if loadfont /boot/grub/fonts/unicode.pf2 ; then set gfxmode=auto; terminal_output gfxterm; fi
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
menuentry "Bada VM Pro OS ${VERSION} (インストール: GUI  Windows | BadaVMPro | Linux)" {
    linux /casper/vmlinuz $CMDLINE badaos.triboot=1
    initrd /casper/initrd
}
menuentry "Bada VM Pro OS ${VERSION} (インストール: GUI セーフグラフィック / 画面が真っ黒になる PC はこちら)" {
    linux /casper/vmlinuz boot=casper username=bada hostname=badaos nomodeset badaos.triboot=1 ---
    initrd /casper/initrd
}
menuentry "Bada VM Pro OS ${VERSION} (インストール: テキスト画面 / GUI がどうしても出ない時)" {
    linux /casper/vmlinuz boot=casper username=bada hostname=badaos nomodeset systemd.unit=multi-user.target badaos.textinstall=1 ---
    initrd /casper/initrd
}
menuentry "Bada VM Pro OS ${VERSION} (セーフグラフィック: 画面が真っ黒になる PC 向け)" {
    linux /casper/vmlinuz boot=casper username=bada hostname=badaos nomodeset ---
    initrd /casper/initrd
}
menuentry "Bada VM Pro OS ${VERSION} (詳細表示: 起動メッセージを全部表示 / 問題調査用)" {
    linux /casper/vmlinuz boot=casper username=bada hostname=badaos systemd.show_status=1 ---
    initrd /casper/initrd
}
menuentry "Bada VM Pro OS ${VERSION} (テキストモード: コマンド操作のみ)" {
    linux /casper/vmlinuz boot=casper username=bada hostname=badaos nomodeset systemd.unit=multi-user.target ---
    initrd /casper/initrd
}
EOF

# ---- Rufus「ISO イメージモード」(FAT32 USB にファイルコピー) 用の UEFI ローダ ----
#   grub-mkrescue の UEFI ローダは ISO の UUID で自分を探すため、ファイルを
#   コピーした USB では見つからないことがある。ISO の中に普通のファイルとして
#   \efi\boot\bootx64.efi を置き (grub-mkrescue の同じパスのローダを上書き。FAT32 で大文字小文字違いの
#   2 つが衝突しないよう同じパスにする)、/casper/vmlinuz があるボリュームを探して
#   /boot/grub/grub.cfg を読むようにする (ISO9660 / FAT32 / exFAT / NTFS どれでも可)。
mkdir -p "$IMAGE/efi/boot"
cat > "$WORK/efi-early.cfg" <<'EOF'
search --no-floppy --set=root --file /casper/vmlinuz
set prefix=($root)/boot/grub
configfile ($root)/boot/grub/grub.cfg
EOF
# ホストの GRUB の版によって無いモジュールがある (例: 新しい版には efi_uga が無い) ので、存在するものだけ入れる
EFI_MODS=""
for m in part_gpt part_msdos fat exfat ntfs iso9660 search search_fs_file normal configfile \
         linux echo test ls all_video efi_gop efi_uga gfxterm font gzio; do
  [ -f "/usr/lib/grub/x86_64-efi/$m.mod" ] && EFI_MODS="$EFI_MODS $m"
done
echo "UEFI loader modules:$EFI_MODS"
# shellcheck disable=SC2086
grub-mkimage -O x86_64-efi -o "$IMAGE/efi/boot/bootx64.efi" -p /boot/grub -c "$WORK/efi-early.cfg" $EFI_MODS
# grub.cfg の insmod 用に UEFI モジュールもツリーに置く (grub-mkrescue も入れるが念のため)
mkdir -p "$IMAGE/boot/grub/x86_64-efi"
cp /usr/lib/grub/x86_64-efi/*.mod /usr/lib/grub/x86_64-efi/*.lst "$IMAGE/boot/grub/x86_64-efi/" 2>/dev/null || true

# GRUB の Unicode フォント (日本語メニュー用) を同梱
mkdir -p "$IMAGE/boot/grub/fonts"
cp /usr/share/grub/unicode.pf2 "$IMAGE/boot/grub/fonts/unicode.pf2"

# ---- 6. ISO 生成: grub-mkrescue が BIOS(El Torito)+UEFI(ESP)+isohybrid を
#         すべて面倒みる。Rufus / dd でそのまま USB に書ける ----------------
grub-mkrescue -o "$OUT/$ISO_NAME" "$IMAGE" \
  --product-name "Bada VM Pro OS" --product-version "$VERSION" \
  -- -volid "BADAVMPRO_OS"
# (各 squashfs は上で 4GiB 未満を確認済みなので ISO9660 の 1 ファイル上限にも収まる)

test -s "$OUT/$ISO_NAME" || { echo "FATAL: ISO 生成に失敗"; exit 1; }
echo "== built: $OUT/$ISO_NAME =="
ls -lh "$OUT/$ISO_NAME"
sha256sum "$OUT/$ISO_NAME" | tee "$OUT/$ISO_NAME.sha256"
