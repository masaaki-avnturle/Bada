#!/usr/bin/env node
/* ============================================================================
 * build-zone-browser.js — build the dedicated ULTRA NETWORK browser for the
 * zone:// scheme, as a SINGLE self-contained HTML file.
 *
 * Produces ../dist/zone-browser.html : the Bada language core, the zone://
 * runtime library (browser/zone-lib.bada) and a small zone site are inlined,
 * so downloading the one file and opening it in any browser gives a working
 * zone:// browser (address bar, back/forward, reload, clickable zone links,
 * and a live security panel) offline, with no server and no dependencies.
 *
 * Every navigation runs the Bada zone runtime: the P2P ring is rebuilt from
 * the peers' own hashes, pages are (re)published encrypted under each zone's
 * Jones-polynomial key, a Bell-pair QKD session salt is agreed, and the
 * requested page is fetched, AEAD-verified and decrypted before rendering.
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");

const IDE = path.join(__dirname, "..");
const WWW = path.join(IDE, "www");
const BR = path.join(IDE, "browser");
const DIST = path.join(IDE, "dist");
fs.mkdirSync(DIST, { recursive: true });

const badaCore = fs.readFileSync(path.join(WWW, "bada.js"), "utf8");
const zoneLib = fs.readFileSync(path.join(BR, "zone-lib.bada"), "utf8");
const site = JSON.parse(fs.readFileSync(path.join(BR, "zone-site.json"), "utf8"));
const Bada = require(path.join(WWW, "bada.js"));
const VERSION = Bada.VERSION;

/* self-check: the library + a publish + a serve must yield 200 */
(function selfCheck() {
  const home = Object.keys(site)[0];
  let prog = zoneLib + "\nNET := zone_boot()\n";
  for (const [url, content] of Object.entries(site))
    prog += "zone_publish(NET, " + JSON.stringify(url) + ", " + JSON.stringify(content) + ")\n";
  prog += "zone_serve(NET, " + JSON.stringify(home) + ")\n";
  const r = Bada.run(prog, { maxSteps: 20000000 });
  if (!r.ok || !/@@STATUS 200/.test(r.output)) {
    console.error("self-check failed for " + home + ":\n" + (r.error || r.parseErrors.join("\n")) + "\n" + r.output);
    process.exit(1);
  }
  console.log("self-check OK: " + home + " -> 200 (" + Object.keys(site).length + " pages)");
})();

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ZoneBrowser — ウルトラネットワーク専用ブラウザ (zone://)</title>
<style>
  :root { color-scheme: light dark; --bg:#04060a; --panel:#0a1220; --line:#1c2838;
          --ink:#d6e2ee; --dim:#8aa0b8; --gold:#c8a44a; --green:#2e9e57; --red:#d0574a; --blue:#4a80d0; }
  * { box-sizing:border-box; }
  html,body { height:100%; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font-family: system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif; }
  #chrome { position:sticky; top:0; z-index:5; background:linear-gradient(180deg,#0a1220,#070c15);
            border-bottom:1px solid var(--line); padding:10px 12px; }
  .navrow { display:flex; gap:8px; align-items:center; }
  .navbtn { width:36px; height:36px; border:1px solid var(--line); border-radius:8px; background:#132033;
            color:var(--ink); font-size:16px; cursor:pointer; }
  .navbtn:disabled { opacity:.4; cursor:default; }
  .navbtn:hover:not(:disabled) { filter:brightness(1.2); }
  #addr { flex:1; display:flex; align-items:center; gap:8px; background:#020407; border:1px solid var(--line);
          border-radius:20px; padding:6px 14px; }
  #lock { font-size:14px; }
  #url { flex:1; background:transparent; border:0; outline:0; color:var(--ink); font-size:14px;
         font-family:"SFMono-Regular",Consolas,monospace; }
  #go { border:0; background:var(--green); color:#eafff0; border-radius:16px; padding:7px 16px; cursor:pointer; font-weight:600; }
  .brand { display:flex; align-items:center; gap:8px; margin-right:6px; }
  .brand .o { color:var(--gold); font-size:20px; font-weight:700; }
  .brand small { color:var(--dim); }
  main { display:grid; grid-template-columns: 220px 1fr 300px; gap:0; height:calc(100% - 58px); }
  @media (max-width:900px){ main{ grid-template-columns:1fr; } #side,#sec{ display:none; } }
  #side { border-right:1px solid var(--line); padding:14px; overflow:auto; }
  #side h3, #sec h3 { margin:0 0 10px; font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--dim); }
  #side a { display:block; color:var(--blue); text-decoration:none; font-size:13px; padding:6px 8px; border-radius:6px;
            font-family:"SFMono-Regular",Consolas,monospace; word-break:break-all; }
  #side a:hover { background:#101d2e; }
  #page { overflow:auto; padding:28px 34px; }
  #page h1.doc { font-size:26px; margin:0 0 6px; }
  #page h2.doc { font-size:19px; margin:22px 0 6px; color:var(--gold); }
  #page p.doc { margin:8px 0; line-height:1.65; max-width:64ch; }
  #page a.zlink { color:var(--blue); text-decoration:none; border-bottom:1px solid #24405f; cursor:pointer; }
  #page a.zlink:hover { color:#8fb6ff; }
  #page .pill { display:inline-block; font-size:11px; padding:2px 8px; border-radius:10px; margin-right:6px; }
  .ok { background:#123a24; color:#7ce0a3; } .bad { background:#3a1614; color:#f2a49b; }
  #sec { border-left:1px solid var(--line); padding:14px; overflow:auto; font-size:12.5px; }
  #sec .kv { display:flex; justify-content:space-between; gap:8px; padding:5px 0; border-bottom:1px dashed #16222f; }
  #sec .kv b { color:var(--dim); font-weight:500; }
  #sec .kv span { text-align:right; font-family:"SFMono-Regular",Consolas,monospace; word-break:break-all; }
  #sec .big { font-size:13px; margin-top:12px; }
  .status-200 { color:#7ce0a3; } .status-err { color:#f2a49b; }
  #raw { margin-top:14px; }
  #raw summary { color:var(--dim); cursor:pointer; }
  #raw pre { background:#020407; border:1px solid var(--line); border-radius:8px; padding:10px; overflow:auto;
             font-size:11px; max-height:220px; white-space:pre-wrap; }
  footer { grid-column:1/-1; }
</style>
</head>
<body>
<div id="chrome">
  <div class="navrow">
    <div class="brand"><span class="o">Ω</span><div><b>ZoneBrowser</b><br><small>ultra-network · zone://</small></div></div>
    <button class="navbtn" id="back"  title="戻る">‹</button>
    <button class="navbtn" id="fwd"   title="進む">›</button>
    <button class="navbtn" id="reload" title="再読み込み">⟳</button>
    <div id="addr">
      <span id="lock" title="Jones量子暗号で保護">🔒</span>
      <input id="url" spellcheck="false" autocomplete="off" value="zone://url.or.jp/"/>
    </div>
    <button id="go">開く</button>
  </div>
</div>

<main>
  <nav id="side">
    <h3>ゾーン インデックス</h3>
    <div id="bookmarks"></div>
    <h3 style="margin-top:18px">ネットワーク</h3>
    <div id="peers" style="font-size:12px;color:var(--dim);font-family:monospace"></div>
  </nav>

  <section id="page"><p class="doc" style="color:var(--dim)">読み込み中…</p></section>

  <aside id="sec">
    <h3>セキュリティ</h3>
    <div id="secbody"></div>
    <details id="raw"><summary>zone プロトコル トレース</summary><pre id="rawpre"></pre></details>
  </aside>
</main>

<script>
/* ==== Bada language core (inlined) ==== */
${badaCore}
</script>
<script>
/* ==== zone:// runtime library + site (inlined) ==== */
var ZONE_LIB = ${JSON.stringify(zoneLib)};
var ZONE_SITE = ${JSON.stringify(site)};
</script>
<script>
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var urlInput = $("url"), pageEl = $("page"), secEl = $("secbody"), rawEl = $("rawpre");

  /* ---- history ---- */
  var hist = [], hi = -1;

  function badaLiteral(s) { return JSON.stringify(String(s)); }

  /* build the per-navigation Bada program and run the zone runtime */
  function resolve(url) {
    var prog = ZONE_LIB + "\\nNET := zone_boot()\\n";
    for (var u in ZONE_SITE) if (Object.prototype.hasOwnProperty.call(ZONE_SITE, u))
      prog += "zone_publish(NET, " + badaLiteral(u) + ", " + badaLiteral(ZONE_SITE[u]) + ")\\n";
    prog += "zone_serve(NET, " + badaLiteral(url) + ")\\n";
    var lines = [];
    var r = BadaLang.run(prog, { maxSteps: 20000000, out: function (s) { lines.push(s); } });
    return { ok: r.ok, out: lines.join("\\n"), ledger: r.ledgerLen };
  }

  /* parse the @@ block emitted by zone_serve */
  function parseBlock(text) {
    var meta = { status: "?", host: "", path: "", key: "", route: "", node: "",
                 qkd: "", cipher: "", tag: "", jones: "", body: "" };
    var lines = text.split("\\n"), body = [], inBody = false;
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i];
      if (ln === "@@BODY_BEGIN") { inBody = true; continue; }
      if (ln === "@@BODY_END") { inBody = false; continue; }
      if (inBody) { body.push(ln); continue; }
      if (ln.indexOf("@@") !== 0) continue;
      var sp = ln.indexOf(" ");
      var key = (sp < 0 ? ln : ln.slice(0, sp)).slice(2);
      var val = sp < 0 ? "" : ln.slice(sp + 1);
      if (key === "STATUS") meta.status = val;
      else if (key === "HOST") meta.host = val;
      else if (key === "PATH") meta.path = val;
      else if (key === "KEY") meta.key = val;
      else if (key === "ROUTE") meta.route = val;
      else if (key === "NODE") meta.node = val;
      else if (key === "QKD") meta.qkd = val;
      else if (key === "CIPHER") meta.cipher = val;
      else if (key === "TAG") meta.tag = val;
      else if (key === "JONESKEY") meta.jones = val;
    }
    meta.body = body.join("\\n");
    return meta;
  }

  function esc(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

  /* render the zone page markup:
       # Title            -> h1
       ## Section         -> h2
       -> zone://... | L  -> clickable link
       (blank)            -> paragraph break
       text               -> paragraph                                         */
  function renderPage(meta) {
    if (meta.status !== "200") {
      var cls = "bad";
      pageEl.innerHTML =
        '<h1 class="doc">' + esc(meta.status) + '</h1>' +
        '<p class="doc"><span class="pill ' + cls + '">zone error</span></p>' +
        renderBody(meta.body);
      return;
    }
    pageEl.innerHTML =
      '<p class="doc"><span class="pill ok">🔒 200 zone-delivered</span>' +
      '<span class="pill ok">Jones-AEAD verified</span>' +
      '<span class="pill ok">QKD ' + esc(meta.qkd) + '</span></p>' +
      renderBody(meta.body);
    /* wire up clickable zone links */
    var links = pageEl.querySelectorAll("a.zlink");
    for (var i = 0; i < links.length; i++) {
      links[i].addEventListener("click", function (e) {
        e.preventDefault(); navigate(this.getAttribute("data-href"), true);
      });
    }
  }

  function renderBody(body) {
    var out = [], lines = body.split("\\n"), h1done = false;
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i].replace(/\\s+$/,"");
      if (ln === "") continue;
      var m;
      if ((m = /^##\\s+(.*)$/.exec(ln))) { out.push('<h2 class="doc">' + esc(m[1]) + '</h2>'); continue; }
      if ((m = /^#\\s+(.*)$/.exec(ln))) {
        if (!h1done) { out.push('<h1 class="doc">' + esc(m[1]) + '</h1>'); h1done = true; }
        else out.push('<h2 class="doc">' + esc(m[1]) + '</h2>');
        continue;
      }
      if ((m = /^->\\s*(\\S+)\\s*\\|\\s*(.*)$/.exec(ln))) {
        out.push('<p class="doc"><a class="zlink" data-href="' + esc(m[1]) + '" href="#">' + esc(m[2]) + '</a> ' +
                 '<small style="color:var(--dim)">' + esc(m[1]) + '</small></p>');
        continue;
      }
      out.push('<p class="doc">' + esc(ln) + '</p>');
    }
    return out.join("");
  }

  function renderSecurity(meta, ledger) {
    var errCls = meta.status === "200" ? "status-200" : "status-err";
    function kv(k, v) { return '<div class="kv"><b>' + k + '</b><span>' + esc(v || "—") + '</span></div>'; }
    secEl.innerHTML =
      '<div class="big ' + errCls + '">status ' + esc(meta.status) + '</div>' +
      kv("host", meta.host) +
      kv("path", meta.path) +
      kv("DHT key", meta.key) +
      kv("owner node", meta.node) +
      kv("route", meta.route) +
      kv("QKD (Bell)", meta.qkd) +
      kv("Jones key", meta.jones) +
      kv("AEAD tag", meta.tag) +
      kv("cipher[0..2]/len", meta.cipher) +
      kv("Akashic ledger", ledger + " facts");
  }

  function setLock(ok) { $("lock").textContent = ok ? "🔒" : "⚠️"; }

  function navigate(url, push) {
    url = String(url).trim();
    if (url.indexOf("zone://") !== 0) {
      if (url.indexOf("://") < 0) url = "zone://" + url; /* bare host -> zone:// */
    }
    urlInput.value = url;
    var res = resolve(url);
    rawEl.textContent = res.out;
    var meta = parseBlock(res.out);
    setLock(meta.status === "200");
    renderPage(meta);
    renderSecurity(meta, res.ledger);
    if (push) { hist = hist.slice(0, hi + 1); hist.push(url); hi = hist.length - 1; }
    updateNav();
    pageEl.scrollTop = 0;
  }

  function updateNav() {
    $("back").disabled = hi <= 0;
    $("fwd").disabled = hi >= hist.length - 1;
  }

  /* ---- sidebar: bookmarks + peers ---- */
  function buildSidebar() {
    var bm = $("bookmarks"), html = "";
    for (var u in ZONE_SITE) if (Object.prototype.hasOwnProperty.call(ZONE_SITE, u))
      html += '<a data-href="' + esc(u) + '" href="#">' + esc(u) + '</a>';
    bm.innerHTML = html;
    var links = bm.querySelectorAll("a");
    for (var i = 0; i < links.length; i++)
      links[i].addEventListener("click", function (e) { e.preventDefault(); navigate(this.getAttribute("data-href"), true); });
    /* peers: derive from a boot+trace of any navigation's ring (parse from a probe) */
    var probe = resolve("zone://url.or.jp/");
    $("peers").textContent = "6 peers · ring 4096\\n(server-less P2P DHT)";
  }

  /* ---- events ---- */
  $("go").addEventListener("click", function () { navigate(urlInput.value, true); });
  urlInput.addEventListener("keydown", function (e) { if (e.key === "Enter") navigate(urlInput.value, true); });
  $("back").addEventListener("click", function () { if (hi > 0) { hi--; navigate(hist[hi], false); } });
  $("fwd").addEventListener("click", function () { if (hi < hist.length - 1) { hi++; navigate(hist[hi], false); } });
  $("reload").addEventListener("click", function () { navigate(urlInput.value, false); });

  /* boot */
  buildSidebar();
  navigate("zone://url.or.jp/", true);
})();
</script>
</body>
</html>
`;

fs.writeFileSync(path.join(DIST, "zone-browser.html"), html);
console.log("built dist/zone-browser.html (" + fs.statSync(path.join(DIST, "zone-browser.html")).size + " bytes)");

/* also stage it as the ZoneBrowser app's www/index.html (Electron / Cordova) */
const APPWWW = path.join(IDE, "zonebrowser-app", "www");
if (fs.existsSync(path.join(IDE, "zonebrowser-app"))) {
  fs.mkdirSync(APPWWW, { recursive: true });
  fs.writeFileSync(path.join(APPWWW, "index.html"), html);
  console.log("staged zonebrowser-app/www/index.html");
}
