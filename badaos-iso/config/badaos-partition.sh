#!/bin/sh
# badaos-partition — パーティションマネージャ GParted を日本語で root 起動。
# 使いたいハードディスクを初期化・パーティション作成・フォーマットできる。
xhost +si:localuser:root >/dev/null 2>&1 || true
if command -v gparted >/dev/null 2>&1; then
  sudo -E env LANG=ja_JP.UTF-8 LANGUAGE=ja_JP:ja gparted
else
  ( command -v zenity >/dev/null 2>&1 && zenity --error --width=420 \
      --text="gparted が見つかりません。'sudo apt install gparted' で導入できます。" ) || true
fi
xhost -si:localuser:root >/dev/null 2>&1 || true
