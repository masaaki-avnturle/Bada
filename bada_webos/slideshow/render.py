"""Render all the equation-group graphs as a PowerPoint-style slideshow video.

Each equation group is a slide: a live 3D animated graph. Advancing between
slides (auto-timer or click / Space / arrow keys — event-driven) fires a
PowerPoint-like transition effect: flash, fade, wipe, zoom, spin, blinds.
"""

from __future__ import annotations

import json


def html_slideshow(frames_by_name: dict, n: int, catalog: dict) -> str:
    data = {name: [[[round(v, 3) for v in row] for row in g] for g in frames]
            for name, frames in frames_by_name.items()}
    meta = {name: {"title": catalog[name][0], "desc": catalog[name][1]}
            for name in frames_by_name}
    return _TEMPLATE.format(data=json.dumps(data), meta=json.dumps(meta), n=n)


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<title>Equation-group slideshow (flash transitions)</title>
<style>
 body{{margin:0;background:#05070f;color:#e8e8e8;font-family:monospace;
   overflow:hidden}}
 .bar{{padding:8px 12px;background:#11162a;border-bottom:2px solid #c8a44a;
   display:flex;gap:14px;align-items:center}}
 .bar b{{color:#c8a44a}} button{{background:#222a44;color:#eee;
   border:1px solid #445;padding:4px 9px;font-family:monospace;cursor:pointer}}
 #stage{{position:relative;width:720px;height:460px;margin:14px auto}}
 #cv{{position:absolute;inset:0;background:#05070f;border-radius:8px}}
 #title{{position:absolute;left:0;right:0;top:8px;text-align:center;
   color:#c8a44a;font-size:20px;text-shadow:0 0 12px #000}}
 #sub{{position:absolute;left:0;right:0;bottom:8px;text-align:center;
   color:#9fb;font-size:12px}}
 #ov{{position:absolute;inset:0;pointer-events:none;opacity:0;border-radius:8px}}
 #dots{{text-align:center;color:#789;font-size:12px}}
 .ov.flash{{background:#fff;animation:flash .5s ease-out}}
 .ov.fade {{background:#000;animation:fade .6s ease-out}}
 .ov.wipe {{background:linear-gradient(90deg,#c8a44a,#0000);
   animation:wipe .6s ease-out}}
 .ov.zoom {{background:#0a1020;animation:zoom .6s ease-out}}
 .ov.spin {{background:#11162a;animation:spin .6s ease-out}}
 .ov.blinds{{background:repeating-linear-gradient(0deg,#000 0 12px,#0000 12px 24px);
   animation:fade .6s steps(6)}}
 @keyframes flash{{from{{opacity:1}}to{{opacity:0}}}}
 @keyframes fade {{from{{opacity:1}}to{{opacity:0}}}}
 @keyframes wipe {{from{{opacity:1;transform:translateX(-100%)}}
   to{{opacity:0;transform:translateX(100%)}}}}
 @keyframes zoom {{from{{opacity:.9;transform:scale(2)}}to{{opacity:0;transform:scale(1)}}}}
 @keyframes spin {{from{{opacity:.9;transform:rotate(180deg) scale(1.5)}}
   to{{opacity:0;transform:rotate(0) scale(1)}}}}
</style></head><body>
<div class="bar"><b>🎞 equation-group slideshow</b>
 <button id="prev">◀ prev</button>
 <button id="play">⏸ pause</button>
 <button id="next">next ▶</button>
 <span id="pos"></span>
 <span style="color:#789">· click / Space / ← → · effect:</span><span id="fx"></span></div>
<div id="stage">
 <canvas id="cv" width="720" height="460"></canvas>
 <div id="title"></div><div id="sub"></div>
 <div id="ov"></div>
</div>
<div id="dots"></div>
<script>
const DATA={data}, META={meta}, N={n};
const NAMES=Object.keys(DATA);
const EFFECTS=['flash','fade','wipe','zoom','spin','blinds'];
let si=0, fi=0, playing=true, autoMs=3600, lastAdv=0;
const cv=document.getElementById('cv'), ctx=cv.getContext('2d'),
 ov=document.getElementById('ov');
function rng(frames){{let lo=1e9,hi=-1e9;for(const g of frames)for(const r of g)
 for(const v of r){{if(v<lo)lo=v;if(v>hi)hi=v;}}return[lo,(hi>lo?hi:lo+1)];}}
function proj(i,j,z){{const cell=20,ox=cv.width/2,oy=150,zs=80;
 return[ox+(i-j)*cell, oy+(i+j)*cell*0.5 - z*zs];}}
function hsl(h,s,l){{return 'hsl('+h+','+s+'%,'+l+'%)';}}
function draw(){{
 const name=NAMES[si], frames=DATA[name], g=frames[fi%frames.length];
 const[lo,hi]=rng(frames), span=(hi-lo)||1;
 ctx.clearRect(0,0,cv.width,cv.height);
 for(let i=0;i<N-1;i++)for(let j=0;j<N-1;j++){{
  const za=(g[i][j]+g[i+1][j]+g[i+1][j+1]+g[i][j+1])/4, v=(za-lo)/span;
  const p0=proj(i,j,g[i][j]),p1=proj(i+1,j,g[i+1][j]),
   p2=proj(i+1,j+1,g[i+1][j+1]),p3=proj(i,j+1,g[i][j+1]);
  ctx.beginPath();ctx.moveTo(p0[0],p0[1]);ctx.lineTo(p1[0],p1[1]);
  ctx.lineTo(p2[0],p2[1]);ctx.lineTo(p3[0],p3[1]);ctx.closePath();
  ctx.fillStyle=hsl(240*(1-v),80,30+v*32);ctx.fill();
  ctx.strokeStyle='rgba(0,0,0,0.25)';ctx.stroke();
 }}
}}
function showSlide(){{
 const name=NAMES[si];
 document.getElementById('title').textContent=META[name].title;
 document.getElementById('sub').textContent=META[name].desc;
 document.getElementById('pos').textContent=(si+1)+'/'+NAMES.length;
 const fx=EFFECTS[si%EFFECTS.length];
 document.getElementById('fx').textContent=fx;
 ov.className='ov '+fx; void ov.offsetWidth; // restart the transition animation
 dots();
}}
function dots(){{let s='';for(let k=0;k<NAMES.length;k++)s+=(k===si?'●':'·');
 document.getElementById('dots').textContent=s;}}
function go(d){{si=(si+d+NAMES.length)%NAMES.length;fi=0;showSlide();
 lastAdv=performance.now();}}
document.getElementById('prev').onclick=()=>go(-1);
document.getElementById('next').onclick=()=>go(1);
cv.onclick=()=>go(1);
document.getElementById('play').onclick=e=>{{playing=!playing;
 e.target.textContent=playing?'⏸ pause':'▶ play';}};
document.addEventListener('keydown',e=>{{
 if(e.key==='ArrowRight')go(1);else if(e.key==='ArrowLeft')go(-1);
 else if(e.key===' '){{playing=!playing;
  document.getElementById('play').textContent=playing?'⏸ pause':'▶ play';
  e.preventDefault();}}}});
showSlide();
let rc=0;
function loop(ts){{if((++rc%5)===0)fi++;draw();
 if(playing && ts-lastAdv>autoMs) go(1);
 requestAnimationFrame(loop);}}
requestAnimationFrame(loop);
</script></body></html>"""
