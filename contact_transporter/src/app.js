/*
 * app.js — Contact Transporter Studio の UI ホスト
 *
 * 3 つのアプリ (ContactGPT / 輸送機 3D CAD / UFO 設計図面) はそれぞれ Bada プログラム
 * (bada/apps/*.bada) で、ここはその実行環境です:
 *   - Bada の ui_* 宣言からパラメータ欄・計算結果・グラフ・ボタンを生成し、値が変わると build() を呼ぶ
 *   - アニメーションの毎フレーム frame(t)、チャットの送信ごとに on_message(q) を呼ぶ
 *   - cad_* で組み立てられたシーンを WebGL で表示し、sheet_draw の図面を表示・書き出す
 *   - Bada IDE: ソースの編集・構文チェック・逆アセンブル・任意のタブへの実行・保存
 */
(function () {
  "use strict";
  const CAD = window.CTCad, Draft = window.CTDraft, GPTm = window.ContactGPT, B = window.Bada, L = window.BadaLib;
  const EQS = window.CT_EQUATIONS || [];
  const INDEX = new window.CTChat.Index(EQS);
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const fmt = (v) => (typeof v === "number" ? (Number.isInteger(v) ? String(v) : String(+v.toPrecision(8))) : B.toText(v));
  const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
  // アプリの種類 (apps.json): ContactGPT / 輸送機 3D CAD / UFO 設計図面 / 統合版
  const APP = window.CT_APP || { key: "studio", tabs: ["chat", "cad", "ufo", "ide", "eqs", "about"] };
  const HAS = (t) => APP.tabs.includes(t);
  // 保存キーはアプリごとに分ける (同じ端末に複数のアプリを入れても混ざらない)
  const nsKey = (k) => k.replace(/^ct\./, `ct.${APP.key}.`);
  const store = {
    get(k, d) { try { const v = localStorage.getItem(nsKey(k)); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(nsKey(k), JSON.stringify(v)); } catch (e) { /* 容量超過などは無視 */ } },
  };
  // このアプリに含まれないタブを取り除く
  $$("#tabs button").forEach((b) => { if (!HAS(b.dataset.tab)) b.remove(); });
  $$("main > .tab").forEach((t) => { if (!HAS(t.id.replace("tab-", ""))) t.remove(); });
  $$("#ide-target option").forEach((o) => { if (o.value !== "console" && !HAS(o.value)) o.remove(); });
  for (const [t, label] of Object.entries(APP.labels || {})) {
    $$(`#tabs [data-tab="${t}"]`).forEach((b) => { b.textContent = label; });
    $$(`#ide-target option[value="${t}"]`).forEach((o) => { o.textContent = label.replace(/^\S+\s/, "") + " タブ"; });
  }
  if (APP.tabs.filter((t) => ["chat", "cad", "ufo"].includes(t)).length === 1) $$("#tabs button").forEach((b) => { if (b.dataset.tab === "ide") b.textContent = "⌨ Bada IDE (ソース)"; });

  // ------------------------------------------------------------ 共通
  let toastT;
  function toast(msg) {
    const t = $("#toast"); t.textContent = msg; t.classList.add("on");
    clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove("on"), 3200);
  }
  function cordovaWrite(name, blob) {
    const F = window.cordova.file;
    const dirs = [F.externalRootDirectory && F.externalRootDirectory + "Download/", F.externalDataDirectory, F.dataDirectory].filter(Boolean);
    return new Promise((resolve, reject) => {
      const tryDir = (i) => {
        if (i >= dirs.length) return reject(new Error("書き込み可能な場所がありません"));
        window.resolveLocalFileSystemURL(dirs[i], (dir) => {
          dir.getFile(name, { create: true, exclusive: false }, (fe) => {
            fe.createWriter((w) => { w.onwriteend = () => resolve(dirs[i] + name); w.onerror = () => tryDir(i + 1); w.write(blob); }, () => tryDir(i + 1));
          }, () => tryDir(i + 1));
        }, () => tryDir(i + 1));
      };
      tryDir(0);
    });
  }
  async function saveFile(name, data, mime) {
    const blob = data instanceof Blob ? data : new Blob([data], { type: mime || "application/octet-stream" });
    if (window.cordova && window.resolveLocalFileSystemURL && window.cordova.file) {
      try { toast("保存しました: " + (await cordovaWrite(name, blob))); } catch (e) { toast("保存に失敗: " + e.message); }
      return;
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
    toast(`${name} を書き出しました`);
  }
  function svgToPng(svg, width) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const w = width || 2480, h = Math.round(w * 297 / 420), c = document.createElement("canvas");
        c.width = w; c.height = h; c.getContext("2d").drawImage(img, 0, 0, w, h); c.toBlob((b) => resolve(b), "image/png");
      };
      img.onerror = reject;
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    });
  }
  function dataUrlToBlob(u) {
    const [h, b] = u.split(","), bin = atob(b), arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return new Blob([arr], { type: h.split(":")[1].split(";")[0] });
  }
  const numv = (v) => (typeof v === "bigint" ? Number(v) : +v);
  // 折れ線グラフ
  function plot(cv, series, o) {
    o = o || {};
    const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth || 300, H = W * 130 / 300;
    cv.width = W * dpr; cv.height = H * dpr;
    const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const pad = { l: 36, r: 8, t: 16, b: 18 };
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const s of series) for (const p of s.pts) { const x = numv(p[0]), y = numv(p[1]); if (!isFinite(y)) continue; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
    if (!isFinite(x0)) return;
    if (x1 === x0) x1 = x0 + 1;
    const dy = (y1 - y0) || 1; y0 -= dy * 0.05; y1 += dy * 0.05;
    const X = (x) => pad.l + (x - x0) / (x1 - x0) * (W - pad.l - pad.r), Y = (y) => H - pad.b - (y - y0) / (y1 - y0) * (H - pad.t - pad.b);
    g.strokeStyle = "#1f2d4a"; g.lineWidth = 1; g.font = "10px sans-serif"; g.fillStyle = "#8aa0c4";
    for (let k = 0; k <= 4; k++) { const y = y0 + (y1 - y0) * k / 4; g.beginPath(); g.moveTo(pad.l, Y(y)); g.lineTo(W - pad.r, Y(y)); g.stroke(); g.fillText(String(+y.toPrecision(3)), 2, Y(y) + 3); }
    for (let k = 0; k <= 4; k++) { const x = x0 + (x1 - x0) * k / 4; g.fillText(String(+x.toPrecision(3)), X(x) - 8, H - 4); }
    if (y0 < 0 && y1 > 0) { g.strokeStyle = "#37507a"; g.beginPath(); g.moveTo(pad.l, Y(0)); g.lineTo(W - pad.r, Y(0)); g.stroke(); }
    for (const s of series) {
      g.strokeStyle = s.color; g.lineWidth = 1.6; g.beginPath(); let first = true;
      for (const p of s.pts) { const x = numv(p[0]), y = numv(p[1]); if (!isFinite(y)) { first = true; continue; } first ? g.moveTo(X(x), Y(y)) : g.lineTo(X(x), Y(y)); first = false; }
      g.stroke();
    }
    for (const m of o.marks || []) {
      const mx = numv(m[0]), my = m[1] == null ? null : numv(m[1]);
      g.strokeStyle = "#ffd54f"; g.setLineDash([3, 3]); g.beginPath(); g.moveTo(X(mx), pad.t); g.lineTo(X(mx), H - pad.b); g.stroke(); g.setLineDash([]);
      if (my != null) { g.fillStyle = "#ffd54f"; g.beginPath(); g.arc(X(mx), Y(my), 3, 0, 7); g.fill(); }
      if (m[2]) { g.fillStyle = "#ffd54f"; g.fillText(String(m[2]), Math.min(X(mx) + 3, W - 90), pad.t + 8); }
    }
    g.fillStyle = "#e6eefc"; g.font = "11px sans-serif"; g.fillText(o.title || "", pad.l, 11);
    if (series.length > 1) { let lx = W - pad.r; for (const s of series.slice().reverse()) { const w = g.measureText(s.name).width; lx -= w + 14; g.fillStyle = s.color; g.fillRect(lx, 4, 8, 8); g.fillText(s.name, lx + 10, 11); } }
  }

  // ------------------------------------------------------------ Bada ファイル (既定 + 利用者の編集)
  const DEFAULT_FILES = window.CT_BADA || {};
  const files = Object.assign({}, DEFAULT_FILES, store.get("ct.bada.files", {}));
  function saveFiles() {
    const changed = {};
    for (const [k, v] of Object.entries(files)) if (DEFAULT_FILES[k] !== v) changed[k] = v;
    store.set("ct.bada.files", changed);
    store.set("ct.bada.deleted", Object.keys(DEFAULT_FILES).filter((k) => !(k in files)));
  }
  for (const k of store.get("ct.bada.deleted", [])) delete files[k];
  const MAIN = Object.assign({ chat: "apps/contactgpt.bada", cad: "apps/transporter.bada", ufo: "apps/ufo.bada" }, store.get("ct.bada.main", {}));

  // ------------------------------------------------------------ コンソール
  function consoleOf(name) { return $(`[data-console="${name}"]`); }
  function conLine(name, text, cls) {
    const c = consoleOf(name); if (!c) return;
    const out = c.querySelector(".out") || c;
    const d = document.createElement("div"); d.className = "cl " + (cls || ""); d.textContent = text; out.appendChild(d);
    while (out.children.length > 400) out.firstChild.remove();
    out.scrollTop = out.scrollHeight;
  }
  function mountConsole(name, onEval) {
    const c = consoleOf(name); if (!c) return;
    c.innerHTML = `<div class="conhead">Bada コンソール <small>print / say の出力・エラー。下の欄に Bada を入力して Enter で実行 (同じ VM 上)</small></div><div class="out"></div>` +
      (onEval ? `<form class="repl"><span>bada&gt;</span><input placeholder='例: print rget(state[0], "phi")  /  ui_set("diameter", 30)  build()'></form>` : "");
    if (onEval) {
      const f = c.querySelector("form"), inp = f.querySelector("input"), hist = []; let hi = 0;
      f.addEventListener("submit", (e) => { e.preventDefault(); const v = inp.value; if (!v.trim()) return; hist.push(v); hi = hist.length; conLine(name, "bada> " + v, "in"); inp.value = ""; onEval(v); });
      inp.addEventListener("keydown", (e) => {
        if (e.key === "ArrowUp" && hi > 0) { inp.value = hist[--hi]; e.preventDefault(); }
        if (e.key === "ArrowDown") { hi = Math.min(hist.length, hi + 1); inp.value = hist[hi] || ""; e.preventDefault(); }
      });
    }
  }

  // ------------------------------------------------------------ Bada UI アダプタ (ui_* → DOM)
  function makeUI(root, tab) {
    const vals = {}, els = {}, outs = {}, plots = {};
    let grid = null, kv = null;
    const section = (title) => {
      const h = document.createElement("h3"); h.textContent = title; root.appendChild(h);
      grid = null; kv = null;
    };
    const ensureGrid = () => { if (!grid) { grid = document.createElement("div"); grid.className = "form"; root.appendChild(grid); } return grid; };
    const ensureKV = () => { if (!kv) { kv = document.createElement("div"); kv.className = "kv"; root.appendChild(kv); } return kv; };
    const field = (key, label, html, full) => {
      if (els[key]) return vals[key];
      const lab = document.createElement("label"); if (full) lab.className = full;
      lab.innerHTML = html; if (label) lab.insertAdjacentText("afterbegin", label);
      ensureGrid().appendChild(lab);
      const el = lab.querySelector("input,select"); els[key] = el;
      el.addEventListener(el.tagName === "SELECT" || el.type === "checkbox" || el.type === "color" ? "change" : "input", () => {
        vals[key] = el.type === "checkbox" ? el.checked : el.type === "number" ? (el.value === "" ? 0 : +el.value) : el.value;
        tab.changed();
      });
      return vals[key];
    };
    const saved = store.get("ct.params." + tab.name, {});
    const init = (key, def) => { if (!(key in vals)) vals[key] = key in saved ? saved[key] : def; };
    return {
      vals,
      reset() { root.innerHTML = ""; grid = null; kv = null; for (const k of Object.keys(els)) delete els[k]; for (const k of Object.keys(outs)) delete outs[k]; for (const k of Object.keys(plots)) delete plots[k]; },
      section,
      param(key, label, def, step) { init(key, def); return field(key, "", `<span>${esc(label)}</span><input type="number" step="${step == null ? "any" : step}" value="${esc(vals[key])}">`) ?? vals[key]; },
      check(key, label, def) { init(key, def); field(key, "", `<input type="checkbox" ${vals[key] ? "checked" : ""}> <span>${esc(label)}</span>`, "chk"); return vals[key]; },
      select(key, label, options, def) { init(key, def); field(key, "", `<span>${esc(label)}</span><select>${options.map((o) => `<option ${o === vals[key] ? "selected" : ""}>${esc(o)}</option>`).join("")}</select>`); return vals[key]; },
      text(key, label, def) { init(key, def); field(key, "", `<span>${esc(label)}</span><input type="text" value="${esc(vals[key])}">`, "full"); return vals[key]; },
      color(key, label, def) { init(key, def); field(key, "", `<span>${esc(label)}</span><input type="color" value="${esc(vals[key])}">`); return vals[key]; },
      set(key, v) {
        vals[key] = typeof v === "bigint" ? Number(v) : v; const el = els[key];
        if (el) { if (el.type === "checkbox") el.checked = !!v; else el.value = v == null ? "" : String(v); }
        return null;
      },
      get(key) { return key in vals ? vals[key] : null; },
      button(label, fn) {
        const b = document.createElement("button"); b.textContent = label;
        let box = root.lastElementChild; if (!box || !box.classList.contains("btns")) { box = document.createElement("div"); box.className = "btns"; root.appendChild(box); }
        box.appendChild(b); b.addEventListener("click", () => tab.invoke(fn));
        grid = null; kv = null; return null;
      },
      output(key, label, v) {
        if (!outs[key]) { const k = document.createElement("div"), d = document.createElement("div"); ensureKV().append(k, d); outs[key] = [k, d]; }
        outs[key][0].textContent = label; outs[key][1].textContent = fmt(v); return null;
      },
      plot(key, title, series, marks) {
        if (!plots[key]) { const c = document.createElement("canvas"); c.className = "plot"; root.appendChild(c); plots[key] = c; grid = null; kv = null; }
        const ser = series.map((s) => ({ name: String(s[0]), color: String(s[1]), pts: Array.isArray(s[2]) ? s[2] : [] }));
        plots[key]._args = [ser, { title, marks }];
        const cv = plots[key];
        requestAnimationFrame(() => { if (cv.isConnected) plot(cv, ser, { title, marks }); });
        return null;
      },
      hud(t) { if (tab.hud) tab.hud.textContent = t; return null; },
      toast(t) { toast(t); return null; },
      chips(list) { if (tab.onChips) tab.onChips(list); return null; },
      view(name) { if (tab.viewer) tab.viewer.setView(name); return null; },
      fit() { if (tab.viewer) tab.fit(); return null; },
      request(placeholder) { tab.mountRequest(placeholder); return null; },
      export(kind) { setTimeout(() => tab.exportAs(kind), 0); return null; },
    };
  }

  // ------------------------------------------------------------ Bada タブ
  class BadaTab {
    constructor(name, opts) {
      this.name = name; this.opts = opts || {};
      this.uiRoot = $(`#${name}-ui`);
      this.scene = new L.Scene();
      this.hud = $(`#${name}-hud`);
      this.viewer = null;
      if (opts.canvas) {
        try { this.viewer = new window.CTViewer($(opts.canvas)); } catch (e) { conLine(name, "WebGL が使えません: " + e.message, "err"); }
      }
      this.ui = makeUI(this.uiRoot, this);
      this.t = 0; this.fitted = false;
      this.env = {
        files, ui: this.ui, chat: opts.chat || null, equations: EQS, index: INDEX, scene: this.scene,
        onFileWrite: (n) => { saveFiles(); if (IDE.refresh) IDE.refresh(); conLine(name, `── ${n} を保存しました`, "sys"); },
        model: () => MODEL.current,
        colorLines: () => { const c = $(`#tab-${name} [data-colorlines]`); return !!(c && c.checked); },
        onSheet: (s) => { const el = $(`[data-sheet="${name}"]`); if (el) el.innerHTML = s.svg; },
        onPrint: (line) => conLine(name, line),
        onError: (e) => { conLine(name, "✖ " + (e.kind || "Error") + ": " + e.message, "err"); toast("Bada エラー: " + e.message); },
      };
      this.app = new L.BadaApp(this.env);
      this.rebuild = debounce(() => this.invoke("build"), 120);
      mountConsole(name, (src) => { try { this.app.eval(src); } catch (e) { this.env.onError(e); } this.refresh(); });
      if (this.viewer) this.bindViewbar();
    }
    get file() { return MAIN[this.name]; }
    // 日本語の要求欄: 入力 → Bada の on_request(q) → 返答を表示
    mountRequest(placeholder) {
      let box = $(`[data-request="${this.name}"]`);
      if (!box) {
        box = document.createElement("div"); box.className = "request"; box.dataset.request = this.name;
        box.innerHTML = `<div class="reqhead">💬 要求・質問 <small>Bada の on_request(q) が答えます</small></div><div class="reqlog"></div><form><input autocomplete="off"><button class="primary">実行</button></form>`;
        this.uiRoot.parentNode.insertBefore(box, this.uiRoot);
        const inp = $("input", box), log = $(".reqlog", box);
        $("form", box).addEventListener("submit", (e) => {
          e.preventDefault(); const q = inp.value.trim(); if (!q) return; inp.value = "";
          const u = document.createElement("div"); u.className = "rq"; u.textContent = q; log.appendChild(u);
          const r = this.invoke("on_request", [q]);
          const a = document.createElement("div"); a.className = "ra"; a.textContent = r == null ? "(on_request がありません)" : B.toText(r); log.appendChild(a);
          while (log.children.length > 40) log.firstChild.remove();
          log.scrollTop = log.scrollHeight;
        });
      }
      box.hidden = false;
      $("input", box).placeholder = placeholder || "要求や質問を入力";
    }
    start(file) {
      if (file) { MAIN[this.name] = file; store.set("ct.bada.main", MAIN); }
      const src = files[this.file];
      $(`#${this.name}-src`).textContent = this.file;
      if (src == null) { conLine(this.name, `✖ ${this.file} がありません`, "err"); return; }
      if (this.hud) this.hud.textContent = "";
      const rq = $(`[data-request="${this.name}"]`); if (rq) rq.hidden = true;
      this.env.lastSheet = null; const sh = $(`[data-sheet="${this.name}"]`); if (sh) sh.innerHTML = "";
      conLine(this.name, `── ${this.file} を実行 (Bada VM)`, "sys");
      const t0 = performance.now();
      this.app.start(src, this.file);
      conLine(this.name, `── 完了 ${(performance.now() - t0).toFixed(0)} ms` + (this.scene.parts.size ? ` / 部品 ${this.scene.parts.size}` : ""), "sys");
      this.refresh(true);
    }
    changed() { store.set("ct.params." + this.name, this.ui.vals); this.rebuild(); }
    invoke(fn, args) {
      if (!this.app.has(fn)) { if (fn !== "build") conLine(this.name, `✖ 関数 ${fn} がありません`, "err"); return null; }
      const r = this.app.call(fn, args || []);
      store.set("ct.params." + this.name, this.ui.vals);
      this.refresh();
      return r;
    }
    refresh(refit) {
      if (!this.viewer) return;
      this.viewer.setParts(this.scene.list());
      if ((refit || !this.fitted) && this.scene.parts.size) { this.fit(); this.fitted = true; }
      this.partList();
    }
    fit() { const b = L.boundsOf(this.scene.baked()); if (isFinite(b.min[0])) this.viewer.frame(b, this.fitted); }
    tick(dt) {
      if (!this.viewer || !this.app.has("frame")) return;
      const anim = $(`#tab-${this.name} [data-anim]`);
      if (anim && !anim.checked) return;
      this.t += dt;
      this.app.call("frame", [this.t]);
      this.viewer.setParts(this.scene.list());
    }
    partList() {
      const box = $(`[data-parts="${this.name}"]`); if (!box) return;
      const key = this.scene.list().map((p) => p.id + p.hidden).join();
      if (box._key === key) return; box._key = key;
      const groups = new Map();
      for (const p of this.scene.list()) { const g = p.id.replace(/\d+$/, ""); if (!groups.has(g)) groups.set(g, []); groups.get(g).push(p); }
      box.innerHTML = Array.from(groups, ([g, ps]) => `<label data-g="${esc(g)}"><input type="checkbox" ${ps[0].hidden ? "" : "checked"}><i style="background:${ps[0].color}"></i>${esc(ps[0].name)}${ps.length > 1 ? ` ×${ps.length}` : ""} <small>${esc(g)}</small></label>`).join("");
      $$("label", box).forEach((l) => {
        const g = l.dataset.g, ps = groups.get(g);
        l.querySelector("input").addEventListener("change", (e) => { for (const p of ps) p.hidden = !e.target.checked; this.viewer.setParts(this.scene.list()); });
        l.addEventListener("mouseenter", () => { this.viewer.selected = g; this.viewer.draw(); });
        l.addEventListener("mouseleave", () => { this.viewer.selected = null; this.viewer.draw(); });
      });
    }
    bindViewbar() {
      const T = $(`#tab-${this.name}`), v = this.viewer;
      $$("[data-view]", T).forEach((b) => b.addEventListener("click", () => v.setView(b.dataset.view)));
      const on = (sel, fn) => { const el = $(sel, T); if (el) el.addEventListener("change", (e) => fn(e.target.checked)); };
      const fitb = $("[data-fit]", T); if (fitb) fitb.addEventListener("click", () => this.fit());
      on("[data-wire]", (c) => { v.wire = c; v.draw(); });
      on("[data-blue]", (c) => { v.blueprint = c; v.draw(); });
      on("[data-grid]", (c) => { v.showGrid = c; v.draw(); });
      on("[data-colorlines]", () => this.invoke("build"));
      $$(`[data-export="${this.name}"] button`, T).forEach((b) => b.addEventListener("click", () => this.exportAs(b.dataset.x)));
      const imp = $(`[data-import="${this.name}"]`);
      if (imp) imp.addEventListener("change", async (e) => {
        const f = e.target.files[0]; if (!f) return;
        try { const j = JSON.parse(await f.text()); for (const [k, val] of Object.entries(j.params || j)) this.ui.set(k, val); this.invoke("build"); this.fit(); toast("設計値を読み込みました"); }
        catch (err) { toast("読み込み失敗: " + err.message); }
      });
    }
    async exportAs(x) {
      const base = String(this.ui.get("name") || (this.name === "cad" ? "contact_transporter" : "bada_design")).replace(/[^\w\-]+/g, "_");
      if (this.app.has("frame") && ["stl", "obj", "dxf3", "sheet", "sheetpng", "sheetdxf"].includes(x)) this.app.call("frame", [0]);
      const baked = this.scene.baked();
      if (x === "stl") return saveFile(`${base}.stl`, CAD.toSTLBinary(baked, base), "model/stl");
      if (x === "obj") { saveFile(`${base}.obj`, CAD.toOBJ(baked, base).replace("mtllib parts.mtl", `mtllib ${base}.mtl`), "text/plain"); return setTimeout(() => saveFile(`${base}.mtl`, CAD.toMTL(baked), "text/plain"), 400); }
      if (x === "dxf3") return saveFile(`${base}_3d.dxf`, CAD.toDXF3D(baked), "application/dxf");
      if (x === "png") return saveFile(`${base}.png`, dataUrlToBlob(this.viewer.screenshot()), "image/png");
      if (x === "params") return saveFile(`${base}.params.json`, JSON.stringify({ format: "bada-params-v1", program: this.file, params: this.ui.vals }, null, 2), "application/json");
      // 図面: Bada に make_sheet があればそれを、無ければ直近の sheet_draw を使う
      if (this.app.has("make_sheet")) this.app.call("make_sheet", []);
      let s = this.env.lastSheet;
      if (!s) { s = Draft.sheet({ parts: baked, dims: this.scene.dims, bom: this.scene.bom, notes: this.scene.notes, title: base }); }
      if (x === "sheet") return saveFile(`${base}_drawing.svg`, s.svg, "image/svg+xml");
      if (x === "sheetdxf") return saveFile(`${base}_drawing.dxf`, s.dxf, "application/dxf");
      if (x === "sheetpng") return saveFile(`${base}_drawing.png`, await svgToPng(s.svg), "image/png");
    }
  }

  // ------------------------------------------------------------ Transformer の重み
  const MODEL = { current: null };
  try { if (window.CT_WEIGHTS) MODEL.current = GPTm.GPT.fromJSON(window.CT_WEIGHTS); } catch (e) { console.warn(e); }
  try { const w = store.get("ct.weights", null); if (w) { const m2 = GPTm.GPT.fromJSON(w); if (!MODEL.current || m2.step > MODEL.current.step) MODEL.current = m2; } } catch (e) { /* ignore */ }

  // ------------------------------------------------------------ タブ切替
  const tabs = {}, tabInit = {};
  function showTab(name) {
    $$("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
    $$(".tab").forEach((t) => t.classList.toggle("on", t.id === "tab-" + name));
    if (tabInit[name] && !tabInit[name].done) { tabInit[name].done = true; tabInit[name](); }
    window.dispatchEvent(new Event("resize"));
    store.set("ct.tab", name);
  }
  $$("#tabs button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
  $$("[data-open]").forEach((b) => b.addEventListener("click", () => { showTab("ide"); IDE.open(MAIN[b.dataset.open], b.dataset.open); }));
  $$("[data-rerun]").forEach((b) => b.addEventListener("click", () => { const t = tabs[b.dataset.rerun]; if (t) t.start(); }));

  // ============================================================ ContactGPT
  function md(s) { return esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>"); }
  function eqHtml(e) {
    const tags = e.tags.map((t) => `<span class="tag">${GPTm.TAG_JA[t] || t}</span>`).join("");
    return `<div class="ref"><b>${esc(e.id)}</b> ${tags} <span class="st-${e.status}">${GPTm.STATUS_JA[e.status]}</span><br>${esc(e.expr)}${e.value ? `<br><span class="st-${e.status}">= ${esc(e.value)}</span>` : ""}</div>`;
  }
  tabInit.chat = function () {
    const byId = new Map(EQS.map((e) => [e.id, e]));
    let bubble = null, streamGen = 0;
    const addMsg = (html, cls) => {
      const d = document.createElement("div"); d.className = "msg " + (cls || ""); d.innerHTML = html;
      $("#chat-log").appendChild(d); d.scrollIntoView({ block: "end" }); return d;
    };
    const chat = {
      reply: (m) => { bubble.insertAdjacentHTML("beforeend", `<div class="ans">${md(m)}</div>`); return null; },
      ref: (id) => { const e = byId.get(id); if (e) bubble.insertAdjacentHTML("beforeend", eqHtml(e)); return null; },
      gen: (t) => { bubble.insertAdjacentHTML("beforeend", `<div class="gen">${esc(t)}</div>`); return null; },
      // Bada が書いた Bada プログラム: コード表示 + 実行 / IDE / 保存
      code: (file, src, target, desc) => {
        const el = document.createElement("div"); el.className = "codeblock";
        const where = target === "console" ? "console" : HAS(target) ? target : HAS("cad") ? "cad" : HAS("ufo") ? "ufo" : "console";
        const label = where === "console" ? "▶ 実行 (結果をここに表示)" : `▶ ${($(`#tabs [data-tab="${where}"]`) || { textContent: where }).textContent.trim()} で実行`;
        el.innerHTML = `<div class="cbhead"><b>${esc(file)}</b><span>${esc(src.split("\n").length)} 行 · Bada</span></div><pre class="cbsrc"></pre>` +
          `<div class="btns"><button class="primary" data-a="run">${esc(label)}</button><button data-a="ide">IDE で開く</button><button data-a="save">保存 (.bada)</button><button data-a="fold">全体を表示</button></div><div class="cbout"></div>`;
        $(".cbsrc", el).innerHTML = IDE.highlightHTML(src);
        const runIt = () => {
          if (where === "console") {
            const out = $(".cbout", el); out.innerHTML = "";
            const lines = [], env = { files, ui: { toast }, chat: {}, equations: EQS, index: INDEX, scene: new L.Scene(), model: () => MODEL.current, onPrint: (l) => lines.push(l) };
            const vm = new B.BadaVM({ host: L.makeHost(env), files, onPrint: env.onPrint, maxSteps: 2e8 });
            const t0 = performance.now();
            try { vm.load(files[file] || src, file); lines.push(`── 完了 ${(performance.now() - t0).toFixed(0)} ms (Bada VM)`); }
            catch (e) { lines.push("✖ " + e.message); }
            out.textContent = lines.join("\n");
          } else { showTab(where); tabs[where].start(file); toast(`${file} を実行しました`); }
        };
        el.addEventListener("click", (e) => {
          const a = e.target.dataset && e.target.dataset.a; if (!a) return;
          if (a === "run") runIt();
          if (a === "ide") { showTab("ide"); IDE.open(file, where === "console" ? "console" : where); }
          if (a === "save") saveFile(file.split("/").pop(), files[file] || src, "text/plain");
          if (a === "fold") { el.classList.toggle("open"); e.target.textContent = el.classList.contains("open") ? "折りたたむ" : "全体を表示"; }
        });
        bubble.appendChild(el);
        if (where === "console") runIt();
        return null;
      },
      // Bada の gen_next(ids) / gen_stop(out) を 1 文字ずつ呼んで流し込む
      stream: (prompt, n) => {
        const G = MODEL.current; if (!G) return null;
        const el = document.createElement("div"); el.className = "gen streaming"; bubble.appendChild(el);
        const ids = G.encode(prompt), my = ++streamGen; let out = "", k = 0;
        const step = () => {
          if (my !== streamGen) { el.classList.remove("streaming"); return; }
          const t0 = performance.now();
          while (k < n && performance.now() - t0 < 30) {
            const tok = tabs.chat.app.call("gen_next", [ids]); if (tok == null) { k = n; break; }
            ids.push(numv(tok)); out += G.decode([numv(tok)]); k++;
            if (tabs.chat.app.call("gen_stop", [out])) { out = out.slice(0, -3); k = n; break; }
          }
          el.textContent = out.trim();
          $("#chat-log").scrollTop = $("#chat-log").scrollHeight;
          if (k < n) setTimeout(step, 0); else el.classList.remove("streaming");
        };
        setTimeout(step, 0);
        return null;
      },
    };
    const T = new BadaTab("chat", { chat });
    T.onChips = (list) => {
      $("#chat-chips").innerHTML = list.map((c) => `<button>${esc(c)}</button>`).join("");
      $$("#chat-chips button").forEach((b) => b.addEventListener("click", () => ask(b.textContent)));
    };
    tabs.chat = T;
    function ask(q) {
      addMsg(esc(q), "user");
      bubble = addMsg("", "bot");
      setTimeout(() => {
        T.invoke("on_message", [q]);
        if (!bubble.innerHTML) bubble.innerHTML = "—";
        bubble.scrollIntoView({ block: "end" });
      }, 10);
    }
    addMsg(md("こんにちは、**ContactGPT** です。この対話エンジンは量子プログラミング言語 **Bada** で書かれています (`apps/contactgpt.bada`)。設計図書の全方程式 2111 本で学習した Transformer のロジットを Bada が受け取り、**量子状態 ψ = √a·e^{iθ} の Born 則測定**で次の文字を選びます。\n例: 「UFO.19」「ローレンツ因子は？」「計算 rs_z(14.1347)」— 計算 のあとは Bada の式です。"), "bot");
    $("#chat-form").addEventListener("submit", (e) => { e.preventDefault(); const v = $("#chat-in").value.trim(); if (v) { ask(v); $("#chat-in").value = ""; } });
    T.start();
    // 学習 (Web Worker)
    let worker = null; const losses = [];
    const WORKER_MAIN = `
      let stop = false;
      self.onmessage = (e) => {
        const m = e.data;
        if (m.cmd === "stop") { stop = true; return; }
        const G = self.ContactGPT;
        const model = m.weights ? G.GPT.fromJSON(m.weights) : new G.GPT(m.cfg, G.buildVocab(m.corpus));
        const data = Int32Array.from(model.encode(m.corpus));
        let s = 0; stop = false;
        const loop = () => {
          const t0 = Date.now();
          while (Date.now() - t0 < 250 && s < m.steps && !stop) {
            const prog = s / m.steps, lr = m.lr * (0.1 + 0.9 * 0.5 * (1 + Math.cos(Math.PI * prog)));
            const loss = model.trainStep(data, { batch: m.batch, lr, wd: 0.01 });
            s++; self.postMessage({ type: "progress", step: s, total: m.steps, loss, gstep: model.step });
          }
          if (s < m.steps && !stop) setTimeout(loop, 0);
          else self.postMessage({ type: "done", weights: model.toJSON() });
        };
        loop();
      };`;
    function train(scratch) {
      if (worker) return;
      worker = new Worker(URL.createObjectURL(new Blob([$("#gpt-src").textContent + "\n" + WORKER_MAIN], { type: "text/javascript" })));
      const corpus = GPTm.buildCorpus(EQS, window.CTPhys.blueprint());
      losses.length = 0;
      const steps = Math.max(10, +$("#train-steps").value || 200);
      $("#train-more").disabled = $("#train-scratch").disabled = true; $("#train-stop").disabled = false;
      const t0 = Date.now();
      worker.onmessage = (e) => {
        const m = e.data;
        if (m.type === "progress") {
          losses.push([m.step, m.loss]);
          if (m.step % 5 === 0 || m.step === m.total) {
            const ema = losses.slice(-20).reduce((s, x) => s + x[1], 0) / Math.min(20, losses.length);
            $("#train-status").textContent = `step ${m.step}/${m.total} (累計 ${m.gstep})  loss ${ema.toFixed(3)}  ${((Date.now() - t0) / 1000).toFixed(0)} s`;
            plot($("#loss-plot"), [{ name: "loss", pts: losses, color: "#4fc3f7" }], { title: "学習損失 (交差エントロピー)" });
          }
        } else if (m.type === "done") {
          MODEL.current = GPTm.GPT.fromJSON(m.weights);
          worker.terminate(); worker = null;
          $("#train-more").disabled = $("#train-scratch").disabled = false; $("#train-stop").disabled = true;
          store.set("ct.weights", m.weights); toast("学習が完了しました"); T.start();
        }
      };
      worker.postMessage({ cmd: "train", corpus, steps, batch: 6, lr: scratch ? 3e-3 : 1e-3,
        weights: scratch || !MODEL.current ? null : MODEL.current.toJSON(),
        cfg: { nLayer: 2, nHead: 4, nEmbd: 64, block: 64, seed: (Date.now() & 0xffff) } });
    }
    $("#train-more").addEventListener("click", () => train(false));
    $("#train-scratch").addEventListener("click", () => train(true));
    $("#train-stop").addEventListener("click", () => worker && worker.postMessage({ cmd: "stop" }));
    $("#gpt-save").addEventListener("click", () => MODEL.current && saveFile("contactgpt_weights.json", JSON.stringify(MODEL.current.toJSON()), "application/json"));
    $("#gpt-load").addEventListener("change", async (e) => {
      const f = e.target.files[0]; if (!f) return;
      try { MODEL.current = GPTm.GPT.fromJSON(JSON.parse(await f.text())); T.start(); toast("重みを読み込みました"); } catch (err) { toast("読み込み失敗: " + err.message); }
    });
  };

  // ============================================================ 輸送機 CAD / UFO
  tabInit.cad = function () { tabs.cad = new BadaTab("cad", { canvas: "#cad-view" }); tabs.cad.start(); };
  tabInit.ufo = function () { tabs.ufo = new BadaTab("ufo", { canvas: "#ufo-view" }); tabs.ufo.start(); };
  let last = performance.now();
  (function loop(now) {
    const dt = Math.min(0.1, (now - last) / 1000); last = now;
    for (const name of ["cad", "ufo"]) if (tabs[name] && $(`#tab-${name}`) && $(`#tab-${name}`).classList.contains("on")) tabs[name].tick(dt);
    requestAnimationFrame(loop);
  })(last);

  // ============================================================ Bada IDE
  const HOST_NAMES = Object.keys(L.makeHost({ files: {}, ui: {}, chat: {}, equations: [], index: INDEX, scene: new L.Scene(), model: () => null })).sort();
  const IDE = (function () {
    let cur = null;
    const text = () => $("#ide-text");
    function listFiles() {
      const groups = {};
      for (const k of Object.keys(files).sort()) { const g = k.includes("/") ? k.split("/")[0] : "."; (groups[g] = groups[g] || []).push(k); }
      $("#ide-files").innerHTML = Object.entries(groups).map(([g, fs]) => `<div class="fgroup">${esc(g)}/</div>` + fs.map((f) =>
        `<div class="file ${f === cur ? "on" : ""}" data-f="${esc(f)}">${esc(f.split("/").pop())}${DEFAULT_FILES[f] !== files[f] ? " <i>●</i>" : ""}</div>`).join("")).join("");
      $$("#ide-files .file").forEach((d) => d.addEventListener("click", () => open(d.dataset.f)));
    }
    function open(f, target) {
      if (!(f in files)) return;
      cur = f; text().value = files[f]; $("#ide-name").textContent = f;
      // 実行先: 指定 → ファイル名からの推測 → このアプリの 3D タブ → コンソール
      let tg = target || (f.startsWith("apps/") ? (f.includes("ufo") ? "ufo" : f.includes("gpt") ? "chat" : "cad") : null);
      if (!tg && /template|my_ship/.test(f)) tg = HAS("cad") ? "cad" : "ufo";
      if (tg && !HAS(tg)) tg = HAS("cad") ? "cad" : HAS("ufo") ? "ufo" : null;
      if (tg === "chat" && !f.includes("gpt")) tg = null;
      $("#ide-target").value = tg || "console";
      highlight(); listFiles(); $("#ide-asmout").textContent = "";
      store.set("ct.ide.cur", f);
    }
    const KW = new Set(Array.from(B.KEYWORDS)), BI = new Set(Array.from(B.BUILTINS)), HN = new Set(HOST_NAMES);
    function highlightHTML(src) {
      let h = "";
      const re = /(\/\/[^\n]*)|("(?:[^"\\]|\\.)*"?|'(?:[^'\\]|\\.)*'?)|(#include[^\n]*)|(\d+\.?\d*)|([\p{L}_][\p{L}\p{N}_]*)|(<->|<-|-<|->|>-|>>|=>|::)|([\s\S])/gu;
      let m;
      while ((m = re.exec(src))) {
        if (m[1]) h += `<span class="c">${esc(m[1])}</span>`;
        else if (m[2]) h += `<span class="s">${esc(m[2])}</span>`;
        else if (m[3]) h += `<span class="k">${esc(m[3])}</span>`;
        else if (m[4]) h += `<span class="n">${esc(m[4])}</span>`;
        else if (m[5]) h += KW.has(m[5]) ? `<span class="k">${m[5]}</span>` : BI.has(m[5]) ? `<span class="b">${m[5]}</span>` : HN.has(m[5]) ? `<span class="h">${m[5]}</span>` : esc(m[5]);
        else if (m[6]) h += `<span class="o">${esc(m[6])}</span>`;
        else h += esc(m[7]);
      }
      return h;
    }
    function highlight() {
      const src = text().value;
      const lines = src.split("\n").length;
      $("#ide-gutter").textContent = Array.from({ length: lines }, (_, i) => i + 1).join("\n");
      $("#ide-hl").innerHTML = highlightHTML(src) + "\n";
      syncScroll();
    }
    function syncScroll() { const t = text(); $("#ide-hl").scrollTop = t.scrollTop; $("#ide-hl").scrollLeft = t.scrollLeft; $("#ide-gutter").scrollTop = t.scrollTop; }
    function status(s, err) { $("#ide-status").textContent = s; $("#ide-status").style.color = err ? "var(--danger)" : ""; }
    function expanded() { const vm = new B.BadaVM({ files }); return vm.expand(text().value, cur); }
    function check() {
      try {
        const diags = B.lint(expanded(), new Set(HOST_NAMES));
        if (!diags.length) { status("✔ 構文 OK"); return true; }
        status(`✖ ${diags[0].message}`, true); conLine("ide", "✖ " + diags[0].message, "err"); return false;
      } catch (e) { status("✖ " + e.message, true); return false; }
    }
    const saveCur = debounce(() => { if (cur) { files[cur] = text().value; saveFiles(); listFiles(); } }, 300);
    function run() {
      if (!cur) return;
      files[cur] = text().value; saveFiles();
      if (!check()) return;
      const target = $("#ide-target").value;
      if (target === "console") {
        conLine("ide", `── ${cur} を実行`, "sys");
        const env = { files, ui: { toast }, chat: {}, equations: EQS, index: INDEX, scene: new L.Scene(), model: () => MODEL.current, onPrint: (l) => conLine("ide", l) };
        const vm = new B.BadaVM({ host: L.makeHost(env), files, onPrint: env.onPrint, maxSteps: 2e8 });
        const t0 = performance.now();
        try { vm.load(files[cur], cur); conLine("ide", `── 完了 ${(performance.now() - t0).toFixed(0)} ms`, "sys"); }
        catch (e) { conLine("ide", "✖ " + e.message, "err"); }
        const ts = Object.entries(vm.tuplespace);
        if (ts.length) conLine("ide", "Omega::DATABASE " + ts.map(([k, v]) => `[${k}] ${B.toText(v)}`).join("  "), "sys");
        return;
      }
      showTab(target);
      tabs[target].start(cur);
      toast(`${cur} を ${ { cad: "輸送機 3D CAD", ufo: "UFO 設計図面", chat: "ContactGPT" }[target]} タブで実行しました`);
    }
    function init() {
      mountConsole("ide", null);
      text().addEventListener("input", () => { highlight(); saveCur(); });
      text().addEventListener("scroll", syncScroll);
      text().addEventListener("keydown", (e) => {
        if (e.key === "Tab") { e.preventDefault(); const t = text(), s = t.selectionStart; t.setRangeText("  ", s, t.selectionEnd, "end"); highlight(); saveCur(); }
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(); }
      });
      $("#ide-run").addEventListener("click", run);
      $("#ide-check").addEventListener("click", check);
      $("#ide-asm").addEventListener("click", () => {
        try { const code = B.compileSource(expanded(), { host: new Set(HOST_NAMES) }); $("#ide-asmout").textContent = `${code.length} 命令\n` + B.disassemble(code); status(`逆アセンブル: ${code.length} 命令`); }
        catch (e) { status("✖ " + e.message, true); }
      });
      $("#ide-save").addEventListener("click", () => cur && saveFile(cur.split("/").pop(), text().value, "text/plain"));
      $("#ide-reset").addEventListener("click", () => {
        if (!cur || !(cur in DEFAULT_FILES)) return;
        if (!confirm(`${cur} を既定の内容に戻しますか？`)) return;
        files[cur] = DEFAULT_FILES[cur]; saveFiles(); open(cur);
      });
      $("#ide-new").addEventListener("click", () => {
        const n = prompt("新しい Bada ファイル名 (例: user/my_ship.bada)", "user/my_app.bada"); if (!n) return;
        const name = n.endsWith(".bada") ? n : n + ".bada";
        if (!(name in files)) files[name] = files["examples/template.bada"] || "say \"hello, Bada\"\n";
        saveFiles(); open(name);
      });
      $("#ide-del").addEventListener("click", () => {
        if (!cur || !confirm(`${cur} を削除しますか？` + (cur in DEFAULT_FILES ? " (既定ファイルは「既定に戻す」で復元できません — 再読み込み時に復元されます)" : ""))) return;
        delete files[cur]; saveFiles(); cur = null; listFiles(); open(Object.keys(files).sort()[0]);
      });
      $("#ide-load").addEventListener("change", async (e) => {
        const f = e.target.files[0]; if (!f) return;
        const name = "user/" + f.name.replace(/[^\w.\-]+/g, "_"); files[name] = await f.text(); saveFiles(); open(name);
      });
      $("#ide-ref").innerHTML = `<b>予約語</b><br>${Array.from(B.KEYWORDS).join(" ")}<br><b>指示オブジェクト</b><br>${Object.entries(B.DIRECTIVES).map(([k, v]) => `<code>${esc(k)}</code> ${esc(v)}`).join("<br>")}<br><b>組込み関数</b><br>${Array.from(B.BUILTINS).join(" ")}<br><b>アプリ用ライブラリ (${HOST_NAMES.length})</b><br>${HOST_NAMES.join(" ")}`;
      const mainFile = HAS("cad") ? "apps/transporter.bada" : HAS("ufo") ? "apps/ufo.bada" : "apps/contactgpt.bada";
      const last = store.get("ct.ide.cur", mainFile);
      open(last in files ? last : mainFile);
    }
    const refresh = () => { if ($("#ide-files") && $("#ide-files").children.length) listFiles(); };
    return { open, init, run, highlightHTML, refresh };
  })();
  tabInit.ide = IDE.init;

  // ============================================================ 方程式レジストリ
  tabInit.eqs = function () {
    const tags = Array.from(new Set(EQS.flatMap((e) => e.tags))).sort();
    $("#eq-tag").innerHTML += tags.map((t) => `<option value="${t}">${GPTm.TAG_JA[t] || t} (${t})</option>`).join("");
    let rows = [], shown = 0;
    function render(reset) {
      if (reset) { $("#eq-list").innerHTML = ""; shown = 0; }
      const html = rows.slice(shown, shown + 150).map((e) => `<div class="eq"><div><div class="id">${esc(e.id)}</div><div class="st-${e.status}" style="font-size:11px">${GPTm.STATUS_JA[e.status]}</div></div><div><div class="ex">${esc(e.expr)}</div>${e.value ? `<div class="val st-${e.status}">= ${esc(e.value)}</div>` : ""}<div>${e.tags.map((t) => `<span class="tag">${GPTm.TAG_JA[t] || t}</span>`).join("")}</div></div></div>`).join("");
      $("#eq-list").insertAdjacentHTML("beforeend", html);
      shown = Math.min(rows.length, shown + 150);
      $("#eq-more").style.display = shown < rows.length ? "" : "none";
      $("#eq-count").textContent = `${rows.length} / ${EQS.length} 本`;
    }
    function filter() {
      const q = $("#eq-q").value.trim(), tg = $("#eq-tag").value, st = $("#eq-status").value;
      const f = (e) => (!tg || e.tags.includes(tg)) && (!st || e.status === st);
      rows = q ? INDEX.search(q, 400, f) : EQS.filter(f);
      render(true);
    }
    $("#eq-q").addEventListener("input", debounce(filter, 200));
    $("#eq-tag").addEventListener("change", filter);
    $("#eq-status").addEventListener("change", filter);
    $("#eq-more").addEventListener("click", () => render(false));
    filter();
    const cv = $("#plot-tags"), dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth || 900, H = 150;
    cv.width = W * dpr; cv.height = H * dpr; const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const counts = tags.map((t) => [t, EQS.filter((e) => e.tags.includes(t)).length]), mx = Math.max(...counts.map((c) => c[1]));
    const bw = (W - 20) / counts.length;
    g.font = "10px sans-serif";
    counts.forEach(([t, c], i) => {
      const h = (H - 40) * c / mx, x = 10 + i * bw;
      g.fillStyle = "#1e88e5"; g.fillRect(x + 4, H - 22 - h, bw - 8, h);
      g.fillStyle = "#e6eefc"; g.fillText(String(c), x + 6, H - 26 - h);
      g.fillStyle = "#8aa0c4"; g.fillText(t, x + 4, H - 8);
    });
    g.fillStyle = "#e6eefc"; g.font = "11px sans-serif"; g.fillText("部品 (タグ) ごとの方程式数", 10, 12);
  };

  // ============================================================ 起動
  const BI = window.CT_BUILD || {};
  $("#build-info").textContent = `build ${BI.version || "dev"} ${BI.date || ""}`;
  const first = store.get("ct.tab", APP.tabs[0]);
  showTab(HAS(first) ? first : APP.tabs[0]);
})();
