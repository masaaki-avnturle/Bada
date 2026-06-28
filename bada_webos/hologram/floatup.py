"""Render the equation-group video so it *floats up* out of a conductive-plastic
tablet (the report's hologram display, with relief + power).

The chosen surface is drawn as a top-down heatmap modulated by the Bada light
field, then raised off a conductive-plastic plane: the per-pixel height is the
**Jones polynomial relief** computed in Bada (the light "mounds up", 盛る), and
the whole image lifts above its contact shadow so the video floats up (浮き上
がる).  A HUD shows the Jones polynomial, the live **power draw** of the tablet
and a power budget (the display dims to stay within it).
"""

from __future__ import annotations

import json


def _round_frames(frames):
    return [[[round(v, 3) for v in row] for row in g] for g in frames]


def _poly_str(poly) -> str:
    parts = []
    for e, c in poly:
        sign = "+" if c >= 0 else "-"
        parts.append(f"{sign} {abs(c)}t^{e}")
    s = " ".join(parts)
    return s[2:] if s.startswith("+ ") else s


def html_floatup(frames_by_name: dict, light_frames: list, relief_frames: list,
                 n: int, catalog: dict, jones_poly: list, power: list,
                 mean_relief: list, budget: float, wh: float) -> str:
    data = {nm: _round_frames(fr) for nm, fr in frames_by_name.items()}
    opts = "".join(f'<option value="{nm}">{catalog[nm][0]}</option>'
                   for nm in frames_by_name)
    return _TEMPLATE.format(
        opts=opts, data=json.dumps(data),
        light=json.dumps(_round_frames(light_frames)),
        relief=json.dumps(_round_frames(relief_frames)),
        n=n, jones=_poly_str(jones_poly),
        power=json.dumps([round(p, 3) for p in power]),
        meanrelief=json.dumps([round(r, 3) for r in mean_relief]),
        budget=budget, wh=wh)


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<title>Hologram Display — float-up (Jones relief, conductive plastic)</title>
<style>
 body{{margin:0;background:#01040a;color:#bfe;font-family:monospace}}
 .bar{{padding:8px 12px;background:#04070f;border-bottom:2px solid #1a8;
   display:flex;gap:12px;align-items:center;flex-wrap:wrap}}
 .bar b{{color:#3fd;letter-spacing:1px}}
 select,button{{background:#0a1320;color:#cfe;border:1px solid #245;
   padding:3px 8px;font-family:monospace;cursor:pointer}}
 .hud{{font-size:12px;color:#7fd}} .hud b{{color:#fe7}}
 input[type=range]{{vertical-align:middle}}
 #stage{{display:flex;justify-content:center;padding:16px}}
 #cap{{text-align:center;color:#69a;font-size:12px;padding:0 12px 16px}}
 .k{{color:#3fd}}
</style></head><body>
<div class="bar"><b>&#x1F52E; FLOAT-UP HOLOGRAM</b>
 <label>project: <select id="pick">{opts}</select></label>
 <button id="play">&#9208; pause</button>
 <span class="hud">Jones V(t)=<b>{jones}</b></span>
 <span class="hud">power <b id="pw"></b> / budget
   <input id="bud" type="range" min="1" max="8" step="0.5" value="{budget}">
   <b id="bv"></b>W</span>
 <span class="hud">battery <b id="bat"></b></span></div>
<div id="stage"><canvas id="holo" width="560" height="560"></canvas></div>
<div id="cap">the video floats up out of the conductive-plastic tablet · height =
 Bada <span class="k">Jones relief</span> (the light mounds up) · brightness ×
 the Bada <span class="k">&beta;(p,q)</span> light field · the panel
 <span class="k">dims</span> to stay within the power budget</div>
<script>
const DATA={data}, LIGHT={light}, RELIEF={relief}, N={n};
const POWER={power}, MEANR={meanrelief}, WH={wh};
let fi=0, playing=true, cur=Object.keys(DATA)[0], ranges={{}}, budget={budget};
const holo=document.getElementById('holo'), hx=holo.getContext('2d');
const RES=300, off=document.createElement('canvas');
off.width=off.height=RES; const octx=off.getContext('2d');

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
// render surface * light * Jones-relief into the tile (relief shades the height)
function renderTile(scale){{
 const fr=DATA[cur],g=fr[fi%fr.length];
 const lg=LIGHT[fi%LIGHT.length], rl=RELIEF[fi%RELIEF.length];
 const[lo,hi]=rng(cur), span=(hi-lo)||1;
 const img=octx.createImageData(RES,RES), d=img.data;
 for(let py=0;py<RES;py++)for(let px=0;px<RES;px++){{
  const idx=(py*RES+px)*4, u=px/(RES-1)*2-1, v=py/(RES-1)*2-1;
  const r=Math.hypot(u,v);
  let z=(sample(g,u,v)-lo)/span; z=Math.max(0,Math.min(1,z));
  let lit=Math.max(0,Math.min(1,sample(lg,u,v)/0.5));
  let h=Math.max(0,Math.min(1,sample(rl,u,v)));          // Jones relief height
  // shade by relief: raised areas catch more light (mound highlight)
  const shade=0.45+0.55*h;
  const c=hsl2rgb((1-z)*0.55,0.9,(0.10+z*0.34)*shade*(0.4+0.6*lit));
  let al=(0.20+0.80*z)*lit*scale;
  if(r>1.0)al*=Math.max(0,1-(r-1)*3);                    // fade outside disk
  d[idx]=c[0];d[idx+1]=c[1];d[idx+2]=c[2];d[idx+3]=Math.round(255*Math.max(0,Math.min(1,al)));}}
 octx.putImageData(img,0,0);}}
function plane(){{
 const W=holo.width,H=holo.height;
 hx.fillStyle='#01040a';hx.fillRect(0,0,W,H);
 // conductive-plastic sheet: faint grid + sheen
 hx.strokeStyle='rgba(40,120,120,0.10)';hx.lineWidth=1;
 for(let i=0;i<=12;i++){{const t=i/12;
  hx.beginPath();hx.moveTo(t*W,H*0.55);hx.lineTo(t*W,H);hx.stroke();
  hx.beginPath();hx.moveTo(0,H*0.55+t*H*0.45);hx.lineTo(W,H*0.55+t*H*0.45);hx.stroke();}}
 const g=hx.createRadialGradient(W/2,H*0.78,10,W/2,H*0.78,W*0.6);
 g.addColorStop(0,'rgba(10,60,60,0.25)');g.addColorStop(1,'rgba(0,0,0,0)');
 hx.fillStyle=g;hx.fillRect(0,0,W,H);}}
function draw(){{
 const scale=Math.min(1,budget/(POWER[fi%POWER.length]||1));   // power dimming
 renderTile(scale);
 const W=holo.width,H=holo.height,cx=W/2,baseY=H*0.62;
 const lift=46*(0.4+0.6*(MEANR[fi%MEANR.length]||0))
            + 5*Math.sin(fi*0.12);                             // float-up height
 plane();
 // contact shadow on the plane
 hx.save();hx.globalAlpha=0.33*scale;hx.filter='blur(6px)';
 hx.translate(cx,baseY+lift*0.5);hx.scale(1,0.32);
 hx.drawImage(off,-RES/2,-RES/2);hx.restore();
 // the floating, mounded-up image
 hx.save();hx.globalAlpha=1;hx.translate(cx,baseY-lift);
 hx.shadowColor='rgba(60,255,210,0.5)';hx.shadowBlur=24*scale;
 hx.imageSmoothingEnabled=true;hx.drawImage(off,-RES/2,-RES/2);hx.restore();
 // HUD
 const pw=(POWER[fi%POWER.length]||0)*scale;
 document.getElementById('pw').textContent=pw.toFixed(2)+'W';
 document.getElementById('bv').textContent=budget.toFixed(1);
 const mins=pw>0?WH/pw*60:0;
 document.getElementById('bat').textContent=(mins/60).toFixed(1)+'h';}}
document.getElementById('pick').onchange=e=>{{cur=e.target.value;}};
document.getElementById('bud').oninput=e=>{{budget=parseFloat(e.target.value);}};
document.getElementById('play').onclick=e=>{{playing=!playing;
 e.target.innerHTML=playing?'&#9208; pause':'&#9654; play';}};
setInterval(()=>{{if(playing)fi++;draw();}},80);
</script></body></html>"""
