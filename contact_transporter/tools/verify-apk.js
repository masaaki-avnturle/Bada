#!/usr/bin/env node
// verify-apk.js — ランナー APK に論文アプリを差し替えて署名し直したものを書き出す (CI で apksigner verify にかける)
//   node tools/verify-apk.js <runner.apk> <out.apk>
const fs = require("fs"), path = require("path"), X = require("../src/exporters.js");
const [tpl, out] = process.argv.slice(2);
const sig = path.join(__dirname, "..", "app", "signing");
X.buildApk(new Uint8Array(fs.readFileSync(tpl)), "<!doctype html><html><head><meta charset=utf-8><title>verify</title></head><body>Bada paper app (verify)</body></html>",
  { pk8: new Uint8Array(fs.readFileSync(path.join(sig, "debug-key.pk8"))), cert: new Uint8Array(fs.readFileSync(path.join(sig, "debug-cert.der"))) })
  .then((apk) => { fs.writeFileSync(out, apk); console.log(`${out}: ${apk.length} bytes, entries ${X.readZip(apk).length}`); })
  .catch((e) => { console.error(e); process.exit(1); });
