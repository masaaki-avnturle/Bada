"""Render the equation-group manifold frames as an ASCII flip-book animation
and as a browsable animated-HTML "video dictionary"."""

from __future__ import annotations

import json

# the dictionary: name -> (title, description)
CATALOG = {
    "eqgen": ("ζ/β equation generator",
              "O(x) = ζ(3) / Σ a_k f^k — the equation group rotating in t"),
    "fermat": ("Fermat complex manifold",
               "z = 1 − |x|ⁿ − |y|ⁿ, n = 2→4 (hypersurface deformation)"),
    "covariant": ("complex covariant integral manifold",
                  "a traveling-wave field (covariant integral), phase in t"),
    "trigbeta": ("trigonometric Beta function",
                 "Beta integrand sinᵖθ·cos²θ over [0,π], p = 1→4"),
    "abelian": ("Abelian manifold (complex torus)",
                "doubly-periodic surface displaced by the modular t"),
}

_RAMP = " .:-=+*#%@"


def ascii_animation(grids: list) -> list[str]:
    """One text frame per animation step (z mapped to a character ramp)."""
    lo = min(v for g in grids for row in g for v in row)
    hi = max(v for g in grids for row in g for v in row)
    span = (hi - lo) or 1.0
    out = []
    for g in grids:
        lines = []
        for row in g:
            s = "".join(
                _RAMP[min(len(_RAMP) - 1, int((v - lo) / span * (len(_RAMP) - 1)))]
                for v in row)
            lines.append(s)
        out.append("\n".join(lines))
    return out


def html_video(frames_by_name: dict, n: int) -> str:
    data = {name: [[[round(v, 3) for v in row] for row in g] for g in frames]
            for name, frames in frames_by_name.items()}
    meta = {name: {"title": CATALOG[name][0], "desc": CATALOG[name][1]}
            for name in frames_by_name}
    options = "".join(f'<option value="{nm}">{CATALOG[nm][0]}</option>'
                      for nm in frames_by_name)
    data_json = json.dumps(data)
    meta_json = json.dumps(meta)
    first = next(iter(frames_by_name))
    return _TEMPLATE.format(options=options, data=data_json, meta=meta_json,
                            n=n, first=first)


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<title>Equation-group 3D animation dictionary</title>
<style>
 body{{margin:0;background:#0b1020;color:#e8e8e8;font-family:monospace}}
 .bar{{padding:8px 12px;background:#161b2e;border-bottom:2px solid #c8a44a;
   display:flex;gap:14px;align-items:center}}
 .bar b{{color:#c8a44a}} select,button{{background:#222a44;color:#eee;
   border:1px solid #445;padding:4px 8px;font-family:monospace}}
 #desc{{padding:6px 12px;color:#9fb}} canvas{{display:block;margin:0 auto;
   background:#0b1020}} #cap{{text-align:center;color:#789;font-size:12px}}
</style></head><body>
<div class="bar"><b>📖 equation-group 3D video dictionary</b>
 <select id="pick">{options}</select>
 <button id="play">⏸ pause</button>
 <span id="frame"></span></div>
<div id="desc"></div>
<canvas id="cv" width="760" height="460"></canvas>
<div id="cap">isometric 3D surface · the manifold displaces over the animation</div>
<script>
const DATA={data}, META={meta}, N={n};
let name="{first}", fi=0, playing=true;
const cv=document.getElementById('cv'), ctx=cv.getContext('2d');
function range(frames){{let lo=1e9,hi=-1e9;for(const g of frames)for(const r of g)
 for(const v of r){{if(v<lo)lo=v;if(v>hi)hi=v;}}return[lo,hi||lo+1];}}
function proj(i,j,z){{const cell=15,ox=cv.width/2,oy=120,zs=70;
 return[ox+(i-j)*cell, oy+(i+j)*cell*0.5 - z*zs];}}
function draw(){{const frames=DATA[name];const g=frames[fi];
 const[lo,hi]=range(frames);const span=(hi-lo)||1;
 ctx.clearRect(0,0,cv.width,cv.height);
 // painter's order: far cells (small i+j) first
 for(let i=0;i<N-1;i++)for(let j=0;j<N-1;j++){{
  const za=(g[i][j]+g[i+1][j]+g[i+1][j+1]+g[i][j+1])/4;
  const v=(za-lo)/span;const p0=proj(i,j,g[i][j]),p1=proj(i+1,j,g[i+1][j]),
   p2=proj(i+1,j+1,g[i+1][j+1]),p3=proj(i,j+1,g[i][j+1]);
  ctx.beginPath();ctx.moveTo(p0[0],p0[1]);ctx.lineTo(p1[0],p1[1]);
  ctx.lineTo(p2[0],p2[1]);ctx.lineTo(p3[0],p3[1]);ctx.closePath();
  ctx.fillStyle='hsl('+(240*(1-v))+',80%,'+(35+v*30)+'%)';ctx.fill();
  ctx.strokeStyle='rgba(0,0,0,0.25)';ctx.stroke();
 }}
 document.getElementById('frame').textContent='frame '+(fi+1)+'/'+frames.length;
}}
function setName(nm){{name=nm;fi=0;
 document.getElementById('desc').textContent=META[nm].title+' — '+META[nm].desc;}}
document.getElementById('pick').onchange=e=>setName(e.target.value);
document.getElementById('play').onclick=e=>{{playing=!playing;
 e.target.textContent=playing?'⏸ pause':'▶ play';}};
setName(name);
setInterval(()=>{{if(playing){{fi=(fi+1)%DATA[name].length;}}draw();}},90);
draw();
</script></body></html>"""
