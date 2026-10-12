/*
 * build.js — src/shell.html に src/*.js を埋め込み、自己完結の index.html
 *            (APK / EXE / AppImage・deb にそのまま同梱する本体) を作る。
 *
 *   node bada_gpt_telegraph/tools/build.js          # index.html を書き出す
 *   node bada_gpt_telegraph/tools/build.js --check  # index.html が src と一致するか検査 (CI 用)
 */
"use strict";
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const read = (p) => fs.readFileSync(path.join(root, p), "utf8");

/* engine → comprehend → generate → paper の順に連結 (後のファイルが前の関数を使う) */
const ENGINE_FILES = ["src/engine.js", "src/comprehend.js", "src/generate.js", "src/paper.js"];
const engine = ENGINE_FILES.map(read).join("\n");
const ui = read("src/ui.js");
for (const [name, src] of [["engine", engine], ["ui.js", ui]]) {
  if (/<\/script/i.test(src)) {
    console.error(name + " に </script が含まれています (インライン化すると壊れます)");
    process.exit(1);
  }
}
const html = read("src/shell.html")
  .replace("/*@ENGINE@*/", () => engine)
  .replace("/*@UI@*/", () => ui);

const out = path.join(root, "index.html");
if (process.argv.includes("--check")) {
  const cur = fs.existsSync(out) ? fs.readFileSync(out, "utf8") : "";
  if (cur !== html) {
    console.error("index.html が src/ と一致しません。node bada_gpt_telegraph/tools/build.js を実行してください。");
    process.exit(1);
  }
  console.log("index.html is up to date");
} else {
  fs.writeFileSync(out, html);
  console.log("wrote " + path.relative(process.cwd(), out) + " (" + html.length + " bytes)");
}
