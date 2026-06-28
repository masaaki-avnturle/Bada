"""Render the equation-group videos onto a Hologram Display.

The chosen equation group's surface is drawn as a top-down heatmap, modulated
per-pixel by the **hologram light field** computed in Bada (the report's
beta(p,q) / light-position amplitude).  It is then projected onto the four SiO2
mirrors of the reflection pyramid — before (top), after (bottom), left, right —
so that a transparent pyramid placed on the screen reconstructs one floating
image.  A "free view" toggle shows the single reconstructed hologram instead,
with the imaginary/reality phase shimmer.
"""

from __future__ import annotations

import json


def _round_frames(frames):
    return [[[round(v, 3) for v in row] for row in g] for g in frames]


def html_hologram(frames_by_name: dict, light_frames: list, n: int,
                  catalog: dict, quads: list, free: bool = False) -> str:
    data = {nm: _round_frames(fr) for nm, fr in frames_by_name.items()}
    light = _round_frames(light_frames)
    meta = {nm: {"title": catalog[nm][0], "desc": catalog[nm][1]}
            for nm in frames_by_name}
    opts = "".join(f'<option value="{nm}">{catalog[nm][0]}</option>'
                   for nm in frames_by_name)
    return _TEMPLATE.format(
        opts=opts, data=json.dumps(data), light=json.dumps(light),
        meta=json.dumps(meta), quads=json.dumps(quads), n=n,
        free="true" if free else "false")


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<title>Hologram Display — equation-group videos</title>
<style>
 body{{margin:0;background:#000;color:#cfe;font-family:monospace}}
 .bar{{padding:8px 12px;background:#06080f;border-bottom:2px solid #1c6;
   display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
 .bar b{{color:#3fd;letter-spacing:1px}}
 select,button{{background:#0b1320;color:#cfe;border:1px solid #245;
   padding:3px 8px;font-family:monospace;cursor:pointer}}
 #stage{{display:flex;justify-content:center;padding:14px}}
 #wrap{{position:relative}}
 #holo{{display:block;background:
   radial-gradient(circle at 50% 50%,#02110c 0%,#000 70%);
   box-shadow:0 0 60px #0f8a55aa inset, 0 0 30px #0c6}}
 .edge{{position:absolute;color:#2c9;font-size:11px;opacity:.7}}
 #cap{{text-align:center;color:#6ab;font-size:12px;padding:0 12px 14px}}
 .k{{color:#3fd}}
</style></head><body>
<div class="bar"><b>&#x1F52E; HOLOGRAM DISPLAY</b>
 <label>project: <select id="pick">{opts}</select></label>
 <button id="view"></button>
 <button id="play">&#9208; pause</button>
 <span class="k" id="mirrors">mirrors: before · after · left · right</span></div>
<div id="stage"><div id="wrap">
 <canvas id="holo" width="540" height="540"></canvas>
 <div class="edge" style="top:6px;left:50%;transform:translateX(-50%)">before</div>
 <div class="edge" style="bottom:6px;left:50%;transform:translateX(-50%)">after</div>
 <div class="edge" style="left:6px;top:50%;transform:translateY(-50%)">left</div>
 <div class="edge" style="right:6px;top:50%;transform:translateY(-50%)">right</div>
</div></div>
<div id="cap">surfaces computed in Bada · modulated by the Bada
 <span class="k">&beta;(p,q)</span> light field · reflected by four SiO&#8322;
 mirrors. Place a transparent pyramid on the screen for the floating image,
 or switch to <span class="k">free view</span> for the reconstruction.</div>
<script>
const DATA={data}, LIGHT={light}, META={meta}, QUADS={quads}, N={n};
let fi=0, playing=true, FREE={free}, cur=Object.keys(DATA)[0], ranges={{}};
const holo=document.getElementById('holo'), hx=holo.getContext('2d');
const TILE=200, off=document.createElement('canvas');
off.width=off.height=TILE; const octx=off.getContext('2d');

function hsl2rgb(h,s,l){{const a=s*Math.min(l,1-l);
 const f=k=>{{const x=(k+h*12)%12;return l-a*Math.max(-1,Math.min(x-3,9-x,1));}};
 return [Math.round(f(0)*255),Math.round(f(8)*255),Math.round(f(4)*255)];}}
function rng(nm){{if(ranges[nm])return ranges[nm];let lo=1e9,hi=-1e9;
 for(const g of DATA[nm])for(const r of g)for(const v of r){{
  if(v<lo)lo=v;if(v>hi)hi=v;}}return ranges[nm]=[lo,(hi>lo?hi:lo+1)];}}
function sample(g,u,v){{let gx=(u+1)/2*(N-1),gy=(v+1)/2*(N-1);
 gx=Math.max(0,Math.min(N-1,gx));gy=Math.max(0,Math.min(N-1,gy));
 const i0=Math.floor(gx),j0=Math.floor(gy),i1=Math.min(i0+1,N-1),
  j1=Math.min(j0+1,N-1),fx=gx-i0,fy=gy-j0;
 const a=g[i0][j0]*(1-fx)+g[i1][j0]*fx,b=g[i0][j1]*(1-fx)+g[i1][j1]*fx;
 return a*(1-fy)+b*fy;}}
// render the equation-group surface * hologram light field into the tile
function renderTile(){{
 const frames=DATA[cur],g=frames[fi%frames.length];
 const lg=LIGHT[fi%LIGHT.length];const[lo,hi]=rng(cur);const span=(hi-lo)||1;
 const img=octx.createImageData(TILE,TILE),d=img.data;
 for(let py=0;py<TILE;py++)for(let px=0;px<TILE;px++){{
  const idx=(py*TILE+px)*4;
  const u=px/(TILE-1)*2-1, v=py/(TILE-1)*2-1;
  let z=(sample(g,u,v)-lo)/span; z=Math.max(0,Math.min(1,z));
  let lit=sample(lg,u,v)/0.5; lit=Math.max(0,Math.min(1,lit));  // 0..1
  const c=hsl2rgb((1-z)*0.62,0.9,(0.10+z*0.34)*(0.35+0.65*lit));
  const al=Math.round(255*Math.max(0,Math.min(1,(0.25+0.75*z)*lit)));
  d[idx]=c[0];d[idx+1]=c[1];d[idx+2]=c[2];d[idx+3]=al;}}
 octx.putImageData(img,0,0);}}
function blit(cx,cy,rotDeg,scale){{
 hx.save();hx.translate(cx,cy);hx.rotate(rotDeg*Math.PI/180);
 hx.imageSmoothingEnabled=true;
 hx.drawImage(off,-TILE*scale/2,-TILE*scale/2,TILE*scale,TILE*scale);
 hx.restore();}}
function draw(){{
 renderTile();
 hx.clearRect(0,0,holo.width,holo.height);
 const W=holo.width,H=holo.height,cx=W/2,cy=H/2;
 if(FREE){{
  // single reconstructed floating hologram in the centre
  blit(cx,cy,fi*0.3,1.6);
 }} else {{
  // four SiO2 mirrors of the reflection pyramid (before/after/left/right)
  const m=0.20, s=0.92;
  for(const q of QUADS){{
   let px=cx,py=cy;
   if(q.name==='before') py=H*m;
   else if(q.name==='after') py=H*(1-m);
   else if(q.name==='left') px=W*m;
   else if(q.name==='right') px=W*(1-m);
   blit(px,py,q.rot,s);
  }}
 }}}}
function setView(){{document.getElementById('view').textContent=
 FREE?'&#9636; pyramid view':'&#9673; free view';
 document.getElementById('mirrors').style.opacity=FREE?0.3:1;}}
document.getElementById('pick').onchange=e=>{{cur=e.target.value;}};
document.getElementById('view').onclick=()=>{{FREE=!FREE;setView();}};
document.getElementById('play').onclick=e=>{{playing=!playing;
 e.target.innerHTML=playing?'&#9208; pause':'&#9654; play';}};
setView();
setInterval(()=>{{if(playing)fi++;draw();}},90);
</script></body></html>"""
