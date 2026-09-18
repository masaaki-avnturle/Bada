#!/usr/bin/env node
/* ============================================================================
 * build-exo-pdf.js — publish the Bada quantum engine source in two forms:
 *   dist/exo-gamma.bada  — the source itself (verbatim copy, .bada extension)
 *   dist/exo-gamma.pdf   — a printable PDF: title page block (what the engine
 *                          is, the Γ×Jones correspondences, how to run it),
 *                          then the full 300+ line source with line numbers
 *                          and light syntax highlighting (comments/keywords/
 *                          strings/quantum ops), Japanese comments intact.
 *
 * The PDF is rendered with headless Chrome/Chromium (print-to-pdf); the tool
 * looks for CHROME_BIN, then google-chrome / chromium on PATH, then the
 * Playwright chromium shipped in this container. GitHub's ubuntu-latest
 * runners have google-chrome preinstalled; apps-dist.yml also installs
 * fonts-noto-cjk so the Japanese comments render.
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const IDE = path.join(__dirname, "..");
const SRC = path.join(IDE, "exo", "exo-gamma.bada");
const DIST = path.join(IDE, "dist");
fs.mkdirSync(DIST, { recursive: true });

/* 1) the .bada source, verbatim, downloadable from dist/ ------------------ */
fs.copyFileSync(SRC, path.join(DIST, "exo-gamma.bada"));
console.log("copied dist/exo-gamma.bada (" + fs.statSync(SRC).size + " bytes)");

/* 2) build the print HTML -------------------------------------------------- */
const code = fs.readFileSync(SRC, "utf8").replace(/\n$/, "");
function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function hlLine(line) {
  const ci = line.indexOf("#");
  let codePart = line, comment = "";
  if (ci >= 0) { codePart = line.slice(0, ci); comment = line.slice(ci); }
  let h = esc(codePart);
  h = h.replace(/"([^"]*)"/g, '<span class="s">"$1"</span>');
  h = h.replace(/&lt;-/g, '<span class="k">&lt;-</span>');          // 矢印代入
  h = h.replace(/-&gt;/g, '<span class="k">-&gt;</span>');          // 矢印条件文
  h = h.replace(/\b(def|return|while|if|else)\b(?![^<]*<\/span>)/g, '<span class="k">$1</span>');
  h = h.replace(/\b(qubit|H|CNOT|Measure|softmax)\b(?=\s*\()/g, '<span class="q">$1</span>');
  h = h.replace(/\b(print|len|sqrt|log|exp|abs|f5|sci)\b(?=\s*\()/g, '<span class="b">$1</span>');
  if (comment) h += '<span class="c">' + esc(comment) + "</span>";
  return h;
}
const lines = code.split("\n");
let body = "";
for (let i = 0; i < lines.length; i++) {
  body += '<div class="ln"><span class="no">' + String(i + 1).padStart(3, " ") +
          '</span><span class="tx">' + (hlLine(lines[i]) || "&nbsp;") + "</span></div>\n";
}
const today = new Date().toISOString().slice(0, 10);
const html = '<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"/>' +
'<title>exo-gamma.bada — Bada量子エンジン ソースコード</title>' +
"<style>" +
"@page{size:A4;margin:13mm 12mm;}" +
"body{font-family:'Noto Sans Mono','DejaVu Sans Mono','Noto Sans CJK JP','Noto Sans JP',monospace;" +
"font-size:8.2pt;line-height:1.42;color:#1f2530;margin:0;}" +
"h1{font-size:15pt;margin:0 0 2pt;color:#0b3a53;}" +
".sub{font-size:8.5pt;color:#456;margin-bottom:8pt;}" +
".box{border:1px solid #b8c4d4;border-radius:6px;padding:8pt 10pt;margin-bottom:8pt;background:#f4f7fb;font-size:8.2pt;}" +
".box b{color:#0b3a53;}" +
"table{border-collapse:collapse;width:100%;font-size:8pt;margin:4pt 0;}" +
"td,th{border:1px solid #c4cede;padding:3pt 6pt;text-align:left;vertical-align:top;}" +
"th{background:#e6edf6;color:#0b3a53;}" +
".code{border:1px solid #d4dae4;border-radius:6px;padding:6pt 0;background:#fbfcfe;}" +
".ln{display:flex;white-space:pre-wrap;word-break:break-all;padding:0 8pt;}" +
".ln:nth-child(even){background:#f4f6fa;}" +
".no{color:#9aa6b8;min-width:26pt;text-align:right;margin-right:8pt;user-select:none;}" +
".tx{flex:1;}" +
".c{color:#1a7f37;}.k{color:#8250df;font-weight:600;}.s{color:#b35900;}" +
".q{color:#0550ae;font-weight:700;}.b{color:#116a6a;}" +
".foot{font-size:7.5pt;color:#789;margin-top:6pt;}" +
"</style></head><body>" +
"<h1>exo-gamma.bada — Bada量子エンジン (" + lines.length + "行)</h1>" +
'<div class="sub">Γ関数における大域的部分積分多様体の機知 × Jones多項式の熱感知 — ' +
"地球と同位 (同型) の地球外惑星と、電磁波を利用し得る生命体候補を探索する Bada 言語ソースコード</div>" +
'<div class="box">' +
"<b>実装の対応表</b>" +
"<table>" +
"<tr><th>要素</th><th>ソース内の実装</th></tr>" +
"<tr><td>Γの大域的部分積分多様体</td><td>gamma_fn (Lanczos近似) + gamma_check — 部分積分恒等式 Γ(z+1)=zΓ(z) を実行時に検証 (=1.000000) し、esi3 の重み正規化に使用</td></tr>" +
"<tr><td>Jones多項式の熱感知</td><td>jones_abs — 三葉結び目 V(t)=−t⁻⁴+t⁻³+t⁻¹ を t=e^{iθ} で評価。heat_theta が惑星の実測平衡温度→θ</td></tr>" +
"<tr><td>地球と同位の惑星</td><td>esi3 (地球類似性指数) × 宇宙望遠鏡の実測カタログ8惑星 (Proxima b, TRAPPIST-1e, Kepler-442b …)</td></tr>" +
"<tr><td>生命体候補の発見</td><td>SETIスコア = ESI × 電波地平 (120光年) で「聞くべき候補」を順位付け — 検出は2026年時点でゼロと明記</td></tr>" +
"<tr><td>Bada量子エンジン</td><td>qubit(2) → H×2 → softmax振幅 → Measure (測定台帳へコミット)、CNOT の Bell対で零保存=盗聴なしを確認</td></tr>" +
"</table>" +
"<b>矢印オブジェクト構文</b>: 代入 <code>name &lt;- 式</code> (:= の矢印形。[]で生まれた器へは流し込み追記) / " +
"条件文 <code>(条件) -&gt; { … } else { … }</code> (if の矢印形。従来の := / if も後方互換)。 " +
"<b>実行方法</b>: <code>node bada_gui_ide/cli/bada-cli.js run bada_gui_ide/exo/exo-gamma.bada</code>" +
" / ブラウザ内: GammaTwin (earth-twin.html)・PlanetCinema (planet-cinema.html) の「Bada量子エンジン」カード。" +
" 完走センチネル: @@EXO-GAMMA-OK / @@GRAV-CHANNEL-OK / @@CIV-OK" +
"</div>" +
'<div class="code">' + body + "</div>" +
'<div class="foot">Bada quantum programming language — github.com/masaaki-avnturle/Bada · ' +
"bada_gui_ide/exo/exo-gamma.bada · generated " + today + "</div>" +
"</body></html>";

const htmlPath = path.join(DIST, "exo-gamma-print.html");
fs.writeFileSync(htmlPath, html);

/* 3) print to PDF with headless Chrome/Chromium ---------------------------- */
const cands = [
  process.env.CHROME_BIN,
  "google-chrome", "google-chrome-stable", "chromium-browser", "chromium",
  "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
].filter(Boolean);
let bin = null;
for (const c of cands) {
  try { execFileSync(c, ["--version"], { stdio: "pipe" }); bin = c; break; } catch (e) {}
}
if (!bin) {
  console.error("ERROR: no Chrome/Chromium found (set CHROME_BIN) — cannot render exo-gamma.pdf");
  process.exit(1);
}
const outPdf = path.join(DIST, "exo-gamma.pdf");
const args = ["--headless=new", "--disable-gpu", "--no-sandbox",
              "--no-pdf-header-footer", "--print-to-pdf=" + outPdf, "file://" + htmlPath];
try {
  execFileSync(bin, args, { stdio: "pipe", timeout: 180000 });
} catch (e) {
  // 古い Chrome 向けフォールバック
  args[0] = "--headless";
  execFileSync(bin, args, { stdio: "pipe", timeout: 180000 });
}
fs.unlinkSync(htmlPath);
const sz = fs.statSync(outPdf).size;
if (sz < 10000) { console.error("ERROR: exo-gamma.pdf too small (" + sz + " bytes)"); process.exit(1); }
console.log("built dist/exo-gamma.pdf (" + sz + " bytes, chrome=" + bin + ")");
