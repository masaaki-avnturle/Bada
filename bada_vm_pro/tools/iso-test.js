/*
 * iso-test.js — ISO 9660 ビルダー/パーサーの自己検査
 *   node bada_vm_pro/tools/iso-test.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { buildIso, parseIso, SECTOR } = require("./iso9660.js");

let failed = 0;
function ok(cond, label){
  console.log((cond ? "PASS" : "FAIL") + "  " + label);
  if (!cond) failed++;
}

/* ── 合成 ISO の round-trip ── */
const payload = "こんにちは Bada VM Pro — 量子 OS ライブ CD テスト\n" + "x".repeat(3000);
const iso = buildIso({
  volumeId: "TESTVOL",
  files: [
    { name: "index.htm", data: payload },
    { name: "readme.txt", data: "hello readme" },
    { name: "empty.txt", data: "" }
  ]
});
ok(iso.length % SECTOR === 0, "image is sector-aligned (" + iso.length + " bytes)");
ok(iso[16 * SECTOR] === 1 && String.fromCharCode.apply(null, iso.slice(16 * SECTOR + 1, 16 * SECTOR + 6)) === "CD001",
   "PVD carries CD001 magic");
ok(iso[17 * SECTOR] === 0 &&
   String.fromCharCode.apply(null, iso.slice(17 * SECTOR + 7, 17 * SECTOR + 30)) === "EL TORITO SPECIFICATION",
   "El Torito boot record present");
{
  /* ブートカタログ検証エントリのチェックサム: 全ワード和 ≡ 0 */
  const o = 22 * SECTOR;
  let sum = 0;
  for (let i = 0; i < 32; i += 2) sum = (sum + iso[o + i] + (iso[o + i + 1] << 8)) & 0xffff;
  ok(sum === 0 && iso[o + 30] === 0x55 && iso[o + 31] === 0xAA, "boot catalog validation entry checksums to 0");
  ok(iso[o + 32] === 0x88, "default boot entry is marked bootable (0x88)");
}
{
  const boot = iso.slice(23 * SECTOR, 23 * SECTOR + 512);
  ok(boot[0] === 0xBE && boot[510] === 0x55 && boot[511] === 0xAA, "boot sector code + 55AA signature");
}

const parsed = parseIso(iso);
ok(parsed.volumeId === "TESTVOL", "volume id round-trips");
ok(parsed.bootable === true, "parser detects El Torito");
ok(parsed.files.length === 3, "3 files in root — got " + parsed.files.length);
const idx = parsed.files.find(function(f){ return f.name === "INDEX.HTM"; });
ok(!!idx, "8.3 name mapping (index.htm → INDEX.HTM)");
ok(idx && Buffer.from(idx.data).toString("utf8") === payload, "file content round-trips (UTF-8/CJK)");
const emp = parsed.files.find(function(f){ return f.name === "EMPTY.TXT"; });
ok(emp && emp.size === 0, "empty file round-trips with size 0");

/* ── 実物のライブ CD をビルドして検査 ── */
require("./build-iso.js");
const live = new Uint8Array(fs.readFileSync(path.join(__dirname, "..", "dist", "BadaVMPro-live.iso")));
const lp = parseIso(live);
ok(lp.volumeId === "BADAVMPRO_LIVE", "live ISO volume id");
ok(lp.bootable, "live ISO is El Torito bootable");
const names = lp.files.map(function(f){ return f.name; }).sort().join(",");
ok(names === "AUTORUN.INF,INDEX.HTM,LICENSE.TXT,README.TXT", "live ISO file set — got " + names);
const htm = lp.files.find(function(f){ return f.name === "INDEX.HTM"; });
const orig = fs.readFileSync(path.join(__dirname, "..", "index.html"));
ok(htm && htm.size === orig.length && Buffer.compare(Buffer.from(htm.data), orig) === 0,
   "INDEX.HTM on the ISO is byte-identical to bada_vm_pro/index.html");

console.log(failed === 0 ? "\nALL ISO TESTS PASSED" : "\n" + failed + " TEST(S) FAILED");
process.exit(failed === 0 ? 0 : 1);
