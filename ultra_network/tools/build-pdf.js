/*
 * build-pdf.js — Bada UltraNetwork の Bada 全ソースを 1 冊の PDF にする
 *
 *   node ultra_network/tools/build-pdf.js
 *   -> ultra_network/dist/BadaUltraNetwork-source.pdf
 *
 * 表紙・目次・層の図に続けて、ultra_network/bada/ の全モジュールと
 * ultra_network/ultra.bada を、行番号つき・簡易色分けで載せる。
 *
 * 組版は Chromium の印刷機能 (Playwright) を使う。日本語は
 * IPAGothic / WenQuanYi Zen Hei Mono、絵文字は Noto Color Emoji に
 * 落ちるようフォント指定を積んである。長い行は折り返して、
 * ぶら下げ字下げで続きだと分かるようにする。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const ROOT = path.join(__dirname, "..");
const DIST = path.join(ROOT, "dist");

/* ---- 収録するファイルと、その一言説明 ---- */
const FILES = [
  ["bada/01_core.bada",     "基本演算", "床関数・三角関数・ニブル表によるビット演算・16 進 / Base64 / UTF-8・32 ビット乗算・擬似乱数"],
  ["bada/02_sha256.bada",   "SHA-256 / HMAC-SHA256", "RFC 6234 と RFC 2104。Webhook 署名の検証に使う。ビット演算子が無いので 01 の表引きの上に組む"],
  ["bada/03_jones.bada",    "L3 Jones 多項式量子暗号", "Kauffman ブラケットから導く結び目鍵・Bell 対 QKD・鍵ストリーム AEAD"],
  ["bada/04_zone.bada",     "L2 zone:// ウルトラネットワーク", "URL 文法・P2P リング DHT・ピアの保管庫・アカシック台帳・@@ ブロック・封筒"],
  ["bada/05_ntt.bada",      "L1 NTT 電話回線への写像", "写像 φ と割当表・音声帯 16-QAM モデム・G.711 µ-law・RTP・ISDN・呼制御"],
  ["bada/06_plc.bada",      "L0 Panasonic HD-PLC", "多重経路伝達関数・適応ビットローディング・ウェーブレット OFDM・CRC-32/24・IEEE 1901 フレーム・CSMA/CA"],
  ["bada/07_json.bada",     "JSON の解析と生成", "Webhook 本文を公式仕様どおりに読むための再帰下降パーサと生成器"],
  ["bada/08_msgmux.bada",   "L4 LINE / Instagram 多重化", "公式 API の Webhook 取り込みと署名検証・送信要求の組立・統合受信箱"],
  ["bada/09_streams.bada",  "AT&T ベル研究所式 STREAMS", "stream head と driver の間に積む wput / rput の対、全 5 層の往復"],
  ["bada/10_main.bada",     "デモ本体", "@reviser で SEND / LINK の動詞を足し、全層を通してから 3 種類の攻撃を見せる"],
  ["bada/11_selftest.bada", "自己診断", "既知答えから全層の折返しまで 107 項目を実際に計算して検算する"],
  ["ultra.bada",            "単一ファイル版リファレンス", "bada-cli の既定ステップ上限で走る、64 サブキャリアの縮小版。全層を 1 本にまとめてある"]
];

/* ---- Bada の簡易色分け ---------------------------------------------
 * コメントと文字列を先に切り出し、残りを語に割る。
 */
const KEYWORDS = new Set(["def", "if", "else", "while", "for", "in", "return", "print",
  "true", "false", "nil", "let", "tuplespace", "rule", "stmt", "expr", "grammar",
  "qubit", "H", "X", "S", "T", "Rz", "CNOT", "Measure"]);

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function highlight(line) {
  // コメントは行末まで。ただし文字列の中の # は対象外。
  let out = "";
  let i = 0;
  while (i < line.length) {
    const c = line[i];
    if (c === "#") {
      out += '<span class="c">' + esc(line.slice(i)) + "</span>";
      return out;
    }
    if (c === '"' || c === "'") {
      const q = c;
      let j = i + 1;
      while (j < line.length) {
        if (line[j] === "\\") { j += 2; continue; }
        if (line[j] === q) { j++; break; }
        j++;
      }
      out += '<span class="s">' + esc(line.slice(i, j)) + "</span>";
      i = j;
      continue;
    }
    if (/[A-Za-z_@]/.test(c)) {
      let j = i;
      while (j < line.length && /[A-Za-z0-9_@?!]/.test(line[j])) j++;
      const w = line.slice(i, j);
      if (w[0] === "@") out += '<span class="r">' + esc(w) + "</span>";
      else if (KEYWORDS.has(w)) out += '<span class="k">' + esc(w) + "</span>";
      else if (j < line.length && line[j] === "(") out += '<span class="f">' + esc(w) + "</span>";
      else out += esc(w);
      i = j;
      continue;
    }
    if (/[0-9]/.test(c)) {
      let j = i;
      while (j < line.length && /[0-9.]/.test(line[j])) j++;
      out += '<span class="n">' + esc(line.slice(i, j)) + "</span>";
      i = j;
      continue;
    }
    if (/[:=<>+\-*/%!&|\[\]{}(),;]/.test(c)) {
      let j = i;
      while (j < line.length && /[:=<>+\-*/%!&|]/.test(line[j])) j++;
      if (j === i) j = i + 1;
      out += '<span class="o">' + esc(line.slice(i, j)) + "</span>";
      i = j;
      continue;
    }
    out += esc(c);
    i++;
  }
  return out;
}

/* ---- 統計 ---- */
let totalLines = 0, totalBytes = 0;
const listings = FILES.map(([rel, title, blurb]) => {
  const abs = path.join(ROOT, rel);
  const text = fs.readFileSync(abs, "utf8");
  const lines = text.replace(/\n$/, "").split("\n");
  totalLines += lines.length;
  totalBytes += Buffer.byteLength(text, "utf8");
  return { rel, title, blurb, lines };
});

let gitRev = "";
try {
  gitRev = execSync("git rev-parse --short HEAD", { cwd: ROOT, encoding: "utf8" }).trim();
} catch (e) { gitRev = ""; }

const today = new Date().toISOString().slice(0, 10);

/* ---- HTML の組み立て ---- */
function section(l, idx) {
  const rows = l.lines.map((ln, k) =>
    '<div class="ln"><i>' + (k + 1) + "</i><code>" + (highlight(ln) || "&nbsp;") + "</code></div>"
  ).join("");
  return `
<section class="file" id="f${idx}">
  <h2><span class="no">${String(idx + 1).padStart(2, "0")}</span>${esc(l.rel)}</h2>
  <p class="sub"><b>${esc(l.title)}</b> — ${esc(l.blurb)}</p>
  <p class="meta">${l.lines.length} 行</p>
  <div class="code">${rows}</div>
</section>`;
}

const toc = listings.map((l, i) => `
  <tr>
    <td class="tno">${String(i + 1).padStart(2, "0")}</td>
    <td class="tfile">${esc(l.rel)}</td>
    <td class="ttitle">${esc(l.title)}</td>
    <td class="tlines">${l.lines.length}</td>
  </tr>`).join("");

const html = `<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<title>Bada UltraNetwork — 全ソースコード</title>
<style>
@page { size: A4 portrait; margin: 14mm 12mm 14mm 12mm; }
:root{ --fg:#111; --mut:#666; --rule:#c9c9c9; --gold:#8a6d1f; }
*{ box-sizing:border-box; }
html,body{ margin:0; padding:0; color:var(--fg); background:#fff; }
body{
  font-family:"DejaVu Sans","IPAGothic","WenQuanYi Zen Hei","Noto Color Emoji",sans-serif;
  font-size:9pt; line-height:1.5;
}
code,.code,.ln code{
  font-family:"DejaVu Sans Mono","WenQuanYi Zen Hei Mono","IPAGothic","Noto Color Emoji",monospace;
}

/* ---- 表紙 ---- */
.cover{ height:262mm; display:flex; flex-direction:column; justify-content:center; page-break-after:always; }
.cover h1{ font-size:26pt; margin:0 0 2mm; letter-spacing:.01em; }
.cover h1 b{ color:var(--gold); }
.cover .tag{ font-size:11pt; color:var(--mut); margin:0 0 8mm; font-family:"DejaVu Sans Mono",monospace; }
.cover .lead{ font-size:10pt; line-height:1.9; margin:0 0 8mm; max-width:160mm; }
.cover .diagram{
  border:1px solid var(--rule); border-radius:2mm; padding:5mm 6mm; margin:0 0 8mm;
  font-family:"DejaVu Sans Mono","WenQuanYi Zen Hei Mono",monospace; font-size:8pt; line-height:1.65;
  white-space:pre; background:#fafafa;
}
.cover .facts{ display:flex; gap:10mm; flex-wrap:wrap; margin:0 0 8mm; }
.cover .facts div{ font-size:9pt; }
.cover .facts b{ display:block; font-size:16pt; color:var(--gold); font-family:"DejaVu Sans Mono",monospace; }
.cover .foot{ font-size:8.5pt; color:var(--mut); border-top:1px solid var(--rule); padding-top:3mm; }

/* ---- 目次 ---- */
.toc{ page-break-after:always; }
.toc h2{ font-size:14pt; margin:0 0 5mm; border-bottom:2px solid var(--gold); padding-bottom:2mm; }
table{ width:100%; border-collapse:collapse; font-size:9pt; }
th,td{ text-align:left; padding:1.6mm 2mm; border-bottom:1px solid #e4e4e4; vertical-align:top; }
th{ color:var(--mut); font-size:8pt; font-weight:600; }
.tno{ width:9mm; color:var(--mut); font-family:"DejaVu Sans Mono",monospace; }
.tfile{ width:52mm; font-family:"DejaVu Sans Mono",monospace; }
.tlines{ width:14mm; text-align:right; font-family:"DejaVu Sans Mono",monospace; color:var(--mut); }
.note{ margin-top:6mm; font-size:8.5pt; color:var(--mut); line-height:1.8; border-left:2px solid var(--rule); padding-left:3mm; }

/* ---- 各ファイル ---- */
section.file{ page-break-before:always; }
section.file h2{
  font-size:12pt; margin:0 0 1.5mm; font-family:"DejaVu Sans Mono",monospace;
  border-bottom:2px solid var(--gold); padding-bottom:1.5mm;
}
section.file h2 .no{
  display:inline-block; min-width:8mm; color:var(--gold);
}
section.file .sub{ margin:0 0 1mm; font-size:9pt; }
section.file .meta{ margin:0 0 3mm; font-size:8pt; color:var(--mut); font-family:"DejaVu Sans Mono",monospace; }

.code{ font-size:7.2pt; line-height:1.42; }
.ln{ display:flex; align-items:flex-start; }
.ln i{
  flex:0 0 9mm; text-align:right; padding-right:2.5mm; color:#aaa; font-style:normal;
  font-family:"DejaVu Sans Mono",monospace; -webkit-user-select:none;
}
.ln code{
  flex:1 1 auto; white-space:pre-wrap; word-break:break-word;
  padding-left:4mm; text-indent:-4mm;      /* 折り返しはぶら下げ字下げ */
}
.c{ color:#6a8a4a; }       /* コメント */
.s{ color:#a0522d; }       /* 文字列 */
.k{ color:#1a5fb4; font-weight:600; }
.f{ color:#7b3fa0; }
.n{ color:#b05a00; }
.o{ color:#777; }
.r{ color:#c01c28; font-weight:600; }
</style></head><body>

<div class="cover">
  <h1>Bada <b>UltraNetwork</b> — 全ソースコード</h1>
  <div class="tag">HD-PLC → NTT → zone://url.or.jp → LINE / Instagram</div>
  <p class="lead">
    Panasonic HD-PLC の技術で家の電力線を物理層にして PC をインターネットにつなぎ、
    そのフレームを NTT の電話回線へ写像し、そこに zone:// のウルトラネットワークを通し、
    LINE と Instagram のメッセージ機能を取り込む通信システム。<br>
    全層を量子プログラミング言語 <b>Bada</b> で記述し、層の組み方は
    <b>AT&amp;T ベル研究所の STREAMS</b>(Dennis Ritchie の Streams I/O)に倣う。
  </p>
  <div class="diagram">        stream head   アプリケーション (統合受信箱)
             ↓ wput                    rput ↑
        ┌── msgmux ──┐  L4  LINE / Instagram メッセージ多重化
        ├── jones  ──┤  L3  Jones 多項式量子暗号 (AEAD + Bell 対 QKD)
        ├── zone   ──┤  L2  zone:// ウルトラネットワーク (P2P リング DHT)
        └── ntt    ──┘  L1  NTT 電話回線への写像 φ + 音声帯モデム
             ↓ put                      srv ↑
          driver  plc   L0  Panasonic HD-PLC (家のコンセント)
          ≈≈≈≈≈≈ 家の電力線 2–28 MHz ≈≈≈≈≈≈</div>
  <div class="facts">
    <div><b>${FILES.length}</b>ファイル</div>
    <div><b>${totalLines.toLocaleString()}</b>行</div>
    <div><b>${Math.round(totalBytes / 1024).toLocaleString()}</b>KB</div>
    <div><b>107</b>自己診断項目 (全合格)</div>
    <div><b>512</b>サブキャリア</div>
  </div>
  <div class="foot">
    Masaaki Yamaguchi — github.com/masaaki-avnturle/Bada${gitRev ? "　·　" + gitRev : ""}　·　${today}<br>
    生成: <code>node ultra_network/tools/build-pdf.js</code>
  </div>
</div>

<div class="toc">
  <h2>目次</h2>
  <table>
    <tr><th></th><th>ファイル</th><th>内容</th><th style="text-align:right">行</th></tr>
    ${toc}
    <tr><td></td><td></td><td style="text-align:right"><b>合計</b></td><td class="tlines"><b>${totalLines.toLocaleString()}</b></td></tr>
  </table>
  <div class="note">
    Bada にモジュール読み込みの仕組みは無いので、実行するときは各モジュールを順に連結して 1 本にする。<br>
    　<code>node ultra_network/tools/build-bada.js</code> が
    <code>dist/ultra-full.bada</code>(デモ本体)と
    <code>dist/ultra-selftest.bada</code>(自己診断)を作り、
    どちらも実際に走らせて出力を検査してから書き出す。<br>
    　連結した全層プログラムは Bada の既定ステップ上限(2000 万)を超えるため、
    <code>node ultra_network/tools/run-bada.js &lt;file.bada&gt;</code> で上限を上げて走らせる。
    SHA-256 と HMAC をソフトウェアのビット演算で回すぶんが重い。<br>
    　12 番の <code>ultra.bada</code> は既定の上限で走る縮小版(64 サブキャリア)で、
    <code>node bada_gui_ide/cli/bada-cli.js run ultra_network/ultra.bada</code> でそのまま動く。
  </div>
</div>

${listings.map(section).join("\n")}

</body></html>`;

const htmlPath = path.join(DIST, "BadaUltraNetwork-source.html");
fs.mkdirSync(DIST, { recursive: true });
fs.writeFileSync(htmlPath, html);
console.log("HTML  -> " + path.relative(process.cwd(), htmlPath) +
            "  (" + FILES.length + " ファイル / " + totalLines.toLocaleString() + " 行)");

/* ---- Chromium で PDF に ---- */
(async () => {
  let chromium;
  try {
    chromium = require("playwright").chromium;
  } catch (e) {
    try {
      chromium = require("/opt/node22/lib/node_modules/playwright").chromium;
    } catch (e2) {
      console.error("playwright が見つからないので PDF は作れない。HTML はできている。");
      process.exit(1);
    }
  }
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto("file://" + htmlPath, { waitUntil: "load" });
  await page.emulateMedia({ media: "print" });
  const pdfPath = path.join(DIST, "BadaUltraNetwork-source.pdf");
  await page.pdf({
    path: pdfPath,
    format: "A4",
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: `<div style="font-size:7pt;color:#888;width:100%;padding:0 12mm;
      font-family:DejaVu Sans,sans-serif;display:flex;justify-content:space-between;">
      <span>Bada UltraNetwork — 全ソースコード</span><span>HD-PLC → NTT → zone:// → LINE / Instagram</span></div>`,
    footerTemplate: `<div style="font-size:7pt;color:#888;width:100%;padding:0 12mm;
      font-family:DejaVu Sans,sans-serif;display:flex;justify-content:space-between;">
      <span>github.com/masaaki-avnturle/Bada</span>
      <span class="pageNumber"></span> / <span class="totalPages"></span></div>`,
    margin: { top: "16mm", bottom: "14mm", left: "12mm", right: "12mm" }
  });
  await browser.close();
  const kb = Math.round(fs.statSync(pdfPath).size / 1024);
  console.log("PDF   -> " + path.relative(process.cwd(), pdfPath) + "  (" + kb + " KB)");
})();
