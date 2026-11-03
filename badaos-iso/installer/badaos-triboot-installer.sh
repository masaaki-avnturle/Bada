#!/bin/bash
# =============================================================================
# badaos-triboot-installer.sh — Windows / Bada VM Pro / Linux トリプルブート
#   の GUI ウィザード (zenity)。install-badaos-triboot ランチャから root で起動。
#   ディスク選択 → 計画の確認 (PLAN_ONLY) → アカウント → 実行 → 再起動。
# =============================================================================
export DISPLAY="${DISPLAY:-:0}"
CORE="/usr/local/lib/badaos/badaos-triboot-core.sh"
LOG="/tmp/badaos-triboot.log"
TITLE="Bada VM Pro トリプルブート インストーラ"
command -v zenity >/dev/null 2>&1 || { xmessage -center "zenity が見つかりません" 2>/dev/null; exit 1; }
Z(){ zenity --window-icon=info "$@"; }

Z --info --width=600 --title="$TITLE" --ok-label="次へ" \
  --text="<span size='xx-large' foreground='#c8a44a'><b>Bada VM Pro トリプルブート</b></span>\n\n<tt>[ Windows ][ ★BADAVMBOOT (FAT)★ ][ ★BADAVMPRO (OS)★ ][ Linux ]</tt>\n\n• Windows の<b>下</b>に Bada VM Pro <b>専用ブートローダの FAT パーティション</b>を作り、\n  その下の空き領域に <b>Bada VM Pro OS</b> をインストールします (Linux との間)\n• Windows の起動パーティションは変更しません\n• <b>UEFI / Legacy BIOS</b> どちらでも、起動メニューで <b>Bada VM Pro / Windows / Linux</b> を選べます\n• 既存の Windows / Linux は消しません\n\n⚠ 事前に Windows の<b>高速スタートアップを無効</b>にし、BitLocker を一時停止し、\n  大切なデータはバックアップしてください。" || exit 0

declare -a ROWS=()
while read -r name size model; do
  [ -n "$name" ] && ROWS+=( FALSE "/dev/$name" "$size" "${model:-(不明)}" )
done < <(lsblk -dn -o NAME,SIZE,MODEL -e 7,11 2>/dev/null)
[ ${#ROWS[@]} -gt 0 ] || { Z --error --title="$TITLE" --text="ディスクが見つかりません。"; exit 1; }
DISK="$(Z --list --radiolist --title="$TITLE — ディスク" --width=600 --height=340 \
  --text="Windows と Linux が入っているディスクを選んでください:" \
  --column="選択" --column="デバイス" --column="容量" --column="モデル" "${ROWS[@]}")" || exit 0
[ -n "$DISK" ] || exit 1

SIZE="$(Z --entry --title="$TITLE — サイズ" --width=520 \
  --text="Bada VM Pro に使う大きさ (GiB, ブート FAT 512MiB 込み)。空欄 = Windows と Linux の間の空きを全部使う:" \
  --entry-text="")" || exit 0
SIZE="${SIZE//[^0-9]/}"; SIZE="${SIZE:-0}"

SHRINK=0
PLAN="$(TARGET_DISK="$DISK" BADA_SIZE_GB="$SIZE" PLAN_ONLY=1 bash "$CORE" 2>&1)"; RC=$?
if [ $RC != 0 ] && echo "$PLAN" | grep -q "空きがありません"; then
  if Z --question --width=640 --title="$TITLE — 空きがありません" --ok-label="Windows を縮小して作る" --cancel-label="やめる" \
      --text="<tt>$(echo "$PLAN" | tail -3 | sed 's/&/\&amp;/g; s/</\&lt;/g')</tt>\n\nWindows (NTFS) の末尾を縮小して、Windows と Linux の間に空きを作りますか?\n(既定 40GiB / 先ほど指定したサイズ)"; then
    SHRINK=1
    PLAN="$(TARGET_DISK="$DISK" BADA_SIZE_GB="$SIZE" SHRINK_WINDOWS=1 PLAN_ONLY=1 bash "$CORE" 2>&1)"; RC=$?
  else exit 0; fi
fi
if [ $RC != 0 ]; then
  Z --error --width=680 --title="$TITLE — 計画できません" --text="<tt>$(echo "$PLAN" | sed 's/&/\&amp;/g; s/</\&lt;/g')</tt>"; exit 1
fi
Z --question --width=720 --title="$TITLE — 計画の確認" --ok-label="この計画で続ける" --cancel-label="やめる" \
  --text="<tt>$(echo "$PLAN" | grep -v PLAN_ONLY | sed 's/&/\&amp;/g; s/</\&lt;/g')</tt>" || exit 0

FORM="$(Z --forms --title="$TITLE — アカウント" --width=480 --separator="|" \
  --add-entry="ホスト名 (既定: badaos)" --add-entry="ユーザー名 (既定: bada)" \
  --add-password="パスワード" --add-password="パスワード(確認)")" || exit 0
IFS='|' read -r HOST USER_NAME PASS PASS2 <<< "$FORM"
PASS="${PASS:-bada}"; PASS2="${PASS2:-$PASS}"
[ "$PASS" = "$PASS2" ] || { Z --error --title="$TITLE" --text="パスワードが一致しません。"; exit 1; }

Z --question --width=520 --title="$TITLE — 最終確認" --ok-label="インストール開始" --cancel-label="やめる" \
  --text="${DISK} にトリプルブート構成で Bada VM Pro をインストールします。\n$( [ $SHRINK = 1 ] && echo '<b>Windows を縮小します。</b>')\n本当に実行してよろしいですか?" || exit 0

: > "$LOG"
TARGET_DISK="$DISK" BADA_SIZE_GB="$SIZE" SHRINK_WINDOWS="$SHRINK" \
NEW_HOST="${HOST:-badaos}" NEW_USER="${USER_NAME:-bada}" NEW_PASS="$PASS" \
  bash "$CORE" 2>>"$LOG" \
| Z --progress --title="$TITLE — インストール中" --width=560 --auto-close --no-cancel --percentage=0 --text="準備しています…"
RC=${PIPESTATUS[0]}
if [ "$RC" = "0" ]; then
  Z --question --width=520 --title="$TITLE — 完了" --ok-label="今すぐ再起動" --cancel-label="あとで" \
    --text="✅ 完了しました。\n\n再起動すると起動メニュー <b>Bada VM Pro</b> から\nBada VM Pro / Windows / Linux を選べます。" && reboot
else
  Z --error --width=640 --height=360 --title="$TITLE — エラー" \
    --text="失敗しました。ログの末尾:\n\n<tt>$(tail -n 18 "$LOG" | sed 's/&/\&amp;/g; s/</\&lt;/g')</tt>\n\n全文: ${LOG}"
fi
