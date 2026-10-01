#!/usr/bin/env node
// make-test-exe.js — ランチャー + 小さなアプリ一式で Windows EXE を作る (CI の Windows 実機テスト用)
//   node tools/make-test-exe.js <bada-launcher.exe> <out.exe>
const fs = require("fs"), X = require("../src/exporters.js");
const [launcher, out] = process.argv.slice(2);
const html = "<!doctype html><html><head><meta charset=utf-8><title>Bada test</title></head><body>論文アプリ (Windows テスト)</body></html>";
const exe = X.buildWinExe(new Uint8Array(fs.readFileSync(launcher)), [
  { name: "index.html", data: html }, { name: "test.bada", data: 'say "hello from Bada"' }, { name: "paper.pdf", data: "%PDF-1.4 test" },
], "bada-ci-test");
fs.writeFileSync(out, exe);
console.log(`${out}: ${exe.length} bytes`);
