#!/bin/sh
# bada-launcher <app>  — Bada アプリを起動する
#   1. .deb で入った Electron 版 (/opt/BadaVMPro/bada-vm-pro など) を探して起動
#   2. 無ければ Chromium 系ブラウザで /opt/bada/<app>/index.html を --app 表示
#   3. それも無ければ、位置を指定した xterm で案内を出す
#      (位置を指定しないと素の w9wm では手で枠を引くまで止まるため。
#       この ISO の w9wm は自動配置パッチ済みだが念のため)
APP="${1:-bada_vm_pro}"

case "$APP" in
  bada_vm_pro) CANDS="bada-vm-pro badavmpro /opt/BadaVMPro/bada-vm-pro" ;;
  laevateinn)  CANDS="laevateinn /opt/Laevateinn/laevateinn" ;;
  *)           CANDS="$APP" ;;
esac

for B in $CANDS; do
  if command -v "$B" >/dev/null 2>&1 || [ -x "$B" ]; then
    # --no-sandbox: ライブ環境/古いカーネルでも chrome-sandbox で止まらないように
    exec "$B" --no-sandbox
  fi
done

HTML="/opt/bada/$APP/index.html"
[ -f "$HTML" ] || HTML="/opt/bada/zone-browser.html"
for C in chromium-browser chromium google-chrome falkon; do
  if command -v "$C" >/dev/null 2>&1; then
    case "$C" in falkon) exec "$C" "file://$HTML" ;; *) exec "$C" --no-sandbox --app="file://$HTML" ;; esac
  fi
done

exec xterm -geometry 70x6+120+120 -T "Bada VM Pro" -e sh -c \
  "echo 'Bada VM Pro アプリ ($APP) が見つかりません。'; echo 'sudo apt install bada-vm-pro か、ブラウザ (sudo apt install falkon) を入れてください。'; sleep 15"
