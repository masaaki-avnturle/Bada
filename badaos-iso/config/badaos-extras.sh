#!/bin/bash
# =============================================================================
# badaos-extras — ISO には入れていない「追加ソフト」を apt で後から導入する
#
#   ISO は必要最小限 (日本語・w9wm・NAT・印刷・vim・emacs・apt) なので、
#   次のものは必要になった時にここ (または sudo apt install ...) で入れる:
#
#     名前      apt パッケージ
#     mlterm    mlterm mlterm-im-fcitx      (日本語端末 + fcitx-mozc 入力プラグイン)
#     ssh       openssh-server              (ssh サーバ。導入後すぐ起動)
#     xinetd    xinetd                      (スーパーサーバ)
#     screen    screen                      (端末多重化。~/.screenrc は UTF-8 設定済み)
#     texlive   texlive-full                (日本語 platex/uplatex/lualatex 含む全部。数 GB)
#
#   使い方:  badaos-extras                 … GUI (チェックリスト) で選ぶ
#            badaos-extras mlterm ssh      … 名前を指定して端末から導入
#   NAT/DHCP で Ubuntu のミラーに出られれば、そのまま apt で取得する。
# =============================================================================
set -u

pkgs_of(){
  case "$1" in
    mlterm)  echo "mlterm mlterm-im-fcitx" ;;
    ssh)     echo "openssh-server" ;;
    xinetd)  echo "xinetd" ;;
    screen)  echo "screen" ;;
    texlive) echo "texlive-full" ;;
    *)       echo "" ;;
  esac; }

NAMES="$*"
if [ -z "$NAMES" ]; then
  if [ -n "${DISPLAY:-}" ] && command -v zenity >/dev/null 2>&1; then
    NAMES="$(zenity --list --checklist --width=680 --height=380 \
      --title="Bada VM Pro OS — 追加ソフトを導入 (apt)" \
      --text="導入するものにチェックを入れてください (NAT/DHCP 経由で apt が取得します)" \
      --column="選択" --column="名前" --column="内容" \
      FALSE mlterm  "mlterm 日本語端末 (+ fcitx-mozc 入力プラグイン)" \
      FALSE ssh     "ssh サーバ (openssh-server)" \
      FALSE xinetd  "xinetd スーパーサーバ" \
      FALSE screen  "screen 端末多重化" \
      FALSE texlive "texlive-full (日本語 TeX 一式。数 GB・時間がかかります)" \
      --separator=' ')" || exit 0
  else
    echo "使い方: badaos-extras <mlterm|ssh|xinetd|screen|texlive> ..."; exit 1
  fi
fi
[ -n "$NAMES" ] || exit 0

PKGS=""
for n in $NAMES; do
  p="$(pkgs_of "$n")"
  [ -n "$p" ] || { echo "不明な名前: $n (mlterm / ssh / xinetd / screen / texlive)"; exit 1; }
  PKGS="$PKGS $p"
done

run(){
  echo "== sudo apt-get update"
  sudo apt-get update || return 1
  echo "== sudo apt-get install$PKGS"
  # shellcheck disable=SC2086
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y $PKGS || return 1
  case " $PKGS " in *" openssh-server "*) sudo systemctl enable --now ssh ;; esac
  case " $PKGS " in *" xinetd "*) sudo systemctl enable --now xinetd ;; esac
  echo "== 完了:$PKGS"
}

if [ -n "${DISPLAY:-}" ] && [ -t 0 ] ; then
  run
elif [ -n "${DISPLAY:-}" ] && command -v xterm >/dev/null 2>&1; then
  # GUI から起動された時は xterm を開いて進捗とパスワード入力を見せる
  export PKGS
  exec xterm -T "追加ソフトを導入" -e bash -c "$(declare -f run); run; echo; read -r -p 'Enter で閉じる' _"
else
  run
fi
