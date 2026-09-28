"""Blueprint video — the process of drawing the Contact Machine, rendered from
the equation stream that apps/contact/contact_video.bada computes on the Bada
VM.  Every equation value and every vertex of every frame comes from Bada; the
player only projects and strokes them.

    python3 -m contact.video [outdir]          # HTML player (+ MP4 if possible)

The HTML player is stdlib-only.  The MP4 needs Node Playwright (Chromium) and
an ffmpeg binary (FFMPEG env var, `ffmpeg` on PATH, or imageio-ffmpeg).
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
from contextlib import redirect_stdout

from . import bridge
from bada import load_program, run_source

VIDEO_APP = os.path.join(os.path.dirname(bridge.APP), "contact_video.bada")
RECORDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "record_video.js")


def run_stream() -> str:
    """Run contact_video.bada on the Bada VM and return its stream text."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(load_program(VIDEO_APP))
    return buf.getvalue()


def parse_stream(text: str) -> dict:
    cards, parts, frames = [], [], []
    for line in text.splitlines():
        if line.startswith("CARD|"):
            _, title, eq, value = line.split("|", 3)
            cards.append({"title": title, "eq": eq, "value": value})
        elif line.startswith("PART "):
            tok = line.split()
            ints = [int(t) for t in tok[3:]]
            parts.append({"name": tok[1], "n": int(tok[2]),
                          "e": [ints[i:i + 2] for i in range(0, len(ints), 2)]})
        elif line.startswith("FRAME "):
            head, _, body = line.partition(" | ")
            h = head.split()
            frames.append({"k": int(h[1]), "tau": float(h[2]),
                           "th": [float(h[3]), float(h[4]), float(h[5])],
                           "zpod": float(h[6]), "tpod": float(h[7]),
                           "xyz": [float(t) for t in body.split()]})
    return {"cards": cards, "parts": parts, "frames": frames}


def player_html(data: dict) -> str:
    return _PLAYER.replace("__DATA__", json.dumps(data, separators=(",", ":")))


def find_ffmpeg() -> str | None:
    if os.environ.get("FFMPEG"):
        return os.environ["FFMPEG"]
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg                        # optional
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def record_mp4(html_path: str, mp4_path: str, fps: int = 30) -> str:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("no ffmpeg found (set FFMPEG or pip install imageio-ffmpeg)")
    env = dict(os.environ)
    if "NODE_PATH" not in env:
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True)
        env["NODE_PATH"] = root.stdout.strip()
    subprocess.run(["node", RECORDER, os.path.abspath(html_path),
                    os.path.abspath(mp4_path), ffmpeg, str(fps)],
                   check=True, env=env)
    return mp4_path


def build(outdir: str, mp4: bool = True) -> dict:
    os.makedirs(outdir, exist_ok=True)
    data = parse_stream(run_stream())
    paths = {"html": os.path.join(outdir, "contact_blueprint_video.html")}
    with open(paths["html"], "w") as f:
        f.write(player_html(data))
    if mp4:
        paths["mp4"] = record_mp4(paths["html"],
                                  os.path.join(outdir, "contact_blueprint_video.mp4"))
    return paths


# --------------------------------------------------------------------- player
# Timeline (seconds): title 0-3 | equation cards 3-30 | drawing 30-46 |
# operation 46-57 | end card 57-61.   render(t) is deterministic in t so the
# recorder can step it frame by frame; in a browser it plays in real time.
_PLAYER = r"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Contact Blueprint Video</title>
<style>
html,body{margin:0;background:#06182e;color:#dbeafe;font-family:system-ui,sans-serif}
main{max-width:1280px;margin:0 auto;padding:12px}
canvas{display:block;width:100%;aspect-ratio:16/9;background:#06182e}
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
const COL = {ring_precession:'#fbbf24', ring_nutation:'#60a5fa', ring_spin:'#34d399', pod:'#f472b6', gantry:'#94a3b8'};
const FONT = '"DejaVu Sans","WenQuanYi Zen Hei",system-ui,sans-serif';
const MONO = '"DejaVu Sans Mono",ui-monospace,monospace';
const T_TITLE = 3, T_CARD = 3, T_CARDS_END = T_TITLE + D.cards.length * T_CARD;
const DRAW_DUR = [3, 3, 3, 4, 2];            // per part
const T_DRAW_END = T_CARDS_END + DRAW_DUR.reduce((a, b) => a + b, 0) + 1;
const T_OP = 9, T_OP_END = T_DRAW_END + T_OP + 2;
const DURATION = T_OP_END + 4;
window.DURATION = DURATION;

// part offsets into the flat vertex array
let off = 0; for (const p of D.parts) { p.off = off; off += p.n; }
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ease = x => x * x * (3 - 2 * x);

function vtx(frame, p, i) { const j = 3 * (p.off + i), a = frame.xyz; return [a[j], a[j + 1], a[j + 2]]; }
function projector(yaw, pitch, cx, cy, scale) {
  const zc = 25, cyw = Math.cos(yaw), syw = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
  return v => {
    const x = v[0], y = v[1], z = v[2] - zc;
    const x1 = cyw * x - syw * y, y1 = syw * x + cyw * y;
    const y2 = cp * y1 - sp * z, z2 = sp * y1 + cp * z;
    const f = 160 / (160 + y2);
    return [cx + x1 * scale * f, cy - z2 * scale * f];
  };
}
function grid(P) {
  ctx.strokeStyle = 'rgba(96,165,250,0.12)'; ctx.lineWidth = 1; ctx.beginPath();
  for (let i = -30; i <= 30; i += 5) {
    let a = P([i, -30, 0]), b = P([i, 30, 0]); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]);
    a = P([-30, i, 0]); b = P([30, i, 0]); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]);
  }
  ctx.stroke();
}
function drawParts(frame, P, upto) {       // upto: [partIndex, edgesDrawn] or null = all
  let pen = null;
  D.parts.forEach((p, pi) => {
    let ne = p.e.length;
    if (upto) { if (pi > upto[0]) return; if (pi === upto[0]) ne = upto[1]; }
    ctx.strokeStyle = COL[p.name] || '#fff'; ctx.lineWidth = 2; ctx.beginPath();
    for (let k = 0; k < ne; k++) {
      const a = P(vtx(frame, p, p.e[k][0])), b = P(vtx(frame, p, p.e[k][1]));
      ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); pen = b;
    }
    ctx.stroke();
  });
  return pen;
}
function text(s, x, y, size, color, font, align) {
  ctx.font = size + 'px ' + (font || FONT); ctx.fillStyle = color || '#dbeafe';
  ctx.textAlign = align || 'left'; ctx.fillText(s, x, y);
}
function fitText(s, x, y, size, color, font, maxW) {   // shrink to fit maxW
  ctx.font = size + 'px ' + (font || FONT);
  const w = ctx.measureText(s).width;
  text(s, x, y, w > maxW ? Math.floor(size * maxW / w) : size, color, font);
}
function blueprintFrame() {
  ctx.fillStyle = '#06182e'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(96,165,250,0.35)'; ctx.lineWidth = 2; ctx.strokeRect(16, 16, W - 32, H - 32);
  text('CONTACT MACHINE — BLUEPRINT  ·  generated by contact_video.bada (Bada VM)', 32, H - 28, 14, 'rgba(219,234,254,0.6)', MONO);
}
const PART_EQ = {
  ring_precession: 'x₀(t) = hub + R_z(φ_door) R_z(θ₀) R_y(π/2) · r₀(cos t, sin t, 0)',
  ring_nutation:   'x₁(t) = hub + R_z(φ_door) R_x(θ₁) R_x(π/2) · r₁(cos t, sin t, 0)',
  ring_spin:       'x₂(t) = hub + R_z(φ_door) R_y(θ₂) · r₂(cos t, sin t, 0)',
  pod:             'x(ϑ,ϕ) = (r sinϑ cosϕ, r sinϑ sinϕ, z_pod + r cosϑ)',
  gantry:          'legs (1.15R cos(πi/2+π/4), 1.15R sin(πi/2+π/4), 0 → hub + 1.6R)'
};
const PART_JA = {ring_precession:'歳差リング', ring_nutation:'章動リング', ring_spin:'自転リング', pod:'ポッド', gantry:'ガントリー'};

function render(t) {
  blueprintFrame();
  const F = D.frames;
  if (t < T_TITLE) {                                   // ---- title
    const a = ease(clamp(t / 1.2, 0, 1));
    ctx.globalAlpha = a;
    text('CONTACT', W / 2, 300, 72, '#fff', FONT, 'center');
    text('The Machine — 方程式から描く3D設計図', W / 2, 360, 28, '#93c5fd', FONT, 'center');
    text('every number and every vertex is computed by the Bada program', W / 2, 410, 18, 'rgba(219,234,254,0.7)', MONO, 'center');
    ctx.globalAlpha = 1; return;
  }
  if (t < T_CARDS_END) {                               // ---- equation cards (the primer)
    const ci = Math.floor((t - T_TITLE) / T_CARD), lt = (t - T_TITLE) - ci * T_CARD;
    // decoded stack on the left
    text('DECODED', 40, 60, 14, '#60a5fa', MONO);
    for (let i = 0; i < ci; i++) text(D.cards[i].title, 40, 90 + i * 26, 15, 'rgba(219,234,254,0.55)', FONT);
    const c = D.cards[ci];
    const x0 = 420;
    text(c.title, x0, 200, 30, '#fff');
    const nch = Math.floor(clamp(lt / 1.3, 0, 1) * c.eq.length);   // typing effect
    ctx.font = '26px ' + MONO;
    const eqSize = Math.min(26, Math.floor(26 * (W - x0 - 50) / ctx.measureText(c.eq).width));
    text(c.eq.slice(0, nch) + (lt < 1.3 && Math.floor(lt * 6) % 2 ? '▌' : ''), x0, 290, eqSize, '#93c5fd', MONO);
    if (lt > 1.5) {
      ctx.globalAlpha = ease(clamp((lt - 1.5) / 0.6, 0, 1));
      text('Bada ⟶', x0, 380, 18, '#34d399', MONO);
      fitText(c.value, x0, 420, 24, '#fde68a', MONO, W - x0 - 50);
      ctx.globalAlpha = 1;
    }
    // progress ticks
    for (let i = 0; i < D.cards.length; i++) {
      ctx.fillStyle = i <= ci ? '#60a5fa' : 'rgba(96,165,250,0.2)';
      ctx.fillRect(x0 + i * 44, 620, 36, 4);
    }
    return;
  }
  const f0 = F[0];
  if (t < T_DRAW_END) {                                // ---- drawing, stroke by stroke
    const lt = t - T_CARDS_END;
    let acc = 0, pi = 0;
    while (pi < DRAW_DUR.length - 1 && lt >= acc + DRAW_DUR[pi]) { acc += DRAW_DUR[pi]; pi++; }
    const frac = clamp((lt - acc) / DRAW_DUR[pi], 0, 1);
    const p = D.parts[pi], ne = Math.round(frac * p.e.length);
    const P = projector(0.5 + 0.03 * lt, 0.32, 820, 400, 7.2);
    grid(P);
    const pen = drawParts(f0, P, [pi, ne]);
    if (pen && frac < 1) { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(pen[0], pen[1], 5, 0, 7); ctx.fill(); }
    text('DRAWING  ' + (pi + 1) + '/' + D.parts.length + '  ' + PART_JA[p.name] + '  (' + p.name + ')', 40, 60, 20, COL[p.name]);
    fitText(PART_EQ[p.name], 40, 96, 17, '#93c5fd', MONO, W - 80);
    if (pi < 3) text('t = ' + (2 * Math.PI * frac).toFixed(3) + ' rad   r = ' + ['15', '7.5', '5.625'][pi] + ' m   θ = 0 (τ = 0)', 40, 126, 16, '#fde68a', MONO);
    else text('edges ' + ne + ' / ' + p.e.length, 40, 126, 16, '#fde68a', MONO);
    return;
  }
  if (t < T_OP_END) {                                  // ---- operation: rings spin, pod drops
    const lt = t - T_DRAW_END, u = clamp(lt / T_OP, 0, 1);
    const fr = F[Math.round(u * (F.length - 1))];
    const P = projector(0.5 + 0.03 * (T_DRAW_END - T_CARDS_END) + 0.05 * lt, 0.32, 820, 400, 7.2);
    grid(P); drawParts(fr, P, null);
    const hms = s => { s = Math.round(s); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60); return h + 'h ' + String(m).padStart(2, '0') + 'm ' + String(s % 60).padStart(2, '0') + 's'; };
    text('OPERATION   θ_k(τ) = ω_k · φ · τ ,   z_pod(τ) = hub + (1 − 2τ)·1.5R', 40, 60, 18, '#fff', MONO);
    text('τ = ' + fr.tau.toFixed(3), 40, 110, 22, '#fde68a', MONO);
    text('θ₀ = ' + fr.th[0].toFixed(3) + ' rad', 40, 150, 18, COL.ring_precession, MONO);
    text('θ₁ = ' + fr.th[1].toFixed(3) + ' rad', 40, 178, 18, COL.ring_nutation, MONO);
    text('θ₂ = ' + fr.th[2].toFixed(3) + ' rad', 40, 206, 18, COL.ring_spin, MONO);
    text('z_pod = ' + fr.zpod.toFixed(3) + ' m', 40, 234, 18, COL.pod, MONO);
    text('Earth clock  ' + fr.tau.toFixed(3) + ' s', 40, 300, 20, '#dbeafe', MONO);
    text('Pod clock    ' + hms(fr.tpod), 40, 330, 20, '#f472b6', MONO);
    text('t_pod = γ · t_earth ,  γ = 64800', 40, 360, 16, 'rgba(219,234,254,0.7)', MONO);
    return;
  }
  // ---- end card
  const a = ease(clamp((t - T_OP_END) / 1, 0, 1));
  const P = projector(0.9, 0.32, 1060, 400, 6.0);
  ctx.globalAlpha = 0.35; drawParts(F[F.length - 1], P, null); ctx.globalAlpha = a;
  text('BLUEPRINT COMPLETE', 80, 300, 44, '#fff');
  text(D.parts.length + ' parts  ·  ' + D.frames[0].xyz.length / 3 + ' vertices  ·  ' + D.frames.length + ' frames', 80, 350, 20, '#93c5fd', MONO);
  text('Design fiction: the numbers are exact,', 80, 400, 16, 'rgba(219,234,254,0.7)', MONO);
  text('the physics reading is hypothetical.', 80, 424, 16, 'rgba(219,234,254,0.7)', MONO);
  ctx.globalAlpha = 1;
}
window.render = render;

// real-time playback (disabled when the recorder drives render(t))
if (!location.hash.includes('record')) {
  let t0 = performance.now(), paused = false, tp = 0;
  const pp = document.getElementById('pp'), sk = document.getElementById('sk'), tt = document.getElementById('tt');
  pp.onclick = () => { paused = !paused; pp.textContent = paused ? '▶' : '⏸'; t0 = performance.now() - tp * 1000; };
  sk.oninput = () => { tp = sk.value / 1000 * DURATION; t0 = performance.now() - tp * 1000; render(tp); };
  (function loop() {
    if (!paused) { tp = ((performance.now() - t0) / 1000) % DURATION; render(tp); sk.value = tp / DURATION * 1000; tt.textContent = tp.toFixed(1) + 's'; }
    requestAnimationFrame(loop);
  })();
} else render(0);
</script></body></html>
"""


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "generated/contact"
    want_mp4 = "--no-mp4" not in sys.argv
    for kind, path in build(out, mp4=want_mp4).items():
        print(f"wrote {kind}: {path}")
