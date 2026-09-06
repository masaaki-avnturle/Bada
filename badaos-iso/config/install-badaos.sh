#!/bin/sh
# install-badaos — w9wm 上から Calamares インストーラを「日本語 UI」で root 起動。
# w9wm には polkit エージェントが無いため sudo で立ち上げ、root が X に接続
# できるよう xhost を一時許可する。Calamares が無い/失敗した場合は簡易
# ウィザード (install-badaos-simple) にフォールバックできる。
xhost +si:localuser:root >/dev/null 2>&1 || true
rc=0
if command -v calamares >/dev/null 2>&1; then
  sudo -E env LANG=ja_JP.UTF-8 LANGUAGE=ja_JP:ja LC_ALL=ja_JP.UTF-8 calamares -d >/tmp/calamares.log 2>&1
  rc=$?
  if [ "$rc" != "0" ]; then
    if command -v zenity >/dev/null 2>&1; then
      zenity --question --width=560 --title="インストーラ" \
        --ok-label="かんたんインストールを使う" --cancel-label="閉じる" \
        --text="Calamares でエラーが発生しました (詳細: /tmp/calamares.log)。\n代わりの GUI インストーラ（ウィザード）を使いますか?" \
        && /usr/local/bin/install-badaos-simple
    else
      /usr/local/bin/install-badaos-simple
    fi
  fi
else
  /usr/local/bin/install-badaos-simple
fi
xhost -si:localuser:root >/dev/null 2>&1 || true
