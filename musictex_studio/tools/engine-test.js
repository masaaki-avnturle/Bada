/*
 * engine-test.js — MusicTeX Studio のエンジンテスト (CI 用)
 *
 * index.html の inline <script> から DOM に触れない前半部
 * (テンプレート / MusixTeX パーサ / MIDI 変換 / コンパイルガイド) を
 * 抽出して node の vm で評価し、動作を検証します。
 *   node musictex_studio/tools/engine-test.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> found"); process.exit(1); }

/* DOM を使い始める箇所より前 (定義のみの部分) を評価する */
const cut = m[1].indexOf('var srcEl = document.getElementById');
if (cut < 0) { console.error("cut marker not found"); process.exit(1); }
const core = m[1].slice(0, cut);

const sandbox = { window: {}, console };
vm.createContext(sandbox);
vm.runInContext(core, sandbox);

let failures = 0;
function check(name, cond) {
  if (cond) console.log("  ok  " + name);
  else { console.error("  FAIL " + name); failures++; }
}

const { TEMPLATES, parseMusixTeX, pitchIndex, midiOf, compileGuide } = sandbox;

console.log("[1] テンプレート");
check("6 templates", Array.isArray(TEMPLATES) && TEMPLATES.length === 6);
for (const t of TEMPLATES) {
  check(`"${t.name}" is a complete MusixTeX document`,
    t.body.includes("\\input musixtex") && t.body.trim().endsWith("\\end") &&
    t.body.includes("\\startpiece") && t.body.includes("\\endpiece"));
}

console.log("[2] 音高 (MusixTeX 文字 → ダイアトニック番号)");
check("c = C4 (28)", pitchIndex("c") === 28);
check("a = A3 (26)", pitchIndex("a") === 26);
check("j = C5 (35)", pitchIndex("j") === 35);
check("uppercase C = C3 (21)", pitchIndex("C") === 21);

console.log("[3] パーサ — B♭ 長音階テンプレート (octave74)");
const bflat = parseMusixTeX(TEMPLATES[0].body);
check("signature = -2 (B flat major)", bflat.signature === -2);
check("meter = 4/4", bflat.meter[0] === 4 && bflat.meter[1] === 4);
const notes = bflat.events.filter(e => e.type === "note");
const bars = bflat.events.filter(e => e.type === "bar");
check("16 notes (asc + desc)", notes.length === 16);
check("3 bar lines", bars.length === 3);
check("starts on b (B3, idx 27)", notes[0].pitches[0].idx === 27);
check("scale ascends to i (B4, idx 34)", notes[7].pitches[0].idx === 34);
check("no parse warnings", bflat.warnings.length === 0);

console.log("[4] パーサ — G と A の和音テンプレート");
const chords = parseMusixTeX(TEMPLATES[2].body);
const triads = chords.events.filter(e => e.type === "note" && e.pitches.length === 3);
check("triads present (\\zq chords)", triads.length >= 6);
check("G triad = g-i-k", JSON.stringify(triads[0].pitches.map(p => p.idx)) === "[32,34,36]");
const withSharp = chords.events.filter(e =>
  e.type === "note" && e.pitches.some(p => p.acc === "sh"));
check("F# (\\sh f) applied to a chord note", withSharp.length === 1);

console.log("[5] MIDI 変換 (調号・臨時記号)");
check("c with C major = MIDI 60", midiOf({ idx: 28, acc: null }, 0) === 60);
check("b with B flat major = MIDI 58 (B♭3)", midiOf({ idx: 27, acc: null }, -2) === 58);
check("e with E flat major = MIDI 63 (E♭4)", midiOf({ idx: 30, acc: null }, -3) === 63);
check("f with \\sh = MIDI 66 (F♯4)", midiOf({ idx: 31, acc: "sh" }, 0) === 66);
check("natural cancels signature", midiOf({ idx: 27, acc: "na" }, -2) === 59);

console.log("[6] コンパイルガイド (texlive-music)");
check("ubuntu guide mentions texlive-music",
  compileGuide("ubuntu").includes("texlive-music"));
check("ubuntu guide uses musixtex -p", compileGuide("ubuntu").includes("musixtex -p"));
check("windows guide mentions MiKTeX / TeX Live",
  compileGuide("windows").includes("MiKTeX") && compileGuide("windows").includes("TeX Live"));
check("android guide explains .tex export", compileGuide("android").includes(".tex"));

console.log("[7] 休符・拍子の解析");
const restSrc = "\\generalmeter{\\meterfrac34}\\startpiece\\NOtes\\qu{c}\\qp\\hpause\\en\\endpiece";
const rests = parseMusixTeX(restSrc);
check("meter 3/4 parsed", rests.meter[0] === 3 && rests.meter[1] === 4);
check("quarter + half rests parsed",
  rests.events.filter(e => e.type === "rest").length === 2);

if (failures) { console.error(`\n${failures} failure(s)`); process.exit(1); }
console.log("\nMusicTeX Studio engine tests: all OK");
