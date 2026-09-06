#!/bin/sh
# install-badaos-simple — 自作 zenity ウィザード (Calamares の代替) を root 起動。
xhost +si:localuser:root >/dev/null 2>&1 || true
sudo -E env LANG=ja_JP.UTF-8 LANGUAGE=ja_JP:ja /usr/local/bin/badaos-installer
xhost -si:localuser:root >/dev/null 2>&1 || true
