#!/bin/sh
# bada-launcher <app>  — Bada アプリを起動する
#   まず同名の電子アプリ(.deb でインストール済み)を探し、
#   無ければ Chromium で /opt/bada/<app>/index.html を --app 表示する。
APP="${1:-bada_vm_pro}"

# 電子アプリのコマンド候補
case "$APP" in
  bada_vm_pro) BIN="badavmpro" ;;
  laevateinn)  BIN="laevateinn" ;;
  *)           BIN="$APP" ;;
esac

if command -v "$BIN" >/dev/null 2>&1; then
  exec "$BIN"
fi

# フォールバック: 単一 HTML を Chromium の app モードで
HTML="/opt/bada/$APP/index.html"
[ -f "$HTML" ] || HTML="/opt/bada/zone-browser.html"
for C in chromium-browser chromium google-chrome; do
  if command -v "$C" >/dev/null 2>&1; then
    exec "$C" --no-sandbox --app="file://$HTML"
  fi
done

# 最後の手段: xdg-open / xterm 通知
xdg-open "file://$HTML" 2>/dev/null || xterm -e "echo 'Bada app not found: $APP'; sleep 5"
