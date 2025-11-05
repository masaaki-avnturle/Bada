#!/bin/sh
# build-win.sh: placeholder to help copy files to Windows or package them
OUT=emacskeys_package.zip
zip -r $OUT emacskeys runner README.txt mymap.json || true
echo "Created $OUT (transfer to Windows and unzip)"
