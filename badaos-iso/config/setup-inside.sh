#!/usr/bin/env bash
# chroot 内で実行 — パッケージ導入・w9wm セッション・Bada アプリ・apt リポジトリ
set -euo pipefail
VERSION="${1:-1.0.0}"
APT_BASE_URL="${2:-}"
export DEBIAN_FRONTEND=noninteractive

# ---- apt ソース (main/universe/multiverse/restricted + updates) ----
cat > /etc/apt/sources.list <<EOF
deb http://archive.ubuntu.com/ubuntu jammy main universe multiverse restricted
deb http://archive.ubuntu.com/ubuntu jammy-updates main universe multiverse restricted
deb http://security.ubuntu.com/ubuntu jammy-security main universe multiverse restricted
EOF

# 注意: あなたのリポジトリの apt リポジトリ (badaos-v* リリース) は
# 「今まさにビルドして作る」ものなので、ビルド中にはまだ存在しません。
# ここで登録して apt-get update すると 404 で失敗するため、登録は
# このスクリプトの最後 (update しない) に回します。まずは Ubuntu 公式のみ。
apt-get update

# ---- ライブ起動 + カーネル + 基本ツール ----
apt-get install -y --no-install-recommends \
  linux-generic casper initramfs-tools \
  network-manager net-tools iproute2 isc-dhcp-client \
  sudo nano less curl wget ca-certificates locales tzdata \
  xserver-xorg xinit x11-xserver-utils \
  lightdm lightdm-gtk-greeter \
  w9wm xterm feh fonts-dejavu \
  calamares || true

# 独自 /etc/calamares 設定を使用 (build-iso.sh が config/calamares を配置済み)
# ブラウザは同梱しない: Bada アプリは Electron 版 (.deb) を優先起動するため不要。
# 必要なら apt で追加可能 (NAT/DHCP で公式ミラーへ到達できる)。

# ---- ロケール/タイムゾーン ----
sed -i 's/# *ja_JP.UTF-8/ja_JP.UTF-8/; s/# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen || true
locale-gen || true
echo "LANG=ja_JP.UTF-8" > /etc/default/locale
ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime || true

# ---- Bada アプリの .deb をプリインストール ----
if compgen -G "/opt/bada/debs/*.deb" > /dev/null; then
  apt-get install -y /opt/bada/debs/*.deb || { dpkg -i /opt/bada/debs/*.deb || true; apt-get -y -f install || true; }
fi

# ---- w9wm セッションを既定に (lightdm 自動ログイン: casper ユーザ bada) ----
mkdir -p /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/50-badaos.conf <<EOF
[Seat:*]
autologin-user=bada
autologin-user-timeout=0
user-session=w9wm
greeter-session=lightdm-gtk-greeter
EOF

# w9wm 起動時に Bada VM Pro を自動起動するためのスケルトン
mkdir -p /etc/skel
cat > /etc/skel/.xsessionrc <<'EOF'
# Bada VM Pro OS: X 起動時のフック (w9wm-session から読まれる)
xsetroot -solid "#0b0e14" 2>/dev/null || true
EOF

# ---- ネットワーク: NetworkManager を有効化 (NAT/DHCP がそのまま通る) ----
systemctl enable NetworkManager 2>/dev/null || true
cat > /etc/NetworkManager/conf.d/10-globally-managed.conf <<EOF
[keyfile]
unmanaged-devices=none
EOF

# ---- デスクトップにインストーラ (Calamares) とアプリのショートカット ----
mkdir -p /etc/skel/Desktop
if [ -f /usr/share/applications/calamares.desktop ] || [ -f /usr/share/applications/io.calamares.calamares.desktop ]; then
  for f in /usr/share/applications/*calamares*.desktop; do
    [ -f "$f" ] && cp "$f" /etc/skel/Desktop/ 2>/dev/null || true
  done
fi
cat > /etc/skel/Desktop/bada-vm-pro.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Bada VM Pro
Exec=/usr/local/bin/bada-launcher bada_vm_pro
Terminal=false
Categories=System;
EOF
chmod +x /etc/skel/Desktop/*.desktop 2>/dev/null || true

# ---- casper 用: 自動ログインユーザ名を bada に固定 ----
echo "export USER=bada" >> /etc/skel/.profile

# ---- あなたのリポジトリの apt リポジトリを登録 (インストール後に使う) ----
# ビルド中は fetch しない (リリースは本ビルドで作られる)。起動後に
#   sudo apt update && sudo apt install laevateinn bada-vm-pro
# で取得できる (badaos-v* リリースの Packages/.deb を参照)。
if [ -n "$APT_BASE_URL" ]; then
  sed "s#@APT_BASE_URL@#${APT_BASE_URL}#g" /tmp/bada.list.tmpl > /etc/apt/sources.list.d/bada.list
  echo "registered bada apt repo: $APT_BASE_URL (fetched at first boot, not now)"
fi

# initramfs を更新 (casper を取り込む)
update-initramfs -u || true

apt-get clean
rm -rf /var/lib/apt/lists/*
echo "setup-inside.sh done (v$VERSION)"
