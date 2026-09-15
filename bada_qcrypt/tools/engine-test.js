/*
 * engine-test.js — Bada QCrypt のエンジン単体テスト (Node で実行)
 *
 *   node bada_qcrypt/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM/localStorage を
 * スタブした上で純ロジック部分を検証します:
 *   1. Bada 言語インタープリタ (badaParse / badaRun)
 *      — 量子ゲート (H/X/Z/CNOT)・測定のボルン則・reset・state
 *      — 古典制御 (let/配列/for/while/if-else/print) と組み込み関数
 *      — 構文エラー・未定義参照・ステップ上限の検出
 *   2. Bada で書かれた BB84 量子鍵配送 (qcRunBB84)
 *      — 盗聴なしで QBER 0 / 鍵の一致
 *      — intercept-resend 盗聴で QBER ≈ 25% → 検出して鍵を破棄
 *   3. ワンタイムパッド (qcEncrypt / qcDecrypt) — 往復・鍵違いの棄却
 *   4. 検疫タグ (qcRunTag) — 1 バイトの改変で必ず変化
 *   5. 量子封印 (qcSealMakeBytes / qcSealDiff / qcSealRestoreBytes)
 *      — テキスト・バイナリ両方で感染検出と完全復元
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

/* ── DOM / localStorage スタブ (UI 部分は評価されるだけで実行しない) ── */
function stubEl(){
  return new Proxy({ style: {}, classList: { add(){}, remove(){} }, value: "", textContent: "", innerHTML: "" }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "querySelector" || p === "appendChild" || p === "createElement") return function(){ return stubEl(); };
      if (p === "addEventListener" || p === "removeEventListener" || p === "focus") return function(){};
      if (p === "getAttribute") return function(){ return "0"; };
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const sandbox = {
  console: console,
  setTimeout: function(fn){ fn(); },
  alert: function(){},
  localStorage: { _d: {}, getItem(k){ return k in this._d ? this._d[k] : null; }, setItem(k, v){ this._d[k] = String(v); } },
  window: {},
  document: {
    getElementById(){ return stubEl(); },
    createElement(){ return stubEl(); },
    querySelectorAll(){ return []; },
    addEventListener(){}, removeEventListener(){}
  }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });

function get(name){ return vm.runInContext(name, sandbox); }
let passed = 0;
function assert(cond, msg){
  if (!cond){ console.error("FAIL: " + msg); process.exit(1); }
  passed++;
  console.log("ok - " + msg);
}
function throws(fn, re, msg){
  let got = null;
  try{ fn(); }catch(e){ got = e.message; }
  assert(got !== null && re.test(got), msg + (got === null ? " (例外が起きませんでした)" : " [" + got + "]"));
}

const badaRun   = get("badaRun");
const badaParse = get("badaParse");
const BADA_SRC  = get("BADA_SRC");

/* ════════ 1. Bada 言語インタープリタ ════════ */
const bell = badaRun("qubit q0 q1\nH q0\nCNOT q0 q1\nstate", { seed: 1 });
assert(/\|00⟩ 0\.707/.test(bell.prints.join("\n")) && /\|11⟩ 0\.707/.test(bell.prints.join("\n")),
  "ベル状態 (|00⟩+|11⟩)/√2 の振幅が 0.707");

for (let seed = 0; seed < 20; seed++){
  const r = badaRun("qubit q0 q1\nH q0\nCNOT q0 q1\nmeasure q0 -> a\nmeasure q1 -> b", { seed: seed });
  if (r.vars.a !== r.vars.b){ console.error("FAIL: もつれの測定相関 (seed " + seed + ")"); process.exit(1); }
}
assert(true, "もつれた 2 量子ビットの測定は 20 通りの乱数系列すべてで一致する");

const ghz = badaRun("qubit q0 q1 q2\nH q0\nCNOT q0 q1\nCNOT q1 q2\nstate", { seed: 3 }).prints.join("\n");
assert(/\|000⟩ 0\.707/.test(ghz) && /\|111⟩ 0\.707/.test(ghz), "GHZ 状態が |000⟩ と |111⟩ に 1/√2 ずつ");

/* 量子乱数 (H|0⟩ の測定) がほぼ 1/2 に分かれる */
let ones = 0;
for (let i = 0; i < 400; i++){
  ones += badaRun("qubit q\nH q\nmeasure q -> v", { seed: 1000 + i }).vars.v;
}
assert(ones > 150 && ones < 250, "量子乱数 H|0⟩ の測定は 400 回中 " + ones + " 回が 1 (ほぼ 1/2)");

/* 測定後の収縮: 一度測ったら同じ値が再現する (射影測定) */
const collapse = badaRun("qubit q\nH q\nmeasure q -> a\nmeasure q -> b\nprint a == b", { seed: 9 });
assert(collapse.prints[0] === "1", "測定後の状態は収縮し、再測定で同じ値が出る");

/* reset / X / Z */
assert(badaRun("qubit q\nX q\nreset q\nmeasure q -> v", { seed: 2 }).vars.v === 0, "reset q が |0⟩ へ戻す");
assert(badaRun("qubit q\nX q\nmeasure q -> v", { seed: 2 }).vars.v === 1, "X が |0⟩ を |1⟩ にする");
assert(/\|0⟩ -1\.000/.test(badaRun("qubit q\nZ q\nH q\nH q\nZ q\nstate").prints.join("")) === false,
  "Z は |0⟩ の符号を変えない (位相の基準)");

/* 古典制御 */
assert(badaRun("let s = 0\nfor i = 1 to 10\n  let s = s + i\nend\nprint s").prints[0] === "55",
  "for ループの総和が 55");
assert(badaRun("let n = 5\nlet f = 1\nwhile n > 1\n  let f = f * n\n  let n = n - 1\nend\nprint f").prints[0] === "120",
  "while ループの階乗が 120");
assert(badaRun('if 1 < 2\n  print "yes"\nelse\n  print "no"\nend').prints[0] === "yes", "if-else の真枝");
assert(badaRun('if 2 < 1\n  print "yes"\nelse\n  print "no"\nend').prints[0] === "no", "if-else の偽枝");
assert(badaRun("let a[0] = 7\nlet a[1] = 8\nprint a[0] + a[1], len(a)").prints[0] === "15 2", "配列の代入・参照・len");
assert(badaRun("print xor(12, 10), mul32(65536, 65536), floor(7 / 2), abs(0 - 3), min(2, 5), max(2, 5)").prints[0]
  === "6 0 3 3 2 5", "組み込み関数 xor/mul32/floor/abs/min/max");
assert(badaRun("print 1 == 1 and 2 != 3, not 0, not (1 == 2), 1 or 0").prints[0] === "1 1 1 1",
  "比較・and/or/not (括弧つき not を含む)");
assert(badaRun("print 2 + 3 * 4, (2 + 3) * 4, 17 % 5, 0 - 4").prints[0] === "14 20 2 -4", "演算子の優先順位と剰余・単項マイナス");
assert(badaRun('# コメントのみ\nlet x = 1 # 行末コメント\nprint x, "a # b"').prints[0] === '1 a # b',
  "# コメントは文字列の外側だけを切り落とす");

/* エラー検出 */
throws(() => badaRun("H q9"), /未宣言の量子ビット/, "未宣言の量子ビットを拒否する");
throws(() => badaRun("print zz"), /未定義の変数/, "未定義の変数を拒否する");
throws(() => badaRun("qubit q\nCNOT q q"), /制御と標的が同じ/, "CNOT の制御=標的を拒否する");
throws(() => badaRun("for i = 1 to 3\n  print i"), /end がありません/, "閉じていない for を拒否する");
throws(() => badaRun("end"), /対応するブロックの無い/, "孤立した end を拒否する");
throws(() => badaRun("while 1\n  let x = 1\nend", { maxSteps: 500 }), /ステップ上限/, "無限ループをステップ上限で止める");
throws(() => badaRun("qubit q\nqubit q"), /宣言済み/, "量子ビットの二重宣言を拒否する");
assert(badaParse("for i = 1 to 2\n  print i\nend").length === 1, "badaParse が for を 1 文へまとめる");

/* ════════ 2. Bada で書かれた BB84 量子鍵配送 ════════ */
const qcRunBB84 = get("qcRunBB84");

const clean = qcRunBB84(256, false, 2024);
assert(clean.qber === 0, "盗聴なしの QBER は 0 (誤り源が無い理想回線)");
assert(clean.eveDetected === false, "盗聴なしでは盗聴判定が出ない");
assert(clean.key.length > 0, "盗聴なしで共有鍵 " + clean.key.length + " ビットを確立する");
assert(clean.sifted > 256 * 0.35 && clean.sifted < 256 * 0.65,
  "ふるい後は送出の約半分 (" + clean.sifted + "/256 — 基底一致の確率 1/2)");
assert(clean.log.length === 12 && clean.log.every(l => l.eve === "—"), "伝送ログ 12 件、Eve 欄は空");

/* 盗聴あり: QBER は理論値 25% 付近に集中し、必ず検出される */
let qsum = 0, detected = 0, runs = 12;
for (let i = 0; i < runs; i++){
  const r = qcRunBB84(256, true, 500 + i);
  qsum += r.qber;
  if (r.eveDetected) detected++;
  if (r.key.length !== 0){ console.error("FAIL: 盗聴検出時に鍵が残っている"); process.exit(1); }
}
const qavg = qsum / runs;
assert(qavg > 0.18 && qavg < 0.32, "intercept-resend 盗聴の平均 QBER " + qavg.toFixed(3) + " は理論値 0.25 付近");
assert(detected === runs, "盗聴された " + runs + " 回すべてで検出し、鍵を破棄した");
assert(qcRunBB84(256, true, 777).keyHex === "", "盗聴検出時は鍵 (16進) が空になる");

/* Alice と Bob の鍵はふるい後で一致している (盗聴なし) */
const cl2 = qcRunBB84(512, false, 31);
assert(cl2.errors === 0, "盗聴なしの照合ビットに誤りが無い (Alice と Bob の鍵が一致)");

/* ════════ 3. ワンタイムパッド ════════ */
const qcEncrypt = get("qcEncrypt"), qcDecrypt = get("qcDecrypt");
const key = cl2.key;
for (const text of ["Bada", "量子暗号のソフト", "改行\nとタブ\tと絵文字 ⚛🔐", ""]){
  const ct = qcEncrypt(text, key);
  assert(qcDecrypt(ct, key) === text, "ワンタイムパッド往復: " + JSON.stringify(text.slice(0, 12)));
}
const secret = "最高機密";
assert(qcEncrypt(secret, key) !== Buffer.from(secret, "utf8").toString("hex"), "暗号文は平文の 16 進そのままではない");
const otherKey = qcRunBB84(512, false, 99).key;
let wrongOut = null;
try{ wrongOut = qcDecrypt(qcEncrypt(secret, key), otherKey); }catch(e){ wrongOut = "!" + e.message; }
assert(wrongOut !== secret, "鍵が違えば復号しても平文に戻らない");
assert(!/URI|malformed/i.test(wrongOut), "鍵違いの失敗は利用者に伝わる日本語で報告される [" + String(wrongOut).slice(0, 40) + "]");
throws(() => qcEncrypt("x", []), /鍵がありません/, "鍵なしでの暗号化を拒否する");
throws(() => qcDecrypt("zz", key), /不正/, "16 進でない暗号文を拒否する");
throws(() => qcDecrypt("abc", key), /不正/, "奇数長の 16 進を拒否する");

/* ════════ 4. 検疫タグ ════════ */
const qcRunTag = get("qcRunTag"), qcTextBytes = get("qcTextBytes");
const base = qcTextBytes("重要な設定ファイルの中身");
const tag0 = qcRunTag(base, key);
assert(/^[0-9a-f]{8}$/.test(tag0), "検疫タグは 32bit の 16 進 8 桁");
assert(qcRunTag(base, key) === tag0, "同じデータ・同じ鍵なら検疫タグは再現する");
assert(qcRunTag(base, otherKey) !== tag0, "鍵が違えば検疫タグも変わる (鍵付きハッシュ)");
let changedAll = true;
for (let i = 0; i < base.length; i++){
  const mut = base.slice();
  mut[i] = mut[i] ^ 1;                       /* 1 ビットだけ反転 */
  if (qcRunTag(mut, key) === tag0) changedAll = false;
}
assert(changedAll, "全 " + base.length + " バイトのどの 1 ビットを反転しても検疫タグが変わる");
assert(qcRunTag(base.concat([0]), key) !== tag0, "末尾に 1 バイト追加しても検疫タグが変わる");

/* ════════ 5. 量子封印 — 感染の検出と解除 ════════ */
const qcSealMakeBytes = get("qcSealMakeBytes");
const qcSealDiff = get("qcSealDiff");
const qcSealRestoreBytes = get("qcSealRestoreBytes");
const qcSealMake = get("qcSealMake"), qcSealCheck = get("qcSealCheck"), qcSealRestore = get("qcSealRestore");

const doc = "起動設定: safe_mode=on\nユーザ: masaaki\n";
const seal = qcSealMake("大事なメモ", doc, key);
assert(seal.kind === "text" && seal.tag.length === 8, "テキスト封印が暗号文と検疫タグを持つ");
assert(!seal.hex.includes(Buffer.from(doc, "utf8").toString("hex")), "封印に平文はそのまま含まれない");
assert(qcSealCheck(seal, doc, key) === true, "無改変のテキストは清浄と判定される");

const infected = doc.slice(0, 10) + "☠VIRUS☠" + doc.slice(10);
assert(qcSealCheck(seal, infected, key) === false, "感染したテキストを検出する");
const d = qcSealDiff(seal, qcTextBytes(infected), key);
const injectAt = qcTextBytes(doc.slice(0, 10)).length;   /* 文字位置 10 に対応するバイト位置 */
assert(d.same === false && d.diffCount > 0 && d.firstAt === injectAt,
  "差分が最初の改変位置 (バイト " + d.firstAt + ") と相違 " + d.diffCount + " バイトを示す");
assert(qcSealRestore(seal, key) === doc, "解除でテキストが封印時の内容へ完全復元される");

/* バイナリ (実ファイル相当) — 1 バイト改変・追記・切り詰めのすべてを検出し復元する */
const bin = [];
for (let i = 0; i < 4096; i++) bin.push((i * 31 + 7) & 255);
const fseal = qcSealMakeBytes("payload.bin", bin, key, "file");
assert(fseal.kind === "file" && fseal.size === 4096, "ファイル封印がサイズを記録する");
assert(qcSealDiff(fseal, bin, key).same === true, "無改変のバイナリは清浄と判定される");

const mut1 = bin.slice(); mut1[2048] ^= 0x80;                 /* 1 ビット改変 */
const mutA = bin.slice().concat([0x90, 0x90, 0xCC]);           /* 追記感染 */
const mutT = bin.slice(0, 4000);                               /* 切り詰め */
for (const [name, mut, first] of [["1 バイト改変", mut1, 2048], ["末尾追記", mutA, 4096], ["切り詰め", mutT, 4000]]){
  const dd = qcSealDiff(fseal, mut, key);
  assert(dd.same === false && dd.firstAt === first, "バイナリの" + name + "を検出 (最初の相違 " + dd.firstAt + ")");
}
const restored = qcSealRestoreBytes(fseal, key);
assert(restored.length === bin.length && restored.every((v, i) => v === bin[i]),
  "解除で 4096 バイトのバイナリが 1 バイト違わず復元される");

/* 鍵を失うと解除できない (封印時の鍵が必要) */
const wrong = qcSealRestoreBytes(fseal, otherKey);
assert(!(wrong.length === bin.length && wrong.every((v, i) => v === bin[i])), "鍵が違えば解除しても元に戻らない");

/* 鍵より長い本文には安全性の警告が出る */
const qcOtpWarn = get("qcOtpWarn");
assert(qcOtpWarn(4096, key).indexOf("⚠") === 0, "本文が鍵より長いとき鍵の巡回を警告する");
assert(qcOtpWarn(1, key) === "", "本文が鍵より短ければ警告しない");

/* ════════ 6. アプリが使う Bada プログラムが実際に書かれている ════════ */
for (const k of ["bb84", "otp", "tag", "lab"]){
  assert(typeof BADA_SRC[k] === "string" && BADA_SRC[k].length > 50, "Bada プログラム " + k + " が同梱されている");
  badaParse(BADA_SRC[k]);                    /* 構文が通ること */
}
assert(/measure\s+ph\s*->\s*bbit/.test(BADA_SRC.bb84), "BB84 は Bada の measure で Bob の測定を行っている");
assert(/xor\(buf\[i\]/.test(BADA_SRC.otp), "OTP は Bada の xor で本文と鍵を重ねている");

console.log("\n" + passed + " 項目すべて合格 — Bada QCrypt engine OK");
