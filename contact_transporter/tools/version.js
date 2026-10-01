// version.js — 全アプリ共通のバージョン (上書きインストールでアップデートできるように)
//
//   バージョン名  <major>.<minor>.<ビルド番号>   (major.minor は app/electron/package.json)
//   versionCode   100000 + ビルド番号            (Android: 前より大きければアップデート)
//   ビルド番号    環境変数 CT_BUILD (GitHub Actions では github.run_number。毎回増える)。ローカルは 0
const path = require("path");
const base = require(path.join(__dirname, "..", "app", "electron", "package.json")).version.split(".");
const build = Math.max(0, parseInt(process.env.CT_BUILD || "0", 10) || 0);
module.exports = { version: `${base[0]}.${base[1]}.${build}`, versionCode: 100000 + build, build };
if (require.main === module) console.log(JSON.stringify(module.exports));
