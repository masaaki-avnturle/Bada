"use strict";

// ---- helpers -------------------------------------------------------------
const $ = (id) => document.getElementById(id);
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html != null) e.innerHTML = html;
  return e;
};
async function api(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(path + " -> " + r.status);
  return r.json();
}
const esc = (s) => String(s).replace(/[&<>"]/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// temperature -> 0..1 over a physiological window 34..41 C
const tnorm = (c) => Math.max(0, Math.min(1, (c - 34) / 7));

// ---- shared sensor bar (IR + thermometer attached to every view) ---------
function paintSensors(s) {
  if (!s) return;
  $("v-ir").textContent = s.ir.toFixed(2);
  $("v-th").textContent = s.thermo.toFixed(2);
  $("v-fu").textContent = s.fused.toFixed(2);
  $("v-en").textContent = s.energy.toFixed(2);
  $("m-ir").style.width = (tnorm(s.ir) * 100) + "%";
  $("m-th").style.width = (tnorm(s.thermo) * 100) + "%";
  $("m-fu").style.width = (tnorm(s.fused) * 100) + "%";
  $("m-en").style.width = Math.min(100, Math.abs(s.energy) * 2) + "%";
}

// ---- small canvas plot ---------------------------------------------------
function lineChart(canvas, pts, opt = {}) {
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.clientWidth, H = opt.h || 220;
  canvas.width = W * dpr; canvas.height = H * dpr;
  canvas.style.height = H + "px";
  const ctx = canvas.getContext("2d"); ctx.scale(dpr, dpr);
  const pad = 36;
  const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
  let minx = Math.min(...xs), maxx = Math.max(...xs);
  let miny = Math.min(0, ...ys), maxy = Math.max(...ys);
  if (maxy === miny) maxy = miny + 1;
  const X = x => pad + (x - minx) / (maxx - minx) * (W - pad - 12);
  const Y = y => H - pad - (y - miny) / (maxy - miny) * (H - pad - 14);
  ctx.strokeStyle = "#1d2838"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(pad, Y(0)); ctx.lineTo(W - 12, Y(0)); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(pad, 8); ctx.lineTo(pad, H - pad); ctx.stroke();
  ctx.fillStyle = "#7e8aa0"; ctx.font = "11px sans-serif";
  ctx.fillText(maxy.toFixed(2), 2, 14);
  ctx.fillText(miny.toFixed(2), 2, H - pad);
  ctx.fillText(opt.xlabel || "", W - 60, H - 10);
  ctx.strokeStyle = opt.color || "#40b8c0"; ctx.lineWidth = 2;
  ctx.beginPath();
  pts.forEach((p, i) => i ? ctx.lineTo(X(p.x), Y(p.y)) : ctx.moveTo(X(p.x), Y(p.y)));
  ctx.stroke();
  if (opt.fill) {
    ctx.lineTo(X(maxx), Y(0)); ctx.lineTo(X(minx), Y(0)); ctx.closePath();
    ctx.fillStyle = (opt.color || "#40b8c0") + "22"; ctx.fill();
  }
}

function bars(container, items, color = "linear-gradient(90deg,#4a80d0,#40b8c0)") {
  const max = Math.max(1e-9, ...items.map(i => i.v));
  items.forEach(it => {
    const row = el("div", "barrow");
    row.appendChild(el("span", "nm", esc(it.name)));
    const bw = el("div", "bw"); const fill = el("i");
    fill.style.width = (it.v / max * 100) + "%";
    fill.style.background = color; bw.appendChild(fill);
    row.appendChild(bw);
    row.appendChild(el("span", "vv mono", it.v.toFixed(4)));
    container.appendChild(row);
  });
}

// ---- views ---------------------------------------------------------------
const panel = $("panel");
function card(title, sub) {
  const c = el("div", "card");
  c.appendChild(el("h2", null, title));
  if (sub) c.appendChild(el("p", "sub", sub));
  return c;
}
function kpis(list) {
  const k = el("div", "kpi");
  list.forEach(([key, val]) => {
    const d = el("div");
    d.appendChild(el("span", "k", key));
    d.appendChild(el("span", "v", val));
    k.appendChild(d);
  });
  return k;
}

const views = {
  async pipeline() {
    const d = await api("/api/pipeline"); paintSensors(d.sensors);
    const c = card("統合パイプライン", "Γ熱 → センサー融合 → 大脳基底核 → 血液/DNA/RNA");
    c.appendChild(kpis([
      ["Γ熱エネルギー T'", d.sensors.energy.toFixed(3)],
      ["融合深部体温", d.sensors.fused.toFixed(2) + " °C"],
      ["末端総出力", d.peripheral.toFixed(3)],
      ["手 / 足", d.hand.toFixed(2) + " / " + d.foot.toFixed(2)],
      ["血液 異常項目", d.abnormal + " / " + d.markers],
      ["DNA長 / GC%", d.dna_len + " / " + (d.gc * 100).toFixed(1)],
    ]));
    c.appendChild(el("p", null, "翻訳ペプチド: <span class='peptide'>" + esc(d.peptide) + "</span>"));
    c.appendChild(el("p", "sub",
      "全画面上部のセンサーバーに赤外線センサーと温度計の現在値を常時表示しています。"));
    panel.replaceChildren(c);
  },

  async gamma() {
    const c = card("Γ 熱多様体", "T' = &int; &Gamma;(&gamma;)' dx<sub>m</sub> &nbsp; (&Gamma;'(g)=&Gamma;(g)&psi;(g))");
    const ctl = el("div", "controls");
    ctl.innerHTML =
      "<label>下限 lo<input id='glo' type='number' step='0.1' value='1'></label>" +
      "<label>上限 hi<input id='ghi' type='number' step='0.1' value='5'></label>" +
      "<label>分割 steps<input id='gst' type='number' value='2000'></label>";
    const btn = el("button", null, "計算");
    ctl.appendChild((() => { const w = el("label"); w.appendChild(el("span", null, "&nbsp;")); w.appendChild(btn); return w; })());
    c.appendChild(ctl);
    const k = el("div"); const cv = el("canvas"); c.appendChild(k); c.appendChild(cv);
    panel.replaceChildren(c);
    async function run() {
      const q = `?lo=${$("glo").value}&hi=${$("ghi").value}&steps=${$("gst").value}`;
      const d = await api("/api/gamma" + q); paintSensors(d.sensors);
      k.replaceChildren(kpis([
        ["T' = &int;&Gamma;' dx", d.energy.toFixed(6)],
        ["対応深部体温", d.temp.toFixed(3) + " °C"],
        ["区間", `[${d.lo}, ${d.hi}]`],
      ]));
      lineChart(cv, d.curve.map(p => ({ x: p.g, y: p.gp })),
        { color: "#c8a44a", fill: true, xlabel: "γ", h: 240 });
    }
    btn.onclick = run; run();
  },

  async basal() {
    const c = card("大脳基底核 エネルギー流", "直接路 / 間接路 / SNc ドーパミン → 視床 → 体末端");
    const ctl = el("div", "controls");
    ctl.innerHTML =
      "<label>入力 E<input id='bE' type='number' step='1' value='23'></label>" +
      "<label>ドーパミン<input id='bD' type='number' step='0.05' min='0' max='1' value='0.6'></label>";
    const btn = el("button", null, "伝播");
    const wrap = el("label"); wrap.appendChild(el("span", null, "&nbsp;")); wrap.appendChild(btn);
    ctl.appendChild(wrap); c.appendChild(ctl);
    const nuc = el("div"); const seg = el("div");
    c.appendChild(el("h2", null, "核")); c.appendChild(nuc);
    c.appendChild(el("h2", null, "脳 → 体末端")); c.appendChild(seg);
    panel.replaceChildren(c);
    async function run() {
      const d = await api(`/api/basal?E=${$("bE").value}&dopamine=${$("bD").value}`);
      paintSensors(d.sensors);
      nuc.replaceChildren(); seg.replaceChildren();
      bars(nuc, d.nuclei, "linear-gradient(90deg,#9060d0,#4a80d0)");
      bars(seg, d.segments, "linear-gradient(90deg,#4a80d0,#40b8c0)");
    }
    btn.onclick = run; run();
  },

  async sensor() {
    const c = card("赤外線センサー + 温度計", "Stefan–Boltzmann εσT⁴ / 接触一次遅れ / 逆分散融合");
    const ctl = el("div", "controls");
    ctl.innerHTML =
      "<label>真の温度 °C<input id='sT' type='number' step='0.1' value='36.8'></label>" +
      "<label>放射率 ε<input id='sE' type='number' step='0.01' min='0' max='1' value='0.97'></label>";
    const btn = el("button", null, "測定"); const wr = el("label");
    wr.appendChild(el("span", null, "&nbsp;")); wr.appendChild(btn); ctl.appendChild(wr);
    c.appendChild(ctl);
    const cv = el("canvas"); c.appendChild(cv);
    panel.replaceChildren(c);
    async function run() {
      const d = await api(`/api/sensor?trueC=${$("sT").value}&emiss=${$("sE").value}`);
      paintSensors(d.sensors);
      // overlay IR / thermo / fused
      const dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = 240;
      cv.width = W * dpr; cv.height = H * dpr; cv.style.height = H + "px";
      const ctx = cv.getContext("2d"); ctx.scale(dpr, dpr);
      const ser = d.series, all = ser.flatMap(p => [p.ir, p.th, p.f]);
      let mn = Math.min(...all) - 0.1, mx = Math.max(...all) + 0.1;
      const X = i => 40 + i / (ser.length - 1) * (W - 52);
      const Y = v => H - 30 - (v - mn) / (mx - mn) * (H - 44);
      ctx.fillStyle = "#7e8aa0"; ctx.font = "11px sans-serif";
      ctx.fillText(mx.toFixed(2), 2, 14); ctx.fillText(mn.toFixed(2), 2, H - 30);
      const draw = (key, col) => {
        ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.beginPath();
        ser.forEach((p, i) => i ? ctx.lineTo(X(i), Y(p[key])) : ctx.moveTo(X(i), Y(p[key])));
        ctx.stroke();
      };
      draw("ir", "#e0604a"); draw("th", "#40b8c0"); draw("f", "#3fbf6f");
      ctx.fillStyle = "#e0604a"; ctx.fillText("IR", W - 120, 14);
      ctx.fillStyle = "#40b8c0"; ctx.fillText("Thermo", W - 90, 14);
      ctx.fillStyle = "#3fbf6f"; ctx.fillText("Fused", W - 40, 14);
    }
    btn.onclick = run; run();
  },

  async mri() {
    const c = card("MRI スピンエコー", "S = ρ(1−e^(−TR/T1))·e^(−TE/T2)");
    const ctl = el("div", "controls");
    ctl.innerHTML = "<label>組織<select id='mt'>" +
      ["gray", "white", "csf", "fat", "muscle", "blood"]
        .map(t => `<option>${t}</option>`).join("") + "</select></label>";
    const btn = el("button", null, "撮像"); const wr = el("label");
    wr.appendChild(el("span", null, "&nbsp;")); wr.appendChild(btn); ctl.appendChild(wr);
    c.appendChild(ctl);
    const k = el("div"); const grid = el("div"); c.appendChild(k); c.appendChild(grid);
    panel.replaceChildren(c);
    async function run() {
      const d = await api("/api/mri?tissue=" + $("mt").value); paintSensors(d.sensors);
      k.replaceChildren(kpis([["T1", d.t1 + " ms"], ["T2", d.t2 + " ms"]]));
      // signal heat-grid TR x TE
      const TRs = [...new Set(d.grid.map(g => g.tr))], TEs = [...new Set(d.grid.map(g => g.te))];
      let html = "<table><tr><th>TR\\TE</th>" + TEs.map(t => `<th>${t}ms</th>`).join("") + "</tr>";
      TRs.forEach(tr => {
        html += `<tr><th>${tr}ms</th>`;
        TEs.forEach(te => {
          const s = d.grid.find(g => g.tr === tr && g.te === te).s;
          const g = Math.round(s * 255);
          html += `<td class='num' style='background:rgb(${g},${Math.round(g*0.85)},${Math.round(g*0.55)});color:${s>0.5?'#000':'#ccc'}'>${s.toFixed(3)}</td>`;
        });
        html += "</tr>";
      });
      grid.innerHTML = html + "</table>";
    }
    btn.onclick = run; run();
  },

  async fmri() {
    const d = await api("/api/fmri"); paintSensors(d.sensors);
    const c = card("fMRI BOLD", "正準二重ガンマ HRF と神経活動の畳み込み");
    const cv = el("canvas"); c.appendChild(cv);
    panel.replaceChildren(c);
    lineChart(cv, d.series.map(p => ({ x: p.t, y: p.bold })),
      { color: "#4a80d0", fill: true, xlabel: "t (s)", h: 240 });
  },

  async topo() {
    const d = await api("/api/topo"); paintSensors(d.sensors);
    const c = card("脳トポグラフィ", "基底核線源 → 頭皮16電極 1/r² 投影");
    const cv = el("canvas"); cv.style.maxWidth = "420px"; c.appendChild(cv);
    panel.replaceChildren(c);
    const dpr = window.devicePixelRatio || 1, S = 400;
    cv.width = S * dpr; cv.height = S * dpr; cv.style.height = S + "px";
    const ctx = cv.getContext("2d"); ctx.scale(dpr, dpr);
    const cx = S / 2, cy = S / 2, R = S * 0.42;
    const max = Math.max(...d.electrodes.map(e => e.v));
    // interpolated scalp field
    const img = ctx.createImageData(S, S);
    for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
      const dx = x - cx, dy = y - cy, rr = Math.sqrt(dx * dx + dy * dy);
      const idx = (y * S + x) * 4;
      if (rr > R) { img.data[idx + 3] = 0; continue; }
      let num = 0, den = 0;
      d.electrodes.forEach(e => {
        const a = e.deg * Math.PI / 180;
        const ex = cx + R * Math.cos(a), ey = cy + R * Math.sin(a);
        const w = 1 / ((x - ex) ** 2 + (y - ey) ** 2 + 80);
        num += w * e.v; den += w;
      });
      const v = (num / den) / max;
      img.data[idx] = Math.round(40 + v * 215);
      img.data[idx + 1] = Math.round(60 + (1 - Math.abs(v - 0.5) * 2) * 120);
      img.data[idx + 2] = Math.round(220 - v * 180);
      img.data[idx + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    ctx.strokeStyle = "#1d2838"; ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7); ctx.stroke();
    d.electrodes.forEach(e => {
      const a = e.deg * Math.PI / 180;
      ctx.fillStyle = "#04060a"; ctx.beginPath();
      ctx.arc(cx + R * Math.cos(a), cy + R * Math.sin(a), 4, 0, 7); ctx.fill();
    });
  },

  async ct() {
    const d = await api("/api/ct"); paintSensors(d.sensors);
    const c = card("CT スキャン (脳 → 末端)", "Beer–Lambert 透過率と Hounsfield 値");
    c.appendChild(kpis([["パス透過率 I/I₀", d.transmission.toExponential(3)]]));
    let html = "<table><tr><th>層</th><th class='num'>μ (cm⁻¹)</th><th class='num'>厚み (cm)</th><th class='num'>HU</th></tr>";
    d.layers.forEach(l => {
      html += `<tr><td>${esc(l.name)}</td><td class='num'>${l.mu.toFixed(4)}</td><td class='num'>${l.thk.toFixed(2)}</td><td class='num'>${l.hu.toFixed(1)}</td></tr>`;
    });
    const t = el("div", null, html + "</table>"); c.appendChild(t);
    panel.replaceChildren(c);
  },

  async blood() {
    const d = await api("/api/blood"); paintSensors(d.sensors);
    const c = card("血液検査", "主要マーカーの基準範囲判定（体熱バイアス連動）");
    let html = "<table><tr><th>マーカー</th><th class='num'>値</th><th>単位</th><th>基準範囲</th><th>判定</th></tr>";
    d.markers.forEach(m => {
      html += `<tr><td>${esc(m.name)}</td><td class='num'>${m.value.toFixed(2)}</td><td>${esc(m.unit)}</td><td class='mono'>${m.lo}–${m.hi}</td><td class='flag-${m.flag}'>${m.flag}</td></tr>`;
    });
    c.appendChild(el("div", null, html + "</table>"));
    panel.replaceChildren(c);
  },

  async dna() {
    const c = card("DNA 解析", "長さ / 塩基組成 / GC含量 / 最頻 k-mer");
    const ctl = el("div", "controls");
    ctl.innerHTML = "<label style='flex:1'>配列 (A/C/G/T)<input id='dseq' style='width:100%' value='ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG'></label>";
    const btn = el("button", null, "解析"); const wr = el("label");
    wr.appendChild(el("span", null, "&nbsp;")); wr.appendChild(btn); ctl.appendChild(wr);
    c.appendChild(ctl);
    const out = el("div"); c.appendChild(out);
    panel.replaceChildren(c);
    async function run() {
      const d = await api("/api/dna?seq=" + encodeURIComponent($("dseq").value));
      paintSensors(d.sensors);
      out.replaceChildren(kpis([
        ["長さ", d.length], ["GC含量", (d.gc * 100).toFixed(1) + "%"],
        ["A/C/G/T", `${d.A}/${d.C}/${d.G}/${d.T}`],
        ["最頻 3-mer", d.kmer + " ×" + d.kmer_count],
        ["妥当性", d.valid ? "OK" : "不正文字"],
      ]));
    }
    btn.onclick = run; run();
  },

  async rna() {
    const c = card("RNA 解析", "転写 (T→U) と標準遺伝暗号による翻訳");
    const ctl = el("div", "controls");
    ctl.innerHTML = "<label style='flex:1'>DNA センス鎖<input id='rseq' style='width:100%' value='ATGGCCATTGTAATGGGCCGCTGA'></label>";
    const btn = el("button", null, "転写・翻訳"); const wr = el("label");
    wr.appendChild(el("span", null, "&nbsp;")); wr.appendChild(btn); ctl.appendChild(wr);
    c.appendChild(ctl);
    const out = el("div"); c.appendChild(out);
    panel.replaceChildren(c);
    async function run() {
      const d = await api("/api/rna?seq=" + encodeURIComponent($("rseq").value));
      paintSensors(d.sensors);
      out.innerHTML =
        `<p class='sub'>mRNA</p><p class='mono' style='word-break:break-all'>${esc(d.rna)}</p>` +
        `<p class='sub'>ペプチド (* = 終止)</p><p class='peptide'>${esc(d.peptide)}</p>`;
    }
    btn.onclick = run; run();
  },
};

// ---- tab wiring ----------------------------------------------------------
const TABS = [
  ["pipeline", "統合パイプライン"], ["gamma", "Γ熱多様体"],
  ["basal", "大脳基底核"], ["sensor", "赤外線+温度計"],
  ["mri", "MRI"], ["fmri", "fMRI"], ["topo", "脳トポグラフィ"],
  ["ct", "CTスキャン"], ["blood", "血液検査"], ["dna", "DNA"], ["rna", "RNA"],
];
let current = "pipeline";
function buildTabs() {
  const nav = $("tabs");
  TABS.forEach(([id, label]) => {
    const b = el("button", id === current ? "active" : null, label);
    b.onclick = () => { current = id; refreshTabs(); show(id); };
    nav.appendChild(b);
  });
}
function refreshTabs() {
  [...$("tabs").children].forEach((b, i) =>
    b.classList.toggle("active", TABS[i][0] === current));
}
async function show(id) {
  panel.replaceChildren(el("div", "loading", "読み込み中…"));
  try { await views[id](); }
  catch (e) { panel.replaceChildren(el("div", "loading", "エラー: " + esc(e.message))); }
}

// live sensor polling (independent of active tab)
async function pollSensors() {
  if (!$("live").checked) return;
  try { const d = await api("/api/sensor"); paintSensors(d.sensors); } catch (e) {}
}
buildTabs();
show(current);
setInterval(pollSensors, 2000);
