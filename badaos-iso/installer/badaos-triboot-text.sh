#!/bin/bash
# =============================================================================
# badaos-triboot-text — 画面 (GUI) が出ない PC 向けの「文字だけ」トリプルブート導入
#   GRUB の「テキストモード」で起動 → ユーザー bada (パスワードなし) でログイン →
#   sudo badaos-triboot-text
#   中身は GUI 版と同じ badaos-triboot-core.sh (Windows と Linux の真ん中に
#   BADAVMBOOT(FAT) + BADAVMPRO を作り、MBR は書き換えない)。
# =============================================================================
CORE=/usr/local/lib/badaos/badaos-triboot-core.sh
[ "$(id -u)" = 0 ] || exec sudo "$0" "$@"

echo "=== Bada VM Pro トリプルブート導入 (テキスト版) ==="
echo "Windows と Linux が入っているディスクを選んでください:"
lsblk -dn -o NAME,SIZE,MODEL -e 7,11 | nl -w2 -s') '
read -r -p "番号: " n
DISK="/dev/$(lsblk -dn -o NAME -e 7,11 | sed -n "${n}p")"
[ -b "$DISK" ] || { echo "ディスクが選ばれていません"; exit 1; }
read -r -p "Bada VM Pro に使う大きさ GiB (空欄 = 間の空き全部): " SIZE
SIZE="${SIZE//[^0-9]/}"; SIZE="${SIZE:-0}"

SHRINK=0
if ! TARGET_DISK="$DISK" BADA_SIZE_GB="$SIZE" PLAN_ONLY=1 bash "$CORE"; then
  read -r -p "空きが無い場合: Windows の末尾を縮小して作りますか? [y/N] " a
  [ "$a" = y ] || exit 1
  SHRINK=1
  TARGET_DISK="$DISK" BADA_SIZE_GB="$SIZE" SHRINK_WINDOWS=1 PLAN_ONLY=1 bash "$CORE" || exit 1
fi
read -r -p "ホスト名 [badaos]: " HOST
read -r -p "ユーザー名 [bada]: " USER_NAME
read -r -s -p "パスワード: " PASS; echo
read -r -p "上の計画でインストールします。よろしいですか? [yes と入力] " ok
[ "$ok" = yes ] || { echo "中止しました"; exit 1; }

TARGET_DISK="$DISK" BADA_SIZE_GB="$SIZE" SHRINK_WINDOWS="$SHRINK" \
NEW_HOST="${HOST:-badaos}" NEW_USER="${USER_NAME:-bada}" NEW_PASS="${PASS:-bada}" \
  bash "$CORE" 2>&1 | grep --line-buffered -v '^[0-9]*$' | sed -u 's/^# /→ /'
rc=${PIPESTATUS[0]}
if [ "$rc" = 0 ]; then echo "完了しました。USB を抜いて再起動してください (sudo reboot)"; else echo "失敗しました (終了コード $rc)"; fi
exit "$rc"
