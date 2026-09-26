/*
 * engine-test.js — BADA Studio (音・映像・作曲スタジオ) のエンジン単体テスト
 *
 *   node bada_studio/tools/engine-test.js
 *
 * index.html のインライン <script> を DOM なしで読み込み、次を検証します:
 *   1. 音名・和音・セル (小節の和音) ・主題テキストの解析
 *   2. 自動作曲 (機能和声の進行、主題、提示部の入り、オーケストラの行) の再現性と妥当性
 *   3. 対位法の生成 (4 声 + 行のオーケストラ、音域、音符の数、平行 5/8 度の数)
 *   4. MIDI / WAV / score.json の書き出し
 *   5. タイムラインのクリップ (分割・長さ) のモデル
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }
const sandbox = { console, TextEncoder, window: { __ENGINE_TEST__: true }, document: undefined, navigator: {}, Math };
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "bada-studio-inline.js" });
const E = sandbox;

let pass = 0, fail = 0;
function ok(cond, name) { if (cond) { pass++; console.log("  ✔ " + name); } else { fail++; console.error("  ✘ " + name); } }
function eq(a, b, name) { const A = JSON.stringify(a), B = JSON.stringify(b); ok(A === B, name + (A === B ? "" : "  [" + A.slice(0, 160) + " !== " + B.slice(0, 160) + "]")); }

console.log("1. 解析");
eq(E.n("D4"), 62, "n(D4)"); eq(E.n("Bb1"), 34, "n(Bb1)"); eq(E.n("X4"), null, "n(不正)");
eq(E.nameOf(61), "C#4", "nameOf(61)");
E.setKey(2, true);
eq(Array.from(E.chord("A7").pcs), [9, 1, 4, 7], "A7 の構成音");
ok(E.chord("Hm") === null, "読めない和音は null");
eq(E.parseCell("Gm A7").h.join(" "), "Gm Gm A7 A7", "セル: 和音 2 個 → 2 拍ずつ");
eq(E.parseCell("Dm Gm A7 A7").h.join(" "), "Dm Gm A7 A7", "セル: 和音 4 個 → 1 拍ずつ");
ok(!!E.parseCell("Dm Gm A7").err, "セル: 3 個はエラー");
eq(E.parseCell(""), null, "セル: 空欄は null (主進行に従う)");
eq(JSON.stringify(E.parseNotes("D4:3 E4:1 R:0.5 f#4").notes), "[[3,62],[1,64],[0.5,null],[1,66]]", "主題テキストの解析");
ok(!!E.parseNotes("D4:x").err && !!E.parseNotes("").err, "主題テキストのエラー");
eq(E.notesToText([[3, 62], [0.5, null]]), "D4:3 R:0.5", "主題テキストへの書き出し");
eq(E.degChord("V", { tonic: 2, minor: true }), "A7", "ニ短調の V = A7");
eq(E.degChord("VI", { tonic: 4, minor: true }), "C", "ホ短調の VI = C");
eq(E.degChord("IV", { tonic: 0, minor: false }), "F", "ハ長調の IV = F");

console.log("2. 自動作曲");
const p1 = E.blankProject(16), p2 = E.blankProject(16);
ok(p1.lines.length >= 5, "オーケストラの行は 5 行以上 (" + p1.lines.length + " 行)");
E.autoCompose(p1); E.autoCompose(p2);
eq(p1.main, p2.main, "同じ乱数なら同じ進行");
ok(p1.main.length === 16 && p1.main.every(c => !E.parseCell(c).err), "進行 16 小節はすべて読める和音");
eq(p1.main[15], "Dm", "最後は主和音");
eq(p1.main[14], "A7", "最後の前は属七");
const sb = p1.subject.reduce((s, x) => s + x[0], 0);
ok(Math.abs(sb - 8) < 1e-9, "主題は 8 拍");
ok(p1.subject.every(x => x[1] === null || (x[1] >= 55 && x[1] <= 84)), "主題の音域");
eq(p1.entries.map(e => e.v + e.bar).join(","), "A0,S2,T4,B6,S12", "提示部の入り (A→S→T→B、2 小節ごと) + 再現");
const p3 = E.blankProject(8); p3.key = { tonic: 0, minor: false }; p3.seed = 11; E.autoCompose(p3);
ok(p3.main.every(c => c.split(/\s+/).every(x => /^[A-G](#|b)?(m|7|dim)?$/.test(x))), "長調の進行も読める和音: " + p3.main.join(" | "));
const slow = E.blankProject(8); slow.seed = 3; E.autoCompose(slow, { slow: true });
ok(slow.lines.every(L => L.pat !== "arp16" && L.pat !== "pulse"), "ゆっくり (レクイエム) では 16 分の分散・刻みを使わない");

console.log("3. 対位法 + オーケストラ");
const R = E.compose(p1);
ok(R.notes.length > 200, "音符が生成される (" + R.notes.length + ")");
const voices = R.notes.filter(x => x.v);
ok(E.VOICES.every(v => voices.some(x => x.v === v)), "4 声すべてに音がある");
ok(voices.every(x => x.m >= E.RANGE[x.v][0] && x.m <= E.RANGE[x.v][1]), "4 声の音域");
ok(R.notes.filter(x => x.i === "timp").length > 0 && R.notes.filter(x => x.i === "cb").length > 0, "ティンパニとコントラバスの行が鳴る");
ok(R.notes.every(x => x.i in E.INST), "楽器名はすべて INST にある");
ok(R.notes.every(x => x.db > 0 && x.b >= 0 && x.b < 16 * 4), "音符の位置と長さ");
ok(R.chk.par <= 6, "平行 5/8 度が少ない (" + R.chk.par + ")");
const R2 = E.compose(p1);
eq(R.notes.length, R2.notes.length, "同じ乱数なら同じ結果");
const labs = voices.filter(x => x.lab);
ok(labs.length === p1.entries.length * p1.subject.filter(x => x[1] !== null).length, "主題の音がすべて置かれる (" + labs.length + ")");
p1.lines[1].cells[0] = "Bb"; p1.lines[1].pat = "hold"; const R3 = E.compose(p1);
ok(R3.notes.some(x => x.line === 1 && x.b < 4 && x.m % 12 === 10), "行ごとの和音 (Vn II の第 1 小節を B♭ に)");
p1.style = "piano"; const R4 = E.compose(p1);
ok(R4.notes.filter(x => x.v).every(x => x.i === "pf"), "ピアノ様式では 4 声がピアノ");
p1.style = "sampler"; const R5 = E.compose(p1);
ok(R5.notes.filter(x => x.v).every(x => x.i === "smp"), "サンプラー様式では 4 声が読み込んだ音源");
p1.style = "orch";

console.log("4. 書き出し");
const mid = E.midiFile(p1, R);
ok(mid[0] === 0x4d && mid[1] === 0x54 && mid[2] === 0x68 && mid[3] === 0x64, "MIDI ヘッダ");
ok(mid.length > 2000, "MIDI の大きさ (" + mid.length + ")");
const wav = E.wavFile([new Float32Array(100), new Float32Array(100)], 44100);
ok(wav.length === 44 + 400 && String.fromCharCode(wav[0], wav[1], wav[2], wav[3]) === "RIFF", "WAV ヘッダ");
const sc = E.scoreJson(p1, R);
ok(sc.notes.length === voices.length && sc.harm.length === 64 && sc.bar_times.length === 17 && sc.extras.length > 0, "score.json (音符・和声・小節時刻・extras)");
ok(sc.notes.every(x => typeof x.t === "number" && x.d > 0 && "SATB".indexOf(x.v) >= 0), "score.json の音符");

console.log("5. タイムライン");
E.S.proj = p1; E.S.R = E.compose(p1); E.S.sources = [{ name: "a.wav", buf: { duration: 10 }, peaks: new Float32Array(500), base: 60 }];
E.S.proj.clips = [E.newClip(0, 0, 1.5)];
eq([E.S.proj.clips[0].start, E.S.proj.clips[0].dur, E.S.proj.clips[0].src], [1.5, 10, "a.wav"], "クリップを置く");
E.S.sel = E.S.proj.clips[0].id; E.$ = () => ({}); E.setMsg = () => {}; E.changed = () => {};
E.splitAt(4);
eq(E.S.proj.clips.map(c => [c.start, c.off, c.dur]), [[1.5, 0, 2.5], [4, 2.5, 7.5]], "再生位置で分割");
ok(Math.abs(E.totalDur() - Math.max(11.5, R.dur)) < 1e-9, "全体の長さ (クリップと作曲の長い方)");
ok(E.activeVideoClip(2) === null, "映像トラックにクリップがなければ null");

console.log("6. 楽譜 (score.json)");
const sj = { bpm: 60, duration: 8, bar_times: [0, 4, 8], notes: [{ v: "S", t: 0, d: 1, m: 62, label: "主題", beat: 0, src: "20260923_080607" }, { v: "B", t: 1, d: 2, m: 50, label: null, beat: 1 }, { v: "Q", t: 2, d: 0, m: 64.4 }],
             extras: [{ v: "SP", t: 0, d: 4, m: 74, gain: 0.1, rid: "VOXSY" }, { v: "REC", t: 4, d: 4, m: 0, gain: 0.5, src: "/x/20260923_080607.wav", off: 12.5, rid: "20260923_080607", fin: 1, fout: 2 }, { v: "TB", t: 4, d: 1, m: 70, gain: 0 }],
             harm: ["Dm", "Dm", "Gm", "A7"], sections: [{ t: 0, bar: 1, title: "Intro" }], meta: { title: "T" } };
const X = E.parseScore(sj);
eq([X.notes.length, X.notes[2].v, X.notes[2].m, X.notes[2].d], [3, "S", 64, 0.5], "音符の正規化 (声部・音高・長さ)");
eq(Object.keys(X.kinds).sort(), ["REC", "SP", "TB"], "追加の種類");
ok(X.duration === 8 && X.bpm === 60, "長さと速さ");
ok(() => { try { E.parseScore({}); return false; } catch (e) { return true; } }, "notes がなければエラー");
E.S.proj = E.blankProject(4); E.S.score = X; E.S.sources = [{ name: "a-20260923_080607.mp3", buf: { duration: 100 }, peaks: new Float32Array(10), base: 60 }];
E.S.proj.scoreTr = 2; E.S.proj.scoreTempo = 200; E.S.proj.scoreStart = 10;
const ev = E.scoreEvents();
ok(ev.length === 4 && ev.every(e => e.i in E.INST), "再生用の音符 (4 声 + SP、TB と REC は除く)");
ok(Math.abs(ev[0].t - 10) < 1e-9 && ev[0].m === 64 && Math.abs(ev[1].t - 10.5) < 1e-9, "開始位置・移調・速さ (200% で半分の時間)");
const rc = E.scoreRecClips();
ok(rc.length === 1 && rc[0].src && Math.abs(rc[0].clip.start - 12) < 1e-9 && rc[0].clip.off === 12.5 && Math.abs(rc[0].clip.dur - 2) < 1e-9, "実音の抜粋を録音の日時でファイルに結びつける");
E.S.sources = []; ok(E.scoreRecClips()[0].missing === "20260923_080607", "録音がなければ missing");
ok(Math.abs(E.scoreEnd() - 14) < 1e-9, "楽譜の終わり (開始 10 + 8/2)");
const xo = E.exportScoreJson();
ok(xo.bpm === 120 && xo.notes[0].m === 64 && xo.notes[1].t === 0.5 && xo.harm[0] === "Em" && xo.extras[0].m === 76 && xo.extras[1].m === 0, "score.json への書き戻し (速さ・移調を反映)");
E.S.proj.scoreTr = 0; E.S.proj.scoreTempo = 100;

console.log("7. mp3 / mp4 → json (採譜)");
const sr = 22050, x = new Float32Array(sr * 2);
for (let i = 0; i < sr; i++) x[i] = 0.5 * Math.sin(2 * Math.PI * 440 * i / sr) * Math.exp(-i / sr * 2);
for (let i = sr; i < sr * 2; i++) { const k = i - sr; x[i] = (0.4 * Math.sin(2 * Math.PI * 220 * k / sr) + 0.35 * Math.sin(2 * Math.PI * 329.63 * k / sr)) * Math.exp(-k / sr * 2); }
const tr = E.transcribe(x, sr);
ok(tr.segs.length >= 2 && tr.segs.length <= 4, "打鍵の数 (2 つの区間): " + tr.segs.length);
ok(tr.segs[0].m.indexOf(69) >= 0, "第 1 区間に A4 (69): " + JSON.stringify(tr.segs[0].m));
const last = tr.segs[tr.segs.length - 1];
ok(last.m.indexOf(57) >= 0 && last.m.indexOf(64) >= 0, "第 2 区間に A3 (57) と E4 (64): " + JSON.stringify(last.m));
ok(tr.harm.length === 4 && /^[A-G]/.test(tr.harm[0]), "和音 (♩=60、4 拍): " + tr.harm[0]);
const sj2 = E.scoreFromTranscription(tr, "20260923_080607.mp3");
ok(sj2.notes.length >= 3 && sj2.extras[0].v === "REC" && sj2.extras[0].rid === "20260923_080607" && sj2.bar_times.length === 2, "score.json の形 (音符・REC・小節)");
const X2 = E.parseScore(sj2); ok(X2.notes.length === sj2.notes.length && X2.kinds.REC === 1, "変換した json は楽譜として読める");

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
