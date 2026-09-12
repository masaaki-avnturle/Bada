/*
 * engine-test.js — Bada Illustrator (量子建築設計スタジオ) のエンジン単体テスト
 *
 *   node bada_illustrator/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、__BADA_TEST__ を立てて
 * DOM 初期化を止めた上で、純ロジックを検証します:
 *   1. 幾何: スナップ / 壁ポリゴン / 靴ひも面積 / 延床面積 / ヒットテスト
 *   2. 情報エンジン: softmax / entropy(bit) / 最大エントロピー事前分布 / update
 *   3. 量子コア: H・X・RY・CNOT / ベル状態 / Born 則 / 決定論サンプル
 *   4. Bada 言語: 字句・構文・評価 (:=, if/while/for, fun, リスト, 台帳)
 *   5. @reviser : extension 拡張トランザクション
 *   6. 建築 API: wall/room/door/... と図面モデル / SVG / 保存往復
 *   7. 組み込み拡張機能 6 本が全てエラーなく実行できること
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

const sandbox = {
  __BADA_TEST__: true,
  console, Math, JSON, Object, Array, String, Number, Date, RegExp, Infinity, NaN,
  parseFloat, parseInt, isNaN, isFinite,
  setTimeout: function (fn) { fn(); },
  localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} },
  document: undefined,
  window: undefined
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });
const G = (name) => vm.runInContext(name, sandbox);

let n = 0;
function assert(cond, msg) {
  n++;
  if (!cond) { console.error("FAIL: " + msg); process.exit(1); }
  console.log("ok - " + msg);
}
const near = (a, b, eps) => Math.abs(a - b) <= (eps === undefined ? 1e-9 : eps);

/* ---------- 1. 幾何 ---------- */
const snapTo = G("snapTo"), distMM = G("distMM");
assert(snapTo(123, 50) === 100, "snapTo(123,50) = 100 (グリッドスナップ)");
assert(snapTo(-130, 250) === -250, "snapTo(-130,250) = -250 (負座標)");
assert(snapTo(777, 0) === 777, "snapTo: グリッド 0 は素通し");
assert(distMM(0, 0, 3000, 4000) === 5000, "distMM: 3-4-5 三角形");

const wallPolygon = G("wallPolygon"), polygonArea = G("polygonArea");
const wp = wallPolygon({ x1: 0, y1: 0, x2: 5000, y2: 0, t: 200 });
assert(wp.length === 4, "wallPolygon は 4 点を返す");
assert(near(polygonArea(wp), 5000 * 200), "壁面積 = 長さ×厚 (5000×200 mm²)");

const totalFloorArea = G("totalFloorArea");
const roomsOnly = [
  { type: "room", x: 0, y: 0, w: 5000, h: 4000 },
  { type: "room", x: 0, y: 0, w: 2000, h: 2500 },
  { type: "wall", x1: 0, y1: 0, x2: 9000, y2: 0, t: 200 }
];
assert(near(totalFloorArea(roomsOnly), 25), "延床面積 = 20 + 5 = 25 m² (壁は不算入)");

const hitTest = G("hitTest");
assert(hitTest({ type: "wall", x1: 0, y1: 0, x2: 5000, y2: 0, t: 200 }, 2500, 80, 50),
  "hitTest: 壁厚の内側はヒット");
assert(!hitTest({ type: "wall", x1: 0, y1: 0, x2: 5000, y2: 0, t: 200 }, 2500, 800, 50),
  "hitTest: 壁から離れた点は外れ");
assert(hitTest({ type: "column", cx: 1000, cy: 1000, r: 150 }, 1100, 1000, 50),
  "hitTest: 柱の内側");

/* ---------- 2. 情報エンジン ---------- */
const softmax = G("softmax"), entropyBits = G("entropyBits");
const unknownPrior = G("unknownPrior"), updateDist = G("updateDist");
const sm = softmax([2, 1, 0, -1]);
assert(near(sm.reduce((a, b) => a + b, 0), 1, 1e-12), "softmax の総和 = 1");
assert(sm[0] > sm[1] && sm[1] > sm[2] && sm[2] > sm[3], "softmax は単調 (logit 順)");
assert(near(entropyBits(unknownPrior(4)), 2, 1e-12), "一様 4 状態のエントロピー = 2 bit");
const post = updateDist(unknownPrior(4), [0.7, 0.2, 0.1, 0.0]);
assert(near(post.reduce((a, b) => a + b, 0), 1, 1e-12), "update 後も確率 (総和 1)");
assert(entropyBits(post) < 2, "証拠で事後エントロピーが減少 (Jaynes)");
assert(post[3] === 0, "ゼロ保存: 証拠 0 の状態は 0");
assert(JSON.stringify(G("zerosOf")(post)) === "[3]", "zerosOf が禁止状態を返す");

/* ---------- 3. 量子コア ---------- */
const qubitState = G("qubitState"), applyGate1 = G("applyGate1"), applyCNOT = G("applyCNOT");
const measureProbs = G("measureProbs"), sampleState = G("sampleState");
const gateH = G("gateH"), gateX = G("gateX"), gateRY = G("gateRY");

let st = qubitState(2);
assert(near(measureProbs(st)[0], 1), "qubit(2) の初期状態は |00>");
st = applyGate1(st, 0, gateH());
st = applyCNOT(st, 0, 1);
const bell = measureProbs(st);
assert(near(bell[0], 0.5) && near(bell[3], 0.5) && near(bell[1], 0) && near(bell[2], 0),
  "H+CNOT でベル状態 [0.5, 0, 0, 0.5]");
assert(near(bell.reduce((a, b) => a + b, 0), 1, 1e-9), "ユニタリ性: |ψ|² の総和 = 1");
assert(sampleState(st, 0.25) === 0 && sampleState(st, 0.75) === 3,
  "sampleState は累積分布から決定論的に基底を選ぶ");

let fx = applyGate1(qubitState(1), 0, gateX());
assert(near(measureProbs(fx)[1], 1), "X|0> = |1>");
let ry = applyGate1(qubitState(1), 0, gateRY(Math.PI / 2));
assert(near(measureProbs(ry)[0], 0.5) && near(measureProbs(ry)[1], 0.5),
  "RY(π/2)|0> は等確率重ね合わせ");

/* ---------- 4. Bada 言語 ---------- */
const badaTokenize = G("badaTokenize"), badaParse = G("badaParse");
const badaRun = G("badaRun"), badaStdEnv = G("badaStdEnv");

assert(badaTokenize("a := 1 + 2").filter(t => t.t === "op" && t.v === ":=").length === 1,
  "字句解析: := を 1 トークンで読む");
assert(badaParse(badaTokenize("x := 1\nprint(x)")).length === 2,
  "構文解析: 2 文のプログラム");

let r = badaRun('x := 2 + 3 * 4\nprint("x =", x)');
assert(r.ok && r.output[0] === "x = 14", "演算子優先順位: 2+3*4 = 14");

r = badaRun('s := 0\ni := 1\nwhile i <= 10 { s := s + i\n i := i + 1 }\nprint(s)');
assert(r.ok && r.output[0] === "55", "while: 1..10 の和 = 55");

r = badaRun('t := 0\nfor x in [1, 2, 3, 4] { t := t + x }\nprint(t)');
assert(r.ok && r.output[0] === "10", "for-in: リスト走査");

r = badaRun('fun fib |n| {\n if n < 2 { return n }\n return fib(n-1) + fib(n-2)\n}\nprint(fib(10))');
assert(r.ok && r.output[0] === "55", "fun + 再帰: fib(10) = 55");

r = badaRun('a := [10, 20, 30]\na[1] := 99\nprint(a, a[-1])');
assert(r.ok && r.output[0] === "[10, 99, 30] 30", "リスト添字の読み書きと負添字");

r = badaRun('if 3 > 2 and not false { print("yes") } else { print("no") }');
assert(r.ok && r.output[0] === "yes", "if/else と and・not");

r = badaRun('p := unknown_prior(4)\np >> tuplespace\nprint(len(tuplespace))');
assert(r.ok && r.output[0] === "1", ">> tuplespace 追記専用台帳");

r = badaRun('print(nothing)');
assert(!r.ok && r.error.indexOf("nothing") >= 0, "未定義変数は行儀よくエラー");

r = badaRun('while true { }');
assert(!r.ok && r.error.indexOf("上限") >= 0, "無限ループはステップ上限で停止");

r = badaRun('reg := qubit(2)\nreg := H(reg, 0)\nreg := CNOT(reg, 0, 1)\nprint(Measure(reg))');
assert(r.ok && r.output[0] === "[0.5, 0, 0, 0.5]", "Bada からのベル状態: Measure が Born 則確率");

r = badaRun('print(f5(entropy([0.5, 0.5])))');
assert(r.ok && r.output[0] === "1.00000", "entropy([0.5,0.5]) = 1 bit (f5 整形)");

/* ---------- 5. @reviser 拡張トランザクション ---------- */
r = badaRun([
  '@reviser : extension bada {',
  '    fun sharpen |d, e| """',
  '        return update(d, e, 0.7)',
  '    """',
  '}',
  'post := sharpen(unknown_prior(4), [0.7, 0.2, 0.1, 0.0])',
  'print(len(tuplespace), f5(entropy(post)))'
].join("\n"));
assert(r.ok, "@reviser : extension bada がコミットできる: " + (r.error || ""));
assert(r.output[0].startsWith("1 ") && parseFloat(r.output[0].split(" ")[1]) < 2,
  "reviser 拡張が台帳へ 1 ファクト + 呼び出し可能 (エントロピー減少)");

r = badaRun('@reviser : extension c {\n fun c_hypot |a, b| """ return sqrt(a*a+b*b); """\n}\nc_hypot(3, 4)');
assert(!r.ok && r.error.indexOf("ネイティブ") >= 0,
  "c 拡張はこの環境ではネイティブ専用の説明つきエラー");

/* ---------- 6. 建築 API ---------- */
const makeDrawingAPI = G("makeDrawingAPI");
const model = { shapes: [], layer: "壁・構造", nextId: 0 };
const api = makeDrawingAPI(model);
r = badaRun([
  'wall(0, 0, 9100, 0, 200)',
  'wall(9100, 0, 9100, 7280, 200)',
  'room(0, 0, 9100, 7280, "LDK")',
  'door(4550, 0, 800, 0)',
  'window(1000, 7280, 3000, 7280)',
  'dim(0, -600, 9100, -600)',
  'label(200, 400, "1F 平面図", 400)',
  'print(count(), total_area())'
].join("\n"), badaStdEnv(api));
assert(r.ok, "建築 API スクリプトが実行できる: " + (r.error || ""));
assert(r.output[0] === "7 66.248", "count()=7 / total_area()=66.248 m² (9.1m×7.28m)");
assert(model.shapes[0].type === "wall" && model.shapes[2].type === "room" &&
       model.shapes[2].name === "LDK", "モデルに壁と部屋 (名前つき) が入る");

r = badaRun('print(areas())', badaStdEnv(api));
assert(r.ok && r.output[0] === "[[LDK, 66.248]]", "areas() が部屋名と m² を返す");

const serializeProject = G("serializeProject"), deserializeProject = G("deserializeProject");
const json = serializeProject(model);
const back = deserializeProject(json);
assert(back.shapes.length === model.shapes.length &&
       back.shapes[2].name === "LDK", "JSON 保存 → 読み込みの往復が一致");
let threw = false;
try { deserializeProject('{"app":"other"}'); } catch (e) { threw = true; }
assert(threw, "他アプリの JSON は拒否する");

const shapesToSVG = G("shapesToSVG");
const svg = shapesToSVG(model.shapes);
assert(svg.indexOf("<svg") === 0 && svg.indexOf("<polygon") > 0 &&
       svg.indexOf("LDK") > 0 && svg.indexOf("</svg>") > 0,
  "SVG 出力: 壁ポリゴン + 部屋名を含む正しい SVG");

r = badaRun('clear()\nprint(count())', badaStdEnv(api));
assert(r.ok && r.output[0] === "0" && model.shapes.length === 0, "clear() で図面が空になる");

r = badaRun('set_layer("宇宙")', badaStdEnv(api));
assert(!r.ok, "set_layer は未知レイヤーを拒否");

/* ---------- 7. 組み込み拡張機能 ---------- */
const BUILTIN_EXTENSIONS = G("BUILTIN_EXTENSIONS");
assert(Array.isArray(BUILTIN_EXTENSIONS) && BUILTIN_EXTENSIONS.length >= 6,
  "組み込み拡張が 6 本以上ある");
for (const ext of BUILTIN_EXTENSIONS) {
  const m2 = { shapes: [], layer: "壁・構造", nextId: 0 };
  const res = badaRun(ext.src, badaStdEnv(makeDrawingAPI(m2)));
  assert(res.ok, "組み込み拡張『" + ext.name + "』がエラーなく実行できる: " + (res.error || ""));
}
{
  const m3 = { shapes: [], layer: "壁・構造", nextId: 0 };
  const res = badaRun(BUILTIN_EXTENSIONS[0].src, badaStdEnv(makeDrawingAPI(m3)));
  assert(res.ok && m3.shapes.filter(s => s.type === "wall").length >= 5 &&
         m3.shapes.filter(s => s.type === "room").length === 2,
    "量子間取りジェネレータ: 壁 5 枚以上 + 部屋 2 室を必ず生成");
  assert(G("totalFloorArea")(m3.shapes) > 40, "量子間取り: 延床 40 m² 超");
}

const CONSOLE_SAMPLES = G("CONSOLE_SAMPLES");
for (const s of CONSOLE_SAMPLES) {
  const m4 = { shapes: [], layer: "壁・構造", nextId: 0 };
  const res = badaRun(s.src, badaStdEnv(makeDrawingAPI(m4)));
  assert(res.ok, "コンソールサンプル『" + s.name + "』が実行できる: " + (res.error || ""));
}

console.log("\n" + n + " tests passed — Bada Illustrator engine OK");
