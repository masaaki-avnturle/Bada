/*
 * build-iso.js — Bada VM Pro ライブ CD (ISO 9660 + El Torito) を生成
 *   node bada_vm_pro/tools/build-iso.js  →  bada_vm_pro/dist/BadaVMPro-live.iso
 *
 * 中身:
 *   INDEX.HTM   … Bada VM Pro OS 本体 (w9wm デスクトップ、完全自己完結)
 *   README.TXT  … 使い方 (ブラウザで INDEX.HTM を開く / VM Pro でマウント)
 *   AUTORUN.INF … Windows でディスクを開いたときの表示名
 *   LICENSE.TXT … MIT ライセンス
 * ブートすると BIOS テキストでバナーを表示します (El Torito no-emulation)。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { buildIso } = require("./iso9660.js");

const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"));
let license = "MIT License — see https://github.com/masaaki-avnturle/Bada\n";
try { license = fs.readFileSync(path.join(root, "..", "LICENSE"), "utf8"); } catch (e){}

const readme = [
  "Bada VM Pro Live CD",
  "===================",
  "",
  "このディスクには量子 Bada 言語 OS「Bada VM Pro」(w9wm デスクトップ版) が",
  "丸ごと入っています。使い方は 2 通り:",
  "",
  "1. どの OS でも: このディスクの INDEX.HTM をウェブブラウザで開く",
  "   (それだけで w9wm デスクトップ + bash/apt/vim/emacs/ssh/xinetd/",
  "    texlive-full/screen/fcitx-mozc プリインストールの OS が起動します)",
  "",
  "2. Bada VM Pro アプリの中で: アプリメニュー →「ISO をマウント」で",
  "   この ISO を選ぶと /mnt/cdrom に中身がマウントされ、ターミナルから",
  "   ls /mnt/cdrom / cat /mnt/cdrom/README.TXT で読めます",
  "",
  "CD から直接ブートすると BIOS テキストの案内バナーを表示します。",
  "ネイティブ版 (APK / Windows EXE / Ubuntu AppImage・deb) は",
  "https://github.com/masaaki-avnturle/Bada の Releases / Actions から。",
  ""
].join("\r\n");

const autorun = [
  "[autorun]",
  "label=Bada VM Pro Live CD",
  "action=Open INDEX.HTM in your browser to boot the OS",
  ""
].join("\r\n");

const iso = buildIso({
  volumeId: "BADAVMPRO_LIVE",
  files: [
    { name: "index.htm", data: new Uint8Array(html) },
    { name: "readme.txt", data: readme },
    { name: "autorun.inf", data: autorun },
    { name: "license.txt", data: license }
  ]
});

const outDir = path.join(root, "dist");
fs.mkdirSync(outDir, { recursive: true });
const out = path.join(outDir, "BadaVMPro-live.iso");
fs.writeFileSync(out, iso);
console.log("wrote " + out + " (" + iso.length + " bytes, " + (iso.length / 2048) + " sectors)");
