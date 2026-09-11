#!/usr/bin/env node
/* ============================================================================
 * zeta_port/build.js — package the ZETA PORT simulator into a single,
 * downloadable, offline HTML application (the repo's standard artifact form).
 *
 * Produces (into ./):
 *   - index.html : ONE self-contained file.  The Bada language core
 *                  (bada_gui_ide/www/bada.js) and the central program
 *                  (bada_gui_ide/examples/zeta_port.bada) are inlined, so
 *                  downloading this one file and opening it in any browser
 *                  runs the interdimensional-port timetable simulation
 *                  offline — no server, no deps.  ALL of the mathematics
 *                  (Riemann–Siegel Z(t), the functional-equation entropy,
 *                  the monopole balance, the port addresses) is computed by
 *                  the Bada program itself; the page only patches the
 *                  simulation constants, runs BadaLang.run(), and renders
 *                  the EVENT|/CURVE| lines the program prints.
 *
 * Usage:  node zeta_port/build.js
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const WWW = path.join(ROOT, "bada_gui_ide", "www");
const EX = path.join(ROOT, "bada_gui_ide", "examples");

const badaCore = fs.readFileSync(path.join(WWW, "bada.js"), "utf8");
const portSrc = fs.readFileSync(path.join(EX, "zeta_port.bada"), "utf8");

/* verify the program actually runs before we ship it */
const Bada = require(path.join(WWW, "bada.js"));
const check = Bada.run(portSrc, { maxSteps: 20000000 });
if (!check.ok) {
  console.error("zeta_port.bada failed to run — refusing to package:\n" +
    (check.error || check.parseErrors.join("\n")));
  process.exit(1);
}
const nEvents = (check.output.match(/^EVENT\|/gm) || []).length;
if (nEvents < 1) {
  console.error("zeta_port.bada produced no EVENT lines — refusing to package");
  process.exit(1);
}
console.log("verified: zeta_port.bada runs, " + nEvents + " gate events, ledger " +
  check.ledgerLen + " facts");

const VERSION = Bada.VERSION;

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ゼータ・ポート — 異次元ポート開閉時刻表 (Bada / visto.pdf)</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, "Segoe UI", "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
         background:#04060a; color:#d6e2ee; line-height:1.55; }
  header { padding:22px 24px 18px; border-bottom:1px solid #1c2838;
           background:linear-gradient(180deg,#0a1220,#04060a); }
  h1 { margin:0 0 4px; font-size:21px; }
  h1 .accent { color:#c8a44a; }
  header p { margin:0; color:#8aa0b8; font-size:13px; }
  main { max-width:1060px; margin:0 auto; padding:20px 16px 70px; }
  h2 { font-size:16px; color:#c8a44a; margin:28px 0 10px; border-bottom:1px solid #1c2838; padding-bottom:6px; }
  .panel { background:#0a1220; border:1px solid #1c2838; border-radius:12px; padding:16px; margin:14px 0; }
  .controls { display:flex; gap:14px; flex-wrap:wrap; align-items:flex-end; }
  .controls label { display:flex; flex-direction:column; gap:4px; font-size:12px; color:#8aa0b8; }
  input, select { font:inherit; background:#020407; color:#d6e2ee; border:1px solid #2a3a4e;
                  border-radius:8px; padding:8px 10px; min-width:110px; }
  button { font:inherit; cursor:pointer; border:1px solid #2a3a4e; border-radius:8px;
           background:#132033; color:#d6e2ee; padding:10px 18px; }
  button.run { background:#1c6b3a; border-color:#2e9e57; color:#eafff0; font-weight:700; }
  button:hover { filter:brightness(1.15); }
  .status { font-size:13px; color:#8aa0b8; margin-top:8px; min-height:1.3em; }
  .tablewrap { overflow-x:auto; }
  table { border-collapse:collapse; width:100%; font-size:13px; white-space:nowrap; }
  th, td { border-bottom:1px solid #16202e; padding:7px 10px; text-align:left; }
  th { color:#8aa0b8; font-weight:600; position:sticky; top:0; background:#0a1220; }
  tr.open td:first-child { border-left:3px solid #2e9e57; }
  tr.close td:first-child { border-left:3px solid #b0413e; }
  .badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:12px; font-weight:700; }
  .badge.open  { background:#0f3d22; color:#7ce8a4; border:1px solid #2e9e57; }
  .badge.close { background:#3d1210; color:#ff9d99; border:1px solid #b0413e; }
  .addr { font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace; color:#c8a44a; font-size:12px; }
  .sky { color:#8aa0b8; font-size:12px; }
  canvas { width:100%; height:280px; background:#020407; border:1px solid #1c2838; border-radius:10px; }
  pre.console { background:#020407; border:1px solid #1c2838; border-radius:10px;
                padding:14px; overflow:auto; max-height:56vh; white-space:pre-wrap;
                font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace; font-size:12px; }
  details { margin-top:16px; }
  summary { cursor:pointer; color:#8aa0b8; }
  code { color:#c8a44a; }
  .eq { font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace; background:#020407;
        border:1px solid #16202e; border-radius:8px; padding:10px 12px; margin:8px 0; font-size:13px;
        overflow-x:auto; }
  .note { color:#8aa0b8; font-size:12.5px; }
  footer { border-top:1px solid #1c2838; color:#5a6c80; font-size:12px; padding:18px 24px;
           text-align:center; }
  .legend span { display:inline-block; margin-right:16px; font-size:12px; color:#8aa0b8; }
  .legend i { display:inline-block; width:22px; height:3px; vertical-align:middle; margin-right:6px; }
</style>
</head>
<body>
<header>
  <h1>⟨ζ⟩ <span class="accent">ゼータ・ポート</span> — 異次元ポート開閉時刻表シミュレータ</h1>
  <p>Bada 量子プログラミング言語 v${VERSION} / visto.pdf「M theory in monopolity of extra dimension」の
     ゼータ関数関係式をエントロピー値として実行 — 依存ゼロ・単一HTML・オフライン動作</p>
</header>
<main>

<div class="panel">
  <div class="controls">
    <label>基準日時（ポート観測の開始時刻）
      <input type="datetime-local" id="baseTime"/></label>
    <label>ゼータ時間 開始 t₀
      <input type="number" id="t0" value="10" step="1" min="5"/></label>
    <label>ゼータ時間 終了 t₁
      <input type="number" id="t1" value="100" step="1" min="15" max="500"/></label>
    <label>1ゼータ単位の実時間（秒）
      <input type="number" id="scale" value="60" step="1" min="1"/></label>
    <button class="run" id="runBtn">▶ Bada でシミュレーション実行</button>
  </div>
  <div class="status" id="status">準備完了 — 実行を押すと Bada インタープリタが zeta_port.bada を走らせます。</div>
</div>

<h2>ポート開閉 時刻表</h2>
<div class="panel tablewrap">
  <table id="timetable">
    <thead><tr>
      <th>#</th><th>状態</th><th>時刻（実時間）</th><th>ゼータ時刻 t</th>
      <th>エントロピー S</th><th>□·□⁻</th><th>ポート住所</th><th>天球座標</th>
    </tr></thead>
    <tbody id="ttBody"><tr><td colspan="8" class="note">（未実行）</td></tr></tbody>
  </table>
</div>

<h2>Z(t) と S(t) — 関係式の形とそのエントロピー</h2>
<div class="panel">
  <div class="legend">
    <span><i style="background:#4a80d0"></i>Z(t) = e<sup>iθ(t)</sup>ζ(½+it)（関数等式が実数化した形）</span>
    <span><i style="background:#c8a44a"></i>S(t) 形のエントロピー</span>
    <span><i style="background:#2e9e57"></i>開</span>
    <span><i style="background:#b0413e"></i>閉</span>
  </div>
  <canvas id="plot" width="1020" height="280"></canvas>
</div>

<h2>模型の解説 — visto.pdf の式がそのまま計算になっている</h2>
<div class="panel">
  <p>中心文献 visto.pdf（Masaaki Yamaguchi,「M theory in monopolity of extra dimension Symmetry theory」）の宣言:</p>
  <div class="eq">「シャノンの公式は、ゼータ関数である」 ∫ x log x = ζ(s)</div>
  <div class="eq">「ゼータ関数は、重力場と反重力場の積である」 ζ(s) = □·□⁻ = 1</div>
  <div class="eq">「統一場理論はモノポールの磁気単極子」 E(σ) = K(σ) ⊗ H(σ)</div>
  <div class="eq">ガウス関数が円周率となる結果 ∫∫ e<sup>−x²−y²</sup> dxdy = π,  πe ≅ eπ</div>
  <p>ゼータ関数の<strong>関係式（関数等式）</strong> ζ(s) = χ(s)·ζ(1−s),
     χ(s) = 2<sup>s</sup>π<sup>s−1</sup>sin(πs/2)Γ(1−s) は、臨界線 s = ½+it を自分自身に折り返します。
     その折返し対称性こそが Riemann–Siegel の実関数 Z(t) = e<sup>iθ(t)</sup>ζ(½+it) を実数にする——
     つまり <strong>Z(t) が「関係式の方程式の形」そのもの</strong>です。Bada プログラムは Z(t) の
     Dirichlet 項を visto.pdf の 2 つの磁気単極子に分解します:</p>
  <div class="eq">K(t) = Σ 正の項（重力場 □）   H(t) = Σ 負の項（反重力場 □⁻）   Z = K − H</div>
  <p>非自明零点では K = H、すなわち <strong>□·□⁻ = 1 が厳密に成立</strong>（時刻表の □·□⁻ 列が 1.00000）。
     この釣り合いの瞬間を、4次元ブレーンと余剰次元（rtl.pdf の D-brane 次元梯子 D5…D11）を結ぶ
     <strong>ポートの開閉イベント</strong>と読みます。そして「シャノン公式＝ゼータ」に従い、
     関係式の形のエントロピー値を</p>
  <div class="eq">p<sub>n</sub> ∝ (1/√n)·(1 + cos(θ(t) − t·log n))/2,   S(t) = −Σ p<sub>n</sub> log p<sub>n</sub></div>
  <p>で計算します（Bada 組み込みの <code>entropy()</code>）。ポート住所は
     πe ≅ eπ とガウス π 積分から K セクタ・H セクタ・ゾーンリング（zone.bada と同じ RING=4096）を導き、
     <code>port://D次元/K···.H···/zone-····</code> の形で与えます。天球座標（RA/DEC）は「どこに向かって
     開くか」の観測方位です。時刻表のゼータ零点はすべて本物の ζ(½+it) の零点
     （14.1347…, 21.0220…, 25.0109…）です。</p>
  <p class="note">※ 本アプリは Yamaguchi 理論草稿の数理アート・シミュレーションです。ゼータ零点は実在の数学、
     ポートは理論上の解釈です。すべての計算は下の Bada ソースがインタープリタ上で実行しています。</p>
</div>

<details>
  <summary>Bada 実行コンソール（プログラムの生出力）</summary>
  <pre class="console" id="consoleOut">（未実行）</pre>
</details>

<details>
  <summary>中心プログラム zeta_port.bada のソース</summary>
  <pre class="console" id="srcView"></pre>
</details>

</main>
<footer>
  ZETA PORT — Bada quantum programming language ${VERSION} · visto.pdf / rtl.pdf (Yamaguchi manuscripts) ·
  単一HTML / オフライン / 依存ゼロ
</footer>

<script>
${badaCore}
</script>
<script>
"use strict";
var PORT_SRC = ${JSON.stringify(portSrc)};

function $(id) { return document.getElementById(id); }

/* default base time: now, rounded to the next minute */
(function () {
  var d = new Date(Date.now() + 60000);
  d.setSeconds(0, 0);
  var pad = function (n) { return (n < 10 ? "0" : "") + n; };
  $("baseTime").value = d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) +
    "T" + pad(d.getHours()) + ":" + pad(d.getMinutes());
})();

$("srcView").textContent = PORT_SRC;

function patchConst(src, name, value) {
  return src.replace(new RegExp("^" + name + " := .*$", "m"), name + " := " + value);
}

function fmtDate(d) {
  var pad = function (n) { return (n < 10 ? "0" : "") + n; };
  return d.getFullYear() + "/" + pad(d.getMonth() + 1) + "/" + pad(d.getDate()) +
    " " + pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
}

function runSim() {
  var t0 = parseFloat($("t0").value) || 10;
  var t1 = parseFloat($("t1").value) || 100;
  if (t0 < 5) t0 = 5;
  if (t1 <= t0 + 5) t1 = t0 + 5;
  if (t1 > 500) t1 = 500;
  var scale = parseFloat($("scale").value) || 60;
  var base = $("baseTime").value ? new Date($("baseTime").value) : new Date();

  var src = PORT_SRC;
  src = patchConst(src, "T_START", t0.toFixed(2));
  src = patchConst(src, "T_END", t1.toFixed(2));
  src = patchConst(src, "CURVES", "1");
  src = patchConst(src, "BASE_HOUR", String(base.getHours()));
  src = patchConst(src, "BASE_MIN", String(base.getMinutes()));
  src = patchConst(src, "SEC_PER_UNIT", String(scale));

  $("status").textContent = "Bada インタープリタ実行中… (t ∈ [" + t0 + ", " + t1 + "])";
  setTimeout(function () {
    var st = Date.now();
    var res = BadaLang.run(src, { maxSteps: 20000000 });
    var ms = Date.now() - st;
    $("consoleOut").textContent = res.output;
    if (!res.ok) {
      $("status").textContent = "実行エラー: " + (res.error || res.parseErrors.join("; "));
      return;
    }
    var events = [], curve = [];
    res.output.split("\\n").forEach(function (line) {
      if (line.indexOf("EVENT|") === 0) {
        var f = line.split("|");
        events.push({ k: parseInt(f[1], 10), t: parseFloat(f[2]), state: f[3].trim(),
                      S: parseFloat(f[4]), bal: parseFloat(f[5]), addr: f[6],
                      ra: f[7], dec: f[8] });
      } else if (line.indexOf("CURVE|") === 0) {
        var c = line.split("|");
        curve.push({ t: parseFloat(c[1]), z: parseFloat(c[2]), s: parseFloat(c[3]) });
      }
    });
    renderTable(events, base, t0, scale);
    renderPlot(curve, events);
    $("status").textContent = "完了: ゲートイベント " + events.length + " 件 / 台帳 " +
      res.ledgerLen + " ファクト / " + ms + "ms （数学はすべて Bada 側で計算）";
  }, 30);
}

function renderTable(events, base, t0, scale) {
  var tb = $("ttBody");
  tb.innerHTML = "";
  if (!events.length) {
    tb.innerHTML = '<tr><td colspan="8" class="note">この範囲にゲートイベントはありません</td></tr>';
    return;
  }
  events.forEach(function (e) {
    var isOpen = e.state.indexOf("OPEN") === 0;
    var when = new Date(base.getTime() + (e.t - t0) * scale * 1000);
    var tr = document.createElement("tr");
    tr.className = isOpen ? "open" : "close";
    tr.innerHTML =
      "<td>" + e.k + "</td>" +
      '<td><span class="badge ' + (isOpen ? "open\\">開" : "close\\">閉") + "</span></td>" +
      "<td>" + fmtDate(when) + "</td>" +
      "<td>t = " + e.t.toFixed(5) + "</td>" +
      "<td>S = " + e.S.toFixed(5) + "</td>" +
      "<td>" + e.bal.toFixed(5) + "</td>" +
      '<td class="addr">' + e.addr + "</td>" +
      '<td class="sky">' + e.ra + " / " + e.dec + "</td>";
    tb.appendChild(tr);
  });
}

function renderPlot(curve, events) {
  var cv = $("plot"), ctx = cv.getContext("2d");
  var W = cv.width, H = cv.height;
  ctx.clearRect(0, 0, W, H);
  if (curve.length < 2) return;
  var tMin = curve[0].t, tMax = curve[curve.length - 1].t;
  var zMax = 0.001, sMax = 0.001;
  curve.forEach(function (c) {
    if (Math.abs(c.z) > zMax) zMax = Math.abs(c.z);
    if (c.s > sMax) sMax = c.s;
  });
  var X = function (t) { return 8 + (t - tMin) / (tMax - tMin) * (W - 16); };
  var Yz = function (z) { return H / 2 - z / zMax * (H / 2 - 12); };
  var Ys = function (s) { return H - 8 - s / sMax * (H - 20); };
  /* zero axis */
  ctx.strokeStyle = "#16202e"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, H / 2); ctx.lineTo(W, H / 2); ctx.stroke();
  /* gate verticals */
  events.forEach(function (e) {
    ctx.strokeStyle = e.state.indexOf("OPEN") === 0 ? "#2e9e57" : "#b0413e";
    ctx.globalAlpha = 0.75;
    ctx.beginPath(); ctx.moveTo(X(e.t), 0); ctx.lineTo(X(e.t), H); ctx.stroke();
    ctx.globalAlpha = 1;
  });
  /* S(t) — the entropy of the equation's shape */
  ctx.strokeStyle = "#c8a44a"; ctx.lineWidth = 1.4;
  ctx.beginPath();
  curve.forEach(function (c, i) { i ? ctx.lineTo(X(c.t), Ys(c.s)) : ctx.moveTo(X(c.t), Ys(c.s)); });
  ctx.stroke();
  /* Z(t) — the functional equation's shape */
  ctx.strokeStyle = "#4a80d0"; ctx.lineWidth = 1.8;
  ctx.beginPath();
  curve.forEach(function (c, i) { i ? ctx.lineTo(X(c.t), Yz(c.z)) : ctx.moveTo(X(c.t), Yz(c.z)); });
  ctx.stroke();
}

$("runBtn").addEventListener("click", runSim);
runSim();
</script>
</body>
</html>
`;

fs.writeFileSync(path.join(__dirname, "index.html"), html);
console.log("wrote zeta_port/index.html (" + (html.length / 1024).toFixed(1) + " KB, Bada core " + VERSION + " inlined)");
