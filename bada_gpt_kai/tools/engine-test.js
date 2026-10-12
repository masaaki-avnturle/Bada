/*
 * engine-test.js — BadaGPT改 エンジンの単体テスト (Node で実行)
 *
 *   node bada_gpt_kai/tools/engine-test.js
 *
 * index.html に埋め込まれた <script id="engine"> を取り出して検証します
 * (= 実際に APK / EXE に入るコードそのものをテストする)。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const zlib = require("zlib");

const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const m = html.match(/<script id="engine">([\s\S]*?)<\/script>/);
if (!m) { console.error("no <script id=\"engine\"> in index.html"); process.exit(1); }
const ui = html.match(/<script id="ui">([\s\S]*?)<\/script>/);
if (!ui) { console.error("no <script id=\"ui\"> in index.html"); process.exit(1); }
new vm.Script(ui[1], { filename: "ui.js" }); /* 構文検査 */

const ctx = { TextEncoder, TextDecoder, btoa, atob, console, Math, JSON, Date };
vm.createContext(ctx);
vm.runInContext(m[1] + "\n;this.E = { utf8, crc32, zipBuild, pdfFromJpegs, bytesToBase64, base64ToBytes, mdBlocks, mdToHtml, stripInline, slugify, safePath, parseFiles, TARGETS, MODELS, buildSystemPrompt, buildUserContent, bioSummary, claudeRequest, sseNew, sseFeed, localGenerateApp, localGenerateDoc, scaffoldPackaging, assembleProject, ppgAnalyze, breathAnalyze, calmIndex, gammaC, gammaR };", ctx, { filename: "engine.js" });
const E = ctx.E;

let pass = 0, fail = 0;
function ok(cond, msg) { if (cond) pass++; else { fail++; console.error("FAIL: " + msg); } }
function near(a, b, tol, msg) { ok(Math.abs(a - b) <= tol, msg + " (got " + a + ", want " + b + ")"); }

/* 1. CRC32 / ZIP */
near(E.crc32(E.utf8("123456789")), 0xCBF43926, 0, "crc32 check value");
{
  const files = [{ path: "apps/x/www/index.html", data: "<p>こんにちは</p>" }, { path: "a.bin", data: new Uint8Array([0, 1, 2, 255]) }];
  const zip = Buffer.from(E.zipBuild(files));
  ok(zip.readUInt32LE(0) === 0x04034b50, "zip local header signature");
  const eocd = zip.length - 22;
  ok(zip.readUInt32LE(eocd) === 0x06054b50, "zip end-of-central-directory");
  ok(zip.readUInt16LE(eocd + 10) === 2, "zip entry count");
  /* 1 件目を読み戻して内容と CRC を確認 */
  const nlen = zip.readUInt16LE(26), size = zip.readUInt32LE(18);
  const name = zip.slice(30, 30 + nlen).toString("utf8");
  const data = zip.slice(30 + nlen, 30 + nlen + size).toString("utf8");
  ok(name === "apps/x/www/index.html", "zip entry name");
  ok(data === "<p>こんにちは</p>", "zip entry data (UTF-8)");
  ok(zip.readUInt16LE(6) & 0x0800, "zip UTF-8 flag");
  ok(zlib.crc32 ? zlib.crc32(Buffer.from(data)) === zip.readUInt32LE(14) : true, "zip crc matches zlib");
}

/* 2. PDF */
{
  const fakeJpeg = new Uint8Array([0xFF, 0xD8, 0xFF, 0xD9]);
  const pdf = Buffer.from(E.pdfFromJpegs([{ jpeg: fakeJpeg, w: 10, h: 14 }, { jpeg: fakeJpeg, w: 10, h: 14 }], "test"));
  const s = pdf.toString("latin1");
  ok(s.startsWith("%PDF-1.4"), "pdf header");
  ok(/\/Count 2/.test(s), "pdf page count");
  ok(s.trimEnd().endsWith("%%EOF"), "pdf trailer");
  /* xref の各オフセットが "N 0 obj" を指していること */
  const xrefPos = +s.match(/startxref\n(\d+)/)[1];
  ok(s.slice(xrefPos, xrefPos + 4) === "xref", "startxref points at xref");
  const entries = s.slice(xrefPos).split("\n").slice(3).filter((l) => / 00000 n $/.test(l));
  ok(entries.length === 3 + 2 * 3, "xref entry count");
  entries.forEach((l, i) => { const off = +l.slice(0, 10); ok(s.slice(off).startsWith((i + 1) + " 0 obj"), "xref offset for obj " + (i + 1)); });
}

/* 3. Markdown */
{
  const b = E.mdBlocks("# 題\n\n本文 **太字**\n続き\n\n- 一\n- 二\n\n```\ncode()\n```\n---\n## 小");
  ok(b.map((x) => x.type).join(",") === "h1,p,li,li,code,hr,h2", "md block types: " + b.map((x) => x.type));
  ok(b[1].text === "本文 **太字** 続き", "md paragraph join");
  ok(E.stripInline("a **b** `c`") === "a b c", "stripInline");
  const h = E.mdToHtml("- <x>\n\n**y**");
  ok(h.includes("<ul>") && h.includes("&lt;x&gt;") && h.includes("<b>y</b>"), "mdToHtml escapes and formats");
}

/* 4. 名前・パス・生成ファイル解析 */
ok(E.slugify("My Todo App!") === "my-todo-app", "slugify ascii");
ok(/^app-[0-9a-f]+$/.test(E.slugify("家計簿")), "slugify non-ascii → hash");
ok(E.slugify("家計簿") === E.slugify("家計簿"), "slugify stable");
ok(E.safePath("../etc/passwd") === null && E.safePath("/abs") === "abs" && E.safePath("a/./b") === null, "safePath rejects traversal");
ok(E.safePath("src\\main.rs") === "src/main.rs", "safePath normalizes backslashes");
{
  const r = E.parseFiles("説明\n=== FILE: www/index.html ===\n```html\n<h1>x</h1>\n```\n=== END FILE ===\n=== FILE: ../bad ===\nz\n=== END FILE ===\n=== FILE: README.md ===\n# r");
  ok(r.files.length === 2, "parseFiles count (bad path skipped, truncated kept)");
  ok(r.files[0].content === "<h1>x</h1>", "parseFiles strips code fence");
  ok(r.truncated && r.files[1].truncated, "parseFiles detects truncation");
  ok(r.notes.includes("説明") && r.notes.includes("../bad"), "parseFiles notes");
}

/* 5. プロンプト / リクエスト / SSE */
{
  ok(E.buildSystemPrompt("both").includes("www/index.html"), "system prompt (app)");
  ok(E.buildSystemPrompt("pdf").includes("document.md"), "system prompt (pdf)");
  ok(E.buildSystemPrompt("source", "Rust").includes("Rust"), "system prompt (source)");
  const content = E.buildUserContent({ text: "瞑想アプリ", name: "瞑想", target: "apk",
    images: ["data:image/png;base64,AAAA", "bogus"], bio: { bpm: 64.4, breath: 6.2, rmssd: NaN, calm: 71 } });
  ok(content.length === 2 && content[0].type === "image" && content[0].source.media_type === "image/png", "user content image block");
  ok(content[1].text.includes("心拍 64 bpm") && content[1].text.includes("思考") === false, "user content bio summary");
  const req = E.claudeRequest({ apiKey: "k", model: "claude-opus-5-5", system: "s", content: content });
  ok(req.body.model === "claude-opus-5-5" && req.body.stream === true && req.body.max_tokens === 64000, "request basics");
  ok(req.body.output_config.effort === "high" && req.body.fallbacks === "default", "request effort + fallbacks");
  ok(req.headers["anthropic-beta"] === "server-side-fallback-2026-07-01", "fallback beta header");
  ok(req.headers["anthropic-dangerous-direct-browser-access"] === "true" && req.headers["x-api-key"] === "k", "browser headers");
  ok(!("thinking" in req.body) && !("temperature" in req.body), "no rejected params");
  const h = E.claudeRequest({ apiKey: "k", model: "claude-haiku-5-5", system: "s", content: content });
  ok(!("fallbacks" in h.body) && !h.headers["anthropic-beta"], "haiku: no fallbacks");

  const st = E.sseNew();
  const stream = 'event: message_start\ndata: {"type":"message_start","message":{}}\n\n' +
    'event: content_block_delta\ndata: {"type":"content_block_delta","index":0,"delta":{"type":"thinking_delta","thinking":"…"}}\n\n' +
    'event: content_block_delta\ndata: {"type":"content_block_delta","index":1,"delta":{"type":"text_delta","text":"こん"}}\n\n' +
    'event: content_block_delta\ndata: {"type":"content_block_delta","index":1,"delta":{"type":"text_delta","text":"にちは"}}\n\n' +
    'event: message_delta\ndata: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":5}}\n\n';
  /* 任意の位置で分割されても同じ結果になること */
  for (let i = 0; i < stream.length; i += 7) E.sseFeed(st, stream.slice(i, i + 7));
  ok(st.text === "こんにちは" && st.stop === "end_turn" && st.outTokens === 5, "sse parse across chunk boundaries");
  const er = E.sseFeed(E.sseNew(), 'event: error\ndata: {"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}\n\n');
  ok(er.error === "Overloaded", "sse error event");
}

/* 6. ローカル生成と雛形 */
{
  const app = E.localGenerateApp({ name: "瞑想タイマー", text: "4秒吸う。6秒吐く。記録を残す", bio: { calm: 80 } });
  ok(app[0].path === "www/index.html" && app[0].content.includes("4秒吸う") && app[0].content.includes("<\/script>"), "local app html");
  const inner = app[0].content.match(/<script>([\s\S]*)<\/script>/)[1];
  new vm.Script(inner, { filename: "generated-app.js" });
  ok(true, "local app script parses");
  const doc = E.localGenerateDoc({ name: "報告", text: "本文" });
  ok(doc[0].path === "document.md" && doc[0].content.startsWith("# 報告"), "local doc");

  const files = E.scaffoldPackaging({ name: "瞑想 <タイマー>", slug: "meditation", target: "both" });
  const byPath = Object.fromEntries(files.map((f) => [f.path, f.content]));
  ok(byPath["apps/meditation/cordova/config.xml"].includes("&lt;タイマー&gt;"), "config.xml escapes name");
  ok(byPath["apps/meditation/cordova/config.xml"].includes("io.github.badagptkai.meditation"), "config.xml app id");
  const pkg = JSON.parse(byPath["apps/meditation/electron/package.json"]);
  ok(pkg.build.win.target.includes("nsis") && pkg.build.extraResources[0].from === "../www", "electron package.json");
  new vm.Script(byPath["apps/meditation/electron/main.js"].replace(/require\(/g, "(function(){return{app:{},BrowserWindow:{},shell:{}}})("), { filename: "main.js" });
  ok(true, "electron main.js parses");
  const wf = byPath[".github/workflows/meditation-build.yml"];
  ok(wf.includes("android-apk:") && wf.includes("windows-exe:") && wf.includes("${{ secrets.GITHUB_TOKEN }}"), "workflow jobs");
  ok(wf.includes("tag_name: meditation-latest") && !/\t/.test(wf), "workflow release tag / no tabs");
  ok(E.scaffoldPackaging({ name: "x", slug: "xyz", target: "apk" }).every((f) => !f.path.includes("electron")), "apk-only scaffold");

  const proj = E.assembleProject({ name: "M", slug: "m-app", target: "exe" },
    [{ path: "app.html", content: "<p>"}, { path: "electron/main.js", content: "evil" }, { path: "README.md", content: "r" }]);
  const pp = proj.map((f) => f.path);
  ok(pp.includes("apps/m-app/www/index.html") && pp.includes("apps/m-app/README.md"), "assemble: html promoted to www/index.html");
  ok(proj.find((f) => f.path === "apps/m-app/electron/main.js").data !== "evil", "assemble: packaging not overridden");
  const docProj = E.assembleProject({ name: "D", slug: "doc", target: "pdf" },
    [{ path: "document.md", content: "# D" }, { path: "document.pdf", data: new Uint8Array([1, 2]) }]);
  ok(docProj.length === 2 && docProj[1].path === "apps/doc/document.pdf" && docProj[1].data.length === 2, "assemble pdf: binary kept, no packaging");
}

/* 7. バイオフィードバック */
{
  let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647) - 0.5;
  for (const bpm of [52, 72, 110]) {
    const s = [];
    for (let i = 0; i < 30 * 15; i++) {
      const t = i / 30;
      /* 脈波 (急な立ち上がり) + 呼吸による基線のゆらぎ + 雑音 */
      const ph = (t * bpm / 60) % 1;
      s.push({ t, v: 180 - 4 * Math.exp(-ph * 6) + 3 * Math.sin(2 * Math.PI * 0.2 * t) + 0.4 * rnd() });
    }
    near(E.ppgAnalyze(s).bpm, bpm, 2, "ppg bpm " + bpm);
  }
  /* 拍間隔をゆらがせると RMSSD が出る */
  {
    const s = []; let t = 0, beat = 0; const ibis = [];
    for (let k = 0; k < 20; k++) ibis.push(k % 2 ? 0.80 : 0.86);
    let next = ibis[0], kk = 0;
    for (let i = 0; i < 30 * 16; i++) {
      t = i / 30;
      if (t - beat >= next) { beat += next; next = ibis[++kk % ibis.length]; }
      s.push({ t, v: 180 - 4 * Math.exp(-(t - beat) * 6) });
    }
    const r = E.ppgAnalyze(s);
    near(r.bpm, 60 / 0.83, 3, "ppg bpm with variability");
    ok(r.rmssd > 30 && r.rmssd < 90, "ppg rmssd ~60ms (got " + r.rmssd + ")");
  }
  ok(isNaN(E.ppgAnalyze([{ t: 0, v: 1 }]).bpm), "ppg too short");
  for (const br of [6, 12]) {
    const s = [];
    for (let i = 0; i < 60 * 45; i++) {
      const t = i / 60;
      s.push({ t, v: 0.02 + 0.02 * Math.max(0, Math.sin(2 * Math.PI * br / 60 * t)) + 0.003 * rnd() });
    }
    near(E.breathAnalyze(s), br, 1, "breath rate " + br);
  }
  ok(isNaN(E.breathAnalyze([])), "breath empty");
  near(E.calmIndex(80, 6), 100, 1e-9, "calm max");
  ok(E.calmIndex(10, 20) < 30, "calm low");
  ok(isNaN(E.calmIndex(NaN, NaN)), "calm none");
  ok(E.bioSummary(null) === "", "bio summary empty");
}

/* 8. 複素ガンマ関数 */
{
  near(E.gammaR(5), 24, 1e-9, "Γ(5)=24");
  near(E.gammaR(0.5), Math.sqrt(Math.PI), 1e-12, "Γ(1/2)=√π");
  near(E.gammaR(-0.5), -2 * Math.sqrt(Math.PI), 1e-12, "Γ(-1/2)=-2√π (reflection)");
  const g = E.gammaC(1, 1);
  near(g[0], 0.4980156681183560, 1e-12, "Re Γ(1+i)");
  near(g[1], -0.1549498283018106, 1e-12, "Im Γ(1+i)");
  /* 関数等式 Γ(z+1) = z Γ(z) */
  const z = [0.3, 1.7], a = E.gammaC(z[0] + 1, z[1]), b = E.gammaC(z[0], z[1]);
  near(a[0], z[0] * b[0] - z[1] * b[1], 1e-12, "Γ(z+1)=zΓ(z) re");
  near(a[1], z[0] * b[1] + z[1] * b[0], 1e-12, "Γ(z+1)=zΓ(z) im");
}

console.log(pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
