/*
 * engine-test.js — Bada Akasha のエンジン単体テスト
 *
 *   node bada_akasha/tools/engine-test.js
 *
 *   1. index.html が src から最新にビルドされていること / UI スクリプトの構文
 *   2. 検索 — トークン化 (日本語 2-gram / 英単語), BM25, 被覆率, 出典の辞書 (KWIC)
 *   3. 「正直な無知」— 論文にない質問は IGNORANCE になる (Bada MODE 1)
 *   4. Bada MODE 1 — 振幅の和 = 1, PICK は重複なし・範囲内, SEED で再現可能
 *   5. 方程式 — 既知の関係を再発見し、ζ(3)・Γ(1/3) は「未知」, Bada が独立に再検証
 *   6. 統計 — 二項分布の上側確率, z 値
 *   7. ポート — 心拍の基準・精度, 隠れた規則, 判定 (Bada MODE 3)
 *   8. 組み換え生成 — 材料の文字だけを使い、seed で再現可能
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");

const root = path.join(__dirname, "..");
let pass = 0, fail = 0;
function ok(cond, msg){ if (cond){ pass++; } else { fail++; console.error("FAIL: " + msg); } }
function near(a, b, eps, msg){ ok(Math.abs(a - b) <= eps, msg + " (got " + a + ", want " + b + ")"); }

/* 1. ビルドと構文 */
try { execFileSync(process.execPath, [path.join(__dirname, "build.js"), "--check"], { stdio: "pipe" }); ok(true, ""); }
catch (e){ ok(false, "index.html が古い: node bada_akasha/tools/build.js を実行してください"); }
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const eng = html.match(/<script id="engine">([\s\S]*?)<\/script>/);
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
ok(eng && scripts.length === 4, "engine + 4 inline scripts (bada.js, akasha.bada, corpus, UI)");
scripts.forEach((s, i) => { try { new vm.Script(s, { filename: "inline" + i + ".js" }); ok(true, ""); } catch (e){ ok(false, "構文エラー inline" + i + ": " + e.message); } });
ok(!/connect-src (?!'none')/.test(html), "CSP で外部通信を禁止 (端末内で完結)");

const ctx = { module: { exports: {} } };
vm.createContext(ctx);
vm.runInContext(eng[1], ctx);
const AK = ctx.module.exports;
const Bada = require(path.join(root, "..", "bada_gui_ide", "www", "bada.js"));
const AKASHA = fs.readFileSync(path.join(root, "src", "akasha.bada"), "utf8");
const CORPUS = JSON.parse(fs.readFileSync(path.join(root, "src", "corpus.json"), "utf8"));
const TEXTS = CORPUS.passages.map(p => p[2]);
function bada(mode, inputs){
  const r = Bada.run(AK.badaHeader(mode, inputs) + AKASHA, { maxSteps: 5000000 });
  ok(r.ok, "Bada MODE " + mode + " が実行できる: " + (r.parseErrors[0] || r.error || ""));
  return AK.parseBadaOutput(r.output);
}

/* 2. 検索 */
ok(CORPUS.docs.length === 16 && TEXTS.length > 1000, "論文 16 本・段落 1000 以上");
ok(CORPUS.passages.every(p => p[0] >= 0 && p[0] < 16 && p[1] >= 1 && p[1] <= CORPUS.docs[p[0]].pages), "出典 (文書・ページ) が範囲内");
const tk = AK.tokenize("ホッジ予想 and the Jones polynomial");
ok(tk.includes("ホッ") && tk.includes("予想") && tk.includes("jones") && tk.includes("polynomial") && !tk.includes("the") && !tk.includes("and"), "日本語 2-gram と英単語, ストップワード除去");
ok(AK.tokenize("曲面").includes("曲面") && AK.tokenize("量").includes("量"), "1 文字の語も残す");
const ix = AK.buildIndex(TEXTS);
function topDoc(q){ const h = AK.search(ix, q, 5); return h.length ? CORPUS.docs[CORPUS.passages[h[0].pid][0]].file : null; }
ok(topDoc("ホッジ予想 調和形式 ゼロモード") === "hodge_zeromodes-1", "ホッジ予想 → hodge_zeromodes");
ok(topDoc("P ≠ NP 充足可能性 ゼロモード") === "pnp_zeromodes", "P≠NP → pnp_zeromodes");
ok(topDoc("Jones 多項式 熱感知 三葉結び目") === "exo-gamma", "Jones 熱感知 → exo-gamma");
ok(topDoc("reviser grammar Q# front end") === "bada-quantum-reviser-paper", "reviser → 論文");
const PR = TEXTS.map(AK.proseScore);
ok(AK.proseScore("零保存とは、位相の段階でも確かな零が生き残る性質のことです。") > 0.9, "文章は文章らしさが高い");
ok(AK.proseScore("87\n def f(x) {\n88\n return (x + 1);\n89\n }") < 0.3, "ソースコードは低い");
const jp = AK.search(ix, "Jones 多項式 熱感知", 3, PR)[0];
ok(PR[jp.pid] > 0.5, "文章優先の検索では最上位が文章の段落 (prose " + PR[jp.pid].toFixed(2) + ")");
const hs = AK.search(ix, "ホッジ予想", 8);
ok(hs.every((h, i) => i === 0 || hs[i - 1].score >= h.score), "スコア降順");
ok(hs[0].cover > 0.9, "ホッジ予想の被覆率は高い (" + hs[0].cover.toFixed(2) + ")");
const kw = AK.concordance(TEXTS, "Riemann", 30, 500);
ok(kw.length > 5 && kw.every(r => r.hit.toLowerCase() === "riemann"), "辞書: 大文字小文字を区別せず出現箇所を返す");
ok(AK.concordance(TEXTS, "  ", 30).length === 0, "空の用語は結果なし");
ok(AK.bestSentences("これは零保存についての説明の文です。まったく関係のない話題の文です。零保存は数値でも確かめられる性質です。", "零保存", 2).length === 2, "質問語を含む文を選ぶ");

/* 3. 正直な無知 */
for (const q of ["2031年の日経平均株価はいくらか", "明日の宝くじの当選番号", "私の前世の名前"]){
  const h = AK.search(ix, q, 8);
  const cover = h.length ? h[0].cover : 0;
  const b = h.length ? bada(1, { SCORES: h.map(x => x.score), COVER: cover, SEED: 7, PICK: Math.min(3, h.length), FLOOR: 0.34 }) : { ignorance: true };
  ok(b.ignorance, "論文にない質問は IGNORANCE: " + q + " (cover " + cover.toFixed(2) + ")");
}

/* 4. Bada MODE 1 */
const sc = [9.1, 7.5, 3.2, 2.0, 1.1, 0.9, 0.5, 0.2];
const m1 = bada(1, { SCORES: sc, COVER: 0.9, SEED: 12345, PICK: 3, FLOOR: 0.34 });
near(m1.amp.reduce((a, b) => a + b, 0), 1, 1e-4, "振幅の和 = 1");
ok(m1.amp.every((a, i) => i === 0 || m1.amp[i - 1] >= a), "振幅はスコア順");
ok(m1.pick.length === 3 && new Set(m1.pick).size === 3 && m1.pick.every(i => i >= 0 && i < 8), "PICK は 3 件・重複なし・範囲内");
const m1b = bada(1, { SCORES: sc, COVER: 0.9, SEED: 12345, PICK: 3, FLOOR: 0.34 });
ok(m1b.pick.join() === m1.pick.join(), "同じ SEED → 同じ選択");
const counts = new Array(8).fill(0);
for (let s = 1; s <= 60; s++){ const r = bada(1, { SCORES: sc, COVER: 0.9, SEED: s * 7919, PICK: 1, FLOOR: 0.34 }); counts[r.pick[0]]++; }
ok(counts[0] > counts[4] && counts[0] + counts[1] > 30, "振幅の大きい段落ほど選ばれる (" + counts.join(",") + ")");
const all = bada(1, { SCORES: [3, 2, 1], COVER: 0.5, SEED: 99, PICK: 3, FLOOR: 0.34 });
ok(all.pick.slice().sort().join() === "0,1,2", "全件抽出は全段落を 1 回ずつ");

/* 5. 方程式 */
const want = { "ζ(2)": "ζ(2) = 1/6 · π^2", "ζ(4)": "ζ(4) = 1/90 · π^4", "ζ(6)": "ζ(6) = 1/945 · π^6", "ζ(8)": "ζ(8) = 1/9450 · π^8",
  "Γ(1/2)": "Γ(1/2) = π^1/2", "Γ(3/2)": "Γ(3/2) = 1/2 · π^1/2", "Γ(5/2)": "Γ(5/2) = 3/4 · π^1/2" };
AK.TARGETS.forEach(t => {
  const r = AK.findRelation(t);
  if (want[t.name]){
    ok(r && AK.formatRelation(t, r) === want[t.name], t.name + " を再発見: " + (r ? AK.formatRelation(t, r) : "なし"));
    if (r){
      const b = bada(2, { KIND_T: t.kind, ARG_T: t.arg, BASE: r.base.id, POW: r.pow, NUM: r.num, DEN: r.den });
      ok(b.diff < 1e-11, t.name + " を Bada が独立に再検証 (diff " + b.diff + ")");
    }
  } else {
    ok(r === null, t.name + " は未知 (閉じた形なし): " + (r ? AK.formatRelation(t, r) : ""));
  }
});
const rr = AK.rng(11); let fake = 0;
for (let i = 0; i < 300; i++){ if (AK.findRelation({ name: "x" }, { value: 0.5 + 4.5 * rr() })) fake++; }
ok(fake <= 3, "ランダムな数から偽の関係はほぼ出ない (" + fake + "/300)");
console.log("  偽の関係: " + fake + "/300");
near(AK.zetaFn(3), 1.2020569031595942, 1e-13, "ζ(3) (Apéry 定数)");
near(AK.gammaFn(1 / 3), 2.678938534707747, 1e-12, "Γ(1/3)");
const rz = AK.rationalize(355 / 113, 1000, 1e-15);
ok(rz && rz.p === 355 && rz.q === 113, "連分数で 355/113");
ok(AK.rationalize(Math.PI, 100, 1e-12) === null, "π は小さい分母の有理数ではない");
const wrong = bada(2, { KIND_T: 1, ARG_T: 3, BASE: 1, POW: 3, NUM: 1, DEN: 26 });
ok(wrong.diff > 1e-4, "偽の関係 ζ(3) = π³/26 は Bada 再検証で否定される (diff " + wrong.diff + ")");

/* 6. 統計 */
near(AK.binomTail(0, 10, 0.3), 1, 1e-15, "P(X≥0)=1");
near(AK.binomTail(11, 10, 0.3), 0, 1e-15, "P(X≥n+1)=0");
near(AK.binomTail(10, 10, 0.5), 1 / 1024, 1e-15, "P(X≥10 | n=10, p=1/2)");
near(AK.binomTail(12, 24, 0.25), 0.007199650007855496, 1e-14, "予感テスト 24 回中 12 回 (有理数で厳密計算した値)");
let sum = 0; for (let k = 0; k <= 24; k++) sum += AK.binomTail(k, 24, 0.25) - AK.binomTail(k + 1, 24, 0.25);
near(sum, 1, 1e-12, "確率の総和 = 1");
near(AK.zBinom(6, 24, 0.25), 0, 1e-12, "期待値ちょうどで z = 0");

/* 7. ポート */
const taps = [0]; for (let i = 1; i <= 36; i++) taps.push(taps[i - 1] + 833 + (i % 3 - 1) * 20);
near(AK.bpmFromTaps(taps), 72, 0.5, "タップ間隔 833 ms → 72 拍/分");
const tapsMiss = taps.slice(); tapsMiss.splice(10, 1); tapsMiss.splice(20, 1);   // 2 拍の叩き損ね
near(AK.bpmFromTaps(tapsMiss), 72, 1, "叩き損ねた間隔は外れ値として除く");
ok(isNaN(AK.bpmFromTaps([0, 800])), "タップ不足は NaN");
near(AK.heartAccuracy(60, [{ sec: 25, count: 25 }, { sec: 35, count: 35 }, { sec: 45, count: 45 }]), 1, 1e-12, "完全一致で精度 1");
near(AK.heartAccuracy(60, [{ sec: 30, count: 15 }]), 0.5, 1e-12, "半分しか感じなければ 0.5");
near(AK.heartAccuracy(60, [{ sec: 30, count: 90 }]), 0, 1e-12, "過大な数でも 0 未満にならない");
const seq = AK.hiddenSequence(6000, 0.8, AK.rng(3));
near(seq.filter((v, i) => v === AK.HIDDEN[i % 6]).length / 6000, 0.8, 0.02, "隠れた規則は 80% で守られる");
ok(AK.blockAccuracy([1, 1, 0, 0, 1, 0], 2).join() === "1,0,0.5", "ブロックごとの的中率");
const evNone = AK.portEvidence({ heart: 0.6, precog: { k: 6, n: 24 }, pattern: { k: 25, n: 48 } });
ok(evNone.qual.join() === "0,0,0", "偶然の範囲なら基準未満");
ok(bada(3, { EVID: evNone.evid, QUAL: evNone.qual }).port === -1, "どのポートも基準未満なら PORT -1");
const evC = AK.portEvidence({ heart: 0.7, precog: { k: 7, n: 24 }, pattern: { k: 36, n: 48 } });
ok(evC.qual.join() === "0,0,1" && bada(3, { EVID: evC.evid, QUAL: evC.qual }).port === 2, "パターンだけ有意 → ポート C");
const evAB = AK.portEvidence({ heart: 0.95, precog: { k: 14, n: 24 }, pattern: null });
const pAB = bada(3, { EVID: evAB.evid, QUAL: evAB.qual });
ok(evAB.qual.join() === "1,1,0" && pAB.port === 1, "両方有意なら証拠 (振幅) の強い方: 予感 z=" + evAB.evid[1].toFixed(2) + " > 心臓 " + evAB.evid[0].toFixed(2));
const evH = AK.portEvidence({ heart: 0.9 });
ok(evH.qual.join() === "1,0,0" && bada(3, { EVID: evH.evid, QUAL: evH.qual }).port === 0, "心臓だけ測って強い → ポート A");
// 偶然だけの参加者 1000 人: 予感ポートの偽陽性は 5% 以下
const R = AK.rng(2026); let fp = 0;
for (let p = 0; p < 1000; p++){ let k = 0; for (let t = 0; t < 24; t++) if (Math.floor(R() * 4) === Math.floor(R() * 4)) k++; if (AK.portEvidence({ precog: { k, n: 24 } }).qual[1]) fp++; }
ok(fp <= 60, "偶然の参加者で予感ポートが有意になるのは約 5% 以下 (" + fp + "/1000)");

/* 8. 組み換え生成 */
const src = ["零保存は位相の段階でも確かな零が生き残ることです。", "測定は追記専用の台帳へのコミットです。"];
const mk = AK.buildMarkov(src, 4);
const g1 = AK.generate(mk, "零保存は", 80, AK.rng(5)), g2 = AK.generate(mk, "零保存は", 80, AK.rng(5));
ok(g1 === g2 && g1.length > 10, "同じ seed → 同じ生成文");
const chars = new Set(src.join("") + " ");
ok([...g1].every(c => chars.has(c)), "材料にない文字は出さない");

/* 9. bada-cli でも単体実行できる */
const cli = path.join(root, "..", "bada_gui_ide", "cli", "bada-cli.js");
const tmp = path.join(require("os").tmpdir(), "akasha-demo.bada");
fs.writeFileSync(tmp, "DEMO := 1\nMODE := 0\n" + AKASHA);
const out = execFileSync(process.execPath, [cli, "run", tmp], { encoding: "utf8" });
ok(out.includes("@@AKASHA-OK") && out.includes("zeta(2) = 1.64493"), "bada-cli run でデモが完走");

console.log(`Bada Akasha engine tests: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
