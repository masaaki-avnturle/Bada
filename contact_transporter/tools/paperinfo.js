#!/usr/bin/env node
// paperinfo.js — 論文 PDF を解析して JSON を出す:  node tools/paperinfo.js paper.pdf [out.json]
const fs = require("fs"), path = require("path");
const P = require("../src/paper.js");
async function loadPaper(file) {
  const pdfjs = require("pdfjs-dist/legacy/build/pdf.js");
  const cmaps = path.join(path.dirname(require.resolve("pdfjs-dist/package.json")), "cmaps") + "/";
  const doc = await P.readPdf(pdfjs, new Uint8Array(fs.readFileSync(file)), { docOptions: { cMapUrl: cmaps, cMapPacked: true, standardFontDataUrl: undefined } });
  return P.analyze(doc, path.basename(file));
}
module.exports = { loadPaper };
if (require.main === module) {
  const origWarn = console.warn; console.warn = (...a) => { if (!String(a[0]).includes("polyfill")) origWarn(...a); };
  const origLog = console.log; console.log = (...a) => { if (!String(a[0]).includes("polyfill")) origLog(...a); };
  loadPaper(process.argv[2]).then((p) => {
    const out = process.argv[3];
    if (out) fs.writeFileSync(out, JSON.stringify(p));
    origLog(JSON.stringify({ title: p.title, pages: p.pages, lines: p.lines, registry: p.registry, eqs: p.equations.length, stat: p.stat, tags: p.tagCount, params: p.params.slice(0, 8), sample: p.equations.slice(0, 4) }, null, 1));
  });
}
