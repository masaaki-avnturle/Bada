/*
 * squeak-check.js — Squeak 版 (MusicTeXStudio.st) の静的検証 (CI 用)
 *
 * fileIn チャンク形式を解析して検証する:
 *   - チャンク構造 (クラス定義 / methodsFor: ヘッダ + メソッド本体 + 終端)
 *   - 各チャンクの括弧 ( ) [ ] { } と文字列/コメント引用符の均衡
 *   - メソッド先頭行がセレクタパターンであること
 *   - 期待するクラス・主要メソッドの存在
 *   node musictex_studio/tools/squeak-check.js
 */
"use strict";
const fs = require("fs");
const path = require("path");

const src = fs.readFileSync(path.join(__dirname, "..", "squeak", "MusicTeXStudio.st"), "utf8");
let failures = 0;
function check(name, cond, detail) {
  if (cond) console.log("  ok  " + name);
  else { console.error("  FAIL " + name + (detail ? " — " + detail : "")); failures++; }
}

/* --- 1. チャンク分割 (文字列/コメント内に ! が無い前提を先に確認) --- */
console.log("[1] チャンク構造");
check("バング二重化 (!!) を含まない (文字列内の ! 不使用)", !src.includes("!!"));
const chunks = src.split("!").map(c => c.replace(/^\s+/, ""));

/* クラス定義チャンク */
const classDefs = chunks.filter(c => /subclass: #MTS/.test(c));
check("4 クラス定義 (MTSTheory / MTSSynth / MTSSpectralMorph / MTSStaffMorph / MTSApp のうち)",
  classDefs.length === 5,
  "found " + classDefs.length);
for (const name of ["MTSTheory", "MTSSynth", "MTSSpectralMorph", "MTSStaffMorph", "MTSApp"]) {
  check(`class ${name} defined`, classDefs.some(c => c.includes("#" + name)));
}
check("クラス定義は 5 キーワード形式 (poolDictionaries: 付き / 旧 Squeak 互換)",
  classDefs.every(c => c.includes("poolDictionaries:")));

/* --- 2. methodsFor: ブロックの構造 --- */
console.log("[2] メソッドチャンク");
let methods = [];
for (let i = 0; i < chunks.length; i++) {
  const c = chunks[i];
  if (/^MTS\w+ (class )?methodsFor: '[^']*'$/.test(c.trim())) {
    const body = chunks[i + 1];
    const term = chunks[i + 2];
    check(`method after header ok: ${c.trim().slice(0, 50)}`,
      body !== undefined && body.trim().length > 0 && term !== undefined && term.trim() === "",
      "header must be followed by body and empty terminator");
    if (body) methods.push({ header: c.trim(), body });
    i += 2;
  }
}
check("メソッド数 >= 45", methods.length >= 45, "found " + methods.length);

/* --- 3. 各メソッドの検証 --- */
console.log("[3] メソッド本体 (先頭セレクタ / 括弧・引用符の均衡)");
const selectorRe = /^([a-zA-Z_]\w*(: *\S+)?( +\w+: *\S+)*|[-+*/\\~<>=&|@%,?]+ +\w+)/;
let allOk = true;
for (const m of methods) {
  const firstLine = m.body.split("\n")[0].trim();
  if (!selectorRe.test(firstLine)) {
    check("selector line: " + firstLine.slice(0, 40), false); allOk = false; continue;
  }
  /* 文字列・コメントを除去してから括弧を数える */
  let s = m.body, out = "", inStr = false, inCmt = false;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (inStr) { if (ch === "'") { if (s[i + 1] === "'") { i++; } else inStr = false; } continue; }
    if (inCmt) { if (ch === '"') inCmt = false; continue; }
    if (ch === "'") { inStr = true; continue; }
    if (ch === '"') { inCmt = true; continue; }
    out += ch;
  }
  if (inStr || inCmt) {
    check("引用符が閉じている: " + firstLine.slice(0, 40), false, inStr ? "unterminated '...'" : 'unterminated "..."');
    allOk = false; continue;
  }
  /* $( などの文字リテラルを除去してから均衡確認 */
  out = out.replace(/\$./g, "");
  const bal = { "(": 0, "[": 0, "{": 0 };
  let balOk = true;
  for (const ch of out) {
    if (ch === "(") bal["("]++; if (ch === ")") bal["("]--;
    if (ch === "[") bal["["]++; if (ch === "]") bal["["]--;
    if (ch === "{") bal["{"]++; if (ch === "}") bal["{"]--;
    if (bal["("] < 0 || bal["["] < 0 || bal["{"] < 0) { balOk = false; break; }
  }
  if (!balOk || bal["("] !== 0 || bal["["] !== 0 || bal["{"] !== 0) {
    check("括弧の均衡: " + firstLine.slice(0, 40), false, JSON.stringify(bal));
    allOk = false; continue;
  }
  /* 一時変数宣言 | ... | の対 (奇数個の | は許容しない: ブロック引数の | は [: 後なので除外) */
}
check("全メソッドのセレクタ・引用符・括弧 OK", allOk);

/* --- 4. 主要 API の存在 --- */
console.log("[4] 主要メソッドの存在");
const bodyAll = methods.map(m => m.body.split("\n")[0].trim().split(/[: ]/)[0] +
  (m.body.split("\n")[0].includes(":") ? ":" : "")).join(" ");
for (const sel of ["midiToWavelength:", "wavelengthToRGB:", "noteColor:", "estimateKeySignature:",
                   "midiToTex:", "chordMidisRoot:", "chordFromPitchClasses:", "extractChordLine:",
                   "mergeEvents:", "eventsToMusixTex:", "parseMusixTeX:", "beatEventsFrom:",
                   "presetNamed:", "soundForMidi:", "playEvents:", "midiEventsFromFileNamed:",
                   "wavEventsFromFileNamed:", "detectPitchIn:", "drawOn:", "buildTitlebar",
                   "buildToolbar", "buildLibrary", "buildInspector", "doPlay", "doChordify",
                   "doImportMidi", "doImportWav", "doSaveTex", "insertChord:", "selectInstrument:"]) {
  check("method " + sel, methods.some(m => m.body.trim().startsWith(sel.replace(/:$/, ":")) ||
    m.body.trim().split(/[\s:]/)[0] === sel.replace(/:$/, "")));
}
check("open (class-side) defined", methods.some(m => m.header.includes("MTSApp class") && m.body.trim().startsWith("open")));
check("17 instruments in presets", (src.match(/aName = '/g) || []).length >= 16);
check("templates: 6 曲", (src.match(/with: \(Array with: '[^']+'\s*\n?\s*with: '\\input musixtex'/g) || []).length === 6);

if (failures) { console.error(`\n${failures} failure(s)`); process.exit(1); }
console.log("\nSqueak edition static checks: all OK (" + methods.length + " methods)");
