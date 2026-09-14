/*
 * engine-test.js — Bada SoundFilm (MP3 → 動画 変換スタジオ) のエンジン単体テスト
 *
 *   node mp3_to_video/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分を検証します:
 *   1. fmtTime / fmtBytes — 時刻・サイズの整形
 *   2. parseTrackMeta / sanitizeName — ファイル名からの曲情報推定・出力名の無害化
 *   3. pickRecorderMime — MP4 → WebM の優先順位で録画形式を選択
 *   4. videoBitrate / estimateSize — 推奨ビットレートとサイズ見積り
 *   5. spectrumBars / energyOf — FFT ビンの対数集計とエネルギー
 *   6. id3Parse — ID3v2.3 / v2.4 (TIT2/TPE1/TALB/APIC) と ID3v1 フォールバック
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

/* ── index.html からインラインスクリプトを抽出 ── */
const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

/* ── サンドボックス (boot は __ENGINE_TEST__ で抑止) ── */
const sandbox = {
  console,
  Math,
  TextDecoder,
  window: { __ENGINE_TEST__: true },
  document: undefined,
  navigator: {},
  requestAnimationFrame: function () { return 0; },
  cancelAnimationFrame: function () {},
  setTimeout: function (fn) { return 0; },
  URL: { createObjectURL: function () { return "blob:stub"; }, revokeObjectURL: function () {} }
};
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "soundfilm-inline.js" });

/* ── テストハーネス ── */
let pass = 0, fail = 0;
function ok(cond, name) {
  if (cond) { pass++; console.log("  ✔ " + name); }
  else { fail++; console.error("  ✘ " + name); }
}
function eq(a, b, name) { ok(a === b, name + "  [" + JSON.stringify(a) + " === " + JSON.stringify(b) + "]"); }

const E = sandbox; /* エンジンの公開関数 */

/* ── 1. fmtTime / fmtBytes ── */
console.log("1. fmtTime / fmtBytes");
eq(E.fmtTime(0), "0:00", "fmtTime(0)");
eq(E.fmtTime(65), "1:05", "fmtTime(65)");
eq(E.fmtTime(3599.9), "59:59", "fmtTime(3599.9)");
eq(E.fmtTime(-5), "0:00", "fmtTime(負値)");
eq(E.fmtTime(NaN), "0:00", "fmtTime(NaN)");
eq(E.fmtBytes(500), "500 B", "fmtBytes(500)");
eq(E.fmtBytes(2048), "2.0 KB", "fmtBytes(2 KB)");
eq(E.fmtBytes(5 * 1024 * 1024), "5.0 MB", "fmtBytes(5 MB)");
eq(E.fmtBytes(3 * 1024 * 1024 * 1024), "3.00 GB", "fmtBytes(3 GB)");

/* ── 2. parseTrackMeta / sanitizeName ── */
console.log("2. parseTrackMeta / sanitizeName");
let t = E.parseTrackMeta("宇多田ヒカル - First Love.mp3");
eq(t.artist, "宇多田ヒカル", "parseTrackMeta artist");
eq(t.title, "First Love", "parseTrackMeta title");
t = E.parseTrackMeta("song.mp3");
eq(t.artist, "", "parseTrackMeta artist なし");
eq(t.title, "song", "parseTrackMeta title のみ");
t = E.parseTrackMeta("track01.final.mp3");
eq(t.title, "track01.final", "parseTrackMeta 拡張子のみ除去");
eq(E.sanitizeName('a<b>:c/"d"?*|e'), "abcde", "sanitizeName 不正文字除去");
eq(E.sanitizeName("  "), "video", "sanitizeName 空 → video");
eq(E.sanitizeName("夜に駆ける"), "夜に駆ける", "sanitizeName 日本語はそのまま");

/* ── 3. pickRecorderMime ── */
console.log("3. pickRecorderMime");
let c = E.pickRecorderMime(function (mime) { return /webm/.test(mime) && /vp9/.test(mime); });
eq(c.ext, "webm", "pickRecorderMime WebM 環境 → webm");
ok(/vp9/.test(c.mime), "pickRecorderMime VP9 を選択");
c = E.pickRecorderMime(function (mime) { return /mp4/.test(mime); });
eq(c.ext, "mp4", "pickRecorderMime MP4 対応環境 → mp4 優先");
c = E.pickRecorderMime(function () { return false; });
eq(c.mime, "", "pickRecorderMime 非対応 → mime 空");
eq(c.ext, "webm", "pickRecorderMime 非対応 → 既定 ext webm");
c = E.pickRecorderMime(function () { throw new Error("boom"); });
eq(c.mime, "", "pickRecorderMime isSupported 例外でも安全");

/* ── 4. videoBitrate / estimateSize ── */
console.log("4. videoBitrate / estimateSize");
const b1080 = E.videoBitrate(1920, 1080, 30);
const b720 = E.videoBitrate(1280, 720, 30);
ok(b1080 >= 3000000 && b1080 <= 10000000, "videoBitrate 1080p30 は 3〜10 Mbps (" + b1080 + ")");
ok(b720 < b1080, "videoBitrate は解像度で増加");
ok(E.videoBitrate(160, 120, 24) >= 1000000, "videoBitrate 下限 1 Mbps");
ok(E.videoBitrate(3840, 2160, 60) <= 20000000, "videoBitrate 上限 20 Mbps");
eq(E.estimateSize(8000000, 0, 10), 10000000, "estimateSize 8 Mbps × 10 s = 10 MB");
eq(E.estimateSize(0, 192000, 100), 2400000, "estimateSize 音声のみ");
eq(E.estimateSize(1000, 0, -5), 0, "estimateSize 負の秒数 → 0");

/* ── 5. spectrumBars / energyOf ── */
console.log("5. spectrumBars / energyOf");
const flat = new Uint8Array(1024).fill(255);
let bars = E.spectrumBars(flat, 64);
eq(bars.length, 64, "spectrumBars 本数");
ok(bars.every(v => Math.abs(v - 1) < 1e-9), "spectrumBars 全ビン 255 → 全バー 1.0");
bars = E.spectrumBars(new Uint8Array(1024), 64);
ok(bars.every(v => v === 0), "spectrumBars 無音 → 全バー 0");
bars = E.spectrumBars(new Uint8Array([255, 0, 0, 0]), 4);
ok(bars[0] === 1, "spectrumBars 低域ビンが先頭バーに反映");
ok(bars.every(v => v >= 0 && v <= 1), "spectrumBars 値域 0..1");
eq(E.energyOf(flat), 1, "energyOf 最大 → 1");
eq(E.energyOf(new Uint8Array(8)), 0, "energyOf 無音 → 0");
eq(E.energyOf(new Uint8Array(0)), 0, "energyOf 空配列 → 0");

/* ── 6. id3Parse ── */
console.log("6. id3Parse");

/* ID3v2 タグをバイト列で組み立てるヘルパ */
function syncsafe(n) { return [(n >> 21) & 0x7f, (n >> 14) & 0x7f, (n >> 7) & 0x7f, n & 0x7f]; }
function u32(n) { return [(n >>> 24) & 0xff, (n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff]; }
function latin1(s) { return Array.from(s, ch => ch.charCodeAt(0) & 0xff); }
function utf16leBOM(s) {
  const out = [0xff, 0xfe];
  for (const ch of s) { const c = ch.charCodeAt(0); out.push(c & 0xff, c >> 8); }
  return out;
}
function frame(id, body, v4) {
  const size = v4 ? syncsafe(body.length) : u32(body.length);
  return [...latin1(id), ...size, 0, 0, ...body];
}
function id3v2(frames, v4) {
  const body = frames.flat ? frames.flat() : [].concat(...frames);
  return new Uint8Array([0x49, 0x44, 0x33, v4 ? 4 : 3, 0, 0, ...syncsafe(body.length + 64), ...body,
                         ...new Array(64).fill(0) /* パディング */]);
}

/* v2.3: TIT2 (latin1) + TPE1 (UTF-16 BOM) + TALB + APIC */
const jpeg = [0xff, 0xd8, 0xff, 0xe0, 1, 2, 3, 4];
const tagV23 = id3v2([
  frame("TIT2", [0, ...latin1("Hello World")]),
  frame("TPE1", [1, ...utf16leBOM("Bada Band")]),
  frame("TALB", [0, ...latin1("Best Album")]),
  frame("APIC", [0, ...latin1("image/jpeg"), 0, 3, ...latin1("cover"), 0, ...jpeg])
], false);
let tag = E.id3Parse(tagV23.buffer);
eq(tag.title, "Hello World", "id3Parse v2.3 TIT2 (latin1)");
eq(tag.artist, "Bada Band", "id3Parse v2.3 TPE1 (UTF-16 BOM)");
eq(tag.album, "Best Album", "id3Parse v2.3 TALB");
ok(!!tag.picture, "id3Parse v2.3 APIC 検出");
eq(tag.picture.mime, "image/jpeg", "id3Parse APIC mime");
eq(tag.picture.data.length, jpeg.length, "id3Parse APIC 画像データ長");
ok(tag.picture.data[0] === 0xff && tag.picture.data[1] === 0xd8, "id3Parse APIC JPEG マジック");

/* v2.4: syncsafe フレームサイズ + UTF-8 (日本語) */
const enc = new TextEncoder();
const tagV24 = id3v2([
  frame("TIT2", [3, ...enc.encode("夜に駆ける")], true),
  frame("TPE1", [3, ...enc.encode("YOASOBI")], true)
], true);
tag = E.id3Parse(tagV24.buffer);
eq(tag.title, "夜に駆ける", "id3Parse v2.4 TIT2 (UTF-8 日本語)");
eq(tag.artist, "YOASOBI", "id3Parse v2.4 TPE1");

/* ID3v1 フォールバック (末尾 128 byte の TAG) */
const v1 = new Uint8Array(400);
const tail = v1.length - 128;
v1.set(latin1("TAG"), tail);
v1.set(latin1("Old Song"), tail + 3);
v1.set(latin1("Old Artist"), tail + 33);
v1.set(latin1("Old Album"), tail + 63);
tag = E.id3Parse(v1.buffer);
eq(tag.title, "Old Song", "id3Parse ID3v1 title");
eq(tag.artist, "Old Artist", "id3Parse ID3v1 artist");
eq(tag.album, "Old Album", "id3Parse ID3v1 album");

/* タグなし */
tag = E.id3Parse(new Uint8Array(64).buffer);
eq(tag.title, "", "id3Parse タグなし → 空");
ok(tag.picture === null, "id3Parse タグなし → picture null");

/* 壊れたタグ (サイズがバッファ超過) でも例外なし */
const broken = new Uint8Array([0x49, 0x44, 0x33, 3, 0, 0, 0x7f, 0x7f, 0x7f, 0x7f, 1, 2, 3]);
tag = E.id3Parse(broken.buffer);
ok(tag && typeof tag.title === "string", "id3Parse 壊れたタグでも安全");

/* ── 結果 ── */
console.log("");
console.log("結果: " + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
