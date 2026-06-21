"""Vision-Pro-equivalent spatial display: launch the hologram on the tablet and
the tablet turns transparent (passthrough) while its applications float out as
spatial windows.

The windows are anchored at the mirror-state lens focal depth and arranged on a
concave shell around the viewer (positions computed in Bada); the tablet's
passthrough transparency, the per-window depth scaling and head-parallax all
come from Bada too.  The centre window is the live holographic display and the
HHKB keyboard floats in front as the spatial input.
"""

from __future__ import annotations

import json

from .keyboard import keys_with_labels


def _round_frames(frames):
    return [[[round(v, 3) for v in row] for row in g] for g in frames]


def html_vision(apps: list, positions: list, display_frames: list,
                light_frames: list, n: int, keys: list, kbd_width: int,
                focus_cm: float, gap_cm: float) -> str:
    return _TEMPLATE.format(
        apps=json.dumps(apps), pos=json.dumps(positions),
        dframes=json.dumps(_round_frames(display_frames)),
        light=json.dumps(_round_frames(light_frames)), n=n,
        keys=json.dumps(keys_with_labels(keys)), kw=kbd_width,
        focus=round(focus_cm, 2), gap=gap_cm)


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<title>Spatial Hologram — Vision-Pro-equivalent passthrough</title>
<style>
 body{{margin:0;background:#05060a;color:#cfe;font-family:monospace}}
 .bar{{padding:8px 12px;background:#04070f;border-bottom:2px solid #1a8;
   display:flex;gap:14px;align-items:center;flex-wrap:wrap}}
 .bar b{{color:#3fd;letter-spacing:1px}} .hud{{font-size:12px;color:#7fd}}
 .hud b{{color:#fe7}} button{{background:#0a1320;color:#cfe;border:1px solid #245;
   padding:3px 8px;font-family:monospace;cursor:pointer}}
 #stage{{display:flex;justify-content:center;padding:12px}}
 #cap{{text-align:center;color:#69a;font-size:12px;padding:0 12px 14px}}
 .k{{color:#3fd}}
</style></head><body>
<div class="bar"><b>&#x1F453; SPATIAL HOLOGRAM (passthrough)</b>
 <button id="launch">&#x21bb; re-launch</button>
 <button id="play">&#9208; pause</button>
 <span class="hud">tablet <b id="tp"></b></span>
 <span class="hud">focus z=<b>{focus}</b>cm / gap {gap}cm</span>
 <span class="hud">move the mouse = look around (head parallax + gaze)</span></div>
<div id="stage"><canvas id="cv" width="760" height="620"></canvas></div>
<div id="cap">launch the display and the tablet goes <span class="k">transparent
 </span> (passthrough) · its apps float out as <span class="k">spatial windows</span>
 on a concave shell (Bada) anchored at the mirror-lens focus · the
 <span class="k">HHKB</span> keyboard floats in front · gaze (hover) to focus a
 window</div>
<script>
const APPS={apps}, POS={pos}, DFRAMES={dframes}, LIGHT={light}, N={n};
const KEYS={keys}, KW={kw};
const cv=document.getElementById('cv'), cx=cv.getContext('2d');
let fi=0, playing=true, launch=0, headX=0, headY=0, hover=-1, focusW=0;
cv.addEventListener('mousemove',e=>{{const r=cv.getBoundingClientRect();
 headX=((e.clientX-r.left)/cv.width-0.5)*2; headY=((e.clientY-r.top)/cv.height-0.5)*2;
 hover=pick(e.clientX-r.left,e.clientY-r.top);}});
cv.addEventListener('click',e=>{{if(hover>=0)focusW=hover;}});

// depth bookkeeping: z in [5,10] (from Bada); near=bigger
function dscale(z){{const t=Math.max(0,Math.min(1,(z-5)/5));return 1-0.45*t;}}
function parallax(z){{return headX*10/Math.max(0.01,z);}}
function rrect(x,y,w,h,r){{cx.beginPath();cx.moveTo(x+r,y);
 cx.arcTo(x+w,y,x+w,y+h,r);cx.arcTo(x+w,y+h,x,y+h,r);
 cx.arcTo(x,y+h,x,y,r);cx.arcTo(x,y,x+w,y,r);cx.closePath();}}

// ---- live content for the display window (surface * light) ---------------
function hsl2rgb(h,s,l){{const a=s*Math.min(l,1-l);
 const f=k=>{{const x=(k+h*12)%12;return l-a*Math.max(-1,Math.min(x-3,9-x,1));}};
 return [Math.round(f(0)*255),Math.round(f(8)*255),Math.round(f(4)*255)];}}
let rangeC=null;
function rng(){{if(rangeC)return rangeC;let lo=1e9,hi=-1e9;
 for(const g of DFRAMES)for(const r of g)for(const v of r){{
  if(v<lo)lo=v;if(v>hi)hi=v;}}return rangeC=[lo,(hi>lo?hi:lo+1)];}}
function sample(g,u,v){{let gx=(u+1)/2*(N-1),gy=(v+1)/2*(N-1);
 gx=Math.max(0,Math.min(N-1,gx));gy=Math.max(0,Math.min(N-1,gy));
 const i0=Math.floor(gx),j0=Math.floor(gy),i1=Math.min(i0+1,N-1),
  j1=Math.min(j0+1,N-1),fx=gx-i0,fy=gy-j0;
 const a=g[i0][j0]*(1-fx)+g[i1][j0]*fx,b=g[i0][j1]*(1-fx)+g[i1][j1]*fx;
 return a*(1-fy)+b*fy;}}
const RES=140, off=document.createElement('canvas');
off.width=off.height=RES; const octx=off.getContext('2d');
function dispTile(){{const g=DFRAMES[fi%DFRAMES.length],lg=LIGHT[fi%LIGHT.length];
 const[lo,hi]=rng(),span=(hi-lo)||1,img=octx.createImageData(RES,RES),d=img.data;
 for(let py=0;py<RES;py++)for(let px=0;px<RES;px++){{
  const idx=(py*RES+px)*4,u=px/(RES-1)*2-1,v=py/(RES-1)*2-1;
  let z=(sample(g,u,v)-lo)/span;z=Math.max(0,Math.min(1,z));
  let lit=Math.max(0,Math.min(1,sample(lg,u,v)/0.5));
  const c=hsl2rgb((1-z)*0.55,0.9,(0.10+z*0.34)*(0.4+0.6*lit));
  d[idx]=c[0];d[idx+1]=c[1];d[idx+2]=c[2];d[idx+3]=255;}}
 octx.putImageData(img,0,0);}}

// ---- window geometry: fly out from the tablet to the arc on launch -------
const cxs=cv.width/2, TABY=cv.height-58;
function winBox(i){{
 const p=POS[i], sc=dscale(p[2])*(0.55+0.45*launch);
 const ax=cxs+p[0]*32+parallax(p[2])*launch;     // arc target x (+ parallax)
 const ay=180+(10-p[2])*10 + headY*8*launch;      // arc target y
 const tx=cxs, ty=TABY-20;                         // tablet origin
 const x=tx+(ax-tx)*launch, y=ty+(ay-ty)*launch;   // interpolate on launch
 const w=150*sc, h=104*sc;
 return [x-w/2,y-h/2,w,h,sc,p[2]];
}}
function pick(mx,my){{let best=-1,bz=-1;
 for(let i=0;i<APPS.length;i++){{const[x,y,w,h,sc,z]=winBox(i);
  if(mx>=x&&mx<=x+w&&my>=y&&my<=y+h&&z>bz){{best=i;bz=z;}}}}return best;}}
function world(){{
 const g=cx.createLinearGradient(0,0,0,cv.height);
 g.addColorStop(0,'#0a1018');g.addColorStop(0.6,'#0c141c');g.addColorStop(1,'#06090e');
 cx.fillStyle=g;cx.fillRect(0,0,cv.width,cv.height);
 // faint passthrough "room" so you see the world through the tablet
 cx.strokeStyle='rgba(60,110,130,0.06)';cx.lineWidth=1;
 for(let i=0;i<=14;i++){{const x=i/14*cv.width;
  cx.beginPath();cx.moveTo(x,cv.height*0.5);cx.lineTo(cv.width/2,cv.height*0.5);
  cx.lineTo(x,cv.height);cx.stroke();}}}}
function tablet(){{
 const a=1-0.85*launch;                            // passthrough_alpha(launch)
 document.getElementById('tp').textContent=
  launch>0.5?('transparent ('+a.toFixed(2)+')'):'opaque';
 const w=300,h=40,x=cxs-w/2,y=TABY;
 cx.save();cx.globalAlpha=Math.max(0.12,a);
 const g=cx.createLinearGradient(x,y,x,y+h);
 g.addColorStop(0,'rgba(40,90,110,'+(0.5*a+0.1)+')');
 g.addColorStop(1,'rgba(10,30,40,'+(0.5*a+0.1)+')');
 cx.fillStyle=g;rrect(x,y,w,h,8);cx.fill();
 cx.strokeStyle='rgba(120,220,230,'+(0.5*a+0.2)+')';cx.lineWidth=1.5;cx.stroke();
 cx.fillStyle='rgba(180,230,240,'+(0.5*a+0.4)+')';cx.font='11px monospace';
 cx.textAlign='center';cx.textBaseline='middle';
 cx.fillText(launch>0.5?'tablet — transparent / passthrough':'tablet',
  cxs,y+h/2);cx.restore();}}
function drawWin(i){{
 const[x,y,w,h,sc,z]=winBox(i); const app=APPS[i];
 const hl=(i===hover)||(i===focusW); const blur=Math.max(0,(10-z)/5);
 cx.save();
 cx.globalAlpha=Math.min(1,launch*1.2)*(0.7+0.3*sc);
 cx.shadowColor='rgba(60,220,255,'+(hl?0.7:0.35)+')';cx.shadowBlur=hl?26:14;
 // glassmorphic card
 const g=cx.createLinearGradient(x,y,x,y+h);
 g.addColorStop(0,'rgba(30,60,80,0.55)');g.addColorStop(1,'rgba(12,24,34,0.5)');
 cx.fillStyle=g;rrect(x,y,w,h,10);cx.fill();
 cx.shadowBlur=0;cx.strokeStyle='rgba(120,230,255,'+(hl?0.9:0.5)+')';
 cx.lineWidth=hl?2:1;cx.stroke();
 // title bar
 cx.fillStyle='rgba(200,240,255,0.9)';cx.font=(11*sc+3)+'px monospace';
 cx.textAlign='left';cx.textBaseline='top';cx.fillText(app.title,x+10,y+8);
 // content
 if(app.kind==='display'){{dispTile();cx.imageSmoothingEnabled=true;
  cx.drawImage(off,x+10,y+26,w-20,h-34);}}
 else{{cx.font=(28*sc)+'px monospace';cx.textAlign='center';
  cx.fillStyle='rgba(120,220,255,0.85)';
  cx.fillText(app.glyph,x+w/2,y+h/2+6);}}
 cx.restore();
}}
// ---- the spatial HHKB keyboard floating in front -------------------------
function keyboard(){{
 const U=22*(0.7+0.3*launch), w=KW*U, ox=cxs-w/2+headX*10*launch,
  oy=TABY-150+headY*6*launch;
 cx.save();cx.globalAlpha=Math.min(1,launch*1.3);
 for(const k of KEYS){{const x=ox+k.x*U+1.5,y=oy+k.y*U+1.5,kw=k.w*U-3,kh=U-3;
  const wave=Math.sin((k.x/KW)*6.283-fi*0.1),glow=0.35+0.4*Math.max(0,wave);
  cx.shadowColor='rgba(60,255,210,'+glow+')';cx.shadowBlur=6+8*glow;
  const g=cx.createLinearGradient(x,y,x,y+kh);
  g.addColorStop(0,'rgba(20,'+Math.round(90+110*glow)+',120,0.92)');
  g.addColorStop(1,'rgba(6,26,38,0.88)');
  cx.fillStyle=g;rrect(x,y,kw,kh,3);cx.fill();cx.shadowBlur=0;
  cx.strokeStyle='rgba(80,255,220,'+(0.35+glow)+')';cx.stroke();
  cx.fillStyle='rgba(225,255,250,0.9)';cx.font=(k.special?7:10)+'px monospace';
  cx.textAlign='center';cx.textBaseline='middle';
  cx.fillText(k.label,x+kw/2,y+kh/2);}}
 cx.restore();}}
function draw(){{
 world();
 // windows back-to-front (far/high-z first)
 const order=APPS.map((a,i)=>i).sort((a,b)=>winBox(b)[5]-winBox(a)[5]);
 for(const i of order)drawWin(i);
 keyboard();
 tablet();
}}
document.getElementById('launch').onclick=()=>{{launch=0;}};
document.getElementById('play').onclick=e=>{{playing=!playing;
 e.target.innerHTML=playing?'&#9208; pause':'&#9654; play';}};
setInterval(()=>{{if(playing)fi++; if(launch<1)launch=Math.min(1,launch+0.03);
 draw();}},70);
</script></body></html>"""
