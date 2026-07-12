"""Render each equation group's domain as a flat 2D top-down video.

Each surface is viewed from straight above (z -> colour) as a flat heatmap of
its [-1,1]^2 domain. A global **kaleidoscope-fold** toggle switches every tile
between the plain top-down view and the radially mirror-folded kaleidoscope
(the "based on the 3D kaleidoscope" mode). Per-animation checkboxes select any
subset; click a tile to enlarge.
"""

from __future__ import annotations

import json


def html_topdown(frames_by_name: dict, n: int, catalog: dict,
                 fold: bool = False) -> str:
    data = {name: [[[round(v, 3) for v in row] for row in g] for g in frames]
            for name, frames in frames_by_name.items()}
    meta = {name: {"title": catalog[name][0], "desc": catalog[name][1]}
            for name in frames_by_name}
    chips = "".join(
        f'<label class="chip"><input type="checkbox" data-nm="{nm}" checked>'
        f'{catalog[nm][0]}</label>' for nm in frames_by_name)
    return _TEMPLATE.format(chips=chips, data=json.dumps(data),
                            meta=json.dumps(meta), n=n,
                            fold="true" if fold else "false")


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<title>Equation-group domains — 2D top-down video</title>
<style>
 body{{margin:0;background:#070a16;color:#e8e8e8;font-family:monospace}}
 .bar{{padding:8px 12px;background:#11162a;border-bottom:2px solid #c8a44a;
   display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
 .bar b{{color:#c8a44a}} button{{background:#222a44;color:#eee;
   border:1px solid #445;padding:3px 7px;font-family:monospace;cursor:pointer}}
 .chip{{background:#1b2240;border:1px solid #3a4a7a;border-radius:12px;
   padding:2px 8px;cursor:pointer;font-size:12px}}
 #grid{{display:flex;flex-wrap:wrap;gap:10px;padding:12px;justify-content:center}}
 .tile{{background:#0b0f1e;border:1px solid #233;border-radius:8px;padding:6px;
   text-align:center;cursor:pointer}}
 .tile canvas{{display:block;box-shadow:0 0 14px #c8a44a33}}
 .tile .lab{{font-size:11px;color:#9fb;margin-top:4px;width:170px}}
 #cap{{text-align:center;color:#789;font-size:12px;padding-bottom:10px}}
 #modal{{position:fixed;inset:0;background:#000c;display:none;
   align-items:center;justify-content:center;flex-direction:column;cursor:pointer}}
 #modal .t{{color:#c8a44a;margin-top:10px}}
</style></head><body>
<div class="bar"><b>🗺 equation-group domains · 2D top-down</b>
 <span id="chips">{chips}</span>
 <button id="all">all</button><button id="none">none</button>
 <label class="chip"><input type="checkbox" id="fold">kaleidoscope fold</label>
 <button id="play">⏸ pause</button></div>
<div id="grid"></div>
<div id="cap">each tile = the equation group's domain seen from straight above ·
 tick "kaleidoscope fold" to mirror-fold into radial symmetry · click to enlarge</div>
<div id="modal"><canvas id="big" width="440" height="440"></canvas>
 <div class="t" id="bigt"></div></div>
<script>
const DATA={data}, META={meta}, N={n};
let fi=0, playing=true, FOLD={fold}, SEG=8, ranges={{}}, big=null;
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
function render(nm,octx,RES){{
 const frames=DATA[nm],g=frames[fi%frames.length];const[lo,hi]=rng(nm);
 const span=(hi-lo)||1,img=octx.createImageData(RES,RES),d=img.data;
 const cx=RES/2,cy=RES/2,maxR=RES/2-1,wedge=Math.PI*2/SEG,rot=fi*0.05;
 for(let py=0;py<RES;py++)for(let px=0;px<RES;px++){{
  const idx=(py*RES+px)*4; let u,v,inside=true;
  if(FOLD){{
   const dx=px-cx,dy=py-cy,r=Math.hypot(dx,dy);
   if(r>maxR){{inside=false;}} else {{
    let th=Math.atan2(dy,dx)+rot,k=Math.floor(th/wedge),a=th-k*wedge;
    if((((k%2)+2)%2)===1)a=wedge-a; const rho=r/maxR;
    u=rho*Math.cos(a); v=rho*Math.sin(a);}}
  }} else {{ u=px/(RES-1)*2-1; v=py/(RES-1)*2-1; }}
  if(!inside){{d[idx]=7;d[idx+1]=10;d[idx+2]=22;d[idx+3]=255;continue;}}
  let z=(sample(g,u,v)-lo)/span; z=Math.max(0,Math.min(1,z));
  const c=hsl2rgb((1-z)*0.66,0.85,0.30+z*0.32);
  d[idx]=c[0];d[idx+1]=c[1];d[idx+2]=c[2];d[idx+3]=255;}}
 octx.putImageData(img,0,0);}}
const grid=document.getElementById('grid'),tiles={{}};
for(const nm of Object.keys(DATA)){{
 const div=document.createElement('div');div.className='tile';
 const cv=document.createElement('canvas');cv.width=cv.height=170;
 const off=document.createElement('canvas');off.width=off.height=96;
 const lab=document.createElement('div');lab.className='lab';
 lab.textContent=META[nm].title;
 div.appendChild(cv);div.appendChild(lab);grid.appendChild(div);
 div.onclick=()=>openBig(nm);
 tiles[nm]={{div,cv,ctx:cv.getContext('2d'),off,octx:off.getContext('2d'),
   visible:true}};}}
function radius(){{return FOLD?'50%':'8px';}}
function drawTile(nm){{const t=tiles[nm];if(!t.visible)return;
 render(nm,t.octx,96);t.ctx.imageSmoothingEnabled=true;
 t.cv.style.borderRadius=radius();t.ctx.drawImage(t.off,0,0,170,170);}}
function openBig(nm){{big=nm;document.getElementById('modal').style.display='flex';
 document.getElementById('bigt').textContent=META[nm].title+' — '+META[nm].desc;}}
const modal=document.getElementById('modal');
modal.onclick=()=>{{big=null;modal.style.display='none';}};
const bigcv=document.getElementById('big'),bigctx=bigcv.getContext('2d'),
 bigoff=document.createElement('canvas');bigoff.width=bigoff.height=220;
const bigoctx=bigoff.getContext('2d');
for(const inp of document.querySelectorAll('#chips input')){{
 inp.onchange=()=>{{const nm=inp.dataset.nm;tiles[nm].visible=inp.checked;
  tiles[nm].div.style.display=inp.checked?'':'none';}};}}
document.getElementById('all').onclick=()=>{{
 for(const inp of document.querySelectorAll('#chips input')){{inp.checked=true;
  tiles[inp.dataset.nm].visible=true;tiles[inp.dataset.nm].div.style.display='';}}}};
document.getElementById('none').onclick=()=>{{
 for(const inp of document.querySelectorAll('#chips input')){{inp.checked=false;
  tiles[inp.dataset.nm].visible=false;tiles[inp.dataset.nm].div.style.display='none';}}}};
document.getElementById('fold').checked=FOLD;
document.getElementById('fold').onchange=e=>{{FOLD=e.target.checked;}};
document.getElementById('play').onclick=e=>{{playing=!playing;
 e.target.textContent=playing?'⏸ pause':'▶ play';}};
setInterval(()=>{{if(playing)fi++;
 for(const nm of Object.keys(tiles))drawTile(nm);
 if(big){{render(big,bigoctx,220);bigctx.imageSmoothingEnabled=true;
  bigcv.style.borderRadius=radius();bigctx.drawImage(bigoff,0,0,440,440);}}}},90);
</script></body></html>"""
