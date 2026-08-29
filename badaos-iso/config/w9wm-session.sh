#!/bin/sh
# w9wm-session — Bada VM Pro OS の X セッション本体
# lightdm がこのスクリプトを (w9wm.desktop 経由で) 起動する。
[ -f "$HOME/.xsessionrc" ] && . "$HOME/.xsessionrc"
xsetroot -solid "#0b0e14" 2>/dev/null || true

# Bada VM Pro を自動起動 (電子アプリがあればそれ、無ければブラウザで単一HTML)
/usr/local/bin/bada-launcher bada_vm_pro &

# w9wm を最後に exec する (これが終了するとセッション終了)
exec w9wm
