#!/usr/bin/env node
/* ============================================================================
 * build-zone-dist.js — package the secure zone:// ultra-network WWW into
 * downloadable artifacts.
 *
 * Produces (into ../dist/):
 *   - bada-zone.html  : a SINGLE self-contained file. The Bada language core
 *                       and examples/zone.bada are inlined, so downloading this
 *                       one file and opening it in any browser runs the
 *                       encrypted zone:// demo offline (no server, no deps).
 *   - zone.bada       : the source program (copy, for the CLI / IDE).
 *   - bada.js         : the language core (copy).
 *   - bada-cli.js     : the Node CLI runner (copy).
 *   - README.txt      : how to run each way.
 *
 * The GitHub Actions workflow zips ../dist and attaches it to a Release, and
 * the committed bada-zone.html is downloadable straight from the repo / Pages.
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");

const IDE = path.join(__dirname, "..");
const WWW = path.join(IDE, "www");
const EX = path.join(IDE, "examples");
const CLI = path.join(IDE, "cli");
const DIST = path.join(IDE, "dist");

fs.mkdirSync(DIST, { recursive: true });

const badaCore = fs.readFileSync(path.join(WWW, "bada.js"), "utf8");
const zoneSrc = fs.readFileSync(path.join(EX, "zone.bada"), "utf8");

/* verify the source actually runs before we ship it */
const Bada = require(path.join(WWW, "bada.js"));
const check = Bada.run(zoneSrc, { maxSteps: 20000000 });
if (!check.ok) {
  console.error("zone.bada failed to run — refusing to package:\n" + (check.error || check.parseErrors.join("\n")));
  process.exit(1);
}

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

const VERSION = Bada.VERSION;

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>zone:// — 安全なウルトラネットワーク WWW (Bada + Jones量子暗号)</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, "Segoe UI", "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
         background:#04060a; color:#d6e2ee; line-height:1.5; }
  header { padding:20px 24px; border-bottom:1px solid #1c2838;
           background:linear-gradient(180deg,#0a1220,#04060a); }
  h1 { margin:0 0 4px; font-size:20px; }
  h1 .accent { color:#c8a44a; }
  header p { margin:0; color:#8aa0b8; font-size:13px; }
  main { max-width:1000px; margin:0 auto; padding:20px 24px 60px; }
  .row { display:flex; gap:10px; flex-wrap:wrap; margin:16px 0; }
  button { font:inherit; cursor:pointer; border:1px solid #2a3a4e; border-radius:8px;
           background:#132033; color:#d6e2ee; padding:9px 16px; }
  button.run { background:#1c6b3a; border-color:#2e9e57; color:#eafff0; font-weight:600; }
  button:hover { filter:brightness(1.15); }
  pre.console { background:#020407; border:1px solid #1c2838; border-radius:10px;
                padding:16px; overflow:auto; max-height:64vh; white-space:pre-wrap;
                font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace; font-size:12.5px; }
  .note { color:#8aa0b8; font-size:12.5px; }
  code { color:#c8a44a; }
  details { margin-top:20px; }
  summary { cursor:pointer; color:#8aa0b8; }
  textarea { width:100%; min-height:220px; margin-top:10px; background:#020407; color:#d6e2ee;
             border:1px solid #1c2838; border-radius:10px; padding:12px;
             font-family:"SFMono-Regular",Consolas,monospace; font-size:12.5px; }
</style>
</head>
<body>
<header>
  <h1>zone:// — 安全な<span class="accent">ウルトラネットワーク WWW</span></h1>
  <p>Bada 量子プログラミング言語 v${VERSION} + Jones 多項式量子暗号 — <code>https:</code>/<code>http:</code> に代わる P2P の zone:// スキーム。この 1 ファイルで完結・オフライン動作します。</p>
</header>
<main>
  <p class="note">
    中央サーバも DNS ルートも無い P2P リング DHT で <code>zone://url.or.jp/</code> を解決し、
    各ゾーンの鍵を結び目図の Kauffman ブラケット/Jones 多項式から導出、Bell 対 QKD で
    セッションソルトを合意して本文を AEAD 暗号化します。改ざんや誤った結び目は
    <code>409 zone-guard-reject</code> として排除されます。
  </p>
  <div class="row">
    <button id="run" class="run">▶ 実行 (zone:// を起動)</button>
    <button id="dlSrc">💾 zone.bada を保存</button>
    <button id="dlC">💾 生成 C を保存</button>
    <button id="dlHtml">💾 この単一 HTML を保存</button>
  </div>
  <pre id="console" class="console">「▶ 実行」を押すと、暗号化された zone:// のデモが動きます。</pre>

  <details>
    <summary>zone.bada のソースを表示 / 編集して実行</summary>
    <textarea id="editor" spellcheck="false"></textarea>
    <div class="row"><button id="runEdit">▶ 編集したソースを実行</button></div>
  </details>

  <p class="note" style="margin-top:24px">
    CLI で動かす場合: <code>node bada-cli.js run zone.bada</code>（同梱の <code>bada.js</code> と同じ階層に配置）。
    GUI IDE では <code>.bada</code> をドラッグ&amp;ドロップすると自動でコンパイル/実行します。
  </p>
</main>

<script>
/* ==== Bada language core (inlined from www/bada.js) ==== */
${badaCore}
</script>
<script>
/* ==== zone.bada source (inlined) ==== */
var ZONE_SRC = ${JSON.stringify(zoneSrc)};
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var out = $("console"), editor = $("editor");
  editor.value = ZONE_SRC;

  function run(src) {
    out.textContent = "";
    var r = BadaLang.run(src, { maxSteps: 20000000, out: function (s) {
      out.textContent += s + "\\n"; out.scrollTop = out.scrollHeight;
    }});
    if (r.parseErrors && r.parseErrors.length) out.textContent += r.parseErrors.join("\\n") + "\\n";
    out.textContent += "\\n── 完了 (ledger " + r.ledgerLen + " facts) ──\\n";
  }
  function download(name, text, type) {
    var blob = new Blob([text], { type: type || "text/plain;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = name; a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
  }
  $("run").addEventListener("click", function () { run(ZONE_SRC); });
  $("runEdit").addEventListener("click", function () { run(editor.value); });
  $("dlSrc").addEventListener("click", function () { download("zone.bada", ZONE_SRC); });
  $("dlC").addEventListener("click", function () {
    download("zone.gen.c", BadaLang.emitC(editor.value || ZONE_SRC).c, "text/x-c;charset=utf-8");
  });
  $("dlHtml").addEventListener("click", function () {
    download("bada-zone.html", "<!DOCTYPE html>\\n" + document.documentElement.outerHTML, "text/html;charset=utf-8");
  });
  /* auto-run once so the page opens alive */
  run(ZONE_SRC);
})();
</script>
</body>
</html>
`;

fs.writeFileSync(path.join(DIST, "bada-zone.html"), html);
fs.copyFileSync(path.join(EX, "zone.bada"), path.join(DIST, "zone.bada"));
fs.copyFileSync(path.join(WWW, "bada.js"), path.join(DIST, "bada.js"));
fs.copyFileSync(path.join(CLI, "bada-cli.js"), path.join(DIST, "bada-cli.js"));

const readme = `zone:// — 安全なウルトラネットワーク WWW (Bada v${VERSION} + Jones 量子暗号)
================================================================

同梱ファイル:
  bada-zone.html  この 1 ファイルだけで完結。ブラウザで開くと暗号化 zone:// が
                  動きます (オフライン可・依存なし)。
  zone.bada       zone:// スキームの Bada ソース。
  bada.js         Bada 言語コア (インタープリタ + Bada->C トランスパイラ)。
  bada-cli.js     Node.js 用 CLI ランナー。

実行方法:
  1) ブラウザ:  bada-zone.html をダブルクリックして開くだけ。
  2) CLI     :  node bada-cli.js run zone.bada
                (bada-cli.js と bada.js を同じ階層に置いてください)
  3) C へ    :  node bada-cli.js emit zone.bada -o zone.c
                gcc -O2 -o zone zone.c -lm && ./zone

セキュリティ:
  - 各ゾーンの鍵は結び目図の Kauffman ブラケット/Jones 多項式標本から導出。
  - Bell 対 QKD (H+CNOT+Measure) がセッションソルトを合意、零の保存が
    チャネル改ざんの証拠。
  - 本文は (Jones 鍵, ソルト) をシードにした鍵ストリームで暗号化し、鍵付き
    認証タグで封緘。改ざん・誤った結び目は 409 zone-guard-reject。

(c) Masaaki Yamaguchi — Bada / Ultra Network
`;
fs.writeFileSync(path.join(DIST, "README.txt"), readme);

console.log("built dist/:");
for (const f of fs.readdirSync(DIST)) {
  console.log("  " + f + "  (" + fs.statSync(path.join(DIST, f)).size + " bytes)");
}
console.log("zone.bada self-check: OK (ledger " + check.ledgerLen + " facts)");
