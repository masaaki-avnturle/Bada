#!/bin/sh
# install-badaos — w9wm 上から Bada VM Pro OS の GUI インストーラを root で起動。
# w9wm には polkit エージェントが無いため、casper のライブユーザ (bada,
# パスワード無し sudo 可) から sudo で立ち上げ、root が X に接続できるよう
# xhost を一時的に許可する。
xhost +si:localuser:root >/dev/null 2>&1 || true
sudo -E /usr/local/bin/badaos-installer
xhost -si:localuser:root >/dev/null 2>&1 || true
