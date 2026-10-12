/*
 * engine.js — BadaGPT改 の純ロジック (DOM 非依存・Node でテスト可能)
 *
 *   - ZIP 書き出し (無圧縮 / UTF-8 ファイル名)
 *   - PDF 書き出し (JPEG ページ画像を DCTDecode で埋め込む)
 *   - Markdown → ブロック列 / HTML
 *   - Claude API リクエスト本体と SSE ストリームの解析
 *   - 生成テキスト → ファイル群の解析 (=== FILE: path === 形式)
 *   - APK (Cordova) / Windows EXE (Electron) / GitHub Actions の雛形生成
 *   - バイオフィードバック: PPG 心拍 / RMSSD / 呼吸数 / 落ち着き指数
 *   - 複素ガンマ関数 Γ(z) (Lanczos 近似 + 相反公式)
 *
 * 正直な範囲: 生体信号は「心拍・呼吸」という身体の状態であり、
 * 思考の内容は読み取れません。生成への入力はあくまで文章・音声・スケッチ・
 * 写真で、生体信号はデザインの雰囲気 (色・テンポ) のヒントとしてのみ使います。
 */
"use strict";

var KAI_VERSION = "1.0.0";

/* ───────────── バイト列ユーティリティ ───────────── */

function utf8(str) { return new TextEncoder().encode(String(str)); }

function concatBytes(chunks) {
  var n = 0, i;
  for (i = 0; i < chunks.length; i++) n += chunks[i].length;
  var out = new Uint8Array(n), off = 0;
  for (i = 0; i < chunks.length; i++) { out.set(chunks[i], off); off += chunks[i].length; }
  return out;
}

var CRC_TABLE = (function () {
  var t = new Uint32Array(256);
  for (var n = 0; n < 256; n++) {
    var c = n;
    for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c >>> 0;
  }
  return t;
})();

function crc32(bytes) {
  var c = 0xFFFFFFFF;
  for (var i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

function bytesToBase64(bytes) {
  var s = "", CH = 0x8000;
  for (var i = 0; i < bytes.length; i += CH) s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
  return btoa(s);
}

function base64ToBytes(b64) {
  var s = atob(b64), out = new Uint8Array(s.length);
  for (var i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
}

/* ───────────── ZIP (無圧縮 store) ───────────── */

function zipBuild(files) {
  var locals = [], centrals = [], offset = 0;
  function u16(v) { return [v & 0xFF, (v >>> 8) & 0xFF]; }
  function u32(v) { return [v & 0xFF, (v >>> 8) & 0xFF, (v >>> 16) & 0xFF, (v >>> 24) & 0xFF]; }
  files.forEach(function (f) {
    var name = utf8(f.path);
    var data = typeof f.data === "string" ? utf8(f.data) : f.data;
    var crc = crc32(data);
    /* DOS 日時は固定 (1980-01-01) — 再現性のある ZIP にする */
    var head = [].concat(u16(20), u16(0x0800), u16(0), u16(0), u16(0x21),
                         u32(crc), u32(data.length), u32(data.length), u16(name.length), u16(0));
    var local = concatBytes([new Uint8Array([0x50, 0x4B, 0x03, 0x04].concat(head)), name, data]);
    locals.push(local);
    var central = concatBytes([new Uint8Array([0x50, 0x4B, 0x01, 0x02].concat(u16(20), head,
                              u16(0), u16(0), u16(0), u32(0), u32(offset))), name]);
    centrals.push(central);
    offset += local.length;
  });
  var cd = concatBytes(centrals);
  var end = new Uint8Array([0x50, 0x4B, 0x05, 0x06].concat(u16(0), u16(0), u16(files.length),
                           u16(files.length), u32(cd.length), u32(offset), u16(0)));
  return concatBytes(locals.concat([cd, end]));
}

/* ───────────── PDF (JPEG ページ画像) ───────────── */

/* pages: [{ jpeg: Uint8Array, w: 画素幅, h: 画素高 }] → A4 (595×842pt) の PDF */
function pdfFromJpegs(pages, title) {
  var PW = 595, PH = 842;
  var parts = [], offsets = [], pos = 0;
  function push(b) { parts.push(b); pos += b.length; }
  function obj(num, bodyBytes) { offsets[num] = pos; push(bodyBytes); }
  push(utf8("%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"));
  var n = pages.length;
  /* 1: Catalog, 2: Pages, 3: Info, 以降 ページごとに (Page, Content, Image) */
  var kids = [];
  for (var i = 0; i < n; i++) kids.push((4 + i * 3) + " 0 R");
  obj(1, utf8("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"));
  obj(2, utf8("2 0 obj\n<< /Type /Pages /Kids [" + kids.join(" ") + "] /Count " + n + " >>\nendobj\n"));
  var t = String(title || "BadaGPT Kai").replace(/[^\x20-\x7E]/g, "?").replace(/[()\\]/g, "");
  obj(3, utf8("3 0 obj\n<< /Title (" + t + ") /Producer (BadaGPT Kai " + KAI_VERSION + ") >>\nendobj\n"));
  pages.forEach(function (p, i) {
    var pn = 4 + i * 3, cn = pn + 1, im = pn + 2;
    obj(pn, utf8(pn + " 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + PW + " " + PH + "] " +
                 "/Resources << /XObject << /Im" + i + " " + im + " 0 R >> >> /Contents " + cn + " 0 R >>\nendobj\n"));
    var content = "q " + PW + " 0 0 " + PH + " 0 0 cm /Im" + i + " Do Q";
    obj(cn, utf8(cn + " 0 obj\n<< /Length " + content.length + " >>\nstream\n" + content + "\nendstream\nendobj\n"));
    offsets[im] = pos;
    push(utf8(im + " 0 obj\n<< /Type /XObject /Subtype /Image /Width " + p.w + " /Height " + p.h +
              " /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length " + p.jpeg.length + " >>\nstream\n"));
    push(p.jpeg);
    push(utf8("\nendstream\nendobj\n"));
  });
  var total = 4 + n * 3;
  var xref = pos;
  var x = "xref\n0 " + total + "\n0000000000 65535 f \n";
  for (var k = 1; k < total; k++) x += ("0000000000" + offsets[k]).slice(-10) + " 00000 n \n";
  x += "trailer\n<< /Size " + total + " /Root 1 0 R /Info 3 0 R >>\nstartxref\n" + xref + "\n%%EOF\n";
  push(utf8(x));
  return concatBytes(parts);
}

/* ───────────── Markdown ───────────── */

function mdBlocks(md) {
  var lines = String(md || "").replace(/\r\n?/g, "\n").split("\n");
  var out = [], para = [], i = 0;
  function flush() { if (para.length) { out.push({ type: "p", text: para.join(" ") }); para = []; } }
  while (i < lines.length) {
    var l = lines[i];
    if (/^```/.test(l)) {
      flush();
      var code = []; i++;
      while (i < lines.length && !/^```/.test(lines[i])) { code.push(lines[i]); i++; }
      out.push({ type: "code", text: code.join("\n") }); i++; continue;
    }
    var h = l.match(/^(#{1,3})\s+(.*)$/);
    if (h) { flush(); out.push({ type: "h" + h[1].length, text: h[2].trim() }); i++; continue; }
    var li = l.match(/^\s*(?:[-*+]|\d+[.)])\s+(.*)$/);
    if (li) { flush(); out.push({ type: "li", text: li[1].trim() }); i++; continue; }
    if (/^\s*(?:---+|\*\*\*+)\s*$/.test(l)) { flush(); out.push({ type: "hr", text: "" }); i++; continue; }
    if (/^\s*$/.test(l)) { flush(); i++; continue; }
    para.push(l.trim()); i++;
  }
  flush();
  return out;
}

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function stripInline(s) { return String(s).replace(/\*\*(.+?)\*\*/g, "$1").replace(/`([^`]+)`/g, "$1"); }

function mdToHtml(md) {
  var html = [], inList = false;
  mdBlocks(md).forEach(function (b) {
    if (b.type !== "li" && inList) { html.push("</ul>"); inList = false; }
    var t = escapeHtml(b.text).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>");
    if (b.type === "li") { if (!inList) { html.push("<ul>"); inList = true; } html.push("<li>" + t + "</li>"); }
    else if (b.type === "code") html.push("<pre>" + escapeHtml(b.text) + "</pre>");
    else if (b.type === "hr") html.push("<hr>");
    else if (b.type === "p") html.push("<p>" + t + "</p>");
    else html.push("<" + b.type + ">" + t + "</" + b.type + ">");
  });
  if (inList) html.push("</ul>");
  return html.join("\n");
}

/* ───────────── 名前・パス ───────────── */

function slugify(name) {
  var s = String(name || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40);
  if (s.length >= 3) return s;
  /* 日本語名など ASCII が残らない場合は名前のハッシュで安定した識別子にする */
  return "app-" + crc32(utf8(String(name || "app"))).toString(16);
}

function safePath(p) {
  var s = String(p || "").trim().replace(/\\/g, "/").replace(/^\.?\/+/, "");
  if (!s || s.length > 200) return null;
  var segs = s.split("/");
  for (var i = 0; i < segs.length; i++) {
    if (segs[i] === "" || segs[i] === "." || segs[i] === "..") return null;
    if (/[\x00-\x1F:*?"<>|]/.test(segs[i])) return null;
  }
  return s;
}

/* 生成テキスト中の
 *   === FILE: path ===
 *   ...内容...
 *   === END FILE ===
 * を抜き出す。未閉じの最終ファイル (max_tokens 打ち切り) は truncated として返す。 */
function parseFiles(text) {
  var lines = String(text || "").replace(/\r\n?/g, "\n").split("\n");
  var files = [], cur = null, notes = [];
  for (var i = 0; i < lines.length; i++) {
    var l = lines[i];
    var m = l.match(/^\s*===\s*FILE:\s*(.+?)\s*===\s*$/);
    if (m && !cur) { cur = { path: safePath(m[1]), raw: m[1], body: [] }; continue; }
    if (cur && /^\s*===\s*END FILE\s*===\s*$/.test(l)) {
      if (cur.path) files.push({ path: cur.path, content: cur.body.join("\n") });
      else notes.push("不正なパスを無視しました: " + cur.raw);
      cur = null; continue;
    }
    if (cur) cur.body.push(l); else if (l.trim()) notes.push(l);
  }
  var truncated = false;
  if (cur) { truncated = true; if (cur.path) files.push({ path: cur.path, content: cur.body.join("\n"), truncated: true }); }
  /* ```lang ... ``` で包まれていたら外す */
  files.forEach(function (f) {
    var mm = f.content.match(/^\s*```[\w+-]*\n([\s\S]*?)\n```\s*$/);
    if (mm) f.content = mm[1];
  });
  return { files: files, notes: notes.join("\n").trim(), truncated: truncated };
}

/* ───────────── 生成ターゲット ───────────── */

var TARGETS = {
  both:   { label: "Android APK + Windows 10/11 EXE", packaging: true },
  apk:    { label: "Android APK",                     packaging: true },
  exe:    { label: "Windows 10/11 EXE",               packaging: true },
  pdf:    { label: "PDF 文書",                         packaging: false },
  source: { label: "任意のソースコード",                packaging: false }
};

function buildSystemPrompt(target, lang) {
  var common = [
    "あなたは BadaGPT改 のコード生成エンジンです。ユーザーの依頼文・スケッチ・写真から、動く成果物を作ります。",
    "出力は必ず次の形式のファイルの並びにしてください (説明文はファイルの外に短く書いてよい):",
    "=== FILE: 相対パス ===",
    "ファイルの内容 (コードフェンスで囲まない)",
    "=== END FILE ===",
    "相対パスに .. や絶対パスを使わないこと。",
    "生体データ (心拍・呼吸・落ち着き指数) が添えられている場合、それは利用者の身体の状態であり思考の内容ではありません。配色やテンポなど雰囲気のヒントとしてだけ使ってください。",
    "UI の言語は依頼文の言語に合わせてください。"
  ];
  var spec;
  if (target === "pdf") {
    spec = [
      "成果物は PDF 文書です。document.md を 1 つだけ Markdown で書いてください。",
      "使える記法: # 見出し / ## / ### / 段落 / - 箇条書き / 1. 番号付き / ``` コード ``` / **太字** / ---。表や画像は使わないこと。"
    ];
  } else if (target === "source") {
    spec = [
      "成果物は任意のソースコードのプロジェクトです。言語・フレームワーク: " + (lang || "依頼文から最適なものを選ぶ") + "。",
      "ビルド・実行手順を書いた README.md を必ず含め、そのまま動く完全なコードを書いてください (省略記号や TODO で済ませない)。"
    ];
  } else {
    spec = [
      "成果物は Android APK (Cordova の WebView) と Windows 10/11 EXE (Electron) で同じ中身として動くアプリです。",
      "www/index.html を 1 つだけ書いてください。CSS と JavaScript はすべてインラインにし、外部 URL (CDN・フォント・画像) を一切読み込まずオフラインで動くこと。",
      "スマートフォン縦画面とデスクトップの両方で使えるレスポンシブなレイアウトにし、データを保存する場合は localStorage を使うこと。",
      "パッケージ設定 (config.xml / package.json / main.js / ワークフロー) は BadaGPT改 が別途生成するので書かないこと。",
      "必要なら README.md (使い方) を追加してよい。"
    ];
  }
  return common.concat(spec).join("\n");
}

/* bio: { bpm, rmssd, breath, calm } (どれも省略可) */
function bioSummary(bio) {
  if (!bio) return "";
  var parts = [];
  if (isFinite(bio.bpm)) parts.push("心拍 " + Math.round(bio.bpm) + " bpm");
  if (isFinite(bio.rmssd)) parts.push("心拍変動 RMSSD " + Math.round(bio.rmssd) + " ms");
  if (isFinite(bio.breath)) parts.push("呼吸 " + bio.breath.toFixed(1) + " 回/分");
  if (isFinite(bio.calm)) parts.push("落ち着き指数 " + Math.round(bio.calm) + "/100");
  return parts.length ? "生体データ (雰囲気のヒント): " + parts.join("、") : "";
}

function dataUrlToImageBlock(dataUrl) {
  var m = String(dataUrl || "").match(/^data:(image\/(?:png|jpeg|gif|webp));base64,(.+)$/);
  if (!m) return null;
  return { type: "image", source: { type: "base64", media_type: m[1], data: m[2] } };
}

/* input: { text, name, target, lang, images: [dataUrl], bio } */
function buildUserContent(input) {
  var content = [];
  (input.images || []).forEach(function (u) { var b = dataUrlToImageBlock(u); if (b) content.push(b); });
  var lines = [];
  if (input.name) lines.push("成果物の名前: " + input.name);
  lines.push("ターゲット: " + (TARGETS[input.target] || TARGETS.both).label);
  if (input.images && input.images.length) lines.push("添付画像は利用者が描いたスケッチ/写真です。画面構成や雰囲気の参考にしてください。");
  var b = bioSummary(input.bio);
  if (b) lines.push(b);
  lines.push("");
  lines.push("依頼:");
  lines.push(String(input.text || "").trim() || "(依頼文なし — 添付画像から意図を汲み取ってください)");
  content.push({ type: "text", text: lines.join("\n") });
  return content;
}

var MODELS = [
  { id: "claude-opus-5-5",   label: "Claude Opus 5.5 (既定)", fallback: true },
  { id: "claude-sonnet-5-5", label: "Claude Sonnet 5.5",      fallback: true },
  { id: "claude-fable-5-1",  label: "Claude Fable 5.1",       fallback: true },
  { id: "claude-haiku-5-5",  label: "Claude Haiku 5.5",       fallback: false }
];

function claudeRequest(opts) {
  var model = opts.model || "claude-opus-5-5";
  var info = MODELS.filter(function (m) { return m.id === model; })[0];
  var headers = {
    "content-type": "application/json",
    "x-api-key": opts.apiKey,
    "anthropic-version": "2023-06-01",
    /* Cordova WebView / Electron から直接呼ぶため (キーは利用者自身のもの) */
    "anthropic-dangerous-direct-browser-access": "true"
  };
  var body = {
    model: model,
    max_tokens: 64000,
    stream: true,
    output_config: { effort: opts.effort || "high" },
    system: opts.system,
    messages: [{ role: "user", content: opts.content }]
  };
  if (info && info.fallback) {
    /* 安全分類器が拒否したときに既定の代替モデルへ自動で回す */
    headers["anthropic-beta"] = "server-side-fallback-2026-07-01";
    body.fallbacks = "default";
  }
  return { url: "https://api.anthropic.com/v1/messages", headers: headers, body: body };
}

/* SSE の逐次パーサ。state = sseNew(); sseFeed(state, chunk) を繰り返す */
function sseNew() { return { buf: "", text: "", stop: null, error: null, stopDetails: null, outTokens: 0 }; }

function sseFeed(state, chunk) {
  state.buf += chunk;
  var idx;
  while ((idx = state.buf.indexOf("\n\n")) >= 0) {
    var evt = state.buf.slice(0, idx); state.buf = state.buf.slice(idx + 2);
    var data = evt.split("\n").filter(function (l) { return l.indexOf("data:") === 0; })
                  .map(function (l) { return l.slice(5).trim(); }).join("");
    if (!data) continue;
    var j; try { j = JSON.parse(data); } catch (e) { continue; }
    if (j.type === "content_block_delta" && j.delta && j.delta.type === "text_delta") state.text += j.delta.text;
    else if (j.type === "message_delta") {
      if (j.delta && j.delta.stop_reason) state.stop = j.delta.stop_reason;
      if (j.delta && j.delta.stop_details) state.stopDetails = j.delta.stop_details;
      if (j.usage && j.usage.output_tokens) state.outTokens = j.usage.output_tokens;
    } else if (j.type === "error") state.error = (j.error && j.error.message) || "stream error";
  }
  return state;
}

/* ───────────── ローカル (オフライン) 生成 ───────────── */

/* API キーがないときの代替。依頼文から機能の箇条を拾い、
 * チェックリスト + メモ + 記録 を持つ自己完結アプリを組み立てる。 */
function localFeatures(text) {
  var t = String(text || "");
  var items = t.split(/[\n。、,.・]+/).map(function (s) { return s.trim(); })
               .filter(function (s) { return s.length >= 2 && s.length <= 60; });
  return items.slice(0, 8);
}

function localGenerateApp(input) {
  var name = input.name || "マイアプリ";
  var feats = localFeatures(input.text);
  var hue = input.bio && isFinite(input.bio.calm) ? Math.round(200 - input.bio.calm) : 200;
  var featJson = JSON.stringify(feats).replace(/</g, "\\u003c");
  var key = "kai_" + slugify(name);
  var html = [
    "<!doctype html>",
    "<html lang=\"ja\"><head><meta charset=\"utf-8\">",
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
    "<title>" + escapeHtml(name) + "</title>",
    "<style>",
    ":root{--h:" + hue + ";--bg:hsl(var(--h) 30% 8%);--fg:hsl(var(--h) 20% 92%);--ac:hsl(var(--h) 80% 60%);--card:hsl(var(--h) 25% 14%)}",
    "*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--fg)}",
    "main{max-width:720px;margin:0 auto;padding:16px}h1{color:var(--ac);font-size:1.5rem}",
    ".card{background:var(--card);border-radius:12px;padding:14px;margin:12px 0}",
    "label{display:flex;gap:8px;align-items:center;padding:6px 0}",
    "textarea,input{width:100%;background:transparent;color:var(--fg);border:1px solid var(--ac);border-radius:8px;padding:8px;font:inherit}",
    "button{background:var(--ac);color:#000;border:0;border-radius:8px;padding:8px 14px;font:inherit;cursor:pointer}",
    "ul{padding-left:20px}",
    "</style></head><body><main>",
    "<h1>" + escapeHtml(name) + "</h1>",
    "<p>" + escapeHtml(String(input.text || "").slice(0, 300)) + "</p>",
    "<section class=\"card\"><h2>機能チェックリスト</h2><div id=\"feats\"></div></section>",
    "<section class=\"card\"><h2>メモ</h2><textarea id=\"memo\" rows=\"6\"></textarea></section>",
    "<section class=\"card\"><h2>記録</h2><input id=\"entry\" placeholder=\"記録を追加\"> <p><button id=\"add\">追加</button></p><ul id=\"log\"></ul></section>",
    "</main><script>",
    "var FEATS=" + featJson + ",KEY=" + JSON.stringify(key) + ";",
    "function load(){try{return JSON.parse(localStorage.getItem(KEY))||{}}catch(e){return {}}}",
    "function save(s){try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}}",
    "var st=load();st.done=st.done||{};st.log=st.log||[];",
    "var fd=document.getElementById('feats');",
    "FEATS.forEach(function(f,i){var l=document.createElement('label');var c=document.createElement('input');c.type='checkbox';c.style.width='auto';c.checked=!!st.done[i];c.onchange=function(){st.done[i]=c.checked;save(st)};l.appendChild(c);l.appendChild(document.createTextNode(f));fd.appendChild(l)});",
    "if(!FEATS.length)fd.textContent='(依頼文から機能を抽出できませんでした)';",
    "var memo=document.getElementById('memo');memo.value=st.memo||'';memo.oninput=function(){st.memo=memo.value;save(st)};",
    "function render(){var ul=document.getElementById('log');ul.innerHTML='';st.log.forEach(function(x){var li=document.createElement('li');li.textContent=x;ul.appendChild(li)})}",
    "document.getElementById('add').onclick=function(){var e=document.getElementById('entry');if(!e.value.trim())return;st.log.unshift(new Date().toLocaleString()+' — '+e.value.trim());e.value='';save(st);render()};",
    "render();",
    "<\/script></body></html>"
  ].join("\n");
  return [{ path: "www/index.html", content: html }];
}

function localGenerateDoc(input) {
  var name = input.name || "文書";
  var md = ["# " + name, "", String(input.text || "").trim() || "(本文なし)", ""];
  var b = bioSummary(input.bio);
  if (b) md.push("---", "", b, "");
  md.push("---", "", "BadaGPT改 (オフライン生成) — " + new Date().toISOString().slice(0, 10));
  return [{ path: "document.md", content: md.join("\n") }];
}

/* ───────────── パッケージング雛形 (APK / EXE / Actions) ───────────── */

function scaffoldPackaging(o) {
  var name = o.name, slug = o.slug, root = "apps/" + slug;
  var pkgId = "io.github.badagptkai." + slug.replace(/-/g, "_");
  var product = slug.replace(/(^|-)([a-z0-9])/g, function (_, a, c) { return c.toUpperCase(); }).replace(/^[0-9]/, "A$&");
  var want = o.target === "both" ? ["apk", "exe"] : [o.target];
  var files = [];
  var xmlName = escapeHtml(name);

  if (want.indexOf("apk") >= 0) {
    files.push({ path: root + "/cordova/config.xml", content: [
      "<?xml version='1.0' encoding='utf-8'?>",
      "<!-- BadaGPT改 が生成した Cordova 設定 (Android APK) -->",
      "<widget id=\"" + pkgId + "\" version=\"1.0.0\"",
      "        xmlns=\"http://www.w3.org/ns/widgets\" xmlns:cdv=\"http://cordova.apache.org/ns/1.0\">",
      "  <name>" + xmlName + "</name>",
      "  <description>" + xmlName + " (generated by BadaGPT Kai)</description>",
      "  <content src=\"index.html\" />",
      "  <access origin=\"*\" />",
      "  <allow-intent href=\"http://*/*\" />",
      "  <allow-intent href=\"https://*/*\" />",
      "  <preference name=\"android-minSdkVersion\" value=\"24\" />",
      "  <platform name=\"android\">",
      "    <preference name=\"AndroidXEnabled\" value=\"true\" />",
      "  </platform>",
      "</widget>", ""].join("\n") });
  }

  if (want.indexOf("exe") >= 0) {
    files.push({ path: root + "/electron/package.json", content: JSON.stringify({
      name: slug, productName: product, version: "1.0.0",
      description: name + " (generated by BadaGPT Kai)", author: "BadaGPT Kai", license: "MIT",
      main: "main.js",
      scripts: { start: "electron .", dist: "electron-builder --win --x64" },
      devDependencies: { electron: "^31.0.0", "electron-builder": "^24.13.3" },
      build: {
        appId: pkgId, productName: product, publish: null,
        files: ["main.js", "package.json"],
        extraResources: [{ from: "../www", to: "www" }],
        directories: { output: "dist" },
        win: { target: ["nsis", "portable"], artifactName: product + "-${version}-${arch}.${ext}" },
        nsis: { oneClick: false, allowToChangeInstallationDirectory: true },
        portable: { artifactName: product + "-${version}-portable.${ext}" }
      }
    }, null, 2) + "\n" });
    files.push({ path: root + "/electron/main.js", content: [
      "/* BadaGPT改 が生成した Electron ラッパー (Windows 10/11 EXE) */",
      "const { app, BrowserWindow, shell } = require(\"electron\");",
      "const path = require(\"path\");",
      "function indexPath() {",
      "  return app.isPackaged",
      "    ? path.join(process.resourcesPath, \"www\", \"index.html\")",
      "    : path.join(__dirname, \"..\", \"www\", \"index.html\");",
      "}",
      "function createWindow() {",
      "  const win = new BrowserWindow({ width: 1200, height: 820, title: " + JSON.stringify(name) + ",",
      "    webPreferences: { contextIsolation: true, nodeIntegration: false } });",
      "  win.setMenuBarVisibility(false);",
      "  win.webContents.setWindowOpenHandler(({ url }) => {",
      "    if (/^https?:\\/\\//i.test(url)) shell.openExternal(url);",
      "    return { action: \"deny\" };",
      "  });",
      "  win.loadFile(indexPath());",
      "}",
      "app.whenReady().then(createWindow);",
      "app.on(\"window-all-closed\", () => { if (process.platform !== \"darwin\") app.quit(); });",
      "app.on(\"activate\", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });",
      ""].join("\n") });
  }

  var E = "${{ ";  /* GitHub Actions の式。JS のテンプレートと混ざらないよう連結で組む */
  var wf = [
    "name: " + slug + " build (BadaGPT Kai)",
    "",
    "# BadaGPT改 が生成したアプリ " + name.replace(/\n/g, " ") + " をビルドします。",
    "# apps/" + slug + "/ を push すると自動で走り、Release '" + slug + "-latest' に添付します。",
    "",
    "on:",
    "  push:",
    "    paths:",
    "      - 'apps/" + slug + "/**'",
    "      - '.github/workflows/" + slug + "-build.yml'",
    "  workflow_dispatch:",
    "",
    "permissions:",
    "  contents: write",
    "",
    "jobs:"
  ];
  if (want.indexOf("apk") >= 0) wf = wf.concat([
    "  android-apk:",
    "    runs-on: ubuntu-latest",
    "    steps:",
    "      - uses: actions/checkout@v4",
    "      - uses: actions/setup-java@v4",
    "        with:",
    "          distribution: temurin",
    "          java-version: '17'",
    "      - uses: actions/setup-node@v4",
    "        with:",
    "          node-version: 20",
    "      - uses: android-actions/setup-android@v3",
    "        with:",
    "          packages: ''",
    "      - name: Install Android SDK packages",
    "        run: |",
    "          yes | sdkmanager --licenses > /dev/null 2>&1 || true",
    "          sdkmanager \"platform-tools\" \"platforms;android-33\" \"build-tools;33.0.2\"",
    "      - name: Pin Gradle 7.6.4 (cordova-android 12)",
    "        run: |",
    "          curl -sSL https://services.gradle.org/distributions/gradle-7.6.4-bin.zip -o \"$HOME/gradle.zip\"",
    "          unzip -q \"$HOME/gradle.zip\" -d \"$HOME/gradle-dist\"",
    "          echo \"$HOME/gradle-dist/gradle-7.6.4/bin\" >> \"$GITHUB_PATH\"",
    "          echo \"CORDOVA_ANDROID_GRADLE_DISTRIBUTION_URL=https://services.gradle.org/distributions/gradle-7.6.4-bin.zip\" >> \"$GITHUB_ENV\"",
    "      - name: Build debug APK (Cordova)",
    "        run: |",
    "          set -e",
    "          npm install -g cordova@12.0.0",
    "          cordova create cordova-build " + pkgId + " " + product,
    "          rm -rf cordova-build/www",
    "          cp -r apps/" + slug + "/www cordova-build/www",
    "          cp apps/" + slug + "/cordova/config.xml cordova-build/config.xml",
    "          cd cordova-build",
    "          cordova platform add android@12.0.1",
    "          cordova build android",
    "          mkdir -p ../out",
    "          cp platforms/android/app/build/outputs/apk/debug/*.apk ../out/" + slug + "-debug.apk",
    "      - uses: actions/upload-artifact@v4",
    "        with:",
    "          name: " + slug + "-android",
    "          path: out/*.apk",
    "      - uses: softprops/action-gh-release@v2",
    "        with:",
    "          tag_name: " + slug + "-latest",
    "          prerelease: true",
    "          files: out/*.apk"
  ]);
  if (want.indexOf("exe") >= 0) wf = wf.concat([
    "  windows-exe:",
    "    runs-on: windows-latest",
    "    steps:",
    "      - uses: actions/checkout@v4",
    "      - uses: actions/setup-node@v4",
    "        with:",
    "          node-version: 20",
    "      - name: Build Windows EXE (Electron)",
    "        working-directory: apps/" + slug + "/electron",
    "        run: |",
    "          npm install",
    "          npm run dist",
    "        env:",
    "          GH_TOKEN: " + E + "secrets.GITHUB_TOKEN }}",
    "      - uses: actions/upload-artifact@v4",
    "        with:",
    "          name: " + slug + "-windows",
    "          path: apps/" + slug + "/electron/dist/*.exe",
    "      - uses: softprops/action-gh-release@v2",
    "        with:",
    "          tag_name: " + slug + "-latest",
    "          prerelease: true",
    "          files: apps/" + slug + "/electron/dist/*.exe"
  ]);
  files.push({ path: ".github/workflows/" + slug + "-build.yml", content: wf.join("\n") + "\n" });
  return files;
}

/* 生成ファイル (プロジェクト相対) をリポジトリ配置へまとめる */
function assembleProject(o, generated) {
  var root = "apps/" + o.slug + "/";
  var out = [], seen = {};
  function add(path, content) { if (!seen[path]) { seen[path] = 1; out.push({ path: path, data: content }); } }
  if (TARGETS[o.target] && TARGETS[o.target].packaging) {
    scaffoldPackaging(o).forEach(function (f) { add(f.path, f.content); });
    var hasIndex = generated.some(function (f) { return f.path === "www/index.html"; });
    if (!hasIndex) {
      /* 生成側が別名で HTML を返したら www/index.html として使う */
      var anyHtml = generated.filter(function (f) { return /\.html?$/i.test(f.path); })[0];
      if (anyHtml) add(root + "www/index.html", anyHtml.content);
    }
  }
  generated.forEach(function (f) {
    /* パッケージ設定は雛形を優先 (生成側の上書きで壊さない) */
    if (TARGETS[o.target] && TARGETS[o.target].packaging && /^(cordova|electron)\//.test(f.path)) return;
    add(root + f.path, f.data !== undefined ? f.data : f.content);
  });
  return out;
}

/* ───────────── バイオフィードバック ───────────── */

function movingAverage(xs, w) {
  var out = new Array(xs.length), s = 0, q = [];
  for (var i = 0; i < xs.length; i++) {
    q.push(xs[i]); s += xs[i];
    if (q.length > w) s -= q.shift();
    out[i] = s / q.length;
  }
  return out;
}

function median(xs) {
  if (!xs.length) return NaN;
  var a = xs.slice().sort(function (p, q) { return p - q; }), m = a.length >> 1;
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

/* samples: [{t: 秒, v: 輝度}] (指先をカメラに当てた PPG) → { bpm, rmssd, peaks } */
function ppgAnalyze(samples) {
  if (samples.length < 30) return { bpm: NaN, rmssd: NaN, peaks: [] };
  var dur = samples[samples.length - 1].t - samples[0].t;
  if (dur < 4) return { bpm: NaN, rmssd: NaN, peaks: [] };
  var fs = (samples.length - 1) / dur;
  /* 血液は光を吸収するので輝度を反転し、ゆっくりした変動を除いて平滑化 */
  var v = samples.map(function (s) { return -s.v; });
  var base = movingAverage(v, Math.max(3, Math.round(fs * 1.0)));
  var d = v.map(function (x, i) { return x - base[i]; });
  var sm = movingAverage(d, Math.max(1, Math.round(fs * 0.12)));
  var sd = Math.sqrt(sm.reduce(function (a, x) { return a + x * x; }, 0) / sm.length) || 1;
  var minGap = 0.33, peaks = [];
  for (var i = 2; i < sm.length - 2; i++) {
    if (sm[i] > 0.3 * sd && sm[i] >= sm[i - 1] && sm[i] >= sm[i - 2] && sm[i] > sm[i + 1] && sm[i] >= sm[i + 2]) {
      var t = samples[i].t;
      if (peaks.length && t - peaks[peaks.length - 1].t < minGap) {
        if (sm[i] > peaks[peaks.length - 1].a) peaks[peaks.length - 1] = { t: t, a: sm[i] };
      } else peaks.push({ t: t, a: sm[i] });
    }
  }
  var ibis = [];
  for (var k = 1; k < peaks.length; k++) {
    var ibi = peaks[k].t - peaks[k - 1].t;
    if (ibi >= 0.33 && ibi <= 1.5) ibis.push(ibi);
  }
  if (ibis.length < 3) return { bpm: NaN, rmssd: NaN, peaks: peaks };
  var med = median(ibis);
  /* 中央値から大きく外れた拍間隔 (誤検出) を除外 */
  var good = ibis.filter(function (x) { return Math.abs(x - med) < 0.25 * med; });
  /* 平均を使う (中央値だとフレーム周期 1/30 秒に量子化された値に張り付く) */
  var bpm = 60 / (good.reduce(function (a, x) { return a + x; }, 0) / good.length);
  var diffs = [];
  for (var j = 1; j < good.length; j++) diffs.push(Math.pow((good[j] - good[j - 1]) * 1000, 2));
  var rmssd = diffs.length ? Math.sqrt(diffs.reduce(function (a, x) { return a + x; }, 0) / diffs.length) : NaN;
  return { bpm: bpm, rmssd: rmssd, peaks: peaks };
}

/* samples: [{t: 秒, v: マイク音量 (RMS)}] → 呼吸数 (回/分)。
 * 包絡を 0.6 秒で平滑化し 8 秒の基線を引いて、ヒステリシス付きの上向き交差を数える。 */
function breathAnalyze(samples) {
  if (samples.length < 30) return NaN;
  var dur = samples[samples.length - 1].t - samples[0].t;
  if (dur < 12) return NaN;
  var fs = (samples.length - 1) / dur;
  var v = movingAverage(samples.map(function (s) { return s.v; }), Math.max(1, Math.round(fs * 0.6)));
  var base = movingAverage(v, Math.max(3, Math.round(fs * 8)));
  var d = v.map(function (x, i) { return x - base[i]; });
  var sd = Math.sqrt(d.reduce(function (a, x) { return a + x * x; }, 0) / d.length);
  if (!(sd > 1e-6)) return NaN;
  var hi = 0.3 * sd, lo = -0.3 * sd, state = d[0] > 0 ? 1 : -1, ups = [];
  for (var i = 1; i < d.length; i++) {
    if (state < 0 && d[i] > hi) { state = 1; ups.push(samples[i].t); }
    else if (state > 0 && d[i] < lo) state = -1;
  }
  if (ups.length < 2) return NaN;
  var span = ups[ups.length - 1] - ups[0];
  var rate = (ups.length - 1) / span * 60;
  return rate >= 2 && rate <= 40 ? rate : NaN;
}

function clamp01(x) { return Math.max(0, Math.min(1, x)); }

/* 落ち着き指数 0..100: 心拍変動 (RMSSD) が大きく、呼吸が毎分 6 回 (共鳴呼吸) に近いほど高い */
function calmIndex(rmssd, breath) {
  var parts = [];
  if (isFinite(rmssd)) parts.push(clamp01(rmssd / 80));
  if (isFinite(breath)) parts.push(clamp01(1 - Math.abs(breath - 6) / 12));
  if (!parts.length) return NaN;
  return 100 * parts.reduce(function (a, x) { return a + x; }, 0) / parts.length;
}

/* ───────────── 複素ガンマ関数 ───────────── */

var LANCZOS = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
  -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];

function cmul(a, b) { return [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]]; }
function cdiv(a, b) { var d = b[0] * b[0] + b[1] * b[1]; return [(a[0] * b[0] + a[1] * b[1]) / d, (a[1] * b[0] - a[0] * b[1]) / d]; }
function cexp(a) { var e = Math.exp(a[0]); return [e * Math.cos(a[1]), e * Math.sin(a[1])]; }
function clog(a) { return [Math.log(Math.hypot(a[0], a[1])), Math.atan2(a[1], a[0])]; }
function cpow(a, b) { return cexp(cmul(b, clog(a))); }
function csin(a) { return [Math.sin(a[0]) * Math.cosh(a[1]), Math.cos(a[0]) * Math.sinh(a[1])]; }

/* Γ(z) — Lanczos (g=7) と相反公式 Γ(z)Γ(1−z) = π / sin(πz) */
function gammaC(re, im) {
  if (re < 0.5) {
    var s = csin([Math.PI * re, Math.PI * im]);
    var g1 = gammaC(1 - re, -im);
    return cdiv([Math.PI, 0], cmul(s, g1));
  }
  var z = [re - 1, im], x = [LANCZOS[0], 0];
  for (var i = 1; i < 9; i++) x = addC(x, cdiv([LANCZOS[i], 0], [z[0] + i, z[1]]));
  var t = [z[0] + 7.5, z[1]];
  var r = cmul(cmul([Math.sqrt(2 * Math.PI), 0], cpow(t, [z[0] + 0.5, z[1]])), cexp([-t[0], -t[1]]));
  return cmul(r, x);
}
function addC(a, b) { return [a[0] + b[0], a[1] + b[1]]; }

/* 実数 Γ(x) (検証用) */
function gammaR(x) { return gammaC(x, 0)[0]; }

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    KAI_VERSION: KAI_VERSION, utf8: utf8, crc32: crc32, zipBuild: zipBuild, pdfFromJpegs: pdfFromJpegs,
    bytesToBase64: bytesToBase64, base64ToBytes: base64ToBytes,
    mdBlocks: mdBlocks, mdToHtml: mdToHtml, stripInline: stripInline, escapeHtml: escapeHtml,
    slugify: slugify, safePath: safePath, parseFiles: parseFiles, TARGETS: TARGETS, MODELS: MODELS,
    buildSystemPrompt: buildSystemPrompt, buildUserContent: buildUserContent, bioSummary: bioSummary,
    claudeRequest: claudeRequest, sseNew: sseNew, sseFeed: sseFeed,
    localGenerateApp: localGenerateApp, localGenerateDoc: localGenerateDoc,
    scaffoldPackaging: scaffoldPackaging, assembleProject: assembleProject,
    ppgAnalyze: ppgAnalyze, breathAnalyze: breathAnalyze, calmIndex: calmIndex,
    gammaC: gammaC, gammaR: gammaR
  };
}
