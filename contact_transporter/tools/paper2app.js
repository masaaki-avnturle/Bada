#!/usr/bin/env node
/*
 * paper2app.js — 論文 PDF → Bada アプリ一式 (Actions の paper-apps ジョブ / ローカル)
 *
 *   node tools/paper2app.js <論文.pdf> <出力ディレクトリ>
 *
 * 必要: node tools/build.js (dist/runner/www/index.html)、APK には data/runner.apk (なければ APK は省略)
 */
const fs = require("fs"), path = require("path");
const quiet = (f) => (...a) => { if (!/polyfill|Cannot find module 'canvas'|Require stack|^- \//.test(String(a[0]))) f(...a); };
console.warn = quiet(console.warn); const log = quiet(console.log); console.log = log;
const { loadPaper } = require("./paperinfo.js");
const H = require("./badahost.js");
const B = require("../src/bada.js"), L = require("../src/badalib.js"), X = require("../src/exporters.js");
const ROOT = path.join(__dirname, "..");

async function main(pdf, outDir) {
  const paper = await loadPaper(pdf);
  fs.mkdirSync(outDir, { recursive: true });
  const files = H.badaFiles();
  const env = { files, ui: {}, chat: {}, paper: () => paper };
  const vm = new B.BadaVM({ host: L.makeHost(env), files, maxSteps: 2e8 });
  vm.load("#include lib/paper.bada\n", "<paper>");
  const apps = {};
  for (const kind of ["manifold", "ufo", "transporter"]) apps[kind] = vm.call("paper_app", [kind]);
  const main = apps.manifold, base = path.basename(main[0], ".bada");
  for (const k of Object.keys(apps)) fs.writeFileSync(path.join(outDir, path.basename(apps[k][0])), apps[k][1]);
  // 作ったアプリを動かして図面を描く (動作確認を兼ねる)
  const env2 = { files: Object.assign({}, files, { [main[0]]: main[1] }), ui: H.stubUI(), chat: {}, scene: new L.Scene(), paper: () => paper, onError: (e) => { throw e; } };
  const run = new L.BadaApp(env2); run.start(main[1], main[0]); run.call("frame", [0]); run.call("make_sheet", []);
  fs.writeFileSync(path.join(outDir, base + "_drawing.svg"), env2.lastSheet.svg);
  // 単体 HTML
  const runner = fs.readFileSync(path.join(ROOT, "dist", "runner", "www", "index.html"), "utf8");
  const title = paper.title.slice(0, 60);
  const html = X.standaloneHtml(runner, { title, from: path.basename(pdf), main: main[0], files: { [main[0]]: main[1] } });
  fs.writeFileSync(path.join(outDir, base + ".html"), html);
  // .deb
  const pdfBytes = new Uint8Array(fs.readFileSync(pdf));
  const deb = await X.buildDeb({ pkg: "bada-" + base.replace(/_/g, "-"), title, description: main[3], html, bada: { name: base + ".bada", src: main[1] }, pdf: { name: path.basename(pdf).replace(/[^\w.\-]+/g, "_"), data: pdfBytes } });
  fs.writeFileSync(path.join(outDir, `${deb.pkg}_1.0.0_all.deb`), deb.bytes);
  // APK (ランナー APK のひな形 + JAR 署名)
  const tpl = process.env.CT_RUNNER_APK || path.join(ROOT, "data", "runner.apk");
  let apkMsg = "APK: ひな形がないため省略";
  if (fs.existsSync(tpl)) {
    const sig = path.join(ROOT, "app", "signing");
    const apk = await X.buildApk(new Uint8Array(fs.readFileSync(tpl)), html, { pk8: new Uint8Array(fs.readFileSync(path.join(sig, "debug-key.pk8"))), cert: new Uint8Array(fs.readFileSync(path.join(sig, "debug-cert.der"))) });
    fs.writeFileSync(path.join(outDir, base + ".apk"), apk); apkMsg = `APK ${(apk.length / 1024).toFixed(0)} KB`;
  }
  fs.copyFileSync(pdf, path.join(outDir, path.basename(pdf).replace(/[^\w.\-]+/g, "_")));
  fs.writeFileSync(path.join(outDir, base + ".json"), JSON.stringify(paper, null, 1));
  log(`${path.basename(pdf)} → ${outDir}\n  「${paper.title}」 ${paper.pages} ページ, 方程式 ${paper.equations.length} 本, 部品 ${env2.scene.parts.size}, ${apkMsg}, deb ${(deb.bytes.length / 1024).toFixed(0)} KB`);
}
if (require.main === module) {
  const [pdf, out] = process.argv.slice(2);
  if (!pdf || !out) { console.error("usage: paper2app.js <paper.pdf> <outdir>"); process.exit(1); }
  main(pdf, out).catch((e) => { console.error(e); process.exit(1); });
}
module.exports = { main };
