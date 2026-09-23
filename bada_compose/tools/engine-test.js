/*
 * engine-test.js — BADA Compose (作曲スタジオ) のエンジン単体テスト
 *
 *   node bada_compose/tools/engine-test.js
 *
 * index.html のインライン <script> を DOM なしで読み込み、次を検証します:
 *   1. 和音・音名・主題テキストの解析
 *   2. ひな形 Piano Concerto BADA が Python 版 (bada_fuga/compose_pconcerto.py の出力
 *      score_pconcerto.json) と和声・テンポ・主題の配置・役割・見出しで一致すること
 *   3. 対位法の生成 (再現性・音域・声部交差・平行 5/8 度の数)
 *   4. 小節の挿入 / 複製 / 削除で主題がずれないこと
 *   5. MIDI / WAV / score.json の書き出し
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }
const sandbox = { console, TextEncoder, window: { __ENGINE_TEST__: true }, document: undefined, navigator: {} };
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "bada-compose-inline.js" });
const E = sandbox;

let pass = 0, fail = 0;
function ok(cond, name) { if (cond) { pass++; console.log("  ✔ " + name); } else { fail++; console.error("  ✘ " + name); } }
function eq(a, b, name) { const A = JSON.stringify(a), B = JSON.stringify(b); ok(A === B, name + (A === B ? "" : "  [" + A.slice(0, 200) + " !== " + B.slice(0, 200) + "]")); }

console.log("1. 解析");
eq(E.n("D4"), 62, "n(D4)"); eq(E.n("Bb1"), 34, "n(Bb1)"); eq(E.n("X4"), null, "n(不正)");
eq(E.nameOf(61), "C#4", "nameOf(61)");
E.setKey(2, true);
eq(Array.from(E.chord("A7").pcs), [9, 1, 4, 7], "A7 の構成音");
eq(E.chord("A7").scale.join(","), "1,2,4,5,7,9,10", "A7 の音階 (ニ短調で C → C#)");
eq(E.chord("G/B").bass, 11, "G/B の低音");
ok(E.chord("Hm") === null && E.chord("Dm9") === null, "読めない和音は null");
eq(E.transposeChordName("F#m7b5/A", 2), "G#m7b5/B", "和音名の移調");
eq(E.parseChordInput("Gm A7").h.join(" "), "Gm Gm A7 A7", "和音 2 個 → 2 拍ずつ");
ok(!!E.parseChordInput("Dm Gm A7").err, "和音 3 個はエラー");
eq(JSON.stringify(E.parseNotes("D4:3 E4:1 R:0.5 f#4").notes), "[[3,62],[1,64],[0.5,null],[1,66]]", "主題テキストの解析");
ok(!!E.parseNotes("D4:x").err && !!E.parseNotes("").err, "主題テキストのエラー");
eq(E.notesToText([[3, 62], [0.5, null]]), "D4:3 R:0.5", "主題テキストへの書き出し");

console.log("2. ひな形と Python 版の一致");
const proj = E.makePreset("pconcerto");
eq(proj.bars.length, 123, "Piano Concerto BADA は 123 小節");
const pyPath = path.join(__dirname, "..", "..", "bada_fuga", "score_pconcerto.json");
if (fs.existsSync(pyPath)) {
  const py = JSON.parse(fs.readFileSync(pyPath, "utf8"));
  const P = E.projectPiece(proj);
  eq(Array.from(P.harm), py.harm, "和声 (492 拍) が一致");
  const bt = E.beatTimes(proj);
  const barT = proj.bars.map((_, i) => +bt[i * 4].toFixed(4)).concat([+bt[bt.length - 1].toFixed(4)]);
  ok(barT.every((t, i) => Math.abs(t - py.bar_times[i]) < 2e-3), "テンポ・マップ (小節の開始時刻) が一致");
  const key = (b, mm, lab, v) => [b, mm, lab, v].join("|");
  const pyLab = py.notes.filter(x => x.label).map(x => key(x.beat, x.m, x.label, x.v)).sort();
  const jsLab = [];
  E.VOICES.forEach(v => P.fixed[v].forEach(f => { if (f[3]) jsLab.push(key(f[0], f[2], f[3], v)); }));
  jsLab.sort();
  eq(jsLab.length, pyLab.length, "主題の音の数が一致 (" + pyLab.length + ")");
  eq(jsLab, pyLab, "主題の音 (拍・音高・名前・声部) が一致");
  const pyH = py.extras.filter(x => x.v === "H").map(x => x.beat + "|" + x.m).sort();
  const jsH = [];
  proj.entries.filter(e => e.v === "H").forEach(e => { let t = e.beat; e.notes.forEach(x => { if (x[1] !== null) jsH.push(t + "|" + x[1]); t += x[0]; }); });
  eq(jsH.sort(), pyH, "最上声の B-A-D-A (H) が一致");
  const roleBad = py.notes.filter(x => { const b = proj.bars[Math.floor(x.beat / 4)]; return b.role !== x.role || Math.abs(b.dyn - x.dyn) > 1e-9 || Math.abs(b.det - x.det) > 1e-9; });
  eq(roleBad.length, 0, "小節ごとの役割・強弱・奏法が一致");
  eq(P.sections.map(s => (s.bar + 1) + " " + s.title), py.sections.map(s => s.bar + " " + s.title), "見出しが一致");
  const pyE = py.entries.map(e => e.bar + " " + e.label + " " + e.v).sort();
  eq(P.entries.map(e => (Math.floor(e[0] / 4) + 1) + " " + e[1] + " " + e[2]).sort(), pyE, "主題の入り (表示) が一致");
} else console.log("  (bada_fuga/score_pconcerto.json が無いので Python 版との比較は省略)");
eq(E.makePreset("mov1").bars.length, 58, "I 楽章は 58 小節");
eq(E.makePreset("mov2").bars.length, 14, "II 楽章は 14 小節");
eq(E.makePreset("mov3").bars.length, 51, "III 楽章は 51 小節");

console.log("3. 対位法の生成");
const R1 = E.compose(proj), R2 = E.compose(E.makePreset("pconcerto"));
eq(R1.notes.length, R2.notes.length, "同じ乱数なら同じ結果 (音数)");
eq(R1.events.S.slice(0, 40), R2.events.S.slice(0, 40), "同じ乱数なら同じ結果 (ソプラノ)");
ok(R1.notes.length > 3000, "協奏曲の音数 " + R1.notes.length);
ok(Math.abs(R1.duration - 449.28) < 0.5, "演奏時間 " + R1.duration.toFixed(1) + " 秒 (Python 版 449.3 秒)");
let outOfRange = 0, crossing = 0;
const Pc = R1.P, G = E.generate(Pc, proj.seed);
for (let b = 0; b < Pc.N; b++) {
  E.VOICES.forEach(v => { const mm = G.skel[v][b]; if (mm !== null && (mm < E.RANGE[v][0] || mm > E.RANGE[v][1])) outOfRange++; });
  const s = E.VOICES.map(v => G.skel[v][b] !== null ? G.skel[v][b] : Pc.fixedCover(v)[b]);
  for (let i = 0; i < 3; i++) if (s[i] !== null && s[i + 1] !== null && s[i] < s[i + 1]) crossing++;
}
eq(outOfRange, 0, "自由声部は音域内");
ok(crossing < 40, "声部交差はごく少ない (" + crossing + ")");
ok(R1.check.par < 60, "平行 5 度・8 度 " + R1.check.par + " (Python 版と同程度)");
const R3 = E.compose(Object.assign(E.makePreset("pconcerto"), { seed: 777 }));
ok(JSON.stringify(R3.events.S.slice(0, 60)) !== JSON.stringify(R1.events.S.slice(0, 60)), "乱数を変えると自由声部が変わる");
const pianoOnly = E.compose(Object.assign(E.makePreset("mov2"), { style: "piano" }));
ok(pianoOnly.notes.every(x => x.i === "pf" || x.i === "pfh"), "ピアノ独奏はピアノの音だけ");
const strOnly = E.compose(Object.assign(E.makePreset("mov2"), { style: "strings" }));
ok(strOnly.notes.every(x => ["vn1", "vn2", "va", "vc", "cb"].includes(x.i)), "弦楽合奏は弦の音だけ");
const tr = E.compose(Object.assign(E.makePreset("mov2"), { transpose: 2 })), tr0 = E.compose(E.makePreset("mov2"));
ok(tr.notes.every((x, i) => x.m === tr0.notes[i].m + 2), "出力の調: +2 半音");
const blank = E.compose(E.blankProject());
ok(blank.notes.length > 50 && blank.P.nbars === 8, "新規 8 小節も作曲できる");
const mel = E.genMelody(E.blankProject(), 0, 4, 42), dur = mel.reduce((a, x) => a + x[0], 0);
ok(Math.abs(dur - 16) < 1e-9 && mel.every(x => x[1] >= 62 && x[1] <= 79), "和音から作る旋律は 4 小節・音域内");

console.log("4. 小節の編集");
const sandboxProj = E.makePreset("mov2");
E.S.proj = sandboxProj;
const before = sandboxProj.entries.filter(e => e.beat >= 12).map(e => e.beat);
E.insertBar(3, null);
eq(sandboxProj.bars.length, 15, "挿入で 15 小節");
eq(sandboxProj.entries.filter(e => e.beat >= 16).map(e => e.beat), before.map(b => b + 4), "挿入の後ろの主題は 1 小節ずれる");
E.deleteBar(3);
eq(sandboxProj.entries.filter(e => e.beat >= 12).map(e => e.beat), before, "削除で元に戻る");
const nEnt = sandboxProj.entries.length;
E.insertBar(1, sandboxProj.bars[0]);
ok(sandboxProj.entries.length > nEnt && sandboxProj.bars[1].h.join() === sandboxProj.bars[0].h.join(), "複製は和音と主題を写す");

console.log("5. 書き出し");
const mid = E.midiFile(proj, R1, 0, 123);
eq(String.fromCharCode(mid[0], mid[1], mid[2], mid[3]), "MThd", "MIDI ヘッダ");
const ntrk = (mid[10] << 8) | mid[11];
ok(ntrk >= 10, "MIDI トラック数 " + ntrk);
let p = 14, tracksOk = true;
for (let i = 0; i < ntrk; i++) {
  if (String.fromCharCode(mid[p], mid[p + 1], mid[p + 2], mid[p + 3]) !== "MTrk") { tracksOk = false; break; }
  const len = (mid[p + 4] << 24) | (mid[p + 5] << 16) | (mid[p + 6] << 8) | mid[p + 7];
  if (mid[p + 8 + len - 3] !== 0xff || mid[p + 8 + len - 2] !== 0x2f) { tracksOk = false; break; }
  p += 8 + len;
}
ok(tracksOk && p === mid.length, "MIDI の各トラックが End of Track で閉じる");
const wav = E.wavFile([new Float32Array([0, 0.5, -0.5, 1]), new Float32Array([0, 0.5, -0.5, -1])], 44100);
eq(String.fromCharCode(wav[0], wav[1], wav[2], wav[3], wav[8], wav[9], wav[10], wav[11]), "RIFFWAVE", "WAV ヘッダ");
eq(wav.length, 44 + 4 * 2 * 2, "WAV の長さ");
const sj = E.scoreJson(proj, R1);
ok(["bpm", "beats_per_bar", "nbars", "duration", "bar_times", "notes", "entries", "sections", "harm", "meta", "extras"].every(k => k in sj), "score.json のキー");
eq(sj.meta.style, "pconcerto", "score.json の様式 (synth.py の pconcerto)");
ok(sj.extras.every(x => ["V1", "V2", "VA", "VC", "CB", "FL", "WW", "CL", "HN", "TR", "TB", "TP", "H"].includes(x.v)), "score.json の重ねは synth.py の楽器名");
eq(sj.bar_times.length, 124, "score.json の小節時刻");
eq(E.sanitizeName("a/b:c d"), "a_b_c_d", "ファイル名の無害化");
eq(E.asciiName("Piano_Concerto_BADA_—_in_D_minor.mid"), "Piano_Concerto_BADA_-_in_D_minor.mid", "ダウンロード名を ASCII に (ダッシュ)");
eq(E.asciiName("新しい曲.wav"), "bada-compose.wav", "ダウンロード名を ASCII に (日本語だけの名前)");

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
