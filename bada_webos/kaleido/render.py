"""Render the manifold animations as a gallery of top-down kaleidoscopes (万華鏡).

Each animation gets its own kaleidoscope tile; a checkbox per animation lets you
turn any subset on/off (individual, arbitrary selection), and clicking a tile
enlarges it. Each surface is viewed from directly above (z -> colour) and one
angular wedge is mirror-folded into radial symmetry, spun over the frames.
"""

from __future__ import annotations

import json


def html_kaleido(frames_by_name: dict, n: int, catalog: dict,
                 segments: int = 8) -> str:
    data = {name: [[[round(v, 3) for v in row] for row in g] for g in frames]
            for name, frames in frames_by_name.items()}
    meta = {name: {"title": catalog[name][0], "desc": catalog[name][1]}
            for name in frames_by_name}
    chips = "".join(
        f'<label class="chip"><input type="checkbox" data-nm="{nm}" checked>'
        f'{catalog[nm][0]}</label>' for nm in frames_by_name)
    return _TEMPLATE.format(chips=chips, data=json.dumps(data),
                            meta=json.dumps(meta), n=n, seg=segments)


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<title>Equation-group kaleidoscope gallery (万華鏡)</title>
<style>
 body{{margin:0;background:#070a16;color:#e8e8e8;font-family:monospace}}
 .bar{{padding:8px 12px;background:#11162a;border-bottom:2px solid #c8a44a;
   display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
 .bar b{{color:#c8a44a}} button,input{{background:#222a44;color:#eee;
   border:1px solid #445;padding:3px 7px;font-family:monospace}}
 .chip{{background:#1b2240;border:1px solid #3a4a7a;border-radius:12px;
   padding:2px 8px;cursor:pointer;font-size:12px}}
 #grid{{display:flex;flex-wrap:wrap;gap:10px;padding:12px;justify-content:center}}
 .tile{{background:#0b0f1e;border:1px solid #233;border-radius:8px;padding:6px;
   text-align:center;cursor:pointer}}
 .tile canvas{{border-radius:50%;box-shadow:0 0 18px #c8a44a44;display:block}}
 .tile .lab{{font-size:11px;color:#9fb;margin-top:4px;width:170px}}
 #cap{{text-align:center;color:#789;font-size:12px;padding-bottom:10px}}
 #modal{{position:fixed;inset:0;background:#000c;display:none;
   align-items:center;justify-content:center;flex-direction:column;cursor:pointer}}
 #modal canvas{{border-radius:50%;box-shadow:0 0 60px #c8a44a88}}
 #modal .t{{color:#c8a44a;margin-top:10px}}
</style></head><body>
<div class="bar"><b>🔮 kaleidoscope gallery (top view)</b>
 <span id="chips">{chips}</span>
 <button id="all">all</button><button id="none">none</button>
 segments <input id="seg" type="range" min="3" max="16" value="{seg}">
 <span id="segv">{seg}</span>
 <button id="play">⏸ pause</button></div>
<div id="grid"></div>
<div id="cap">pick any subset with the chips · click a tile to enlarge ·
 the kaleidoscope is the top-down surface mirror-folded into radial symmetry</div>
<div id="modal"><canvas id="big" width="460" height="460"></canvas>
 <div class="t" id="bigt"></div></div>
<script>
const DATA={data}, META={meta}, N={n};
let fi=0, playing=true, SEG={seg}, ranges={{}}, big=null;
function hsl2rgb(h,s,l){{const a=s*Math.min(l,1-l);
 const f=k=>{{const x=(k+h*12)%12;return l-a*Math.max(-1,Math.min(x-3,9-x,1));}};
 return [Math.round(f(0)*255),Math.round(f(8)*255),Math.round(f(4)*255)];}}
function rng(nm){{if(ranges[nm])return ranges[nm];let lo=1e9,hi=-1e9;
 for(const g of DATA[nm])for(const r of g)for(const v of r){{
  if(v<lo)lo=v;if(v>hi)hi=v;}} return ranges[nm]=[lo,(hi>lo?hi:lo+1)];}}
function sample(g,u,v){{let gx=(u+1)/2*(N-1),gy=(v+1)/2*(N-1);
 gx=Math.max(0,Math.min(N-1,gx));gy=Math.max(0,Math.min(N-1,gy));
 const i0=Math.floor(gx),j0=Math.floor(gy),i1=Math.min(i0+1,N-1),
  j1=Math.min(j0+1,N-1),fx=gx-i0,fy=gy-j0;
 const a=g[i0][j0]*(1-fx)+g[i1][j0]*fx,b=g[i0][j1]*(1-fx)+g[i1][j1]*fx;
 return a*(1-fy)+b*fy;}}
// render one kaleidoscope frame of `nm` into an offscreen of size RES
function kaleido(nm,octx,RES){{
 const frames=DATA[nm],g=frames[fi%frames.length];const[lo,hi]=rng(nm);
 const span=(hi-lo)||1,img=octx.createImageData(RES,RES),d=img.data;
 const cx=RES/2,cy=RES/2,maxR=RES/2-1,wedge=Math.PI*2/SEG,rot=fi*0.06;
 for(let py=0;py<RES;py++)for(let px=0;px<RES;px++){{
  const dx=px-cx,dy=py-cy,r=Math.hypot(dx,dy),idx=(py*RES+px)*4;
  if(r>maxR){{d[idx]=7;d[idx+1]=10;d[idx+2]=22;d[idx+3]=255;continue;}}
  let th=Math.atan2(dy,dx)+rot,k=Math.floor(th/wedge),a=th-k*wedge;
  if((((k%2)+2)%2)===1)a=wedge-a;                 // mirror fold
  const rho=r/maxR;let z=(sample(g,rho*Math.cos(a),rho*Math.sin(a))-lo)/span;
  z=Math.max(0,Math.min(1,z));const c=hsl2rgb((1-z)*0.66,0.85,0.32+z*0.30);
  d[idx]=c[0];d[idx+1]=c[1];d[idx+2]=c[2];d[idx+3]=255;}}
 octx.putImageData(img,0,0);}}
// build a tile per animation
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
function drawTile(nm){{const t=tiles[nm];if(!t.visible)return;
 kaleido(nm,t.octx,96);t.ctx.imageSmoothingEnabled=true;
 t.ctx.drawImage(t.off,0,0,170,170);}}
function openBig(nm){{big=nm;document.getElementById('modal').style.display='flex';
 document.getElementById('bigt').textContent=META[nm].title+' — '+META[nm].desc;}}
const modal=document.getElementById('modal');
modal.onclick=()=>{{big=null;modal.style.display='none';}};
const bigcv=document.getElementById('big'),bigctx=bigcv.getContext('2d'),
 bigoff=document.createElement('canvas');bigoff.width=bigoff.height=230;
const bigoctx=bigoff.getContext('2d');
// chip toggles
for(const inp of document.querySelectorAll('#chips input')){{
 inp.onchange=()=>{{const nm=inp.dataset.nm;tiles[nm].visible=inp.checked;
  tiles[nm].div.style.display=inp.checked?'':'none';}};}}
document.getElementById('all').onclick=()=>{{
 for(const inp of document.querySelectorAll('#chips input')){{inp.checked=true;
  tiles[inp.dataset.nm].visible=true;tiles[inp.dataset.nm].div.style.display='';}}}};
document.getElementById('none').onclick=()=>{{
 for(const inp of document.querySelectorAll('#chips input')){{inp.checked=false;
  tiles[inp.dataset.nm].visible=false;tiles[inp.dataset.nm].div.style.display='none';}}}};
document.getElementById('seg').oninput=e=>{{SEG=+e.target.value;
 document.getElementById('segv').textContent=SEG;}};
document.getElementById('play').onclick=e=>{{playing=!playing;
 e.target.textContent=playing?'⏸ pause':'▶ play';}};
setInterval(()=>{{if(playing)fi++;
 for(const nm of Object.keys(tiles))drawTile(nm);
 if(big){{kaleido(big,bigoctx,230);bigctx.imageSmoothingEnabled=true;
  bigctx.drawImage(bigoff,0,0,460,460);}}}},90);
</script></body></html>"""
