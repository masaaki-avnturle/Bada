// badahost.js — Node 上で Bada アプリを動かすためのヘッドレス環境 (テスト・CLI 用)
const fs = require("fs"), path = require("path");
global.CTCad = require("../src/cad.js");
global.ContactGPT = require("../src/gpt.js");
global.CTDraft = require("../src/drafting.js");
global.Bada = require("../src/bada.js");
const L = require("../src/badalib.js");
const { Index } = require("../src/chat.js");
const ROOT = path.join(__dirname, "..");

function badaFiles() {
  const out = {}, base = path.join(ROOT, "bada");
  (function walk(d) {
    for (const f of fs.readdirSync(d)) {
      const p = path.join(d, f);
      if (fs.statSync(p).isDirectory()) walk(p); else if (f.endsWith(".bada")) out[path.relative(base, p).split(path.sep).join("/")] = fs.readFileSync(p, "utf8");
    }
  })(base);
  return out;
}
// UI スタブ: 宣言されたパラメータの既定値を保持し、出力を記録する
function stubUI() {
  const vals = {}, outputs = {}, plots = {}, log = [];
  return {
    vals, outputs, plots, log,
    reset() {},
    param(k, l, d) { if (!(k in vals)) vals[k] = d; return vals[k]; },
    check(k, l, d) { if (!(k in vals)) vals[k] = d; return vals[k]; },
    select(k, l, o, d) { if (!(k in vals)) vals[k] = d; return vals[k]; },
    text(k, l, d) { if (!(k in vals)) vals[k] = d; return vals[k]; },
    color(k, l, d) { if (!(k in vals)) vals[k] = d; return vals[k]; },
    set(k, v) { vals[k] = v; return null; },
    get(k) { return k in vals ? vals[k] : null; },
    output(k, l, v) { outputs[k] = [l, v]; return null; },
    plot(k, t, s, m) { plots[k] = { title: t, series: s, marks: m }; return null; },
    hud(t) { log.push(["hud", t]); }, toast(t) { log.push(["toast", t]); }, chips() {}, section() {}, button() {}, view(v) { log.push(["view", v]); }, fit() {},
    request() {}, export(k) { log.push(["export", k]); },
  };
}
function makeApp(file, opts) {
  opts = opts || {};
  const eqs = JSON.parse(fs.readFileSync(path.join(ROOT, "data", "equations.json"), "utf8"));
  const files = badaFiles(), ui = stubUI(), chat = { replies: [], refs: [], gens: [] };
  chat.reply = (m) => { chat.replies.push(m); }; chat.ref = (id) => { chat.refs.push(id); }; chat.gen = (t) => { chat.gens.push(t); };
  chat.codes = []; chat.code = (file, src, target, desc) => { chat.codes.push({ file, src, target, desc }); };
  // ストリーム生成の同期版: Bada の gen_next / gen_stop を 1 文字ずつ呼ぶ
  chat.stream = (prompt, n) => {
    const G = env.model(); if (!G) return null;
    const ids = G.encode(prompt); let out = "";
    for (let k = 0; k < n; k++) {
      const tok = app.call("gen_next", [ids]); ids.push(tok); out += G.decode([tok]);
      if (app.call("gen_stop", [out])) { out = out.slice(0, -3); break; }
    }
    chat.gens.push(out.trim()); return null;
  };
  let model = null;
  const wPath = path.join(ROOT, "data", "contactgpt_weights.json");
  if (opts.model !== false && fs.existsSync(wPath)) model = ContactGPT.GPT.fromJSON(JSON.parse(fs.readFileSync(wPath, "utf8")));
  const printed = [];
  const env = { files, ui, chat, equations: eqs, index: new Index(eqs), scene: new L.Scene(), model: () => model,
    onPrint: (l) => printed.push(l), onError: (e) => { throw e; } };
  const app = new L.BadaApp(env);
  app.start(files[file], file);
  return { app, env, ui, chat, printed, files };
}
module.exports = { makeApp, badaFiles, stubUI };

if (require.main === module) {
  // CLI: node tools/badahost.js apps/ufo.bada  — Bada アプリをヘッドレス実行
  const r = makeApp(process.argv[2] || "apps/transporter.bada");
  console.log(r.printed.join("\n"));
  for (const [k, [l, v]] of Object.entries(r.ui.outputs)) console.log(`${l}: ${Array.isArray(v) ? JSON.stringify(v) : v}`);
  console.log(`部品 ${r.env.scene.parts.size} 個, 寸法 ${r.env.scene.dims.length}, 部材表 ${r.env.scene.bom.length}`);
}
