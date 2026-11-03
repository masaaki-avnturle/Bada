#!/bin/sh
# install-badaos-triboot — Windows / Bada VM Pro / Linux トリプルブートのウィザードを root 起動。
xhost +si:localuser:root >/dev/null 2>&1 || true
sudo -E env LANG=ja_JP.UTF-8 LANGUAGE=ja_JP:ja /usr/local/bin/badaos-triboot-installer
xhost -si:localuser:root >/dev/null 2>&1 || true
