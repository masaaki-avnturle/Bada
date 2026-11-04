#!/bin/sh
# w9wm-session — Bada VM Pro OS の X セッション本体
# lightdm がこのスクリプトを (badaos-w9wm.desktop 経由で) 起動する。

# 日本語環境 + 入力メソッド (fcitx-mozc) を読み込む
export LANG=ja_JP.UTF-8
export LANGUAGE=ja_JP:ja
export LC_ALL=ja_JP.UTF-8
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
[ -f "$HOME/.xprofile" ]   && . "$HOME/.xprofile"
[ -f "$HOME/.xsessionrc" ] && . "$HOME/.xsessionrc"
xsetroot -solid "#0b0e14" 2>/dev/null || true
# 日本語 106/109 キーボード配列 (念のためセッションでも設定)
setxkbmap -model jp106 -layout jp 2>/dev/null || true
# ネットワークのアイコン (有線/Wi-Fi の接続・NAT/DHCP 状態)
command -v nm-applet >/dev/null 2>&1 && (nm-applet >/dev/null 2>&1 &)

# 日本語入力 fcitx (mozc) を起動 — .xprofile 未起動時の保険
if command -v fcitx-autostart >/dev/null 2>&1; then fcitx-autostart >/dev/null 2>&1 &
elif command -v fcitx >/dev/null 2>&1; then fcitx -d >/dev/null 2>&1 & fi

# 端末を1枚開いておく (mlterm 優先、無ければ xterm)。ここから各コマンドを実行。
HINT='echo; echo "=== Bada VM Pro OS ライブ環境 (日本語) ==="; \
echo "実ディスクへインストール (Calamares/日本語): install-badaos"; \
echo "パーティションマネージャ (GParted):          badaos-partition"; \
echo "かんたんインストール (ウィザード):           install-badaos-simple"; \
echo "トリプルブート (Win|BadaVMPro|Linux):         install-badaos-triboot"; \
echo "Ubuntu アプリを簡単導入 (GUI):               badaos-apps"; \
echo "追加ソフト (apt):                            badaos-extras ssh xinetd screen texlive"; \
echo "  (または sudo apt update && sudo apt install openssh-server xinetd screen texlive-full)"; \
echo "ネットワーク (有線/Wi-Fi):                   nmtui  /  nm-connection-editor  (NAT/DHCP は自動)"; \
echo "NAT ルータ:                                  sudo badaos-nat on <外側IF> <内側IF> / share <内側IF>"; \
echo "プリンター:                                  system-config-printer (または http://localhost:631)"; \
echo "エディタ:                                    vim / gvim / emacs"; \
echo "日本語入力の設定 (fcitx):                    fcitx-configtool"; \
echo "アプリ再起動:                                bada-launcher bada_vm_pro"; \
echo "Ubuntu アプリ導入例:                         sudo apt update && sudo apt install <pkg>"; \
echo "日本語入力の ON/OFF: Ctrl+Space"; echo; exec bash'
if command -v mlterm >/dev/null 2>&1; then
  (mlterm -g 104x30+20+20 -T "Bada VM Pro OS — mlterm" -e sh -c "$HINT" &) 2>/dev/null || true
else
  (xterm -fa "DejaVu Sans Mono" -fd "Noto Sans Mono CJK JP" -fs 12 -geometry 100x30+20+20 \
     -T "Bada VM Pro OS — terminal" -e sh -c "$HINT" &) 2>/dev/null || true
fi

# GRUB で「トリプルブート導入」を選んだ時はウィザードを自動起動
if grep -qw "badaos.triboot=1" /proc/cmdline 2>/dev/null; then
  (sleep 3; /usr/local/bin/install-badaos-triboot) &
fi

# Bada VM Pro を自動起動 (電子アプリがあればそれ、無ければブラウザで単一HTML)
#   インストール用に起動した時は、インストーラの上に大きなアプリ画面を重ねない
if ! grep -qw "badaos.triboot=1" /proc/cmdline 2>/dev/null; then
  /usr/local/bin/bada-launcher bada_vm_pro &
fi

# w9wm を最後に exec する (これが終了するとセッション終了)
exec w9wm
