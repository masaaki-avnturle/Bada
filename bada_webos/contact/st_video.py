"""System-transport video — the equation group of the reports (system_transport,
quantum_computer4, caostics, port directory) analysed with the Contact-Machine
principle, and the transport machine built from the surviving equations.

Everything numeric comes from apps/system_transport/system_transport_video.bada
running on the Bada VM (values, verdicts, every vertex of every frame); the
player below only projects, interpolates between Bada frames, and strokes.

    python3 -m contact.st_video [outdir] [--no-mp4]
"""

from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stdout

from . import bridge
from .video import record_mp4
from bada import load_program, run_source

ST_APP = os.path.join(os.path.dirname(os.path.dirname(bridge.APP)),
                      "system_transport", "system_transport_video.bada")


def run_stream() -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(load_program(ST_APP))
    return buf.getvalue()


def _floats(s: str) -> list[float]:
    return [float(t) for t in s.split()]


def parse_stream(text: str) -> dict:
    cards, sites, parts, frames = [], [], {}, {}
    order = []
    for line in text.splitlines():
        if line.startswith("CARD§"):
            f = line.split("§")
            cards.append(dict(zip(["id", "src", "title", "eq", "result", "verdict", "comp"], f[1:8])))
        elif line.startswith("SITE "):
            t = line.split()
            sites.append({"k": int(t[1]), "geom": t[2], "comp": t[3], "x": float(t[4]), "y": float(t[5])})
        elif line.startswith("PART "):
            head, _, edges = line.partition(" | ")
            t = head.split()
            e = [int(x) for x in edges.split()]
            parts[t[1]] = {"name": t[1], "static": t[2] == "1", "site": int(t[3]), "n": int(t[4]),
                           "e": [e[i:i + 2] for i in range(0, len(e), 2)]}
            order.append(t[1])
        elif line.startswith("SV "):
            head, _, v = line.partition(" | ")
            parts[head.split()[1]]["v"] = _floats(v)
        elif line.startswith("FH "):
            t = line.split()
            keys = ["tau", "th0", "th1", "th2", "zpod", "tpod", "alpha", "rricci", "bloch", "mobu", "zetat"]
            frames[int(t[1])] = {"h": dict(zip(keys, (float(x) for x in t[2:]))), "p": {}}
        elif line.startswith("FV "):
            head, _, v = line.partition(" | ")
            t = head.split()
            frames[int(t[1])]["p"][t[2]] = _floats(v)
    return {"cards": cards, "sites": sites, "parts": [parts[n] for n in order],
            "frames": [frames[k] for k in sorted(frames)]}


def player_html(data: dict) -> str:
    return _PLAYER.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))


def build(outdir: str, mp4: bool = True, stream_text: str | None = None) -> dict:
    os.makedirs(outdir, exist_ok=True)
    text = stream_text if stream_text is not None else run_stream()
    data = parse_stream(text)
    paths = {"stream": os.path.join(outdir, "system_transport_stream.txt"),
             "html": os.path.join(outdir, "system_transport_video.html")}
    with open(paths["stream"], "w") as f:                # raw Bada output, for audit
        f.write(text)
    with open(paths["html"], "w") as f:
        f.write(player_html(data))
    if mp4:
        paths["mp4"] = record_mp4(paths["html"], os.path.join(outdir, "system_transport_video.mp4"))
    return paths


_PLAYER = r"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>System Transport Video</title>
<style>
html,body{margin:0;background:#050f1f;color:#dbeafe;font-family:system-ui,sans-serif}
main{max-width:1280px;margin:0 auto;padding:12px}
canvas{display:block;width:100%;aspect-ratio:16/9;background:#050f1f}
.bar{display:flex;gap:10px;align-items:center;padding:8px 0}
button{background:#1e3a5f;color:#dbeafe;border:1px solid #3b6ea5;border-radius:6px;padding:6px 14px;font-size:14px}
input[type=range]{flex:1}
</style></head><body><main>
<canvas id="c" width="1280" height="720"></canvas>
<div class="bar"><button id="pp">⏸</button><input id="sk" type="range" min="0" max="1000" value="0"><span id="tt">0.0s</span></div>
</main>
<script>
const D = __DATA__;
const W = 1280, H = 720;
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const FONT = '"DejaVu Sans","WenQuanYi Zen Hei",system-ui,sans-serif';
const MONO = '"DejaVu Sans Mono","WenQuanYi Zen Hei",ui-monospace,monospace';
const VCOL = {'VERIFIED':'#34d399', 'CONDITIONAL':'#fbbf24', 'NOT VERIFIED':'#f87171'};
const COL = {gantry:'#94a3b8', ring_precession:'#fbbf24', ring_nutation:'#60a5fa', ring_spin:'#34d399', pod:'#f472b6',
  ads5_throat:'#818cf8', kk_torus:'#22d3ee', gauss_bell:'#a3e635', hopf_fibres:'#38bdf8', cell600:'#e879f9',
  mobius:'#fb923c', mobius_normal:'#fde047', ricci_sphere:'#f87171', paraboloid:'#2dd4bf', bloch_sphere:'#93c5fd',
  bloch_arrow:'#fde047', tetra:'#c4b5fd', zeta_curve:'#facc15', zeta_zeros:'#f472b6', zeta_runner:'#ffffff'};
const INFO = {
  gantry:['E21','drop gantry  legs 1.15R, top hub + 1.6R','ガントリー'],
  ring_precession:['E01','x₀(t) = hub + R_z(φ_d) R_z(θ₀) R_y(π/2) r₀(cos t, sin t, 0),  r₀ = R Γ(½)/(Γ(1)Γ(½))','歳差リング'],
  ring_nutation:['E22','x₁(t) = hub + R_z(φ_d) R_x(θ₁) R_x(π/2) r₁(cos t, sin t, 0),  ω₁ = |V(e^{iπ})| = 3','章動リング'],
  ring_spin:['E03','x₂(t) = hub + R_z(φ_d) R_y(θ₂) r₂(cos t, sin t, 0),  e^{iθ} = cos θ + i sin θ','自転リング'],
  pod:['E21','x(ϑ,ϕ) = (r sinϑ cosϕ, r sinϑ sinϕ, z_pod + r cosϑ)','ポッド'],
  ads5_throat:['E09','ρ(z) = 12 · e^{−2πT|ψ|},  T = (z_top − z)/z_top,  |ψ| = 0.31','AdS5 スロート'],
  kk_torus:['E08','((22 + φ cos v) cos u, (22 + φ cos v) sin u, hub + φ sin v),  φ = 2.5','カルツァ・クライン円環'],
  gauss_bell:['E23','z = 8 e^{−(x²+y²)/16}   (∫∫ e^{−x²−y²} = π)','ガウス積分の鐘'],
  hopf_fibres:['E11','{ e^{αu} q : α ∈ [0,2π) } → 12 fibres of S³ (Seifert / Hopf)','ホップ・ファイバー'],
  cell600:['E12','⟨β, θ | β⁵ = (βθ)² = θ³⟩ → 120 unit quaternions, 720 edges','600胞体'],
  mobius:['E10','((7 + v w cos u/2) cos u, (7 + v w cos u/2) sin u, v w sin u/2)','メビウスの帯'],
  mobius_normal:['E10','n(u) transported once around:  n(2π)·n(0) = −1','法線ベクトル'],
  ricci_sphere:['E06','∂g/∂t = −2 Ric  →  r(t) = √(r₀² − 4t)','リッチ流の球'],
  paraboloid:['E15','f(r) = ¼ |r|²   (Δf = 1)','重力井戸'],
  bloch_sphere:['E14','Bloch sphere of Ĥ = σ_z','ブロッホ球'],
  bloch_arrow:['E14','⟨σ⟩(t) from Â(t) = e^{iĤt} Â e^{−iĤt}','歳差ベクトル'],
  tetra:['E13','a₀a₁a₂a₃ :  4 − 6 + 4 − 1 = 1 ,  ∂ : 4 − 6 + 4 = 2','四面体'],
  zeta_curve:['E20','(3 Re ζ(½+it), 3 Im ζ(½+it), 0.6 t),  0.5 ≤ t ≤ 50','ゼータ曲線'],
  zeta_zeros:['E20','ζ(½ + iγ_n) = 0 : crossings of the axis','ゼータ零点'],
  zeta_runner:['E20','point ζ(½ + it) running along the curve','走査点']
};
const P = {}; D.parts.forEach(p => P[p.name] = p);
const cardOf = {}; D.cards.forEach(c => cardOf[c.id] = c);
const tally = {'VERIFIED':0,'CONDITIONAL':0,'NOT VERIFIED':0}; D.cards.forEach(c => tally[c.verdict]++);

// ---- timeline
const T_TITLE = 5, T_ENUM = 12, T_CARD = 3.6;
const T_ENUM0 = T_TITLE, T_CARDS0 = T_ENUM0 + T_ENUM, T_BUILD0 = T_CARDS0 + D.cards.length * T_CARD;
const siteCenter = k => k < 0 ? [0, 0, 22] : [D.sites[k].x, D.sites[k].y, 10];
const BUILD = [];                 // [partName, duration, focusSite]
['gantry','ring_precession','ring_nutation','ring_spin','pod','ads5_throat','kk_torus'].forEach(n => BUILD.push(n));
['gauss_bell','hopf_fibres','cell600','mobius','mobius_normal','ricci_sphere','paraboloid','bloch_sphere','bloch_arrow','tetra','zeta_curve','zeta_zeros','zeta_runner'].forEach(n => BUILD.push(n));
let acc = T_BUILD0;
const BSTEPS = BUILD.map(n => { const p = P[n]; const d = Math.max(1.4, Math.min(3.6, p.e.length / 120 + 1.2)); const s = { name: n, t0: acc, dur: d, site: p.site }; acc += d; return s; });
const T_OP0 = acc + 1, T_OP = 22, T_END0 = T_OP0 + T_OP, DURATION = T_END0 + 7;
window.DURATION = DURATION;

const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ease = x => x * x * (3 - 2 * x);
const lerp = (a, b, u) => a + (b - a) * u;

// ---- geometry access: static verts, or interpolated Bada frames
function frameVerts(name, u) {
  const p = P[name]; if (p.static) return p.v;
  const F = D.frames, x = clamp(u, 0, 1) * (F.length - 1), i = Math.floor(x), j = Math.min(i + 1, F.length - 1), f = x - i;
  const a = F[i].p[name], b = F[j].p[name]; if (f === 0) return a;
  const out = new Array(a.length); for (let k = 0; k < a.length; k++) out[k] = a[k] + (b[k] - a[k]) * f; return out;
}
function frameHead(u) {
  const F = D.frames, x = clamp(u, 0, 1) * (F.length - 1), i = Math.floor(x), j = Math.min(i + 1, F.length - 1), f = x - i, o = {};
  for (const k in F[i].h) o[k] = lerp(F[i].h[k], F[j].h[k], f); return o;
}
// ---- camera
function camera(target, dist, yaw, pitch, cx) {
  cx = cx === undefined ? W * 0.62 : cx;
  const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
  return v => {
    const x = v[0] - target[0], y = v[1] - target[1], z = v[2] - target[2];
    const x1 = cy * x - sy * y, y1 = sy * x + cy * y;
    const y2 = cp * y1 - sp * z, z2 = sp * y1 + cp * z;
    const f = 620 / (dist + y2);
    return [cx + x1 * f, H * 0.55 - z2 * f, dist + y2];
  };
}
function strokePart(name, verts, cam, nEdges, alpha) {
  const p = P[name]; const ne = nEdges === undefined ? p.e.length : nEdges; let pen = null;
  ctx.globalAlpha = alpha === undefined ? 1 : alpha;
  ctx.strokeStyle = COL[name] || '#fff'; ctx.lineWidth = (name === 'bloch_arrow' || name === 'mobius_normal' || name === 'zeta_runner') ? 3 : 1.4;
  ctx.beginPath();
  for (let k = 0; k < ne; k++) {
    const a = p.e[k][0] * 3, b = p.e[k][1] * 3;
    const A = cam([verts[a], verts[a + 1], verts[a + 2]]), B = cam([verts[b], verts[b + 1], verts[b + 2]]);
    if (A[2] < 5 || B[2] < 5) continue;
    ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); pen = B;
  }
  ctx.stroke(); ctx.globalAlpha = 1; return pen;
}
function grid(cam, alpha) {
  ctx.strokeStyle = 'rgba(96,165,250,' + (0.10 * alpha) + ')'; ctx.lineWidth = 1; ctx.beginPath();
  for (let i = -80; i <= 80; i += 10) {
    let a = cam([i, -80, 0]), b = cam([i, 80, 0]); if (a[2] > 5 && b[2] > 5) { ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); }
    a = cam([-80, i, 0]); b = cam([80, i, 0]); if (a[2] > 5 && b[2] > 5) { ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); }
  }
  ctx.stroke();
  // port ring
  ctx.strokeStyle = 'rgba(96,165,250,' + (0.25 * alpha) + ')'; ctx.beginPath();
  for (let k = 0; k <= 64; k++) { const a = cam([62 * Math.cos(k * Math.PI / 32), 62 * Math.sin(k * Math.PI / 32), 0]); k ? ctx.lineTo(a[0], a[1]) : ctx.moveTo(a[0], a[1]); }
  ctx.stroke();
}
function siteLabels(cam, alpha) {
  ctx.globalAlpha = alpha;
  for (const s of D.sites) { const a = cam([s.x, s.y, -2]); if (a[2] < 5) continue; text(s.geom + '-PORT', a[0], a[1] + 16, 12, '#60a5fa', MONO, 'center'); }
  ctx.globalAlpha = 1;
}
function text(s, x, y, size, color, font, align) {
  ctx.font = size + 'px ' + (font || FONT); ctx.fillStyle = color || '#dbeafe'; ctx.textAlign = align || 'left'; ctx.fillText(s, x, y);
}
function fitText(s, x, y, size, color, font, maxW, align) {
  ctx.font = size + 'px ' + (font || FONT); const w = ctx.measureText(s).width;
  text(s, x, y, w > maxW ? Math.max(9, Math.floor(size * maxW / w)) : size, color, font, align);
}
function frameBg() {
  ctx.fillStyle = '#050f1f'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(96,165,250,0.3)'; ctx.lineWidth = 2; ctx.strokeRect(14, 14, W - 28, H - 28);
  text('SYSTEM TRANSPORT — equation group → transport machine  ·  computed by system_transport_video.bada (Bada VM)', 30, H - 26, 13, 'rgba(219,234,254,0.55)', MONO);
}
function stamp(v, x, y, size, a) {
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.rotate(-0.06);
  ctx.font = 'bold ' + size + 'px ' + MONO; const w = ctx.measureText(v).width;
  ctx.strokeStyle = VCOL[v]; ctx.lineWidth = 3; ctx.strokeRect(-10, -size - 6, w + 20, size + 16);
  ctx.fillStyle = VCOL[v]; ctx.textAlign = 'left'; ctx.fillText(v, 0, 0); ctx.restore();
}
// ---- the whole machine, all parts, at operation phase u
function drawAll(cam, u, alpha) {
  for (const p of D.parts) strokePart(p.name, frameVerts(p.name, u), cam, undefined, alpha);
}

function render(t) {
  frameBg();
  if (t < T_ENUM0) {                                               // ---- title
    const a = ease(clamp(t / 1.5, 0, 1)); ctx.globalAlpha = a;
    text('SYSTEM TRANSPORT', W / 2, 270, 64, '#fff', FONT, 'center');
    text('方程式群の列挙・解析と次元輸送機', W / 2, 330, 30, '#93c5fd', FONT, 'center');
    text(D.cards.length + ' equations  ·  system_transport / quantum_computer4 / caostics / port directory', W / 2, 380, 18, 'rgba(219,234,254,0.75)', MONO, 'center');
    text('every value, verdict and vertex is computed by a Bada program', W / 2, 410, 16, 'rgba(219,234,254,0.6)', MONO, 'center');
    ctx.globalAlpha = 1; return;
  }
  if (t < T_CARDS0) {                                              // ---- enumeration
    const lt = t - T_ENUM0;
    text('I. ENUMERATION — 方程式群の列挙', 40, 60, 24, '#fff');
    const n = D.cards.length, per = 7.0 / n;
    for (let i = 0; i < n; i++) {
      const c = D.cards[i], col = i < 13 ? 0 : 1, row = i < 13 ? i : i - 13;
      const x = 40 + col * 610, y = 110 + row * 42, a = clamp((lt - i * per) / 0.4, 0, 1);
      if (a <= 0) continue; ctx.globalAlpha = a;
      text(c.id, x, y, 15, '#60a5fa', MONO);
      fitText(c.title, x + 56, y, 15, '#dbeafe', FONT, 330);
      fitText(c.src, x + 56, y + 17, 11, 'rgba(219,234,254,0.5)', MONO, 330);
      const va = clamp((lt - 7.5 - i * (3 / n)) / 0.3, 0, 1);
      if (va > 0) { ctx.globalAlpha = va; text(c.verdict, x + 400, y + 4, 13, VCOL[c.verdict], MONO); }
      ctx.globalAlpha = 1;
    }
    if (lt > 10.5) {
      ctx.globalAlpha = ease(clamp((lt - 10.5) / 0.8, 0, 1));
      text('VERIFIED ' + tally['VERIFIED'] + '   CONDITIONAL ' + tally['CONDITIONAL'] + '   NOT VERIFIED ' + tally['NOT VERIFIED'], 40, 675, 17, '#fff', MONO);
      ctx.globalAlpha = 1;
    }
    return;
  }
  if (t < T_BUILD0) {                                              // ---- analysis cards
    const ci = Math.floor((t - T_CARDS0) / T_CARD), lt = (t - T_CARDS0) - ci * T_CARD, c = D.cards[ci];
    text('II. ANALYSIS', 40, 56, 16, '#60a5fa', MONO);
    for (let i = 0; i < D.cards.length; i++) {           // left index with verdict dots
      const y = 86 + i * 23.5, done = i < ci, cur = i === ci;
      ctx.fillStyle = done ? VCOL[D.cards[i].verdict] : (cur ? '#fff' : 'rgba(96,165,250,0.25)');
      ctx.beginPath(); ctx.arc(46, y - 4, 4, 0, 7); ctx.fill();
      fitText(D.cards[i].id + ' ' + D.cards[i].title, 58, y, 12, cur ? '#fff' : (done ? 'rgba(219,234,254,0.65)' : 'rgba(219,234,254,0.3)'), FONT, 250);
    }
    const x0 = 340, mw = W - x0 - 50;
    text(c.id + '   ' + c.src, x0, 110, 16, '#60a5fa', MONO);
    fitText(c.title, x0, 160, 30, '#fff', FONT, mw);
    const nch = Math.floor(clamp(lt / 1.1, 0, 1) * c.eq.length);
    ctx.font = '26px ' + MONO; const es = Math.min(26, Math.floor(26 * mw / ctx.measureText(c.eq).width));
    text(c.eq.slice(0, nch) + (lt < 1.1 && Math.floor(lt * 6) % 2 ? '▌' : ''), x0, 250, es, '#93c5fd', MONO);
    if (lt > 1.2) {
      ctx.globalAlpha = ease(clamp((lt - 1.2) / 0.5, 0, 1));
      text('Bada ⟶', x0, 330, 16, '#34d399', MONO);
      fitText(c.result, x0, 368, 19, '#fde68a', MONO, mw);
      ctx.globalAlpha = 1;
    }
    if (lt > 2.0) stamp(c.verdict, x0 + 10, 470, 30, ease(clamp((lt - 2.0) / 0.3, 0, 1)));
    if (lt > 2.4) { ctx.globalAlpha = ease(clamp((lt - 2.4) / 0.4, 0, 1)); fitText('→ component: ' + c.comp, x0, 560, 20, c.comp[0] === '—' ? 'rgba(219,234,254,0.5)' : '#fff', FONT, mw); ctx.globalAlpha = 1; }
    for (let i = 0; i < D.cards.length; i++) { ctx.fillStyle = i <= ci ? '#60a5fa' : 'rgba(96,165,250,0.2)'; ctx.fillRect(x0 + i * 34, 640, 28, 4); }
    return;
  }
  if (t < T_OP0) {                                                 // ---- construction
    let si = 0; while (si < BSTEPS.length - 1 && t >= BSTEPS[si + 1].t0) si++;
    const st = BSTEPS[si], frac = clamp((t - st.t0) / st.dur, 0, 1);
    // camera eases from previous focus to this one during the first 35 % of the step
    const prev = si > 0 ? siteCenter(BSTEPS[si - 1].site) : [0, 0, 22], cur = siteCenter(st.site);
    const m = ease(clamp(frac / 0.35, 0, 1)), tgt = [lerp(prev[0], cur[0], m), lerp(prev[1], cur[1], m), lerp(prev[2], cur[2], m)];
    const yawOf = i => { const b = BSTEPS[i]; if (b.site < 0) return 0.55 + 0.02 * (b.t0 - T_BUILD0);
      const sc = D.sites[b.site]; return -Math.PI / 2 - Math.atan2(sc.y, sc.x) + 0.3; };
    let y0 = si > 0 ? yawOf(si - 1) : yawOf(0), y1 = yawOf(si);
    while (y1 - y0 > Math.PI) y1 -= 2 * Math.PI; while (y1 - y0 < -Math.PI) y1 += 2 * Math.PI;
    const dPrev = si > 0 && BSTEPS[si - 1].site >= 0 ? 55 : 120, dCur = st.site >= 0 ? 55 : 120;
    const cam = camera(tgt, lerp(dPrev, dCur, m), lerp(y0, y1, m) + 0.015 * (t - st.t0), 0.36);
    grid(cam, 1); siteLabels(cam, 0.8);
    for (let i = 0; i < si; i++) strokePart(BSTEPS[i].name, frameVerts(BSTEPS[i].name, 0), cam, undefined, 0.55);
    const pen = strokePart(st.name, frameVerts(st.name, 0), cam, Math.round(frac * P[st.name].e.length), 1);
    if (pen && frac < 1) { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(pen[0], pen[1], 5, 0, 7); ctx.fill(); }
    const inf = INFO[st.name];
    text('III. CONSTRUCTION  ' + (si + 1) + '/' + BSTEPS.length, 40, 56, 16, '#60a5fa', MONO);
    text(inf[2] + '  (' + st.name + ')', 40, 92, 24, COL[st.name]);
    fitText(inf[0] + ' · ' + cardOf[inf[0]].eq, 40, 124, 16, '#93c5fd', MONO, W - 80);
    fitText(inf[1], 40, 150, 15, '#fde68a', MONO, W - 80);
    text('edges ' + Math.round(frac * P[st.name].e.length) + ' / ' + P[st.name].e.length + (st.site >= 0 ? '   ·   ' + D.sites[st.site].geom + '-PORT' : '   ·   core'), 40, 176, 14, 'rgba(219,234,254,0.7)', MONO);
    return;
  }
  if (t < T_END0) {                                                // ---- operation
    const lt = t - T_OP0, u = clamp((lt - 1) / (T_OP - 3), 0, 1), h = frameHead(u);
    const cam = camera([0, 0, 18], 150 - 25 * ease(clamp(lt / T_OP, 0, 1)), 0.9 + 0.045 * lt, 0.42);
    grid(cam, 1); siteLabels(cam, 1); drawAll(cam, u, 1);
    const hms = s => { s = Math.round(s); const hh = Math.floor(s / 3600), mm = Math.floor(s % 3600 / 60); return hh + 'h ' + String(mm).padStart(2, '0') + 'm ' + String(s % 60).padStart(2, '0') + 's'; };
    text('IV. OPERATION', 40, 56, 16, '#60a5fa', MONO);
    const rows = [
      ['τ', h.tau.toFixed(3), '#fff'], ['θ₀ θ₁ θ₂', h.th0.toFixed(2) + '  ' + h.th1.toFixed(2) + '  ' + h.th2.toFixed(2), '#fbbf24'],
      ['z_pod', h.zpod.toFixed(2) + ' m', '#f472b6'], ['600-cell  α = φτ', h.alpha.toFixed(3) + ' rad', '#e879f9'],
      ['Ricci  r = √(49 − 4t)', h.rricci.toFixed(3), '#f87171'], ['Bloch  ωt', h.bloch.toFixed(3) + ' rad', '#fde047'],
      ['Möbius  u', h.mobu.toFixed(3) + ' rad', '#fb923c'], ['ζ(½+it)  t', h.zetat.toFixed(2), '#facc15'],
      ['Earth clock', (h.tau).toFixed(3) + ' s', '#dbeafe'], ['Pod clock', hms(h.tpod), '#f472b6']];
    rows.forEach((r, i) => { text(r[0], 40, 96 + i * 30, 15, 'rgba(219,234,254,0.7)', MONO); text(r[1], 250, 96 + i * 30, 15, r[2], MONO); });
    return;
  }
  // ---- end card
  const a = ease(clamp((t - T_END0) / 1.2, 0, 1));
  const cam = camera([0, 0, 18], 150, 0.9 + 0.045 * T_OP + 0.03 * (t - T_END0), 0.42, W * 0.78);
  drawAll(cam, 1, 0.2); ctx.globalAlpha = a;
  text('TRANSPORT MACHINE COMPLETE', 60, 200, 40, '#fff');
  text(D.cards.length + ' equations analysed', 60, 250, 20, '#93c5fd', MONO);
  text('VERIFIED ' + tally['VERIFIED'], 60, 290, 20, VCOL['VERIFIED'], MONO);
  text('CONDITIONAL ' + tally['CONDITIONAL'], 60, 320, 20, VCOL['CONDITIONAL'], MONO);
  text('NOT VERIFIED ' + tally['NOT VERIFIED'], 60, 350, 20, VCOL['NOT VERIFIED'], MONO);
  let nv = 0; D.parts.forEach(p => nv += p.n);
  text(D.parts.length + ' parts · ' + nv + ' vertices · ' + D.frames.length + ' Bada frames', 60, 400, 16, 'rgba(219,234,254,0.8)', MONO);
  text('Only verified / conditional equations became components.', 60, 440, 15, 'rgba(219,234,254,0.7)', MONO);
  text('Design fiction: the numbers are exact, the physics reading is hypothetical.', 60, 464, 15, 'rgba(219,234,254,0.7)', MONO);
  ctx.globalAlpha = 1;
}
window.render = render;

if (!location.hash.includes('record')) {
  let t0 = performance.now(), paused = false, tp = 0;
  const pp = document.getElementById('pp'), sk = document.getElementById('sk'), tt = document.getElementById('tt');
  pp.onclick = () => { paused = !paused; pp.textContent = paused ? '▶' : '⏸'; t0 = performance.now() - tp * 1000; };
  sk.oninput = () => { tp = sk.value / 1000 * DURATION; t0 = performance.now() - tp * 1000; render(tp); };
  (function loop() {
    if (!paused) { tp = ((performance.now() - t0) / 1000) % DURATION; render(tp); sk.value = tp / DURATION * 1000; tt.textContent = tp.toFixed(1) + 's / ' + DURATION.toFixed(0) + 's'; }
    requestAnimationFrame(loop);
  })();
} else render(0);
</script></body></html>
"""


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "generated/st"
    for kind, path in build(out, mp4="--no-mp4" not in sys.argv).items():
        print(f"wrote {kind}: {path}")
