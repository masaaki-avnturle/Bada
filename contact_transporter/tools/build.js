#!/usr/bin/env node
/*
 * build.js — src/ を 1 枚の自己完結 HTML (dist/<アプリ>/www/index.html) にまとめる
 *
 *   node tools/build.js [contactgpt|transporter|ufo|studio|runner|all]   (既定: all。runner は常に作る)
 *   アプリの定義 (名前・ID・含めるタブ) は apps.json。
 *   方程式 2111 本 (data/equations.json) と ContactGPT の学習済み重み
 *   (data/contactgpt_weights.json) も埋め込むので、オフラインで動きます。
 *   Bada ソース (bada/ 以下の .bada) も仮想ファイル表として埋め込みます。
 *   このファイルを Android (Cordova) / Windows・Linux (Electron) が同梱します。
 */
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), SRC = path.join(ROOT, "src"), DATA = path.join(ROOT, "data");
const APPS = JSON.parse(fs.readFileSync(path.join(ROOT, "apps.json"), "utf8"));
const which = process.argv[2] || "all";
if (which !== "all" && !APPS[which]) { console.error(`unknown app ${which} (${Object.keys(APPS).join(" / ")} / all)`); process.exit(1); }
const ORDER = ["physics.js", "gpt.js", "cad.js", "drafting.js", "viewer.js", "chat.js", "bada.js", "badalib.js", "paper.js", "exporters.js", "app.js"];

const read = (p) => fs.readFileSync(p, "utf8");
const safe = (s) => s.replace(/<\/(script)/gi, "<\\/$1").replace(/<!--/g, "<\\!--");
const pkg = JSON.parse(read(path.join(ROOT, "app", "electron", "package.json")));
const wPath = path.join(DATA, "contactgpt_weights.json");
const weights = fs.existsSync(wPath) ? read(wPath) : "null";
if (weights === "null") console.warn("warning: data/contactgpt_weights.json がありません (ContactGPT は生成なしで動作)");

const esc = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
function build(key) {
  const A = APPS[key];
  let html = read(path.join(SRC, "index.html"));
  // String.prototype.split/join ではなく関数置換で $ を安全に扱う
  function put(key, val) { const k = `/*@@${key}@@*/`; const i = html.indexOf(k); if (i < 0) throw new Error("placeholder " + key); html = html.slice(0, i) + val + html.slice(i + k.length); }
  put("STYLE", read(path.join(SRC, "style.css")));
  put("GPT_SRC", safe(read(path.join(SRC, "gpt.js"))));
  put("EQUATIONS", safe(read(path.join(DATA, "equations.json")).replace(/\n/g, "")));
  put("WEIGHTS", A.weights ? safe(weights) : "null");
  // BadaClaude: 論文 10 本のチャンク (方程式は EQUATIONS と共通なので除く)
  if (A.kb) {
    const kb = JSON.parse(read(path.join(DATA, "badaclaude", "kb.json")));
    put("KB", safe(JSON.stringify({ sources: kb.sources, chunks: kb.chunks })));
  } else put("KB", "null");
  // Bada ソース (apps / lib / examples) を仮想ファイル表として埋め込む
  const badaFiles = {};
  (function walk(d) {
    for (const f of fs.readdirSync(d).sort()) {
      const p = path.join(d, f);
      if (fs.statSync(p).isDirectory()) walk(p);
      else if (f.endsWith(".bada")) badaFiles[path.relative(path.join(ROOT, "bada"), p).split(path.sep).join("/")] = read(p);
    }
  })(path.join(ROOT, "bada"));
  put("BADA", safe(JSON.stringify(badaFiles)));
  put("BUILD", JSON.stringify({ version: pkg.version, date: new Date().toISOString().slice(0, 10) }));
  put("APP", JSON.stringify(Object.assign({ key }, A)));
  // Claude API モード (BadaClaude) だけ api.anthropic.com への接続を許可する
  if (A.claude) html = html.replace("default-src 'self' data: blob: gap: file:;", "default-src 'self' data: blob: gap: file:; connect-src 'self' data: blob: file: https://api.anthropic.com;");
  html = html.split("@@APP_TITLE@@").join(esc(A.title)).split("@@APP_SUBTITLE@@").join(esc(A.subtitle));
  // 論文 PDF → アプリ: pdf.js (+ 日本語 CMap)、書き出し用のランナー HTML / APK ひな形 / 署名鍵
  if (A.paper) {
    const pdfjsDir = path.join(path.dirname(require.resolve("pdfjs-dist/package.json")), "legacy", "build");
    const cmapDir = path.join(path.dirname(require.resolve("pdfjs-dist/package.json")), "cmaps");
    const cmaps = {};
    for (const f of fs.readdirSync(cmapDir)) if (/Japan1|UniJIS|90ms|EUC-[HV]|^[HV]\.bcmap|Identity/.test(f)) cmaps[f.replace(".bcmap", "")] = fs.readFileSync(path.join(cmapDir, f)).toString("base64");
    put("PDFJS", safe(read(path.join(pdfjsDir, "pdf.min.js"))));
    put("PDFJS_WORKER", safe(read(path.join(pdfjsDir, "pdf.worker.min.js"))));
    put("CMAPS", JSON.stringify(cmaps));
    put("RUNNER_HTML", runnerB64 || "");
    const apkPath = process.env.CT_RUNNER_APK || path.join(DATA, "runner.apk");
    put("RUNNER_APK", fs.existsSync(apkPath) ? fs.readFileSync(apkPath).toString("base64") : "");
    if (!fs.existsSync(apkPath)) console.warn(`  (${key}: APK のひな形 ${path.relative(ROOT, apkPath)} がないため、アプリ内の APK 作成は無効 — Actions では runner-apk ジョブが作って同梱)`);
    const sig = path.join(ROOT, "app", "signing");
    const exePath = process.env.CT_LAUNCHER_EXE || path.join(DATA, "bada-launcher.exe");
    put("LAUNCHER_EXE", fs.existsSync(exePath) ? fs.readFileSync(exePath).toString("base64") : "");
    if (!fs.existsSync(exePath)) console.warn(`  (${key}: Windows ランチャー ${path.relative(ROOT, exePath)} がないため、アプリ内の .exe 作成は無効 — Actions では win-launcher ジョブが作って同梱)`);
    put("SAMPLE_PDF", JSON.stringify(fs.readFileSync(path.join(ROOT, "contact_blueprint.pdf")).toString("base64")));
    put("SIGNING_KEY", JSON.stringify({ pk8: fs.readFileSync(path.join(sig, "debug-key.pk8")).toString("base64"), cert: fs.readFileSync(path.join(sig, "debug-cert.der")).toString("base64") }));
  } else {
    for (const k of ["PDFJS", "PDFJS_WORKER", "RUNNER_HTML", "RUNNER_APK", "SIGNING_KEY", "LAUNCHER_EXE"]) put(k, "");
    put("CMAPS", "null");
    put("SAMPLE_PDF", "null");
  }
  put("SCRIPTS", ORDER.map((f) => `\n/* ---- ${f} ---- */\n` + safe(read(path.join(SRC, f)))).join("\n"));

  const OUT = path.join(ROOT, "dist", key, "www");
  fs.mkdirSync(OUT, { recursive: true });
  fs.writeFileSync(path.join(OUT, "index.html"), html);
  console.log(`dist/${key}/www/index.html  ${(html.length / 1024).toFixed(0)} KB  (${A.name}: ${A.tabs.join(", ")})`);
  return html;
}
// ランナー (論文から作ったアプリの入れ物) を先に作り、各アプリに base64 で埋め込む
let runnerB64 = "";
const runnerHtml = build("runner");
runnerB64 = Buffer.from(runnerHtml, "utf8").toString("base64");
for (const key of which === "all" ? Object.keys(APPS) : [which]) if (key !== "runner") build(key);
