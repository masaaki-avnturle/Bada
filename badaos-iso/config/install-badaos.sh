#!/bin/sh
# install-badaos — w9wm 上から Calamares インストーラを root で起動する。
# w9wm には polkit エージェントが無いため pkexec は使わず、casper の
# ライブユーザ (bada, パスワード無し sudo 可) から sudo で立ち上げる。
# root が X に接続できるよう xhost を一時的に許可する。
xhost +si:localuser:root >/dev/null 2>&1 || true
if command -v calamares >/dev/null 2>&1; then
  sudo -E calamares -d 2>&1 | tee /tmp/calamares.log
  RC=${PIPESTATUS:-$?}
  xhost -si:localuser:root >/dev/null 2>&1 || true
  if [ "${RC:-0}" != "0" ]; then
    xmessage -center "インストーラでエラーが発生しました。詳細は /tmp/calamares.log を参照してください。" 2>/dev/null \
      || xterm -e "echo 'Calamares error. See /tmp/calamares.log'; tail -n 40 /tmp/calamares.log; sleep 20" 2>/dev/null || true
  fi
else
  xmessage -center "calamares が見つかりません" 2>/dev/null \
    || xterm -e "echo 'calamares not installed'; sleep 10" || true
fi
