#!/bin/bash
# =============================================================================
# badaos-installer.sh — Bada VM Pro OS の GUI インストーラ (zenity ウィザード)
#   install-badaos ランチャから root で起動される。
#   ディスク選択 → アカウント設定 → 確認 → 進捗表示 → 完了/再起動。
# =============================================================================
export DISPLAY="${DISPLAY:-:0}"
CORE="/usr/local/lib/badaos/badaos-install-core.sh"
LOG="/tmp/badaos-install.log"
TITLE="Bada VM Pro OS インストーラ"

# zenity が無ければ端末で通知して終了
command -v zenity >/dev/null 2>&1 || { xmessage -center "zenity が見つかりません" 2>/dev/null; exit 1; }

Z(){ zenity --window-icon=info "$@"; }

# ── 1. ようこそ ────────────────────────────────────────────────
Z --info --width=520 --title="$TITLE" \
  --text="<span size='xx-large' foreground='#c8a44a'><b>Bada VM Pro OS</b></span>\n\n量子 Bada 言語の OS を、この PC の<b>実ディスク</b>にインストールします。\n\n• ウィンドウマネージャ: w9wm\n• アプリ同梱: Bada VM Pro / Laevateinn\n• ネットワーク: NAT/DHCP + apt\n\n⚠ <b>選択したディスクの内容はすべて消去されます。</b>\n続けるには「OK」を押してください。" \
  --ok-label="次へ" || exit 0

# ── 2. インストール先ディスクの選択 ───────────────────────────
# 実ディスク (loop/CD を除外) を列挙し、ラジオリストにする
declare -a ROWS=()
while read -r name size model; do
  [ -n "$name" ] || continue
  ROWS+=( FALSE "/dev/$name" "$size" "${model:-(不明)}" )
done < <(lsblk -dn -o NAME,SIZE,MODEL -e 7,11 2>/dev/null)

[ ${#ROWS[@]} -gt 0 ] || { Z --error --title="$TITLE" --width=460 \
  --text="インストール可能なディスクが見つかりません。"; exit 1; }

DISK="$(Z --list --radiolist --title="$TITLE — インストール先" --width=560 --height=340 \
  --text="Bada VM Pro OS をインストールするディスクを選んでください（全消去されます）:" \
  --column="選択" --column="デバイス" --column="容量" --column="モデル" \
  "${ROWS[@]}")" || exit 0
[ -n "$DISK" ] || { Z --error --title="$TITLE" --width=420 --text="ディスクが選択されていません。"; exit 1; }

# ── 3. アカウント / ホスト名 ──────────────────────────────────
FORM="$(Z --forms --title="$TITLE — アカウント設定" --width=480 \
  --text="ログインアカウントとホスト名を設定します。" \
  --separator="|" \
  --add-entry="ホスト名 (既定: badaos)" \
  --add-entry="ユーザー名 (既定: bada)" \
  --add-password="パスワード" \
  --add-password="パスワード(確認)")" || exit 0

HOST="$(echo "$FORM" | cut -d'|' -f1)"
USER_NAME="$(echo "$FORM" | cut -d'|' -f2)"
PASS="$(echo "$FORM" | cut -d'|' -f3)"
PASS2="$(echo "$FORM" | cut -d'|' -f4)"
HOST="${HOST:-badaos}"
USER_NAME="${USER_NAME:-bada}"
PASS="${PASS:-bada}"; PASS2="${PASS2:-$PASS}"
if [ "$PASS" != "$PASS2" ]; then
  Z --error --title="$TITLE" --width=420 --text="パスワードが一致しません。最初からやり直してください。"
  exit 1
fi

# ── 4. 最終確認 ───────────────────────────────────────────────
Z --question --width=520 --title="$TITLE — 最終確認" --ok-label="インストール開始" --cancel-label="やめる" \
  --text="次の内容でインストールします:\n\n• ディスク: <b>${DISK}</b> （<b>全データ消去</b>）\n• ホスト名: <b>${HOST}</b>\n• ユーザー: <b>${USER_NAME}</b>\n\n本当に実行してよろしいですか?" || exit 0

# ── 5. インストール実行 (進捗バー) ────────────────────────────
: > "$LOG"
TARGET_DISK="$DISK" NEW_HOST="$HOST" NEW_USER="$USER_NAME" NEW_PASS="$PASS" \
  bash "$CORE" 2>>"$LOG" \
| Z --progress --title="$TITLE — インストール中" --width=560 --auto-close --no-cancel \
    --percentage=0 --text="準備しています…"
RC=${PIPESTATUS[0]}

# ── 6. 結果 ───────────────────────────────────────────────────
if [ "$RC" = "0" ]; then
  if Z --question --width=480 --title="$TITLE — 完了" --ok-label="今すぐ再起動" --cancel-label="あとで" \
      --text="✅ インストールが完了しました。\n\nUSB を抜いてから再起動してください。今すぐ再起動しますか?"; then
    reboot
  fi
else
  Z --error --width=620 --height=360 --title="$TITLE — エラー" \
    --text="インストールに失敗しました。ログの末尾:\n\n<tt>$(tail -n 18 "$LOG" | sed 's/&/\&amp;/g; s/</\&lt;/g')</tt>\n\n全文: ${LOG}"
fi
