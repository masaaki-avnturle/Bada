#!/usr/bin/env node
/*
 * gen-config.js — apps/apps.json からビルド用設定を生成するヘルパー
 *
 * 使い方 (リポジトリのルートで実行):
 *   node apps/tools/gen-config.js list             # アプリ id 一覧 (1 行 1 id)
 *   node apps/tools/gen-config.js version          # マニフェストのバージョン
 *   node apps/tools/gen-config.js check            # 各アプリの src/index.html を検証
 *   node apps/tools/gen-config.js appjson <id>     # Electron ラッパー用 app.json を stdout へ
 *   node apps/tools/gen-config.js cordova <id>     # Cordova 用 config.xml を stdout へ
 *   node apps/tools/gen-config.js env <id>         # BADA_* 環境変数 (GITHUB_ENV 形式) を stdout へ
 *   node apps/tools/gen-config.js notes            # Release 本文 (Markdown) を stdout へ
 */
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..", "..");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "apps", "apps.json"), "utf8"));

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&apos;");
}

function findApp(id) {
  const a = manifest.apps.find((x) => x.id === id);
  if (!a) { console.error("unknown app id: " + id); process.exit(1); }
  return a;
}

const mode = process.argv[2];
const id = process.argv[3];

switch (mode) {
  case "list":
    for (const a of manifest.apps) console.log(a.id);
    break;

  case "version":
    console.log(manifest.version);
    break;

  case "check": {
    let ok = true;
    for (const a of manifest.apps) {
      const idx = path.join(root, a.src, "index.html");
      if (!fs.existsSync(idx)) { console.error("MISSING: " + a.id + " -> " + a.src + "/index.html"); ok = false; }
      else console.log("ok: " + a.id.padEnd(24) + " " + a.src);
      for (const k of ["id", "product", "name", "src", "summary", "category"]) {
        if (!a[k]) { console.error("MISSING FIELD '" + k + "' in " + JSON.stringify(a.id)); ok = false; }
      }
      if (!/^[a-z][a-z0-9_]*$/.test(a.id)) { console.error("BAD ID (must be [a-z][a-z0-9_]*): " + a.id); ok = false; }
    }
    if (!ok) process.exit(1);
    console.log("manifest OK: " + manifest.apps.length + " apps, version " + manifest.version);
    break;
  }

  case "appjson": {
    const a = findApp(id);
    const w = a.window || {};
    process.stdout.write(JSON.stringify({
      title: a.name,
      width: w.width || 1100,
      height: w.height || 780,
      background: w.background || "#04060a"
    }, null, 2) + "\n");
    break;
  }

  case "cordova": {
    const a = findApp(id);
    process.stdout.write(`<?xml version='1.0' encoding='utf-8'?>
<widget id="io.github.masaaki_avnturle.${a.id}" version="${esc(manifest.version)}"
        xmlns="http://www.w3.org/ns/widgets" xmlns:cdv="http://cordova.apache.org/ns/1.0">
  <name>${esc(a.name)}</name>
  <description>${esc(a.summary)}</description>
  <author email="masaaki.tabu4@gmail.com" href="https://github.com/masaaki-avnturle/Bada">Masaaki Yamaguchi</author>
  <content src="index.html" />
  <allow-intent href="http://*/*" />
  <allow-intent href="https://*/*" />
  <preference name="BackgroundColor" value="0xff04060a" />
  <preference name="android-minSdkVersion" value="24" />
  <preference name="AndroidWindowSplashScreenBackgroundColor" value="#04060a" />
  <preference name="Orientation" value="default" />
  <platform name="android">
    <preference name="AndroidXEnabled" value="true" />
  </platform>
</widget>
`);
    break;
  }

  case "env": {
    const a = findApp(id);
    process.stdout.write(
      "BADA_APP_ID=" + a.id + "\n" +
      "BADA_PRODUCT=" + a.product + "\n" +
      "BADA_VERSION=" + manifest.version + "\n" +
      "BADA_CATEGORY=" + a.category + "\n" +
      "BADA_SRC=" + a.src + "\n"
    );
    break;
  }

  case "notes": {
    const v = manifest.version;
    let s = "# Ω apps — 全アプリ ネイティブ版 v" + v + "\n\n";
    s += "各アプリの Android APK / Windows 10・11 EXE / Ubuntu AppImage+deb を同梱しています。\n";
    s += "いずれも概念シミュレーション/アート・非医療です。\n\n";
    s += "| アプリ | Android | Windows 10/11 | Ubuntu |\n|:---|:---|:---|:---|\n";
    for (const a of manifest.apps) {
      s += `| **${a.name}** — ${a.summary} | \`${a.id}-debug.apk\` | \`${a.product}-${v}-x64.exe\` (インストーラ) / \`${a.product}-${v}-portable.exe\` | \`${a.product}-${v}-x86_64.AppImage\` / \`${a.product}-${v}-amd64.deb\` |\n`;
    }
    process.stdout.write(s);
    break;
  }

  default:
    console.error("usage: gen-config.js list|version|check|appjson <id>|cordova <id>|env <id>|notes");
    process.exit(1);
}
