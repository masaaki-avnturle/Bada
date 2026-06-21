"""Render the manifold animations as a top-down kaleidoscope (万華鏡).

Each surface is viewed from directly above (z -> colour) and a single angular
wedge is mirror-folded around the centre into radial symmetry, then spun over
the animation frames — a true kaleidoscope of the equation-group videos.
"""

from __future__ import annotations

import json


def html_kaleido(frames_by_name: dict, n: int, catalog: dict,
                 segments: int = 8) -> str:
    data = {name: [[[round(v, 3) for v in row] for row in g] for g in frames]
            for name, frames in frames_by_name.items()}
    meta = {name: {"title": catalog[name][0], "desc": catalog[name][1]}
            for name in frames_by_name}
    options = "".join(f'<option value="{nm}">{catalog[nm][0]}</option>'
                      for nm in frames_by_name)
    first = next(iter(frames_by_name))
    return _TEMPLATE.format(options=options, data=json.dumps(data),
                            meta=json.dumps(meta), n=n, first=first,
                            seg=segments)


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<title>Equation-group kaleidoscope (万華鏡)</title>
<style>
 body{{margin:0;background:#070a16;color:#e8e8e8;font-family:monospace}}
 .bar{{padding:8px 12px;background:#11162a;border-bottom:2px solid #c8a44a;
   display:flex;gap:14px;align-items:center;flex-wrap:wrap}}
 .bar b{{color:#c8a44a}} select,button,input{{background:#222a44;color:#eee;
   border:1px solid #445;padding:4px 8px;font-family:monospace}}
 #desc{{padding:6px 12px;color:#9fb}} canvas{{display:block;margin:8px auto;
   border-radius:50%;box-shadow:0 0 40px #c8a44a55}}
 #cap{{text-align:center;color:#789;font-size:12px}}
</style></head><body>
<div class="bar"><b>🔮 equation-group kaleidoscope (top view)</b>
 <select id="pick">{options}</select>
 segments <input id="seg" type="range" min="3" max="16" value="{seg}">
 <span id="segv">{seg}</span>
 <button id="play">⏸ pause</button>
 <span id="frame"></span></div>
<div id="desc"></div>
<canvas id="cv" width="520" height="520"></canvas>
<div id="cap">a single wedge of the top-down surface, mirror-folded into radial
symmetry and spun over the animation</div>
<script>
const DATA={data}, META={meta}, N={n};
let name="{first}", fi=0, playing=true, SEG={seg};
const cv=document.getElementById('cv'), ctx=cv.getContext('2d');
const RES=200, off=document.createElement('canvas');
off.width=off.height=RES; const octx=off.getContext('2d');
function hsl2rgb(h,s,l){{
 const a=s*Math.min(l,1-l);
 const f=k=>{{const x=(k+h*12)%12;return l-a*Math.max(-1,Math.min(x-3,9-x,1));}};
 return [Math.round(f(0)*255),Math.round(f(8)*255),Math.round(f(4)*255)];}}
function rng(frames){{let lo=1e9,hi=-1e9;for(const g of frames)for(const r of g)
 for(const v of r){{if(v<lo)lo=v;if(v>hi)hi=v;}}return[lo,(hi>lo?hi:lo+1)];}}
function sample(g,u,v){{ // bilinear over [-1,1]^2
 let gx=(u+1)/2*(N-1), gy=(v+1)/2*(N-1);
 gx=Math.max(0,Math.min(N-1,gx)); gy=Math.max(0,Math.min(N-1,gy));
 const i0=Math.floor(gx), j0=Math.floor(gy);
 const i1=Math.min(i0+1,N-1), j1=Math.min(j0+1,N-1);
 const fx=gx-i0, fy=gy-j0;
 const a=g[i0][j0]*(1-fx)+g[i1][j0]*fx, b=g[i0][j1]*(1-fx)+g[i1][j1]*fx;
 return a*(1-fy)+b*fy;}}
function draw(){{
 const frames=DATA[name], g=frames[fi];
 const[lo,hi]=rng(frames), span=(hi-lo)||1;
 const img=octx.createImageData(RES,RES), d=img.data;
 const cx=RES/2, cy=RES/2, maxR=RES/2-2, wedge=Math.PI*2/SEG, rot=fi*0.06;
 for(let py=0;py<RES;py++)for(let px=0;px<RES;px++){{
  const dx=px-cx, dy=py-cy, r=Math.hypot(dx,dy), idx=(py*RES+px)*4;
  if(r>maxR){{d[idx]=7;d[idx+1]=10;d[idx+2]=22;d[idx+3]=255;continue;}}
  let th=Math.atan2(dy,dx)+rot;
  let k=Math.floor(th/wedge), a=th-k*wedge;
  if((((k%2)+2)%2)===1) a=wedge-a;            // mirror fold -> kaleidoscope
  const rho=r/maxR, u=rho*Math.cos(a), v=rho*Math.sin(a);
  let z=(sample(g,u,v)-lo)/span; z=Math.max(0,Math.min(1,z));
  const c=hsl2rgb((1-z)*0.66,0.85,0.32+z*0.30);
  d[idx]=c[0];d[idx+1]=c[1];d[idx+2]=c[2];d[idx+3]=255;
 }}
 octx.putImageData(img,0,0);
 ctx.imageSmoothingEnabled=true;
 ctx.clearRect(0,0,cv.width,cv.height);
 ctx.drawImage(off,0,0,cv.width,cv.height);
 document.getElementById('frame').textContent=
   'frame '+(fi+1)+'/'+frames.length+' · '+SEG+' segments';
}}
function setName(nm){{name=nm;fi=0;
 document.getElementById('desc').textContent=META[nm].title+' — '+META[nm].desc;}}
document.getElementById('pick').onchange=e=>setName(e.target.value);
document.getElementById('seg').oninput=e=>{{SEG=+e.target.value;
 document.getElementById('segv').textContent=SEG;draw();}};
document.getElementById('play').onclick=e=>{{playing=!playing;
 e.target.textContent=playing?'⏸ pause':'▶ play';}};
setName(name);
setInterval(()=>{{if(playing)fi=(fi+1)%DATA[name].length;draw();}},90);
draw();
</script></body></html>"""
