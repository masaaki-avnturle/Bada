#!/usr/bin/env node
/*
 * package-app.js — アプリごとのネイティブ ラッパーを用意する
 *
 *   node tools/package-app.js <contactgpt|transporter|ufo|badaclaude|studio>
 *
 *   dist/<アプリ>/electron/  … Windows 10/11 EXE (NSIS + ポータブル) / Linux AppImage・deb 用
 *                              (app/electron の main.js・preload.js・package.json をアプリ名・ID で書き換え)
 *   dist/<アプリ>/cordova/config.xml … Android APK 用 (app/cordova/config.xml をアプリ名・ID で書き換え)
 *   dist/<アプリ>/cordova/www/index.html … Android 用 (cordova.js を <head> に追加)
 *   dist/<アプリ>/cordova/bada-files/ … ファイル取り込み・保存プラグイン (app/cordova/bada-files)
 *
 * 先に node tools/build.js <アプリ> で dist/<アプリ>/www/index.html を作っておくこと。
 */
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
const APPS = JSON.parse(fs.readFileSync(path.join(ROOT, "apps.json"), "utf8"));
const key = process.argv[2];
const A = APPS[key];
if (!A) { console.error(`usage: package-app.js <${Object.keys(APPS).join("|")}>`); process.exit(1); }
const DIST = path.join(ROOT, "dist", key);
if (!fs.existsSync(path.join(DIST, "www", "index.html"))) { console.error(`dist/${key}/www/index.html がありません — 先に build.js ${key}`); process.exit(1); }
const VER = require("./version.js");
const xml = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// ---- Electron
const E = path.join(DIST, "electron");
fs.mkdirSync(E, { recursive: true });
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, "app", "electron", "package.json"), "utf8"));
pkg.name = A.file.toLowerCase();
pkg.productName = A.name;
pkg.description = A.description;
pkg.version = VER.version;
pkg.build.appId = A.id;
pkg.build.productName = A.name;
pkg.build.extraResources = [{ from: "../www", to: "www" }];
// ファイル名にバージョンを入れない: 毎回同じ名前 (上書き保存・上書きインストール)
pkg.build.win.artifactName = `${A.file}-Setup-\${arch}.\${ext}`;
pkg.build.portable.artifactName = `${A.file}-portable.\${ext}`;
pkg.build.linux.artifactName = `${A.file}-\${arch}.\${ext}`;
pkg.build.linux.category = A.category;
fs.writeFileSync(path.join(E, "package.json"), JSON.stringify(pkg, null, 2));
const lock = path.join(ROOT, "app", "electron", "package-lock.json");
if (fs.existsSync(lock)) {
  const l = JSON.parse(fs.readFileSync(lock, "utf8")); l.name = pkg.name; if (l.packages && l.packages[""]) l.packages[""].name = pkg.name;
  fs.writeFileSync(path.join(E, "package-lock.json"), JSON.stringify(l, null, 2));
}
let main = fs.readFileSync(path.join(ROOT, "app", "electron", "main.js"), "utf8");
main = main.replace('path.join(__dirname, "..", "..", "dist", "www", "index.html")', 'path.join(__dirname, "..", "www", "index.html")')
  .replace('title: "Contact Transporter Studio"', `title: ${JSON.stringify(A.name)}`);
fs.writeFileSync(path.join(E, "main.js"), main);
fs.copyFileSync(path.join(ROOT, "app", "electron", "preload.js"), path.join(E, "preload.js"));

// ---- Cordova
const C = path.join(DIST, "cordova");
fs.mkdirSync(C, { recursive: true });
let cfg = fs.readFileSync(path.join(ROOT, "app", "cordova", "config.xml"), "utf8");
cfg = cfg.replace(/<widget id="[^"]*" version="[^"]*"/, `<widget id="${A.id}" version="${VER.version}" android-versionCode="${VER.versionCode}"`)
  .replace(/<name>[^<]*<\/name>/, `<name>${xml(A.name)}</name>`)
  .replace(/<description>[^<]*<\/description>/, `<description>${xml(A.description)}</description>`);
// 論文から作ったアプリの APK (ランナー) は v1 (JAR) 署名で配るため targetSdk 29 にする
if (A.targetSdk) cfg = cfg.replace('<preference name="android-minSdkVersion" value="24" />', `<preference name="android-minSdkVersion" value="24" />\n  <preference name="android-targetSdkVersion" value="${A.targetSdk}" />\n  <preference name="android-compileSdkVersion" value="33" />`);
// Claude API モード (BadaClaude): 通信先は api.anthropic.com だけを許可
if (A.claude) cfg = cfg.replace('<content src="index.html" />', '<content src="index.html" />\n  <access origin="https://api.anthropic.com" />');
fs.writeFileSync(path.join(C, "config.xml"), cfg);
// 署名: 全ビルド共通の固定鍵 (app/signing/bada-apps-*)。同じ署名 + 大きい versionCode / バージョンなので
// Android・Windows・Linux とも上書きインストールでアップデートできる (Actions の Secrets で差し替え可)
const SIG = path.join(DIST, "signing");
fs.mkdirSync(SIG, { recursive: true });
for (const f of ["bada-apps-key.pk8", "bada-apps-cert.der", "bada-apps-codesign.pfx"]) fs.copyFileSync(path.join(ROOT, "app", "signing", f), path.join(SIG, f));
// Android 用の www: cordova.js を読み込む <script> を <head> に 1 つだけ入れる。
// (以前は CI の sed で「</head>」を置換していたため、アプリの JavaScript 内の文字列 "</head>" まで書き換わり、
//  Android 版ではスクリプト全体が構文エラーになって、ファイル画面・フォルダが開かず何も動かなかった)
{
  const html = fs.readFileSync(path.join(DIST, "www", "index.html"), "utf8");
  const at = html.indexOf("</head>");
  if (at < 0 || at > html.indexOf("<script")) throw new Error("index.html の <head> が見つかりません");
  const W = path.join(C, "www");
  fs.mkdirSync(W, { recursive: true });
  fs.writeFileSync(path.join(W, "index.html"), html.slice(0, at) + '<script src="cordova.js"></script>\n' + html.slice(at));
}
// ファイルの取り込み・保存プラグイン (Storage Access Framework / MediaStore) を同梱
fs.cpSync(path.join(ROOT, "app", "cordova", "bada-files"), path.join(C, "bada-files"), { recursive: true });
console.log(`${A.name} ${VER.version} (versionCode ${VER.versionCode}): dist/${key}/electron (appId ${A.id}) + dist/${key}/cordova/config.xml + dist/${key}/signing`);
