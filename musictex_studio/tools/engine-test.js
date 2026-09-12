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

const { TEMPLATES, parseMusixTeX, pitchIndex, midiOf, compileGuide,
        estimateKeySignature, midiToTex, parseMidi, midiNotesToEvents,
        notesToMusixTex, detectPitch, pitchFramesToEvents,
        midiToWavelength, wavelengthToRGB, scoreToSpectral } = sandbox;

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

console.log("[8] 自動採譜 — 調号推定と音名変換");
// B♭ 長音階 (B♭3〜B♭4): 58 60 62 63 65 67 69 70
check("B flat scale → signature -2",
  estimateKeySignature([58, 60, 62, 63, 65, 67, 69, 70]) === -2);
check("C major scale → signature 0",
  estimateKeySignature([60, 62, 64, 65, 67, 69, 71, 72]) === 0);
check("midiToTex: 60 in C = c (no accidental)",
  JSON.stringify(midiToTex(60, 0)) === JSON.stringify({ idx: 28, letter: "c", acc: null }));
check("midiToTex: 58 in B flat major = b (flat from signature, no accidental)",
  midiToTex(58, -2).letter === "b" && midiToTex(58, -2).acc === null);
check("midiToTex: 66 in C = f sharp (explicit \\sh)",
  midiToTex(66, 0).letter === "f" && midiToTex(66, 0).acc === "sh");
check("midiToTex: 59 in B flat major = b natural (explicit \\na)",
  midiToTex(59, -2).letter === "b" && midiToTex(59, -2).acc === "na");

console.log("[9] 自動採譜 — SMF (MIDI) パーサ");
// 合成 SMF: format 0, division 480。C4(♩) D4(♩) E4(𝅗𝅥) + 和音 C4+E4+G4(♩)
function vlq(n) { // MIDI 可変長数値
  const out = [n & 0x7F];
  while ((n >>= 7) > 0) out.unshift((n & 0x7F) | 0x80);
  return out;
}
function midiFile(track) {
  const trk = [].concat(...track);
  return Uint8Array.from([
    0x4D, 0x54, 0x68, 0x64, 0, 0, 0, 6, 0, 0, 0, 1, (480 >> 8), (480 & 0xFF),
    0x4D, 0x54, 0x72, 0x6B,
    (trk.length >> 24) & 0xFF, (trk.length >> 16) & 0xFF, (trk.length >> 8) & 0xFF, trk.length & 0xFF,
    ...trk
  ]);
}
const Q = 480;
const smf = midiFile([
  [...vlq(0), 0x90, 60, 100], [...vlq(Q), 0x80, 60, 0],       // C4 quarter
  [...vlq(0), 0x90, 62, 100], [...vlq(Q), 0x80, 62, 0],       // D4 quarter
  [...vlq(0), 0x90, 64, 100], [...vlq(2 * Q), 0x80, 64, 0],   // E4 half
  [...vlq(0), 0x90, 60, 100], [...vlq(0), 0x90, 64, 100], [...vlq(0), 0x90, 67, 100], // chord on
  [...vlq(Q), 0x80, 60, 0], [...vlq(0), 0x80, 64, 0], [...vlq(0), 0x80, 67, 0],       // chord off
  [...vlq(0), 0xFF, 0x2F, 0x00]                                // end of track
]);
const parsed = parseMidi(smf);
check("SMF parsed: division 480", parsed && parsed.division === 480);
check("SMF parsed: 6 notes", parsed.notes.length === 6);
check("first note C4 at tick 0, 1 beat",
  parsed.notes[0].midi === 60 && parsed.notes[0].startTick === 0 && parsed.notes[0].durTick === Q);
const mev = midiNotesToEvents(parsed);
check("events: 4 (chord folded)", mev.length === 4);
check("chord event = C4+E4+G4", JSON.stringify(mev[3].midis) === "[60,64,67]");

console.log("[10] 自動採譜 — MusixTeX 生成");
const gen = notesToMusixTex(mev, { source: "test.mid" });
check("generated doc is complete MusixTeX",
  gen.includes("\\input musixtex") && gen.trim().endsWith("\\end") &&
  gen.includes("\\startpiece") && gen.includes("\\endpiece"));
check("C major signature", gen.includes("\\generalsignature{0}"));
check("quarter c present", gen.includes("\\qu{c}"));
check("half e present", gen.includes("\\hu{e}"));
check("chord uses \\zq c + \\zq e + top g", gen.includes("\\zq{c}\\zq{e}\\qu{g}"));
const genParsed = parseMusixTeX(gen);
check("generated doc parses back: 4 note events + no warnings",
  genParsed.events.filter(e => e.type === "note").length === 4 && genParsed.warnings.length === 0);
check("empty input → null", notesToMusixTex([], {}) === null);

console.log("[11] 自動採譜 — 音声ピッチ検出 (合成サイン波)");
const sr = 11025, frame = new Float32Array(1024);
for (let i = 0; i < frame.length; i++) frame[i] = 0.4 * Math.sin(2 * Math.PI * 440 * i / sr);
const m440 = detectPitch(frame, sr);
check("440 Hz sine → MIDI 69 (A4)", Math.abs(m440 - 69) < 0.5);
const silent = new Float32Array(1024);
check("silence → 0", detectPitch(silent, sr) === 0);
// フレーム列 → イベント: A4 を 8 フレーム、休み 8、C5 を 8
const seq = [];
for (let i = 0; i < 8; i++) seq.push(69);
for (let i = 0; i < 8; i++) seq.push(0);
for (let i = 0; i < 8; i++) seq.push(72);
const aev = pitchFramesToEvents(seq, 0.05);
check("2 notes segmented from frames", aev.length === 2 &&
  aev[0].midis[0] === 69 && aev[1].midis[0] === 72);
check("audio events → MusixTeX doc", (notesToMusixTex(aev, { source: "test.wav" }) || "").includes("\\input musixtex"));

console.log("[12] モーツァルト・ビジョン — 音 → 光の波長帯");
const a4 = midiToWavelength(69);
check("A4 440Hz → ≈484THz", Math.abs(a4.thz - 484) < 2);
check("A4 → ≈620nm (赤)", a4.nm > 610 && a4.nm < 630);
const c4w = midiToWavelength(60);
check("C4 → 510〜530nm (緑)", c4w.nm > 510 && c4w.nm < 530);
check("同じ音名は同じ波長 (オクターブ不変)",
  Math.abs(midiToWavelength(69).nm - midiToWavelength(81).nm) < 0.01);
let inRange = true;
for (let m = 21; m <= 108; m++) {
  const nm = midiToWavelength(m).nm;
  if (nm < 380 || nm > 780) inRange = false;
}
check("全ピアノ音域 (A0〜C8) が可視域 380〜780nm に収まる", inRange);
const red = wavelengthToRGB(620), blue = wavelengthToRGB(460), green = wavelengthToRGB(520);
check("620nm は赤が優勢", red[0] > 200 && red[1] < 150 && red[2] < 60);
check("460nm は青が優勢", blue[2] > 200 && blue[0] < 100);
check("520nm は緑が優勢", green[1] > 200 && green[0] < 100 && green[2] < 100);

console.log("[13] モーツァルト・ビジョン — 楽譜 → スペクトル帯");
const spec = scoreToSpectral(parseMusixTeX(TEMPLATES[0].body));
check("B♭ 音階 16 音が 16 帯になる", spec.items.length === 16);
check("帯の開始拍が単調非減少",
  spec.items.every((it, i) => i === 0 || it.startBeat >= spec.items[i - 1].startBeat));
check("各帯が色・波長・イベント番号を持つ",
  spec.items.every(it => /^rgb\(/.test(it.color) && it.nm >= 380 && it.nm <= 780 &&
                         Number.isInteger(it.eventIndex)));
check("先頭は B♭3 (MIDI 58) の帯", spec.items[0].midi === 58);
check("イベント総数 16 (休符なし・小節線除く)", spec.eventCount === 16);
const chordSpec = scoreToSpectral(parseMusixTeX(TEMPLATES[2].body));
check("和音は同一開始拍に複数の帯",
  chordSpec.items.filter(it => it.startBeat === 0).length === 3);

if (failures) { console.error(`\n${failures} failure(s)`); process.exit(1); }
console.log("\nMusicTeX Studio engine tests: all OK");
