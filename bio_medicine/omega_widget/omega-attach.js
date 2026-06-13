/*
 * omega-attach.js — 任意のWebアプリに「貼るだけ」で付加する未知事前エンジン・ウィジェット
 * Masaaki Yamaguchi / Bada — bio_medicine/omega_widget
 *
 * 読み込むだけで:
 *   ・window.omegaApriori (エンジン+プラグイン) を生成
 *   ・フローティング Ω ボタン+パネル(機能起動)を注入
 *   ・ページ内の input[type=text]/textarea に「単語補完」を自動付加 (Tabで採用)
 * を行う、依存なし・単一ファイルの完成ウィジェット。
 *
 * 付加方法(いずれも可):
 *   <script src="omega-attach.js"></script>
 *   userscript / DevToolsコンソールに貼付 / bookmarklet からロード
 *
 * ⚠ 概念実証・教育用／非医療。付加は自分が管理/許諾されたアプリに対してのみ。
 */
(function () {
  "use strict";
  if (window.__omegaAttached) { console.log("Ω already attached"); return; }
  window.__omegaAttached = true;

  /* ========== 未知事前エンジン (LUTファブリック, popcount genome) ========== */
  var CFG = { inbits: 6, layers: 3, width: 8, outbits: 3 }, CB = 6;
  var GENOME = "a3b77311438a66c00cbbae927e1ca5ea6061348e00fe47f075f2e1bdd444c082000a5287d5b76843d76f21afcfb2af3b6d7c5e325c8600ad63b36df86724dc9f950461b3cd15bf114b60be96a3f7704aa105b5d3e85ba2c72d74c845e3c01e47d0a79a8659a44375b56919af8b4d545bf54243c677820cbce313b79716de80e68ddb055c7804e4294017664276afb05e";
  function h2b(h) { var n = h.length >> 1, b = new Uint8Array(n); for (var i = 0; i < n; i++) b[i] = parseInt(h.substr(i * 2, 2), 16); return b; }
  function b2h(b) { return Array.prototype.map.call(b, function (x) { return x.toString(16).padStart(2, "0"); }).join(""); }
  function fnv(s) { var h = 2166136261 >>> 0; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function evalFab(g, x) {
    var prev = x & ((1 << CFG.inbits) - 1), src = CFG.inbits, cur = 0;
    for (var L = 0; L < CFG.layers; L++) { cur = 0;
      for (var w = 0; w < CFG.width; w++) { var cell = L * CFG.width + w, p = cell * CB, addr = 0;
        for (var k = 0; k < 4; k++) { var sel = g[p + k] % Math.max(1, (L === 0 ? CFG.inbits : CFG.width)); if (sel >= src) sel = src ? sel % src : 0; addr |= ((prev >> sel) & 1) << k; }
        cur |= (((g[p + 4] | (g[p + 5] << 8)) >> addr) & 1) << w; }
      prev = cur; src = CFG.width; }
    return cur & ((1 << CFG.outbits) - 1);
  }

  var ENG = {
    cfg: CFG, meta: { genome_hex: GENOME }, _g: h2b(GENOME), plugins: {}, _telomere: 1000, _hayflick: 200,
    infer: function (x) { return evalFab(this._g, x); },
    register: function (p) { this.plugins[p.name] = p; return this; },
    call: function (n) { var p = this.plugins[n]; if (!p) throw new Error("no plugin " + n); return p.run.apply(p, [this].concat([].slice.call(arguments, 1))); },
    capabilities: function () { return Object.keys(this.plugins); }
  };

  /* ========== プラグイン群 ========== */
  var DEFAULT_VOCAB = ["function","return","const","let","var","class","import","export","async","await",
    "value","vector","matrix","manifold","gamma","integral","telomere","evolution","engine","apriori",
    "pattern","complete","completion","overview","quantum","fabric","genome","verilog","application",
    "attach","plugin","signature","source","module","compute","calculate","generate","analyze","network",
    "neural","learning","model","the","this","that","with","word","words","prefix","please","project","problem"];
  ENG.register({ name: "word_complete", run: function (e, prefix, opt) {
    opt = opt || {}; var p = String(prefix || "").toLowerCase();
    var vocab = opt.vocab && opt.vocab.length ? opt.vocab : DEFAULT_VOCAB, k = opt.k || 8, freq = opt.freq || {}, ctx = (opt.context || "").toLowerCase();
    var im = (1 << e.cfg.inbits) - 1, om = (1 << e.cfg.outbits) - 1, seen = {}, c = [];
    for (var i = 0; i < vocab.length; i++) { var w = vocab[i]; if (typeof w !== "string") continue; var wl = w.toLowerCase();
      if (p && wl.indexOf(p) !== 0) continue; if (wl === p) continue; if (seen[wl]) continue; seen[wl] = 1;
      var cover = p.length ? p.length / wl.length : 0.1, fr = freq[w] || freq[wl] || 0, bias = (e.infer(fnv(ctx + ">" + wl) & im) & om) / (om || 1);
      c.push({ word: w, score: cover * 2 + Math.log(1 + fr) + bias * 0.8 }); }
    c.sort(function (a, b) { return b.score - a.score; }); return c.slice(0, k);
  }});
  ENG.register({ name: "completion", run: function (e, seq, k) { k = k || 6; var im = (1 << e.cfg.inbits) - 1, om = (1 << e.cfg.outbits) - 1;
    var codes = typeof seq === "string" ? Array.prototype.map.call(seq, function (c) { return c.charCodeAt(0); }) : seq.slice(), out = [];
    for (var s = 0; s < k; s++) { var n = codes.length, ctx = ((codes[n - 1] || 0) ^ ((codes[n - 2] || 0) << 1)) & im, pred = e.infer(ctx) & om;
      var nx = ((codes[n - 1] || 0) + pred + 1) & 0x7f; if (nx < 32) nx = 32 + (nx % 95); codes.push(nx); out.push(String.fromCharCode(nx)); }
    return { predicted: out.join("") }; }});
  ENG.register({ name: "overview", run: function (e, text) {
    var freq = {}, words = (String(text).toLowerCase().match(/[a-z]+/g) || []); for (var i = 0; i < words.length; i++) if (words[i].length >= 2) freq[words[i]] = (freq[words[i]] || 0) + 1;
    var top = Object.keys(freq).sort(function (a, b) { return freq[b] - freq[a]; }).slice(0, 8);
    return { words: words.length, unique: Object.keys(freq).length, top: top.map(function (w) { return w + "(" + freq[w] + ")"; }) }; }});
  ENG.register({ name: "patternmatch", run: function (e, mode, arg) { if (Array.isArray(arg)) return arg.map(function (x) { return e.infer(x); }); return e.infer((arg | 0) & 63); }});
  ENG.register({ name: "self_evolve", run: function (e, mode, arg) { mode = mode || "uid";
    if (mode === "uid") return "OAE-" + fnv(b2h(e._g)).toString(36).toUpperCase().padStart(7, "0") + "-" + fnv(b2h(e._g) + JSON.stringify(e.cfg) + "Ω").toString(36).toUpperCase().padStart(7, "0");
    if (mode === "step") { var tf = function (x) { var c = 0; for (var i = 0; i < 6; i++) c += (x >> i) & 1; return c; };
      function fit(g) { var m = 0, t = 0; for (var x = 0; x < 64; x++) { var d = evalFab(g, x) ^ (tf(x) & 7); for (var b = 0; b < 3; b++) { t++; if (!((d >> b) & 1)) m++; } } return m / t; }
      var g = e._g.slice(), bf = fit(g); for (var gen = 0; gen < (arg && arg.gens || 15) && e._telomere > e._hayflick; gen++) { var c = g.slice(); for (var i = 0; i < c.length; i++) if (Math.random() < 0.04) c[i] = Math.random() * 256 | 0; var f = fit(c); if (f >= bf) { bf = f; g = c; } e._telomere -= 30; }
      e._g = g; e.meta.genome_hex = b2h(g); return { fitness: bf, uid: e.call("self_evolve", "uid"), telomere: e._telomere }; }
    return "?"; }});
  ENG.register({ name: "codegen", run: function (e, target) { var by = e._g, cfg = e.cfg, idx = 0, prev = "din", s = ["module omega_apriori (input [" + (cfg.inbits - 1) + ":0] din, output [" + (cfg.outbits - 1) + ":0] dout);"];
    for (var L = 0; L < cfg.layers; L++) { var wn = "s" + L; s.push("  wire [" + (cfg.width - 1) + ":0] " + wn + ";"); var src = L === 0 ? cfg.inbits : cfg.width;
      for (var w = 0; w < cfg.width; w++) { var p = idx * CB, sel = []; for (var k = 0; k < 4; k++) sel.push(by[p + k] % Math.max(1, src));
        var lut = ((by[p + 4] | (by[p + 5] << 8)) & 0xFFFF).toString(16).toUpperCase().padStart(4, "0");
        s.push("  localparam [15:0] LUT_" + L + "_" + w + " = 16'h" + lut + ";");
        s.push("  assign " + wn + "[" + w + "] = LUT_" + L + "_" + w + "[{" + prev + "[" + sel[3] + "]," + prev + "[" + sel[2] + "]," + prev + "[" + sel[1] + "]," + prev + "[" + sel[0] + "}];"); idx++; }
      prev = wn; }
    s.push("  assign dout = " + prev + "[" + (cfg.outbits - 1) + ":0];"); s.push("endmodule"); return s.join("\n"); }});

  window.omegaApriori = ENG;

  /* ========== UI 注入 ========== */
  var css = ".oa-btn{position:fixed;right:18px;bottom:18px;width:46px;height:46px;border-radius:50%;background:#0d1320;color:#c8a44a;border:2px solid #c8a44a;font:700 20px monospace;cursor:pointer;z-index:2147483600;box-shadow:0 4px 14px #000a}" +
    ".oa-btn:hover{background:#1f2f4a}" +
    ".oa-panel{position:fixed;right:18px;bottom:74px;width:300px;max-height:70vh;overflow:auto;background:#0a0e16;color:#d8e0ec;border:1px solid #c8a44a;border-radius:10px;padding:12px;z-index:2147483600;font:13px -apple-system,Meiryo,sans-serif;box-shadow:0 6px 24px #000c;display:none}" +
    ".oa-panel.on{display:block}.oa-panel h4{margin:0 0 8px;color:#c8a44a;font-size:14px}" +
    ".oa-panel button{background:#0d1320;color:#40b8c0;border:1px solid #1b2638;border-radius:6px;padding:6px 9px;margin:3px 3px 0 0;cursor:pointer;font-size:12px}" +
    ".oa-panel button:hover{border-color:#40b8c0}.oa-row{display:flex;align-items:center;gap:6px;margin:6px 0;font-size:12px;color:#8794a8}" +
    ".oa-out{background:#06090f;border:1px solid #1b2638;border-radius:6px;padding:8px;margin-top:8px;font:11px monospace;color:#40b8c0;white-space:pre-wrap;max-height:160px;overflow:auto}" +
    ".oa-sugg{position:absolute;background:#0a0e16;border:1px solid #c8a44a;border-radius:6px;z-index:2147483640;font:13px monospace;box-shadow:0 4px 14px #000a;max-width:280px}" +
    ".oa-sugg div{padding:4px 10px;cursor:pointer;color:#d8e0ec}.oa-sugg div.sel,.oa-sugg div:hover{background:#1f2f4a;color:#c8a44a}" +
    ".oa-sugg b{color:#c8a44a}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  var btn = document.createElement("button"); btn.className = "oa-btn"; btn.textContent = "Ω"; btn.title = "Ω-Apriori 付加機能";
  var panel = document.createElement("div"); panel.className = "oa-panel";
  panel.innerHTML = '<h4>Ω-Apriori 付加機能</h4>' +
    '<div class="oa-row"><label><input type="checkbox" id="oa-wc" checked> 入力欄に単語補完(Tab採用)</label></div>' +
    '<div><button data-a="overview">俯瞰</button><button data-a="completion">系列補完</button>' +
    '<button data-a="uid">一意ID</button><button data-a="evolve">自己進化</button>' +
    '<button data-a="codegen">FPGAソース</button><button data-a="caps">機能一覧</button></div>' +
    '<div class="oa-out" id="oa-out">window.omegaApriori で全機能利用可</div>';
  document.body.appendChild(btn); document.body.appendChild(panel);
  btn.onclick = function () { panel.classList.toggle("on"); };
  var out = panel.querySelector("#oa-out");
  function lastField() { var el = document.activeElement; if (el && (el.tagName === "TEXTAREA" || (el.tagName === "INPUT"))) return el; return OA_LAST; }
  panel.querySelectorAll("button[data-a]").forEach(function (b) { b.onclick = function () {
    var a = b.dataset.a, fld = lastField(), txt = fld ? (fld.value || "") : (document.body.innerText || "").slice(0, 4000);
    try {
      if (a === "overview") { var r = ENG.call("overview", txt); out.textContent = "俯瞰: 語数=" + r.words + " 異なり=" + r.unique + "\n頻出: " + r.top.join(", "); }
      else if (a === "completion") { out.textContent = "系列補完: +\"" + ENG.call("completion", txt.slice(-12) || "the", 8).predicted + "\""; }
      else if (a === "uid") { out.textContent = "一意ID(UID): " + ENG.call("self_evolve", "uid"); }
      else if (a === "evolve") { var e = ENG.call("self_evolve", "step", { gens: 15 }); out.textContent = "自己進化: fit=" + e.fitness.toFixed(4) + " telo=" + e.telomere + "\nUID=" + e.uid; }
      else if (a === "codegen") { out.textContent = ENG.call("codegen", "verilog"); }
      else if (a === "caps") { out.textContent = "付加機能: " + ENG.capabilities().join(", "); }
    } catch (err) { out.textContent = "err: " + err.message; }
  }; });

  /* ========== 入力欄への単語補完付加 ========== */
  var OA_LAST = null, sugg = null, SUGG = [], curField = null, curRange = null;
  function docFreq(text) { var f = {}, ws = (text.toLowerCase().match(/[a-z]+/g) || []); for (var i = 0; i < ws.length; i++) if (ws[i].length >= 2) f[ws[i]] = (f[ws[i]] || 0) + 1; return f; }
  function getPrefix(el) { if (el.selectionStart == null) return null; var before = el.value.slice(0, el.selectionStart); var m = before.match(/[A-Za-z]+$/); return m ? { prefix: m[0], start: el.selectionStart - m[0].length, end: el.selectionStart } : null; }
  function closeSugg() { if (sugg) { sugg.remove(); sugg = null; } SUGG = []; }
  function showSugg(el) {
    if (!panel.querySelector("#oa-wc").checked) { closeSugg(); return; }
    if (!el || (el.tagName !== "TEXTAREA" && el.tagName !== "INPUT")) { closeSugg(); return; }
    var cp = getPrefix(el); if (!cp || cp.prefix.length < 1) { closeSugg(); return; }
    var freq = docFreq(el.value), vocab = DEFAULT_VOCAB.concat(Object.keys(freq));
    SUGG = ENG.call("word_complete", cp.prefix, { vocab: vocab, freq: freq, k: 6 });
    curField = el; curRange = cp;
    if (!SUGG.length) { closeSugg(); return; }
    if (!sugg) { sugg = document.createElement("div"); sugg.className = "oa-sugg"; document.body.appendChild(sugg); }
    sugg.innerHTML = SUGG.map(function (s, i) { return '<div class="' + (i === 0 ? "sel" : "") + '" data-i="' + i + '"><b>' + cp.prefix + "</b>" + s.word.slice(cp.prefix.length) + "</div>"; }).join("");
    var r = el.getBoundingClientRect();
    sugg.style.left = (r.left + window.scrollX + 6) + "px";
    sugg.style.top = (r.bottom + window.scrollY + 2) + "px";
    sugg.querySelectorAll("div").forEach(function (d) { d.onmousedown = function (ev) { ev.preventDefault(); accept(+d.dataset.i); }; });
  }
  function accept(i) { if (!curField || !SUGG[i] || !curRange) return; var w = SUGG[i].word, v = curField.value;
    curField.value = v.slice(0, curRange.start) + w + v.slice(curRange.end); var np = curRange.start + w.length;
    try { curField.setSelectionRange(np, np); } catch (e) {} curField.focus();
    curField.dispatchEvent(new Event("input", { bubbles: true })); closeSugg(); }
  document.addEventListener("focusin", function (e) { if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) OA_LAST = e.target; });
  document.addEventListener("input", function (e) { showSugg(e.target); }, true);
  document.addEventListener("keydown", function (e) {
    if (!sugg || !SUGG.length) return;
    if (e.key === "Tab") { e.preventDefault(); accept(0); }
    else if (e.key === "Escape") closeSugg();
  }, true);
  document.addEventListener("click", function (e) { if (sugg && e.target !== sugg && !sugg.contains(e.target)) closeSugg(); });

  console.log("Ω-Apriori attached. capabilities:", ENG.capabilities(), "| UID", ENG.call("self_evolve", "uid"));
})();
