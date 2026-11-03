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

# ---- パッケージを 1 つずつ導入するヘルパ ----
#   グループ一括 `apt-get install a b c || true` は 1 つでも無効名があると
#   グループ全体が入らない。ここでは 1 パッケージずつ入れ、失敗しても続行する。
apt_try(){ for p in "$@"; do apt-get install -y --no-install-recommends "$p" \
  && echo "  [ok] $p" || echo "  [WARN] $p の導入に失敗 (スキップ)"; done; }
apt_try_rec(){ for p in "$@"; do apt-get install -y "$p" \
  && echo "  [ok] $p" || echo "  [WARN] $p の導入に失敗 (スキップ)"; done; }

# ---- デスクトップ (w9wm) + mlterm 端末 + 日本語フォント ----
apt_try nano less curl wget ca-certificates \
  xserver-xorg xinit x11-xserver-utils \
  lightdm lightdm-gtk-greeter \
  w9wm mlterm mlterm-common mlterm-im-fcitx xterm x11-utils feh \
  fonts-dejavu fonts-noto-cjk fonts-noto-color-emoji

# ---- エディタ (vim / emacs / neovim) と定番 CLI/GUI アプリ ----
#   vim-gtk3: X クリップボード + 日本語対応。emacs: GTK 版。
apt_try vim vim-gtk3 emacs neovim \
  git tmux htop tree file unzip zip p7zip-full xz-utils \
  pcmanfm mousepad gpicview xarchiver galculator

# ---- 日本語入力 (fcitx-mozc + fcitx-configtool) ----
#   fcitx-mozc の依存で fcitx 本体・モジュールが入る。recommends 込みで
#   フロントエンド/モジュールを確実に揃える。
apt_try_rec fcitx fcitx-mozc fcitx-config-gtk \
  fcitx-frontend-gtk3 fcitx-frontend-gtk2 fcitx-frontend-qt5 \
  fcitx-module-dbus fcitx-ui-classic im-config mozc-utils-gui
# 既定の入力メソッドを fcitx に
im-config -n fcitx 2>/dev/null || true

# fcitx プロファイルで mozc を既定有効化 (これが無いと日本語入力が出ない)
mkdir -p /etc/skel/.config/fcitx
cat > /etc/skel/.config/fcitx/profile <<EOF
[Profile]
IMName=mozc
EnabledIMList=fcitx-keyboard-us:True,mozc:True
PreeditStringInApplication=False
ShareStateAmongWindow=No
DefaultQuickPhrase=
EOF
cat > /etc/skel/.config/fcitx/config <<EOF
[Hotkey]
TriggerKey=CTRL_SPACE ZENKAKU_HANKAKU
SwitchKey=Disabled
IMSwitchHotkey=ALT_SHIFT
TimeInterval=250
[Program]
DelayStart=2
[Output]
EOF

# ---- インストーラ Calamares (日本語 UI) + パーティションマネージャ GParted ----
#   Calamares は system の LANG に従って日本語表示になる (ja 翻訳同梱)。
#   recommends 込みで QML/kpmcore(パーティション処理)を確実に入れる。加えて
#   実ディスク初期化用の GParted、GRUB 設置一式、squashfs 展開ツールを導入。
apt_try_rec calamares gparted
apt_try qml-module-qtquick2 qml-module-qtquick-window2 qml-module-qtquick-controls2 \
  qml-module-qtquick-layouts \
  parted gdisk dosfstools e2fsprogs util-linux zenity \
  squashfs-tools rsync \
  grub-common grub2-common grub-pc-bin grub-efi-amd64-bin os-prober
# トリプルブート用: NTFS 検出/縮小、UEFI 起動メニュー登録、Secure Boot 用署名済み GRUB
apt_try ntfs-3g efibootmgr fdisk shim-signed grub-efi-amd64-signed python3-minimal

# ---- サーバ/ネットワーク: ssh・xinetd・NAT ルータ用ツール・screen ----
apt_try openssh-server xinetd screen \
  iptables dnsmasq-base network-manager-gnome \
  iputils-ping dnsutils traceroute netcat-openbsd telnet rsync
# ---- 一通りのアプリケーション (apt の deb。ブラウザ/PDF/動画/画像/端末) ----
apt_try falkon evince mpv ristretto mousepad pcmanfm lxtask \
  software-properties-common apt-transport-https gnupg

# ---- 印刷: CUPS + ドライバ一式 + GUI 設定 ----
#   USB プリンタ (ipp-usb でドライバ不要機も) / ネットワークプリンタ (avahi で
#   AirPrint・IPP Everywhere を自動検出、cups-browsed で共有プリンタを自動追加)。
#   ドライバ: printer-driver-all (gutenprint=Epson/Canon 等, hplip=HP, brlaser=Brother,
#   foo2zjs, splix, ...)。GUI は system-config-printer、ブラウザなら http://localhost:631
apt_try cups cups-client cups-bsd cups-filters cups-browsed ipp-usb \
  avahi-daemon libnss-mdns printer-driver-all hplip openprinting-ppds \
  system-config-printer system-config-printer-udev sane-utils simple-scan
systemctl enable cups cups-browsed avahi-daemon ipp-usb 2>/dev/null || true
# ライブ環境の自動ログインユーザ (casper → user-setup が作る bada) を
# プリンタ管理 (lpadmin)・スキャナ・音声/映像グループに入れる
echo 'user-setup passwd/user-default-groups string adm cdrom dip lpadmin plugdev sudo netdev audio video scanner' \
  | debconf-set-selections

# ---- TeX: texlive-full (日本語 platex/uplatex/lualatex-ja 含む全パッケージ) ----
#   PDF マニュアル (texlive-doc, 約 2GB) だけは ISO を軽くするため展開しない。
#   必要なら /etc/dpkg/dpkg.cfg.d/01-badaos-texlive-nodoc を消して
#   `sudo apt install --reinstall $(dpkg -l 'texlive-*-doc' | awk '/^ii/{print $2}')`。
cat > /etc/dpkg/dpkg.cfg.d/01-badaos-texlive-nodoc <<'EOF'
path-exclude=/usr/share/doc/texlive-doc/*
EOF
# 要求機能なので失敗したらビルドを止める (|| true を付けない)
apt-get install -y --no-install-recommends texlive-full
# エディタ連携: Emacs の AUCTeX と mozc (Emacs 内の日本語入力)、vim-latexsuite
apt_try auctex emacs-mozc vim-latexsuite

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
EDITOR=vim
VISUAL=vim
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
# type_engine = xft では ~/.mlterm/aafont が使われる (font は X コアフォント用)。
# これが無いと日本語が「□」(豆腐) になる
cat > /etc/skel/.mlterm/aafont <<EOF
DEFAULT = Noto Sans Mono CJK JP 14
ISO10646_UCS4_1 = Noto Sans Mono CJK JP 14
ISO10646_UCS4_1_BOLD = Noto Sans Mono CJK JP:weight=bold 14
JISX0208_1983 = Noto Sans Mono CJK JP 14
JISX0213_2000_1 = Noto Sans Mono CJK JP 14
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

# ---- ssh: 起動時に「その PC 固有の」ホスト鍵を作る (ISO に鍵を焼き込まない) ----
rm -f /etc/ssh/ssh_host_*
cat > /etc/systemd/system/badaos-ssh-hostkeys.service <<'EOF'
[Unit]
Description=Bada VM Pro OS: generate SSH host keys on first boot
Before=ssh.service
ConditionPathExists=!/etc/ssh/ssh_host_ed25519_key
[Service]
Type=oneshot
ExecStart=/usr/bin/ssh-keygen -A
[Install]
WantedBy=multi-user.target
EOF
systemctl enable badaos-ssh-hostkeys.service ssh 2>/dev/null || true

# ---- xinetd: 有効化。サンプルサービス bada-info (TCP 7777, 既定は無効) ----
systemctl enable xinetd 2>/dev/null || true
cat > /usr/local/bin/bada-info <<'EOF'
#!/bin/sh
echo "Bada VM Pro OS $(cat /etc/badaos-version 2>/dev/null) on $(hostname) — $(date)"
EOF
chmod 755 /usr/local/bin/bada-info
cat > /etc/xinetd.d/bada-info <<'EOF'
# Bada VM Pro OS のサンプル xinetd サービス (TCP 7777)。
# 使うには disable = no にして `sudo systemctl restart xinetd`
service bada-info
{
    disable     = yes
    type        = UNLISTED
    port        = 7777
    socket_type = stream
    protocol    = tcp
    wait        = no
    user        = nobody
    server      = /usr/local/bin/bada-info
}
EOF
echo "$VERSION" > /etc/badaos-version

# ---- screen: UTF-8 / 日本語で使いやすい既定 ----
cat > /etc/skel/.screenrc <<'EOF'
defutf8 on
defencoding utf8
startup_message off
defscrollback 10000
hardstatus alwayslastline "%{= kw}[Bada VM Pro] %-w%{= Wk}%n %t%{-}%+w %=%Y-%m-%d %c"
EOF

# ---- NAT ルータ: badaos-nat on <外側IF> <内側IF> で IP マスカレード ----
cat > /usr/local/bin/badaos-nat <<'EOF'
#!/bin/sh
# badaos-nat — この PC を NAT ルータにする (内側の PC を外側のネットワークへ出す)
#   sudo badaos-nat on  <外側IF> <内側IF>   例: sudo badaos-nat on enp0s3 enp0s8
#   sudo badaos-nat off <外側IF> <内側IF>
#   sudo badaos-nat share <内側IF>          NetworkManager の「共有」(DHCP+NAT) を内側に設定
#   badaos-nat status
set -e
case "$1" in
  on)  [ -n "$3" ] || { echo "使い方: badaos-nat on <外側IF> <内側IF>"; exit 1; }
       sysctl -qw net.ipv4.ip_forward=1
       iptables -t nat -C POSTROUTING -o "$2" -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o "$2" -j MASQUERADE
       iptables -C FORWARD -i "$3" -o "$2" -j ACCEPT 2>/dev/null || iptables -A FORWARD -i "$3" -o "$2" -j ACCEPT
       iptables -C FORWARD -i "$2" -o "$3" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || \
         iptables -A FORWARD -i "$2" -o "$3" -m state --state RELATED,ESTABLISHED -j ACCEPT
       echo "NAT 有効: $3 → $2" ;;
  off) [ -n "$3" ] || { echo "使い方: badaos-nat off <外側IF> <内側IF>"; exit 1; }
       iptables -t nat -D POSTROUTING -o "$2" -j MASQUERADE 2>/dev/null || true
       iptables -D FORWARD -i "$3" -o "$2" -j ACCEPT 2>/dev/null || true
       iptables -D FORWARD -i "$2" -o "$3" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
       sysctl -qw net.ipv4.ip_forward=0; echo "NAT 無効" ;;
  share) [ -n "$2" ] || { echo "使い方: badaos-nat share <内側IF>"; exit 1; }
       nmcli con add type ethernet ifname "$2" con-name "bada-share-$2" ipv4.method shared ipv6.method ignore
       nmcli con up "bada-share-$2"; echo "$2 に DHCP+NAT 共有を設定しました" ;;
  status|*) echo "ip_forward=$(sysctl -n net.ipv4.ip_forward)"; iptables -t nat -S POSTROUTING 2>/dev/null || true
       nmcli -t -f DEVICE,STATE,CONNECTION dev 2>/dev/null || true ;;
esac
EOF
chmod 755 /usr/local/bin/badaos-nat

# ---- apt: Bada の apt リポジトリが未公開 (404) でも apt update がエラーにならないよう、
#      起動時に到達確認して有効/無効を切り替える。apt update は起動時にはしない
#      (ロックを握って利用者の apt を失敗させないため)。パッケージ索引は ISO に
#      同梱済みなので、起動直後から `sudo apt install <pkg>` が使える ----
cat > /usr/local/sbin/badaos-apt-check <<'EOF'
#!/bin/sh
L=/etc/apt/sources.list.d/bada.list; D=/etc/apt/sources.list.d/bada.list.disabled
F="$L"; [ -f "$F" ] || F="$D"; [ -f "$F" ] || exit 0
URL="$(sed -n 's#^deb \[[^]]*\] \([^ ]*\) \./.*#\1#p' "$F" | head -1)"
if [ -n "$URL" ] && curl -fsIL --max-time 15 "${URL%/}/Packages" >/dev/null 2>&1; then
  [ "$F" = "$D" ] && mv "$D" "$L"
else
  [ "$F" = "$L" ] && mv "$L" "$D"
fi
EOF
chmod 755 /usr/local/sbin/badaos-apt-check
cat > /etc/systemd/system/badaos-apt-check.service <<'EOF'
[Unit]
Description=Bada VM Pro OS: enable/disable the Bada apt repository by reachability
Wants=network-online.target
After=network-online.target
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/badaos-apt-check
TimeoutStartSec=60
[Install]
WantedBy=multi-user.target
EOF
systemctl enable badaos-apt-check.service NetworkManager-wait-online.service 2>/dev/null || true

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
cat > /etc/skel/Desktop/install-badaos-triboot.desktop <<EOF
[Desktop Entry]
Type=Application
Name=トリプルブート導入 (Windows | Bada VM Pro | Linux)
Comment=Windows と Linux の間に Bada VM Pro 専用ブート FAT と OS パーティションを作成 (UEFI / Legacy)
Exec=/usr/local/bin/install-badaos-triboot
Terminal=false
Icon=drive-harddisk
Categories=System;
EOF
cat > /etc/skel/Desktop/printers.desktop <<EOF
[Desktop Entry]
Type=Application
Name=プリンターの設定
Comment=USB / ネットワークプリンターを追加して印刷 (CUPS)
Exec=system-config-printer
Terminal=false
Icon=printer
Categories=Settings;
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
cat > /etc/skel/Desktop/badaos-apps.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Ubuntu アプリを導入
Comment=vim/emacs/LibreOffice/GIMP など人気アプリを apt で簡単導入
Exec=/usr/local/bin/badaos-apps
Terminal=false
Icon=system-software-install
Categories=System;
EOF
cat > /etc/skel/Desktop/vim.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Vim (gvim)
Exec=gvim
Terminal=false
Icon=gvim
Categories=Development;
EOF
cat > /etc/skel/Desktop/emacs.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Emacs
Exec=emacs
Terminal=false
Icon=emacs
Categories=Development;
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

# ---- 要求パッケージの最終確認 (1 つでも欠けたらビルド失敗) ----
REQUIRED="openssh-server xinetd network-manager iptables dnsmasq-base apt
  cups cups-filters cups-browsed avahi-daemon printer-driver-all system-config-printer
  fcitx fcitx-mozc mozc-server fcitx-config-gtk fonts-noto-cjk locales
  screen mlterm mlterm-im-fcitx xterm w9wm lightdm xserver-xorg
  vim vim-gtk3 emacs neovim texlive-full texlive-lang-japanese
  falkon evince mpv pcmanfm mousepad"
MISSING=""
for p in $REQUIRED; do dpkg -s "$p" >/dev/null 2>&1 || MISSING="$MISSING $p"; done
if [ -n "$MISSING" ]; then echo "FATAL: 必須パッケージが入っていません:$MISSING"; exit 1; fi
echo "required packages OK"
for c in sshd xinetd cupsd lp lpstat system-config-printer screen mlterm vim gvim emacs nvim platex uplatex lualatex pdflatex; do
  command -v "$c" >/dev/null 2>&1 || { echo "FATAL: コマンド $c がありません"; exit 1; }
done
echo "required commands OK"

# initramfs を更新 (casper を取り込む)
update-initramfs -u || true

apt-get clean
# /var/lib/apt/lists は消さない: 起動直後 (オフライン含む) から apt install / apt search が使える。
# 古くなったら `sudo apt update`。
echo "setup-inside.sh done (v$VERSION)"
