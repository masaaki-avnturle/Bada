#!/usr/bin/env node
/* build.js — src/ から自己完結の index.html を作る。  --check: index.html が最新か確認する (CI 用)
 * SHA-256 は bada_gpt/src/engine.js (BadaGPT のエンジン) のものを使う。 */
"use strict";
const fs = require("fs"), path = require("path");
const root = path.join(__dirname, "..");
const rd = f => fs.readFileSync(path.join(root, "src", f), "utf8");
// zone:// ウルトラネットワーク: Bada 処理系 (bada_gui_ide/www/bada.js) と、zone の実行系 (browser/zone-lib.bada) を取り込む
const ide = f => fs.readFileSync(path.join(root, "..", "bada_gui_ide", f), "utf8");
const zoneLib = "var BADA_ZONE_LIB = " + JSON.stringify(ide("browser/zone-lib.bada")) + ";";
// 同梱する Bada プラグイン (src/plugins/*.bada)
const plugDir = path.join(root, "src", "plugins");
const bundled = "var BADA_PLUGINS = " + JSON.stringify(fs.readdirSync(plugDir).filter(f => f.endsWith(".bada")).sort().map(f => fs.readFileSync(path.join(plugDir, f), "utf8"))) + ";";
// Bada Predict の種 (Bada Precog の seed コーパス)
const seedDir = path.join(root, "src", "seed");
const seeds = "var BADA_PREDICT_SEED = " + JSON.stringify(fs.readdirSync(seedDir).sort().map(f => fs.readFileSync(path.join(seedDir, f), "utf8"))) + ";";
const libs = [ide("www/bada.js"), zoneLib, bundled, seeds, fs.readFileSync(path.join(root, "..", "bada_gpt", "src", "engine.js"), "utf8"), rd("entropy.js"), rd("agents.js"), rd("meeting.js"), rd("thought.js"), rd("net.js"), rd("telegraph.js"), rd("acoustic.js"), rd("zone.js"), rd("p2p.js"), rd("badaxp.js"), rd("badapredict.js"), rd("plugins.js")].join("\n");
if (/<\/script/i.test(libs)) throw new Error("libs must not contain </script");
const html = rd("ui.html").replace("/*__LIBS__*/", () => libs);
const out = path.join(root, "index.html");
if (process.argv.includes("--check")) {
  if (!fs.existsSync(out) || fs.readFileSync(out, "utf8") !== html) { console.error("index.html が古い: node bada_meeting/tools/build.js を実行してください"); process.exit(1); }
  console.log("index.html は最新");
} else { fs.writeFileSync(out, html); console.log("wrote index.html (" + (html.length / 1024).toFixed(0) + " KB)"); }
