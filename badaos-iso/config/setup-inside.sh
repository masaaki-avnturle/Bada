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

# ---- 必須: カーネル + casper (ライブ起動) — 失敗したらビルドを止める ----
# ここが入らないと「kernel が無い」状態の ISO になるため || true を付けない。
apt-get install -y --no-install-recommends \
  linux-generic casper initramfs-tools \
  network-manager net-tools iproute2 isc-dhcp-client \
  sudo locales tzdata

# 導入確認 (カーネルの実体があるか)
ls -1 /boot/vmlinuz-* >/dev/null 2>&1 || { echo "FATAL: kernel not installed in chroot"; exit 1; }

# ---- デスクトップ (w9wm) + mlterm 端末 + 日本語フォント ----
apt-get install -y --no-install-recommends \
  nano less curl wget \
  xserver-xorg xinit x11-xserver-utils \
  lightdm lightdm-gtk-greeter \
  w9wm mlterm mlterm-common xterm x11-utils feh \
  fonts-dejavu fonts-noto-cjk fonts-noto-color-emoji || true

# ---- 日本語入力 (fcitx-mozc + fcitx-configtool) ----
apt-get install -y --no-install-recommends \
  fcitx fcitx-mozc fcitx-configtool fcitx-frontend-gtk3 fcitx-frontend-gtk2 \
  im-config mozc-utils-gui || true
# 既定の入力メソッドを fcitx に
im-config -n fcitx 2>/dev/null || true

# ---- インストーラ Calamares (日本語 UI) + パーティションマネージャ GParted ----
#   Calamares は system の LANG に従って日本語表示になる (ja 翻訳同梱)。
#   recommends 込みで QML/kpmcore(パーティション処理)を確実に入れる。加えて
#   実ディスク初期化用の GParted、GRUB 設置一式、squashfs 展開ツールを導入。
apt-get install -y \
  calamares \
  qml-module-qtquick2 qml-module-qtquick-window2 qml-module-qtquick-controls2 \
  qml-module-qtquick-layouts \
  gparted \
  parted gdisk dosfstools e2fsprogs util-linux zenity \
  squashfs-tools rsync \
  grub-common grub2-common grub-pc-bin grub-efi-amd64-bin os-prober || true

# 独自 /etc/calamares 設定を使用 (build-iso.sh が config/calamares を配置済み)
# ブラウザは同梱しない: Bada アプリは Electron 版 (.deb) を優先起動するため不要。
# Ubuntu 向けアプリは NAT/DHCP + apt でそのまま追加できる (sudo apt install ...)。

# ---- ロケール/タイムゾーン (日本語) ----
sed -i 's/# *ja_JP.UTF-8/ja_JP.UTF-8/; s/# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen || true
locale-gen || true
cat > /etc/default/locale <<EOF
LANG=ja_JP.UTF-8
LANGUAGE=ja_JP:ja
LC_ALL=ja_JP.UTF-8
EOF
ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime || true
echo "Asia/Tokyo" > /etc/timezone

# CLI (tty/SSH) でも日本語ロケールと入力メソッド環境変数が効くように
cat >> /etc/environment <<EOF
LANG=ja_JP.UTF-8
LANGUAGE=ja_JP:ja
GTK_IM_MODULE=fcitx
QT_IM_MODULE=fcitx
XMODIFIERS=@im=fcitx
EOF

# ---- X セッションの日本語環境 + fcitx 自動起動 (.xprofile) ----
cat > /etc/skel/.xprofile <<'EOF'
# Bada VM Pro OS — 日本語環境 & 入力メソッド
export LANG=ja_JP.UTF-8
export LANGUAGE=ja_JP:ja
export LC_ALL=ja_JP.UTF-8
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
# fcitx (mozc) を起動 (Ctrl+Space で日本語入力 ON/OFF)
(command -v fcitx-autostart >/dev/null 2>&1 && fcitx-autostart || fcitx -d) 2>/dev/null &
EOF

# ---- mlterm を日本語 UTF-8 + CJK フォントで既定設定 ----
mkdir -p /etc/skel/.mlterm
cat > /etc/skel/.mlterm/main <<EOF
ENCODING = UTF8
fontsize = 14
line_space = 1
scrollbar_mode = right
logsize = 2000
input_method = fcitx
use_anti_alias = true
type_engine = xft
EOF
cat > /etc/skel/.mlterm/font <<EOF
ISO10646_UCS4_1 = Noto Sans Mono CJK JP
ISO10646_UCS4_1_BOLD = Noto Sans Mono CJK JP:weight=bold
DEFAULT = Noto Sans Mono CJK JP
EOF

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

# ---- デスクトップ ショートカット ----
# 既定の calamares.desktop は pkexec を使い、w9wm には polkit エージェントが
# 無いため起動できない。sudo + 日本語ロケールで起動する専用ランチャに差し替える。
mkdir -p /etc/skel/Desktop
cat > /etc/skel/Desktop/install-badaos.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Bada VM Pro OS をインストール (Calamares)
Comment=日本語 GUI で実ディスクへインストール
Exec=/usr/local/bin/install-badaos
Terminal=false
Icon=calamares
Categories=System;
EOF
cat > /etc/skel/Desktop/badaos-partition.desktop <<EOF
[Desktop Entry]
Type=Application
Name=パーティションマネージャ (GParted)
Comment=使いたいハードディスクを初期化・パーティション作成
Exec=/usr/local/bin/badaos-partition
Terminal=false
Icon=gparted
Categories=System;
EOF
cat > /etc/skel/Desktop/install-badaos-simple.desktop <<EOF
[Desktop Entry]
Type=Application
Name=かんたんインストール (ウィザード)
Comment=Calamares が使えない場合の代替 GUI インストーラ
Exec=/usr/local/bin/install-badaos-simple
Terminal=false
Icon=drive-harddisk
Categories=System;
EOF
cat > /etc/skel/Desktop/fcitx-config.desktop <<EOF
[Desktop Entry]
Type=Application
Name=日本語入力の設定 (fcitx)
Comment=fcitx-configtool / mozc の設定
Exec=fcitx-configtool
Terminal=false
Icon=fcitx
Categories=Settings;
EOF
cat > /etc/skel/Desktop/mlterm.desktop <<EOF
[Desktop Entry]
Type=Application
Name=端末 (mlterm)
Comment=日本語対応ターミナル
Exec=mlterm
Terminal=false
Icon=utilities-terminal
Categories=System;
EOF
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
