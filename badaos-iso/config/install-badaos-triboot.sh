#!/bin/sh
# install-badaos-triboot — Windows / Bada VM Pro / Linux トリプルブートのウィザードを root 起動。
xhost +si:localuser:root >/dev/null 2>&1 || true
# Ubuntu 風 GUI インストーラ (GTK)。python3-gi が無い時だけ zenity 版を使う
if python3 -c 'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk' 2>/dev/null; then
  sudo -E env LANG=ja_JP.UTF-8 LANGUAGE=ja_JP:ja /usr/local/bin/badaos-installer-gtk
else
  sudo -E env LANG=ja_JP.UTF-8 LANGUAGE=ja_JP:ja /usr/local/bin/badaos-triboot-installer
fi
xhost -si:localuser:root >/dev/null 2>&1 || true
