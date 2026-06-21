"""The smartphone "mirror app": hold the phone face-down over the tablet and a
real aerial image forms in the gap, realizing the holographic display and the
Happy Hacking keyboard.

Side cross-section (computed in Bada): the tablet shows the source, the phone
mirror faces down, and rays converge to the **eyeglass-lens focal point** whose
height in the gap is set by the special-relativity Jones polynomial (Lorentz
factor × |V(t)|).  The front view shows the realized floating image — toggle
between the equation-group display and the HHKB keyboard.
"""

from __future__ import annotations

import json

from .keyboard import keys_with_labels


def _round_frames(frames):
    return [[[round(v, 3) for v in row] for row in g] for g in frames]


def _poly_str(poly) -> str:
    parts = [f"{'+' if c >= 0 else '-'} {abs(c)}t^{e}" for e, c in poly]
    s = " ".join(parts)
    return s[2:] if s.startswith("+ ") else s


def html_mirror(display_name: str, display_frames: list, light_frames: list,
                n: int, keys: list, kbd_width: int, focus_table: list,
                gap: float, vmax: float, jones_poly: list,
                keyboard: bool = False) -> str:
    return _TEMPLATE.format(
        dname=display_name,
        dframes=json.dumps(_round_frames(display_frames)),
        light=json.dumps(_round_frames(light_frames)), n=n,
        keys=json.dumps(keys_with_labels(keys)), kw=kbd_width,
        focus=json.dumps([[round(z, 3) for z in row] for row in focus_table]),
        gap=gap, vmax=vmax, jones=_poly_str(jones_poly),
        kb="true" if keyboard else "false")


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<title>Mirror App — aerial hologram between tablet & phone</title>
<style>
 body{{margin:0;background:#01040a;color:#bfe;font-family:monospace}}
 .bar{{padding:8px 12px;background:#04070f;border-bottom:2px solid #1a8;
   display:flex;gap:14px;align-items:center;flex-wrap:wrap}}
 .bar b{{color:#3fd;letter-spacing:1px}} .hud{{font-size:12px;color:#7fd}}
 .hud b{{color:#fe7}} button{{background:#0a1320;color:#cfe;border:1px solid #245;
   padding:3px 8px;font-family:monospace;cursor:pointer}}
 #stage{{display:flex;justify-content:center;padding:14px}}
 #cap{{text-align:center;color:#69a;font-size:12px;padding:0 12px 16px}}
 .k{{color:#3fd}} input[type=range]{{vertical-align:middle}}
</style></head><body>
<div class="bar"><b>&#x1F52E; MIRROR APP — aerial hologram</b>
 <button id="mode"></button>
 <span class="hud">v/c <input id="vel" type="range" min="0" max="{vmax}"
   step="0.01" value="0.3"><b id="vv"></b></span>
 <span class="hud">&gamma;=<b id="gm"></b></span>
 <span class="hud">focus z=<b id="fz"></b>cm</span>
 <span class="hud">Jones V(t)=<b>{jones}</b></span>
 <button id="play">&#9208; pause</button></div>
<div id="stage"><canvas id="cv" width="720" height="660"></canvas></div>
<div id="cap">phone held face-down over the tablet · its <span class="k">mirror</span>
 + the <span class="k">eyeglass-lens</span> focus form a real image in the gap ·
 the focal height is set by the <span class="k">special-relativity Jones
 polynomial</span> · move <span class="k">v/c</span> to shift the focus
 relativistically · toggle the realized display / HHKB keyboard</div>
<script>
const DFRAMES={dframes}, LIGHT={light}, N={n}, KEYS={keys}, KW={kw};
const FOCUS={focus}, GAP={gap}, VMAX={vmax};
let fi=0, playing=true, KB={kb}, vidx=null, range_=null;
const cv=document.getElementById('cv'), cx=cv.getContext('2d');
const vel=document.getElementById('vel');
function NV(){{return FOCUS.length-1;}}
function vrow(){{return Math.round(parseFloat(vel.value)/VMAX*NV());}}

// ---- front view: the realized floating aerial image ----------------------
function hsl2rgb(h,s,l){{const a=s*Math.min(l,1-l);
 const f=k=>{{const x=(k+h*12)%12;return l-a*Math.max(-1,Math.min(x-3,9-x,1));}};
 return [Math.round(f(0)*255),Math.round(f(8)*255),Math.round(f(4)*255)];}}
function rng(){{if(range_)return range_;let lo=1e9,hi=-1e9;
 for(const g of DFRAMES)for(const r of g)for(const v of r){{
  if(v<lo)lo=v;if(v>hi)hi=v;}}return range_=[lo,(hi>lo?hi:lo+1)];}}
function sample(g,u,v){{let gx=(u+1)/2*(N-1),gy=(v+1)/2*(N-1);
 gx=Math.max(0,Math.min(N-1,gx));gy=Math.max(0,Math.min(N-1,gy));
 const i0=Math.floor(gx),j0=Math.floor(gy),i1=Math.min(i0+1,N-1),
  j1=Math.min(j0+1,N-1),fx=gx-i0,fy=gy-j0;
 const a=g[i0][j0]*(1-fx)+g[i1][j0]*fx,b=g[i0][j1]*(1-fx)+g[i1][j1]*fx;
 return a*(1-fy)+b*fy;}}
const RES=200, off=document.createElement('canvas');
off.width=off.height=RES; const octx=off.getContext('2d');
function tile(){{
 const g=DFRAMES[fi%DFRAMES.length], lg=LIGHT[fi%LIGHT.length];
 const[lo,hi]=rng(), span=(hi-lo)||1, img=octx.createImageData(RES,RES), d=img.data;
 for(let py=0;py<RES;py++)for(let px=0;px<RES;px++){{
  const idx=(py*RES+px)*4,u=px/(RES-1)*2-1,v=py/(RES-1)*2-1,r=Math.hypot(u,v);
  let z=(sample(g,u,v)-lo)/span; z=Math.max(0,Math.min(1,z));
  let lit=Math.max(0,Math.min(1,sample(lg,u,v)/0.5));
  const c=hsl2rgb((1-z)*0.55,0.9,(0.10+z*0.34)*(0.4+0.6*lit));
  let al=(0.2+0.8*z)*lit; if(r>1)al*=Math.max(0,1-(r-1)*3);
  d[idx]=c[0];d[idx+1]=c[1];d[idx+2]=c[2];d[idx+3]=Math.round(255*Math.max(0,Math.min(1,al)));}}
 octx.putImageData(img,0,0);}}
function rrect(x,y,w,h,r){{cx.beginPath();cx.moveTo(x+r,y);
 cx.arcTo(x+w,y,x+w,y+h,r);cx.arcTo(x+w,y+h,x,y+h,r);
 cx.arcTo(x,y+h,x,y,r);cx.arcTo(x,y,x+w,y,r);cx.closePath();}}
function frontDisplay(cxp,cyp,scale){{
 tile(); cx.save(); cx.globalAlpha=0.95;
 cx.shadowColor='rgba(60,255,210,0.55)';cx.shadowBlur=26;
 cx.imageSmoothingEnabled=true;
 cx.drawImage(off,cxp-RES*scale/2,cyp-RES*scale/2,RES*scale,RES*scale);
 cx.restore();}}
function frontKeyboard(cxp,cyp){{
 const U=30, w=KW*U, ox=cxp-w/2, oy=cyp-2.6*U;
 for(let i=0;i<KEYS.length;i++){{const k=KEYS[i];
  const x=ox+k.x*U+2, y=oy+k.y*U+2, kw=k.w*U-4, kh=U-4;
  const wave=Math.sin((k.x/KW)*6.283-fi*0.10), lift=4*Math.max(0,wave);
  const glow=0.4+0.5*Math.max(0,wave);
  cx.save();cx.shadowColor='rgba(60,255,210,'+glow+')';cx.shadowBlur=8+12*glow;
  const g=cx.createLinearGradient(x,y-lift,x,y-lift+kh);
  g.addColorStop(0,'rgba(20,'+Math.round(90+120*glow)+',120,0.95)');
  g.addColorStop(1,'rgba(6,28,40,0.9)');
  cx.fillStyle=g; rrect(x,y-lift,kw,kh,4); cx.fill(); cx.shadowBlur=0;
  cx.strokeStyle='rgba(80,255,220,'+(0.4+glow)+')';cx.stroke();
  cx.fillStyle='rgba(225,255,250,0.9)';
  cx.font=(k.special?9:12)+'px monospace';
  cx.textAlign='center';cx.textBaseline='middle';
  cx.fillText(k.label,x+kw/2,y-lift+kh/2);cx.restore();}}}}

// ---- side cross-section: tablet, phone mirror, rays, focus ----------------
function side(zf){{
 const W=cv.width, x0=70, x1=W-70, yTab=620, yMir=430;  // tablet / mirror lines
 // map z in [0,GAP] -> screen y between tablet(0) and mirror(GAP)
 const yf=yTab-(zf/GAP)*(yTab-yMir);
 // tablet (face up, glowing source)
 const tg=cx.createLinearGradient(0,yTab,0,yTab+26);
 tg.addColorStop(0,'#0a4');tg.addColorStop(1,'#031');
 cx.fillStyle=tg; rrect(x0,yTab,x1-x0,26,5); cx.fill();
 cx.fillStyle='#9fe';cx.font='11px monospace';cx.textAlign='left';
 cx.fillText('TABLET (hologram source, face up)',x0+6,yTab+38);
 // phone mirror (face down)
 const mg=cx.createLinearGradient(0,yMir-22,0,yMir);
 mg.addColorStop(0,'#123');mg.addColorStop(1,'#9cf');
 cx.fillStyle=mg; rrect(x0+40,yMir-22,x1-x0-80,22,5); cx.fill();
 cx.fillStyle='#9fe';cx.fillText('SMARTPHONE — MIRROR facing down',x0+46,yMir-28);
 // rays: tablet points -> mirror -> converge to focus
 const pts=[-0.6,-0.3,0,0.3,0.6];
 for(const p of pts){{
  const xs=(x0+x1)/2+p*(x1-x0)*0.32;
  const xm=(x0+x1)/2+p*(x1-x0)*0.16;
  cx.strokeStyle='rgba(90,255,210,'+(0.25+0.2*Math.sin(fi*0.1+p*6))+')';
  cx.lineWidth=1.2; cx.beginPath();
  cx.moveTo(xs,yTab); cx.lineTo(xm,yMir);            // up to mirror
  cx.lineTo((x0+x1)/2,yf); cx.stroke();              // reflect to focus
 }}
 // the aerial focal image (real image floating in the gap)
 cx.save();cx.shadowColor='rgba(120,255,230,0.8)';cx.shadowBlur=24;
 cx.strokeStyle='rgba(150,255,235,0.95)';cx.lineWidth=3;
 cx.beginPath();cx.moveTo((x0+x1)/2-70,yf);cx.lineTo((x0+x1)/2+70,yf);cx.stroke();
 cx.restore();
 cx.fillStyle='#fe7';cx.textAlign='center';
 cx.fillText('aerial focus  z='+zf.toFixed(2)+'cm  ('+(KB?'HHKB':'display')+')',
   (x0+x1)/2,yf-10);
 cx.fillStyle='rgba(120,160,180,0.7)';cx.textAlign='right';
 cx.fillText('gap d='+GAP+'cm',x1,yMir-28);
}}
function draw(){{
 cx.fillStyle='#01040a';cx.fillRect(0,0,cv.width,cv.height);
 const row=FOCUS[vrow()], zf=row[fi%row.length];
 // front view (the realized floating image)
 const cyp=200;
 if(KB) frontKeyboard(cv.width/2,cyp); else frontDisplay(cv.width/2,cyp,1.4);
 cx.fillStyle='#69b';cx.font='11px monospace';cx.textAlign='center';
 cx.fillText('— realized aerial image (what you see floating) —',cv.width/2,360);
 // side optics
 side(zf);
 // HUD
 const b=parseFloat(vel.value), gm=1/Math.sqrt(1-Math.min(0.998,b)*Math.min(0.998,b));
 document.getElementById('vv').textContent=b.toFixed(2);
 document.getElementById('gm').textContent=gm.toFixed(3);
 document.getElementById('fz').textContent=zf.toFixed(2);
}}
function setMode(){{document.getElementById('mode').textContent=
 KB?'show: DISPLAY':'show: HHKB KEYBOARD';}}
document.getElementById('mode').onclick=()=>{{KB=!KB;setMode();}};
document.getElementById('play').onclick=e=>{{playing=!playing;
 e.target.innerHTML=playing?'&#9208; pause':'&#9654; play';}};
setMode();
setInterval(()=>{{if(playing)fi++;draw();}},80);
</script></body></html>"""
