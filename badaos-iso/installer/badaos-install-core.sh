#!/bin/bash
# =============================================================================
# badaos-install-core.sh — Bada VM Pro OS を実ディスクへインストールする本体
#   GUI (badaos-installer.sh の zenity ウィザード) から root で呼ばれる。
#   引数は環境変数で受け取る:
#     TARGET_DISK  例 /dev/sda, /dev/nvme0n1   (この全体を消去する)
#     NEW_HOST     ホスト名   (既定 badaos)
#     NEW_USER     ユーザー名 (既定 bada)
#     NEW_PASS     パスワード (既定 bada)
#   標準出力に「NN<改行># メッセージ」を出し、zenity --progress を進める。
#   エラーは標準エラーへ (GUI がログ末尾を表示)。
# =============================================================================
set -euo pipefail

DISK="${TARGET_DISK:?TARGET_DISK 未指定}"
HOST="${NEW_HOST:-badaos}"
USER_NAME="${NEW_USER:-bada}"
PASS="${NEW_PASS:-bada}"

emit(){ printf '%s\n# %s\n' "$1" "$2"; }
fail(){ echo "ERROR: $*" >&2; exit 1; }

# ライブメディア上の squashfs を探す
SQUASH=""
for c in /cdrom/casper/filesystem.squashfs /run/live/medium/casper/filesystem.squashfs /isodevice/casper/filesystem.squashfs; do
  [ -f "$c" ] && { SQUASH="$c"; break; }
done
[ -n "$SQUASH" ] || fail "ライブシステム (filesystem.squashfs) が見つかりません"

# パーティションデバイス名 (nvme/mmc は p を挟む)
partdev(){ case "$DISK" in *nvme*|*mmcblk*|*loop*) echo "${DISK}p$1";; *) echo "${DISK}$1";; esac; }

# ファームウェア判定
if [ -d /sys/firmware/efi ]; then FW="uefi"; else FW="bios"; fi
emit 2 "ファームウェア: ${FW}, 対象ディスク: ${DISK}"

# 使用中なら解放
umount -Rf /mnt 2>/dev/null || true
swapoff -a 2>/dev/null || true
for p in $(lsblk -ln -o NAME "$DISK" | tail -n +2); do umount -f "/dev/$p" 2>/dev/null || true; done

emit 5 "パーティションを作成中"
wipefs -a "$DISK" >/dev/null 2>&1 || true
sgdisk --zap-all "$DISK" >/dev/null 2>&1 || true

if [ "$FW" = "uefi" ]; then
  parted -s "$DISK" mklabel gpt
  parted -s "$DISK" mkpart ESP fat32 1MiB 513MiB
  parted -s "$DISK" set 1 esp on
  parted -s "$DISK" mkpart root ext4 513MiB 100%
  sleep 1; partprobe "$DISK" 2>/dev/null || true; sleep 1
  ESP="$(partdev 1)"; ROOT="$(partdev 2)"
  emit 12 "フォーマット中 (EFI + ext4)"
  mkfs.vfat -F32 "$ESP" >/dev/null
  mkfs.ext4 -F -L badaos "$ROOT" >/dev/null
  mount "$ROOT" /mnt
  mkdir -p /mnt/boot/efi
  mount "$ESP" /mnt/boot/efi
else
  parted -s "$DISK" mklabel msdos
  parted -s "$DISK" mkpart primary ext4 1MiB 100%
  parted -s "$DISK" set 1 boot on
  sleep 1; partprobe "$DISK" 2>/dev/null || true; sleep 1
  ROOT="$(partdev 1)"
  emit 12 "フォーマット中 (ext4)"
  mkfs.ext4 -F -L badaos "$ROOT" >/dev/null
  mount "$ROOT" /mnt
fi

emit 20 "システムをコピー中… (数分かかります)"
unsquashfs -f -d /mnt "$SQUASH" >/dev/null

emit 72 "システム設定を書き込み中"
ROOT_UUID="$(blkid -s UUID -o value "$ROOT")"
{
  echo "# /etc/fstab — Bada VM Pro OS"
  echo "UUID=${ROOT_UUID} / ext4 defaults,noatime,errors=remount-ro 0 1"
  if [ "$FW" = "uefi" ]; then
    ESP_UUID="$(blkid -s UUID -o value "$ESP")"
    echo "UUID=${ESP_UUID} /boot/efi vfat umask=0077 0 1"
  fi
} > /mnt/etc/fstab

echo "$HOST" > /mnt/etc/hostname
if grep -q '^127.0.1.1' /mnt/etc/hosts 2>/dev/null; then
  sed -i "s/^127.0.1.1.*/127.0.1.1\t${HOST}/" /mnt/etc/hosts
else
  printf '127.0.0.1\tlocalhost\n127.0.1.1\t%s\n' "$HOST" >> /mnt/etc/hosts
fi

# chroot 用マウント
mount --bind /dev     /mnt/dev
mount --bind /dev/pts /mnt/dev/pts
mount -t proc  none   /mnt/proc
mount -t sysfs none   /mnt/sys
mount --bind /run     /mnt/run 2>/dev/null || true
cp -f /etc/resolv.conf /mnt/etc/resolv.conf 2>/dev/null || true

emit 80 "ユーザー ${USER_NAME} を作成中"
chroot /mnt /bin/bash -e <<CHROOT
id "${USER_NAME}" >/dev/null 2>&1 || useradd -m -s /bin/bash -G sudo,adm,cdrom,plugdev,netdev,audio,video "${USER_NAME}"
echo "${USER_NAME}:${PASS}" | chpasswd
# lightdm 自動ログインを新ユーザー + w9wm セッションに
mkdir -p /etc/lightdm/lightdm.conf.d
printf '[Seat:*]\nautologin-user=%s\nautologin-user-timeout=0\nuser-session=w9wm\ngreeter-session=lightdm-gtk-greeter\n' "${USER_NAME}" > /etc/lightdm/lightdm.conf.d/50-badaos.conf
# インストール後は不要なライブ専用パッケージを除去
apt-get -y purge casper 2>/dev/null || true
apt-get -y autoremove --purge 2>/dev/null || true
systemctl enable NetworkManager 2>/dev/null || true
systemctl enable lightdm 2>/dev/null || true
CHROOT

emit 90 "GRUB ブートローダを設置中 (${FW})"
if [ "$FW" = "uefi" ]; then
  chroot /mnt grub-install --target=x86_64-efi --efi-directory=/boot/efi \
        --bootloader-id=BadaVMProOS --recheck --no-nvram \
    || chroot /mnt grub-install --target=x86_64-efi --efi-directory=/boot/efi --removable --recheck
  # フォールバックのため removable パスにもコピー
  chroot /mnt grub-install --target=x86_64-efi --efi-directory=/boot/efi --removable --recheck 2>/dev/null || true
else
  chroot /mnt grub-install --target=i386-pc --recheck "$DISK"
fi
chroot /mnt update-grub 2>/dev/null || chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg

emit 96 "後始末"
sync
umount -R /mnt 2>/dev/null || umount -lR /mnt 2>/dev/null || true

emit 100 "インストール完了"
