#!/usr/bin/env node
/*
 * prepare.js — 各アプリのパッケージ用ディレクトリを作る (GitHub Actions から呼ぶ)。
 *   node app/tools/prepare.js <transporter|chatgpt|ufo> electron <outDir>
 *       → <outDir>/{main.js, preload.js, package.json, www/}   (electron-builder 用)
 *   node app/tools/prepare.js <transporter|chatgpt|ufo> cordova <outDir>
 *       → <outDir>/{config.xml, www/}                           (Cordova 用)
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const [APP, KIND, OUT] = process.argv.slice(2);
const ROOT = path.resolve(__dirname, "..");
const apps = JSON.parse(fs.readFileSync(path.join(ROOT, "apps.json"), "utf8"));
const VERSION = "1.0.0";
if (!apps[APP] || !["electron", "cordova"].includes(KIND) || !OUT) {
  console.error("usage: prepare.js <" + Object.keys(apps).join("|") + "> <electron|cordova> <outDir>");
  process.exit(2);
}
const a = apps[APP];
const out = path.resolve(OUT);
fs.mkdirSync(out, { recursive: true });
execFileSync(process.execPath, [path.join(__dirname, "build_www.js"), APP, path.join(out, "www")], { stdio: "inherit" });

if (KIND === "electron") {
  for (const f of ["main.js", "preload.js"]) fs.copyFileSync(path.join(ROOT, "electron", f), path.join(out, f));
  const pkg = {
    name: a.artifact,
    productName: a.productName,
    version: VERSION,
    description: a.description,
    author: "Masaaki Yamaguchi",
    license: "MIT",
    homepage: "https://github.com/masaaki-avnturle/Bada",
    main: "main.js",
    blueprint: { displayName: a.displayName },
    scripts: {
      start: "electron .",
      dist: "electron-builder --win --x64",
      "dist:linux": "electron-builder --linux --x64"
    },
    devDependencies: { electron: "^31.0.0", "electron-builder": "^24.13.3" },
    build: {
      appId: a.appId,
      productName: a.productName,
      publish: null,
      files: ["main.js", "preload.js", "package.json"],
      extraResources: [{ from: "www", to: "www" }],
      directories: { output: "dist" },
      win: { target: ["nsis", "portable"], artifactName: a.productName + "-${version}-${arch}.${ext}" },
      nsis: { oneClick: false, allowToChangeInstallationDirectory: true, shortcutName: a.displayName },
      portable: { artifactName: a.productName + "-${version}-portable.${ext}" },
      linux: {
        target: ["AppImage", "deb"],
        category: "Graphics",
        artifactName: a.productName + "-${version}-${arch}.${ext}",
        maintainer: "masaaki-avnturle <masaaki.tabu4@gmail.com>",
        desktop: { Name: a.displayName }
      }
    }
  };
  fs.writeFileSync(path.join(out, "package.json"), JSON.stringify(pkg, null, 2));
} else {
  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  const xml = fs.readFileSync(path.join(ROOT, "cordova", "config.template.xml"), "utf8")
    .split("__APPID__").join(a.appId).split("__VERSION__").join(VERSION)
    .split("__NAME__").join(esc(a.displayName)).split("__DESC__").join(esc(a.description));
  fs.writeFileSync(path.join(out, "config.xml"), xml);
}
console.log("prepared", APP, KIND, "→", out);
