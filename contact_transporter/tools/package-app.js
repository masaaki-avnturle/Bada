#!/usr/bin/env node
/*
 * package-app.js — アプリごとのネイティブ ラッパーを用意する
 *
 *   node tools/package-app.js <contactgpt|transporter|ufo|studio>
 *
 *   dist/<アプリ>/electron/  … Windows 10/11 EXE (NSIS + ポータブル) / Linux AppImage・deb 用
 *                              (app/electron の main.js・preload.js・package.json をアプリ名・ID で書き換え)
 *   dist/<アプリ>/cordova/config.xml … Android APK 用 (app/cordova/config.xml をアプリ名・ID で書き換え)
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
const xml = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// ---- Electron
const E = path.join(DIST, "electron");
fs.mkdirSync(E, { recursive: true });
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, "app", "electron", "package.json"), "utf8"));
pkg.name = A.file.toLowerCase();
pkg.productName = A.name;
pkg.description = A.description;
pkg.build.appId = A.id;
pkg.build.productName = A.name;
pkg.build.extraResources = [{ from: "../www", to: "www" }];
pkg.build.win.artifactName = `${A.file}-\${version}-\${arch}.\${ext}`;
pkg.build.portable.artifactName = `${A.file}-\${version}-portable.\${ext}`;
pkg.build.linux.artifactName = `${A.file}-\${version}-\${arch}.\${ext}`;
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
cfg = cfg.replace(/<widget id="[^"]*"/, `<widget id="${A.id}"`)
  .replace(/<name>[^<]*<\/name>/, `<name>${xml(A.name)}</name>`)
  .replace(/<description>[^<]*<\/description>/, `<description>${xml(A.description)}</description>`);
fs.writeFileSync(path.join(C, "config.xml"), cfg);
console.log(`${A.name}: dist/${key}/electron (appId ${A.id}) + dist/${key}/cordova/config.xml`);
