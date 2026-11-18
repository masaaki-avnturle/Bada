/*
 * build-pdf-cmaps.js — pdf/cmaps.js を作り直す
 *
 *   npm i pdfjs-dist@3.11.174
 *   node bada_cinevim/tools/build-pdf-cmaps.js node_modules/pdfjs-dist/cmaps
 *
 * pdf.js の CJK 用 CMap (*.bcmap) を base64 にして 1 つの JS にまとめます。
 * file:// では fetch が使えないため、CMap は <script> で読み込める形で同梱します
 * (これが無いと、ToUnicode を持たない日本語 PDF が文字化けします)。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const dir = process.argv[2];
if (!dir) { console.error("usage: node build-pdf-cmaps.js <pdfjs-dist/cmaps>"); process.exit(1); }
const names = fs.readdirSync(dir).filter(f => f.endsWith(".bcmap")).sort();
let out = "/* pdf.js 3.11.174 の bcmap (Adobe CMap Resources, BSD-3-Clause) を base64 で同梱。\n" +
          "   tools/build-pdf-cmaps.js が生成します。手で編集しないでください。 */\n" +
          "window.__CINEVIM_CMAPS__ = {\n";
out += names.map(f => JSON.stringify(f.slice(0, -6)) + ":" +
  JSON.stringify(fs.readFileSync(path.join(dir, f)).toString("base64"))).join(",\n");
out += "\n};\n";
fs.writeFileSync(path.join(__dirname, "..", "pdf", "cmaps.js"), out);
console.log(names.length + " cmaps -> pdf/cmaps.js (" + out.length + " bytes)");
