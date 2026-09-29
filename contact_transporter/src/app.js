/*
 * app.js — Contact Transporter Studio の UI
 *   ContactGPT / 輸送機 3D CAD / UFO 設計図面 / 方程式レジストリ
 */
(function () {
  "use strict";
  const Phys = window.CTPhys, CAD = window.CTCad, Models = window.CTModels, Draft = window.CTDraft;
  const GPTm = window.ContactGPT, ChatM = window.CTChat;
  const EQS = window.CT_EQUATIONS || [];
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const fmt = (v, p) => (+(+v).toPrecision(p || 6)).toString();
  const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

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
      try { toast("保存しました: " + (await cordovaWrite(name, blob))); return; } catch (e) { toast("保存に失敗: " + e.message); return; }
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
        c.width = w; c.height = h; const g = c.getContext("2d");
        g.drawImage(img, 0, 0, w, h); c.toBlob((b) => resolve(b), "image/png");
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
  // 折れ線グラフ
  function plot(cv, series, o) {
    o = o || {};
    const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth || cv.width, H = W * cv.height / cv.width;
    cv.width = W * dpr; cv.height = H * dpr;
    const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const pad = { l: 34, r: 8, t: 16, b: 18 };
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const s of series) for (const [x, y] of s.pts) { if (!isFinite(y)) continue; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
    if (o.ylim) [y0, y1] = o.ylim;
    if (o.zero) { y0 = Math.min(y0, 0); y1 = Math.max(y1, 0); }
    const dy = (y1 - y0) || 1; y0 -= dy * 0.05; y1 += dy * 0.05;
    const X = (x) => pad.l + (x - x0) / (x1 - x0) * (W - pad.l - pad.r), Y = (y) => H - pad.b - (y - y0) / (y1 - y0) * (H - pad.t - pad.b);
    g.strokeStyle = "#1f2d4a"; g.lineWidth = 1; g.font = "10px sans-serif"; g.fillStyle = "#8aa0c4";
    for (let k = 0; k <= 4; k++) {
      const y = y0 + (y1 - y0) * k / 4; g.beginPath(); g.moveTo(pad.l, Y(y)); g.lineTo(W - pad.r, Y(y)); g.stroke();
      g.fillText(fmt(y, 3), 2, Y(y) + 3);
    }
    for (let k = 0; k <= 4; k++) { const x = x0 + (x1 - x0) * k / 4; g.fillText(fmt(x, 3), X(x) - 8, H - 4); }
    if (y0 < 0 && y1 > 0) { g.strokeStyle = "#37507a"; g.beginPath(); g.moveTo(pad.l, Y(0)); g.lineTo(W - pad.r, Y(0)); g.stroke(); }
    for (const s of series) {
      g.strokeStyle = s.color; g.lineWidth = 1.6; g.beginPath(); let first = true;
      for (const [x, y] of s.pts) { if (!isFinite(y)) { first = true; continue; } first ? g.moveTo(X(x), Y(y)) : g.lineTo(X(x), Y(y)); first = false; }
      g.stroke();
    }
    for (const m of o.marks || []) {
      g.strokeStyle = m.color || "#ffd54f"; g.setLineDash([3, 3]); g.beginPath(); g.moveTo(X(m.x), pad.t); g.lineTo(X(m.x), H - pad.b); g.stroke(); g.setLineDash([]);
      if (m.y != null) { g.fillStyle = m.color || "#ffd54f"; g.beginPath(); g.arc(X(m.x), Y(m.y), 3, 0, 7); g.fill(); }
      if (m.label) { g.fillStyle = m.color || "#ffd54f"; g.fillText(m.label, Math.min(X(m.x) + 3, W - 60), pad.t + 8); }
    }
    g.fillStyle = "#e6eefc"; g.font = "11px sans-serif"; g.fillText(o.title || "", pad.l, 11);
    if (o.legend) { let lx = W - pad.r; for (const s of series.slice().reverse()) { const w = g.measureText(s.name).width; lx -= w + 14; g.fillStyle = s.color; g.fillRect(lx, 4, 8, 8); g.fillText(s.name, lx + 10, 11); } }
  }
  function partsBounds(parts) {
    let m = new CAD.Mesh();
    const baked = Models.bake(parts);
    const mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
    for (const p of baked) { const b = p.mesh.bounds(); for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], b.min[k]); mx[k] = Math.max(mx[k], b.max[k]); } }
    m = null; return { min: mn, max: mx };
  }
  function exportParts(kind, parts, base) {
    const baked = Models.bake(parts);
    if (kind === "stl") return saveFile(`${base}.stl`, CAD.toSTLBinary(baked, base), "model/stl");
    if (kind === "obj") { saveFile(`${base}.obj`, CAD.toOBJ(baked, base).replace("mtllib parts.mtl", `mtllib ${base}.mtl`), "text/plain"); return setTimeout(() => saveFile(`${base}.mtl`, CAD.toMTL(baked), "text/plain"), 400); }
    if (kind === "dxf3") return saveFile(`${base}_3d.dxf`, CAD.toDXF3D(baked), "application/dxf");
  }

  // ------------------------------------------------------------ タブ
  const tabInit = {};
  function showTab(name) {
    $$("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
    $$(".tab").forEach((t) => t.classList.toggle("on", t.id === "tab-" + name));
    if (tabInit[name] && !tabInit[name].done) { tabInit[name].done = true; tabInit[name](); }
    window.dispatchEvent(new Event("resize"));
    try { localStorage.setItem("ct.tab", name); } catch (e) { /* ignore */ }
  }
  $$("#tabs button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));

  // ============================================================ ContactGPT
  let model = null;
  try { if (window.CT_WEIGHTS) model = GPTm.GPT.fromJSON(window.CT_WEIGHTS); } catch (e) { console.warn(e); }
  const bp0 = Phys.blueprint();
  const chat = new ChatM.Chat(EQS, model, bp0);

  function gptInfo() {
    const kv = model ? [
      ["構成", `${model.cfg.nLayer} 層 × ${model.cfg.nHead} ヘッド, d=${model.cfg.nEmbd}`],
      ["文脈長", `${model.cfg.block} 文字`], ["語彙", `${model.vocab.length} 文字`],
      ["パラメータ", model.nParams.toLocaleString()], ["学習ステップ", model.step.toLocaleString()],
    ] : [["状態", "重みなし (検索・即答のみ)"]];
    $("#gpt-info").innerHTML = kv.map(([k, v]) => `<div>${k}</div><div>${esc(v)}</div>`).join("");
  }
  function md(s) { return esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>"); }
  function eqHtml(e) {
    const tags = e.tags.map((t) => `<span class="tag">${GPTm.TAG_JA[t] || t}</span>`).join("");
    return `<div class="ref"><b>${esc(e.id)}</b> ${tags} <span class="st-${e.status}">${GPTm.STATUS_JA[e.status]}</span><br>${esc(e.expr)}${e.value ? `<br><span class="st-${e.status}">= ${esc(e.value)}</span>` : ""}</div>`;
  }
  function addMsg(html, cls) {
    const d = document.createElement("div"); d.className = "msg " + (cls || ""); d.innerHTML = html;
    $("#chat-log").appendChild(d); d.scrollIntoView({ block: "end" }); return d;
  }
  function ask(q) {
    addMsg(esc(q), "user");
    const pending = addMsg("…");
    setTimeout(() => {
      const r = chat.ask(q, { generate: $("#gpt-gen").checked && !!model, temperature: +$("#gpt-temp").value, seed: Date.now() });
      let h = r.answer.map(md).join("\n");
      if (r.error) h += `<div class="err">${esc(r.error)}</div>`;
      h += r.refs.map(eqHtml).join("");
      if (r.gen) h += `<div class="gen">${esc(r.gen)}</div>`;
      pending.innerHTML = h || "—";
      pending.scrollIntoView({ block: "end" });
    }, 20);
  }
  tabInit.chat = function () {
    gptInfo();
    addMsg(md("こんにちは、**ContactGPT** です。設計図書「異次元への輸送機」の全方程式 2111 本と設計パラメータで学習した小型 Transformer と、方程式検索・数式電卓を組み合わせて答えます。\n例: 「UFO.19」「ローレンツ因子は？」「Jones 結び目の共鳴」「計算 Z(11.7722)」"));
    const chips = ["ローレンツ因子 Γ は？", "Z(φ) とリーマン・ジーゲル", "Jones 結び目の共鳴", "反重力で上昇するには？", "部品の寸法", "UFO.24", "計算 gamma(0.5)^2", "計算 beta(2,3)", "多様体の式を見せて"];
    $("#chat-chips").innerHTML = chips.map((c) => `<button>${esc(c)}</button>`).join("");
    $$("#chat-chips button").forEach((b) => b.addEventListener("click", () => ask(b.textContent)));
    $("#chat-form").addEventListener("submit", (e) => { e.preventDefault(); const v = $("#chat-in").value.trim(); if (v) { ask(v); $("#chat-in").value = ""; } });
    $("#gpt-temp").addEventListener("input", () => { $("#gpt-temp-v").textContent = $("#gpt-temp").value; });
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
      const src = $("#gpt-src").textContent + "\n" + WORKER_MAIN;
      worker = new Worker(URL.createObjectURL(new Blob([src], { type: "text/javascript" })));
      const corpus = GPTm.buildCorpus(EQS, bp0);
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
            plot($("#loss-plot"), [{ pts: losses, color: "#4fc3f7" }], { title: "学習損失 (交差エントロピー)" });
          }
        } else if (m.type === "done") {
          model = GPTm.GPT.fromJSON(m.weights); chat.model = model; gptInfo();
          worker.terminate(); worker = null;
          $("#train-more").disabled = $("#train-scratch").disabled = false; $("#train-stop").disabled = true;
          toast("学習が完了しました"); try { localStorage.setItem("ct.weights", JSON.stringify(m.weights)); } catch (err) { /* 容量超過は無視 */ }
        }
      };
      worker.postMessage({
        cmd: "train", corpus, steps, batch: 6, lr: scratch ? 3e-3 : 1e-3,
        weights: scratch || !model ? null : model.toJSON(),
        cfg: { nLayer: 2, nHead: 4, nEmbd: 64, block: 64, seed: (Date.now() & 0xffff) },
      });
    }
    $("#train-more").addEventListener("click", () => train(false));
    $("#train-scratch").addEventListener("click", () => train(true));
    $("#train-stop").addEventListener("click", () => worker && worker.postMessage({ cmd: "stop" }));
    $("#gpt-save").addEventListener("click", () => model && saveFile("contactgpt_weights.json", JSON.stringify(model.toJSON()), "application/json"));
    $("#gpt-load").addEventListener("change", async (e) => {
      const f = e.target.files[0]; if (!f) return;
      try { model = GPTm.GPT.fromJSON(JSON.parse(await f.text())); chat.model = model; gptInfo(); toast("重みを読み込みました"); } catch (err) { toast("読み込み失敗: " + err.message); }
    });
    try { const w = localStorage.getItem("ct.weights"); if (w) { const m2 = GPTm.GPT.fromJSON(JSON.parse(w)); if (!model || m2.step > model.step) { model = m2; chat.model = m2; gptInfo(); } } } catch (e) { /* ignore */ }
  };

  // ============================================================ 輸送機 CAD
  tabInit.cad = function () {
    const view = new window.CTViewer($("#cad-view"));
    const P = {
      riderHours: 18, earthSeconds: 1, targetLy: 25.04, theta0Deg: 30, omegaOuterRpm: 1, podMass: 12000, timeScale: 1,
      ringOuter: 60.088, ringMid: 47.431, ringInner: 37.44, tube: 2.066, podR: 5.021, tower: 132.194, well: 38.8, coil31: 70.269, coil51: 56.215, coil41: 30,
    };
    const FIELDS = [
      ["riderHours", "搭乗者の時間 [h]", 0.1], ["earthSeconds", "地球の時間 [s]", 0.1], ["targetLy", "目的地 [ly] (ベガ)", 0.01],
      ["theta0Deg", "θ₀ [deg]", 1], ["omegaOuterRpm", "外環 回転 [rpm]", 0.1], ["podMass", "ポッド質量 [kg]", 100],
      ["timeScale", "アニメ速度 ×", 0.1],
      ["ringOuter", "外環 R [m]", 0.001], ["ringMid", "中環 R [m]", 0.001], ["ringInner", "内環 R [m]", 0.001], ["tube", "管径 [m]", 0.001],
      ["podR", "ポッド r [m]", 0.001], ["tower", "塔高 [m]", 0.001], ["well", "井戸深さ [m]", 0.001],
      ["coil31", "Jones 3_1 R [m]", 0.001], ["coil51", "Jones 5_1 R [m]", 0.001], ["coil41", "Jones 4_1 R [m]", 0.1],
    ];
    $("#cad-form").innerHTML = FIELDS.map(([k, l, st]) => `<label>${l}<input type="number" step="${st}" data-k="${k}" value="${P[k]}"></label>`).join("")
      + `<label class="full"><button id="cad-reset">設計図書の値に戻す</button></label>`;
    let bp, parts, t = 0, hidden = new Set();
    function compute() {
      bp = Phys.blueprint({
        riderHours: P.riderHours, earthSeconds: P.earthSeconds, targetLy: P.targetLy, theta0: P.theta0Deg * Math.PI / 180,
        omegaOuter: P.omegaOuterRpm * 2 * Math.PI / 60, podMass: P.podMass, podRadius: P.podR,
        dims: { ringOuter: P.ringOuter, ringMid: P.ringMid, ringInner: P.ringInner, tube: P.tube, podR: P.podR, tower: P.tower, well: P.well, coil31: P.coil31, coil51: P.coil51, coil41: P.coil41 },
      });
      const kv = [
        ["Γ", fmt(bp.Gamma)], ["1 − β", bp.oneMinusBeta.toExponential(5)], ["φ = arcosh Γ", fmt(bp.phi)],
        ["T|ψ|", fmt(bp.TPsi)], ["x log x = 1", fmt(bp.xlogxRoot)],
        ["収縮距離", bp.distKm.toExponential(4) + " km"], ["片道", fmt(bp.oneWayH, 5) + " h"],
        ["Θ", `${fmt(bp.Theta.re)} + ${fmt(bp.phi)}i`], ["ω 外/中/内", bp.omega.map((w) => fmt(w, 5)).join(", ") + " rad/s"],
        ["歳差 Ω", fmt(bp.Omega) + " rad/s"], ["θ(φ)", fmt(bp.rsTheta)], ["Z(φ)", fmt(bp.Z)],
      ];
      for (const k of Object.keys(bp.jones)) kv.push([`V_${k}(t*)`, bp.jones[k].str]);
      kv.push(["扉の軸 n̂", bp.doorAxis.map((v) => fmt(v, 5)).join(", ")]);
      $("#cad-calc").innerHTML = kv.map(([k, v]) => `<div>${k}</div><div>${esc(v)}</div>`).join("");
      // グラフ
      const zs = []; for (let x = 1; x <= 40; x += 0.1) zs.push([x, Phys.rsZ(x)]);
      plot($("#plot-z"), [{ pts: zs, color: "#4fc3f7", name: "Z(t)" }], { title: "臨界線上の Z(t) = e^{iθ(t)} ζ(½+it)", marks: [{ x: bp.phi, y: bp.Z, label: `φ → Z = ${fmt(bp.Z, 4)}` }] });
      const cols = { "3_1": "#ef5350", "4_1": "#66bb6a", "5_1": "#ab47bc" };
      plot($("#plot-j"), Object.keys(cols).map((k) => ({ name: k, color: cols[k], pts: Phys.resonanceMinima(k, 2).curve })), { title: "|V_K(e^{iα})| — 極小 = 扉の共鳴角", legend: true });
    }
    function build() {
      parts = Models.transporter(bp, t, { timeScale: P.timeScale });
      for (const p of parts) p.hidden = hidden.has(p.id);
      view.setParts(parts);
    }
    function partList() {
      const seen = new Map();
      for (const p of parts) { const g = p.id.replace(/[-\d]+$/, ""); if (!seen.has(g)) seen.set(g, p); }
      $("#cad-parts").innerHTML = Array.from(seen, ([g, p]) => `<label data-g="${g}"><input type="checkbox" ${hidden.has(p.id) ? "" : "checked"}><i style="background:${p.color}"></i>${esc(p.name.replace(/[-\d.=R ]+$/, "") || p.name)}</label>`).join("");
      $$("#cad-parts label").forEach((l) => {
        const g = l.dataset.g;
        l.querySelector("input").addEventListener("change", (e) => {
          for (const p of parts) if (p.id.replace(/[-\d]+$/, "") === g) { if (e.target.checked) hidden.delete(p.id); else hidden.add(p.id); }
          build();
        });
        l.addEventListener("mouseenter", () => { view.selected = g; view.draw(); });
        l.addEventListener("mouseleave", () => { view.selected = null; view.draw(); });
      });
    }
    function sheet(theme) {
      return Draft.sheet({
        parts: Models.bake(Models.transporter(bp, 0)), dims: Models.transporterDims(bp), theme,
        title: "CONTACT TRANSPORTER 異次元輸送機", number: "CT-TR-001",
        bom: [["1", "ジンバル外環", `R${bp.dims.ringOuter} 管径${bp.dims.tube}`, "1"], ["2", "ジンバル中環", `R${bp.dims.ringMid}`, "1"], ["3", "ジンバル内環", `R${bp.dims.ringInner}`, "1"],
          ["4", "ポッド", `r${bp.dims.podR}`, "1"], ["5", "塔・ガントリー", `H${bp.dims.tower}`, "1"], ["6", "Jones 3_1 コイル", `R${bp.dims.coil31}`, "1"],
          ["7", "Jones 5_1 コイル", `R${bp.dims.coil51}`, "1"], ["8", "Jones 4_1 コイル (床下)", `井戸 ${bp.dims.well}`, "1"], ["9", "扉の軸・共鳴窓", "n̂", "1"]],
        notes: [`Γ = ${fmt(bp.Gamma)}, φ = ${fmt(bp.phi)}, Z(φ) = ${fmt(bp.Z)}`, `ω = ${bp.omega.map((w) => fmt(w, 4)).join(" / ")} rad/s, Ω = ${fmt(bp.Omega, 5)} rad/s`,
          "論文の方程式に基づく思索的・フィクションの設計図 (幾何的な可視化) です。"],
      });
    }
    const refresh = debounce(() => { compute(); build(); partList(); }, 150);
    $$("#cad-form input").forEach((inp) => inp.addEventListener("input", () => { P[inp.dataset.k] = +inp.value; refresh(); }));
    $("#cad-reset").addEventListener("click", () => location.reload());
    compute(); build(); partList(); view.frame(partsBounds(parts));
    $$("#tab-cad [data-view]").forEach((b) => b.addEventListener("click", () => view.setView(b.dataset.view)));
    $("#cad-fit").addEventListener("click", () => view.frame(partsBounds(parts), true));
    $("#cad-wire").addEventListener("change", (e) => { view.wire = e.target.checked; view.draw(); });
    $("#cad-blue").addEventListener("change", (e) => { view.blueprint = e.target.checked; view.draw(); });
    $("#cad-grid").addEventListener("change", (e) => { view.showGrid = e.target.checked; view.draw(); });
    // HUD と回転アニメーション
    let last = performance.now();
    function tick(now) {
      const dt = Math.min(0.1, (now - last) / 1000); last = now;
      if ($("#cad-anim").checked && $("#tab-cad").classList.contains("on")) {
        t += dt; build();
        $("#cad-hud").textContent = `地球時間  t = ${t.toFixed(2)} s\n搭乗者    τ = ${(t * bp.Gamma / 3600).toFixed(3)} h  (Γ = ${fmt(bp.Gamma)})\n外環 ${fmt((bp.omega[0] * t * P.timeScale * 180 / Math.PI) % 360, 4)}°  中環 ${fmt(((bp.Theta.re + bp.omega[1] * t * P.timeScale) * 180 / Math.PI) % 360, 4)}°\nZ(φ) = ${fmt(bp.Z)}   n̂ = (${bp.doorAxis.map((v) => v.toFixed(3)).join(", ")})`;
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
    // 書き出し
    $$("#cad-export button").forEach((b) => b.addEventListener("click", async () => {
      const x = b.dataset.x;
      if (["stl", "obj", "dxf3"].includes(x)) return exportParts(x, Models.transporter(bp, 0), "contact_transporter");
      if (x === "png") return saveFile("contact_transporter.png", dataUrlToBlob(view.screenshot()), "image/png");
      if (x === "json") return saveFile("contact_transporter_params.json", JSON.stringify({ params: P, computed: { Gamma: bp.Gamma, phi: bp.phi, Z: bp.Z, rsTheta: bp.rsTheta, omega: bp.omega, Omega: bp.Omega, jones: Object.fromEntries(Object.entries(bp.jones).map(([k, j]) => [k, j.str])), doorAxis: bp.doorAxis } }, null, 2), "application/json");
      const s = sheet("blue");
      $("#cad-sheet").innerHTML = s.svg;
      if (x === "sheet") return saveFile("contact_transporter_drawing.svg", s.svg, "image/svg+xml");
      if (x === "sheetdxf") return saveFile("contact_transporter_drawing.dxf", s.dxf, "application/dxf");
    }));
    setTimeout(() => { $("#cad-sheet").innerHTML = sheet("blue").svg; }, 600);
  };

  // ============================================================ UFO 設計図面
  tabInit.ufo = function () {
    const view = new window.CTViewer($("#ufo-view"));
    const D = Models.UFO_DEFAULTS;
    let P = Object.assign({ number: "UFO-0001", author: "", mass: 12000, gain: 1 }, D);
    const PRESETS = {
      "標準円盤 01": {},
      "アダムスキー型": { name: "ADAMSKI-TYPE", diameter: 10, upperH: 1.6, lowerH: 1.0, rim: 0.4, domeD: 4.6, domeH: 2.6, windows: 6, legs: 3, engines: 3, legLen: 1.6, contactRing: false, mass: 3500 },
      "大型母船": { name: "MOTHERSHIP M-1", diameter: 60, upperH: 7, lowerH: 5, rim: 1.6, domeD: 18, domeH: 7, windows: 24, legs: 6, engines: 8, legLen: 6, coilKnot: "5_1", mass: 250000 },
      "コンタクト機": { name: "CONTACT CRAFT", diameter: 18, domeD: 7, domeH: 2.8, coilKnot: "4_1", contactRing: true, windows: 10, legs: 4, engines: 4, mass: 8000, hullColor: "#b0bec5", accent: "#4fc3f7" },
    };
    $("#ufo-presets").innerHTML = Object.keys(PRESETS).map((k) => `<button>${k}</button>`).join("");
    $$("#ufo-presets button").forEach((b) => b.addEventListener("click", () => { P = Object.assign({ number: P.number, author: P.author, gain: 1 }, D, PRESETS[b.textContent]); form(); update(true); }));
    const FIELDS = [
      ["name", "機体名", "text", "full"], ["number", "図番", "text"], ["author", "設計者", "text"],
      ["diameter", "直径 [m]", 0.1], ["rim", "縁の厚さ [m]", 0.05], ["upperH", "上殻高さ [m]", 0.05], ["lowerH", "下殻高さ [m]", 0.05],
      ["domeD", "ドーム直径 [m]", 0.1], ["domeH", "ドーム高さ [m]", 0.05], ["windows", "舷窓数", 1], ["engines", "推進ポッド数", 1],
      ["legs", "着陸脚数", 1], ["legLen", "脚長 [m]", 0.1], ["coilKnot", "反重力コイル", ["3_1", "4_1", "5_1"]], ["contactRing", "コンタクト・リング", "check"],
      ["hullColor", "船体色", "color"], ["domeColor", "ドーム色", "color"], ["accent", "アクセント色", "color"],
      ["mass", "質量 m [kg]", 100], ["gain", "反重力ゲイン", 0.05],
    ];
    function form() {
      $("#ufo-form").innerHTML = FIELDS.map(([k, l, t, cls]) => {
        if (Array.isArray(t)) return `<label>${l}<select data-k="${k}">${t.map((o) => `<option ${P[k] === o ? "selected" : ""}>${o}</option>`).join("")}</select></label>`;
        if (t === "check") return `<label class="chk"><input type="checkbox" data-k="${k}" ${P[k] ? "checked" : ""}> ${l}</label>`;
        if (t === "text" || t === "color") return `<label class="${cls || ""}">${l}<input type="${t}" data-k="${k}" value="${esc(P[k] || "")}"></label>`;
        return `<label>${l}<input type="number" step="${t}" data-k="${k}" value="${P[k]}"></label>`;
      }).join("");
      $$("#ufo-form [data-k]").forEach((el) => el.addEventListener(el.tagName === "SELECT" || el.type === "checkbox" ? "change" : "input", () => {
        const k = el.dataset.k;
        P[k] = el.type === "checkbox" ? el.checked : el.type === "number" ? +el.value : el.value;
        if (["windows", "legs", "engines"].includes(k)) P[k] = Math.max(0, Math.round(P[k]));
        update(false);
      }));
    }
    let parts = [], t = 0, lastSheet = null;
    function clampP() {
      P.diameter = Math.max(1, P.diameter); P.domeD = Math.min(Math.max(0.2, P.domeD), P.diameter * 0.9);
      P.rim = Math.max(0.02, P.rim); P.upperH = Math.max(P.rim / 2 + 0.05, P.upperH); P.lowerH = Math.max(P.rim / 2 + 0.05, P.lowerH);
    }
    const drawSheet = debounce(() => {
      const s = Draft.sheet({
        parts: Models.bake(Models.ufo(P, 0)), dims: Models.ufoDims(P), bom: Models.ufoBOM(P), theme: $("#ufo-theme").value, colorLines: $("#ufo-colorlines").checked,
        title: P.name, number: P.number, author: P.author || undefined,
        notes: flightNotes(),
      });
      lastSheet = s; $("#ufo-sheet").innerHTML = s.svg;
    }, 250);
    function flightNotes() {
      const U = Phys.ufo, tr = U.ascend(10, 1, P.gain).pop();
      return [`反重力 L = cosh(x log x) = ${fmt(U.L(0), 5)} (UFO.11)`, `a = (L−1)·g_eff·ゲイン = ${fmt(U.accel(0, P.gain), 5)} m/s² (UFO.19)`,
        `10 s 後: 高度 ${fmt(tr.h, 5)} m, v = ${fmt(tr.v, 5)} m/s (UFO.24)`, `質量 ${P.mass} kg, E_ag = ${Phys.ufo.Eag(P.mass, 0).toExponential(4)} J (UFO.13)`,
        "論文の方程式に基づく思索的・フィクションの設計図です。"];
    }
    function flight() {
      const U = Phys.ufo, tr = U.ascend(60, 1, P.gain), v10 = tr[10];
      const kv = [
        ["x = 1 + r₀/r", fmt(U.manifoldX(0))], ["L = cosh(x log x)", fmt(U.L(0))], ["L(1 km) / L(100 km)", `${fmt(U.L(1000))} / ${fmt(U.L(1e5))}`],
        ["g_eff", fmt(U.gEff(0), 5) + " m/s²"], ["a = (L−1)g·ゲイン", fmt(U.accel(0, P.gain), 5) + " m/s²"],
        ["U = GMm/r", U.Ugrav(P.mass, 0).toExponential(5) + " J"], ["E_ag = U·L", U.Eag(P.mass, 0).toExponential(5) + " J"],
        ["E⊥ = mc² − ½mv²", U.Eperp(P.mass, v10.v).toExponential(5) + " J"],
        ["10 s 後", `h = ${fmt(v10.h, 5)} m, v = ${fmt(v10.v, 5)} m/s`], ["60 s 後", `h = ${fmt(tr[60].h / 1000, 5)} km`],
      ];
      $("#ufo-flight").innerHTML = kv.map(([k, v]) => `<div>${k}</div><div>${esc(v)}</div>`).join("");
      plot($("#plot-ascent"), [{ pts: tr.map((p) => [p.t, p.h / 1000]), color: "#ff7043", name: "高度 km" }], { title: "上昇シミュレーション h(t) [km]  (半陰的オイラー, dt = 1 s)", marks: [{ x: 10, y: v10.h / 1000, label: `10 s: ${fmt(v10.h, 4)} m` }] });
    }
    function update(refit) {
      clampP();
      parts = Models.ufo(P, t); view.setParts(parts);
      if (refit) view.frame(partsBounds(parts));
      flight(); drawSheet();
    }
    form(); update(true);
    $$("#tab-ufo [data-view]").forEach((b) => b.addEventListener("click", () => view.setView(b.dataset.view)));
    $("#ufo-wire").addEventListener("change", (e) => { view.wire = e.target.checked; view.draw(); });
    $("#ufo-theme").addEventListener("change", drawSheet);
    $("#ufo-colorlines").addEventListener("change", drawSheet);
    let last = performance.now(), flyT = 0;
    function tick(now) {
      const dt = Math.min(0.1, (now - last) / 1000); last = now;
      if ($("#tab-ufo").classList.contains("on") && ($("#ufo-anim").checked || $("#ufo-fly").checked)) {
        if ($("#ufo-anim").checked) t += dt;
        parts = Models.ufo(P, t);
        if ($("#ufo-fly").checked) {
          flyT = (flyT + dt) % 8;
          // 表示は実高度の 1/20 (UFO.24 の上昇則)
          const h = Phys.ufo.ascend(Math.floor(flyT * 4), 0.25, P.gain).pop().h / 20;
          const M = CAD.m4.translate(0, 0, h);
          for (const p of parts) p.matrix = p.matrix ? CAD.m4.mul(M, p.matrix) : M;
        }
        view.setParts(parts);
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
    $$("#ufo-export button").forEach((b) => b.addEventListener("click", async () => {
      const x = b.dataset.x, base = (P.name || "ufo").replace(/[^\w\-]+/g, "_");
      if (["stl", "obj", "dxf3"].includes(x)) return exportParts(x, Models.ufo(P, 0), base);
      if (x === "save") return saveFile(`${base}.ufo.json`, JSON.stringify({ format: "bada-ufo-project-v1", params: P }, null, 2), "application/json");
      if (!lastSheet) return;
      if (x === "sheet") return saveFile(`${base}_drawing.svg`, lastSheet.svg, "image/svg+xml");
      if (x === "sheetdxf") return saveFile(`${base}_drawing.dxf`, lastSheet.dxf, "application/dxf");
      if (x === "sheetpng") return saveFile(`${base}_drawing.png`, await svgToPng(lastSheet.svg), "image/png");
    }));
    $("#ufo-load").addEventListener("change", async (e) => {
      const f = e.target.files[0]; if (!f) return;
      try { const j = JSON.parse(await f.text()); P = Object.assign({}, D, j.params || j); form(); update(true); toast("プロジェクトを読み込みました"); } catch (err) { toast("読み込み失敗: " + err.message); }
    });
  };

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
      rows = q ? chat.index.search(q, 400, f) : EQS.filter(f);
      render(true);
    }
    $("#eq-q").addEventListener("input", debounce(filter, 200));
    $("#eq-tag").addEventListener("change", filter);
    $("#eq-status").addEventListener("change", filter);
    $("#eq-more").addEventListener("click", () => render(false));
    filter();
    // タグ別の本数 (設計図書 第 3 章の棒グラフ)
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
  const B = window.CT_BUILD || {};
  $("#build-info").textContent = `build ${B.version || "dev"} ${B.date || ""}`;
  let first = "chat";
  try { first = localStorage.getItem("ct.tab") || "chat"; } catch (e) { /* ignore */ }
  showTab(tabInit[first] ? first : "chat");
})();
