"""Holographic Happy Hacking Keyboard — the HHKB layout (computed in Bada)
rendered as a floating, glowing hologram.

The HHKB Professional (US) arrangement comes from apps/hologram/lib/keyboard.bada
as [x, y, w, code] keys; Python maps each code to its glyph and the canvas
renderer floats the keyboard above a conductive-plastic plane, with the keycaps
mounded up and a holographic ripple sweeping across them (浮き上がる).
"""

from __future__ import annotations

import json

# code -> (label, is_special)
_SPECIAL = {
    256: "esc", 257: "tab", 258: "ctrl", 259: "shift", 260: "⏎",
    261: "del", 262: "fn", 263: "◇", 264: "alt", 265: "",
}


def code_label(code: int) -> str:
    if code in _SPECIAL:
        return _SPECIAL[code]
    return chr(code) if 33 <= code <= 126 else "?"


def keys_with_labels(keys: list) -> list:
    out = []
    for x, y, w, code in keys:
        out.append({"x": x, "y": y, "w": w,
                    "label": code_label(int(code)),
                    "special": int(code) >= 256})
    return out


def html_keyboard(keys: list, width: int, rows: int,
                  power: float, jones: str = "") -> str:
    klabs = keys_with_labels(keys)
    return _TEMPLATE.format(keys=json.dumps(klabs), width=width, rows=rows,
                            power=round(power, 2), jones=jones)


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<title>Holographic Happy Hacking Keyboard</title>
<style>
 body{{margin:0;background:#01040a;color:#bfe;font-family:monospace}}
 .bar{{padding:8px 12px;background:#04070f;border-bottom:2px solid #1a8;
   display:flex;gap:14px;align-items:center;flex-wrap:wrap}}
 .bar b{{color:#3fd;letter-spacing:1px}} .hud{{font-size:12px;color:#7fd}}
 .hud b{{color:#fe7}} button{{background:#0a1320;color:#cfe;border:1px solid #245;
   padding:3px 8px;font-family:monospace;cursor:pointer}}
 #stage{{display:flex;justify-content:center;padding:18px}}
 #cap{{text-align:center;color:#69a;font-size:12px;padding:0 12px 16px}}
 .k{{color:#3fd}}
</style></head><body>
<div class="bar"><b>&#x1F52E; HOLOGRAPHIC HAPPY HACKING KEYBOARD</b>
 <button id="play">&#9208; pause</button>
 <span class="hud">layout: <b>HHKB Professional (US)</b> · {width}U · {rows} rows</span>
 <span class="hud">power <b>{power}W</b></span>
 <span class="hud" id="jw"></span></div>
<div id="stage"><canvas id="kb" width="720" height="420"></canvas></div>
<div id="cap">the Happy Hacking Keyboard floats up out of the conductive-plastic
 plane · layout computed in <span class="k">Bada</span> · a holographic ripple
 mounds the keycaps up · hover/click a key to light it</div>
<script>
const KEYS={keys}, WIDTH={width}, JONES="{jones}";
if(JONES)document.getElementById('jw').innerHTML='Jones V(t)=<b>'+JONES+'</b>';
const kb=document.getElementById('kb'), cx=kb.getContext('2d');
const U=42, OX=(kb.width-WIDTH*U)/2, OY=70, GAP=3;
let t=0, playing=true, hover=-1, flash={{}};
kb.addEventListener('mousemove',e=>{{const r=kb.getBoundingClientRect();
 hover=hit(e.clientX-r.left,e.clientY-r.top);}});
kb.addEventListener('mouseleave',()=>hover=-1);
kb.addEventListener('click',e=>{{const r=kb.getBoundingClientRect();
 const h=hit(e.clientX-r.left,e.clientY-r.top); if(h>=0)flash[h]=1;}});
function keyRect(k){{return [OX+k.x*U+GAP, OY+k.y*U+GAP, k.w*U-2*GAP, U-2*GAP];}}
function hit(mx,my){{for(let i=0;i<KEYS.length;i++){{
 const[x,y,w,h]=keyRect(KEYS[i]); const lift=liftOf(KEYS[i]);
 if(mx>=x&&mx<=x+w&&my>=y-lift&&my<=y+h-lift)return i;}}return -1;}}
function liftOf(k){{
 // a ripple sweeping left->right mounds the keys up (Jones-relief shimmer)
 const cxk=k.x+k.w/2, wave=Math.sin((cxk/WIDTH)*6.283-t*0.06);
 return 10+8*Math.max(0,wave);}}
function rrect(x,y,w,h,r){{cx.beginPath();
 cx.moveTo(x+r,y);cx.arcTo(x+w,y,x+w,y+h,r);cx.arcTo(x+w,y+h,x,y+h,r);
 cx.arcTo(x,y+h,x,y,r);cx.arcTo(x,y,x+w,y,r);cx.closePath();}}
function plane(){{cx.fillStyle='#01040a';cx.fillRect(0,0,kb.width,kb.height);
 cx.strokeStyle='rgba(40,140,140,0.10)';cx.lineWidth=1;
 for(let i=0;i<=16;i++){{const x=i/16*kb.width;
  cx.beginPath();cx.moveTo(x,OY+10);cx.lineTo(x,kb.height);cx.stroke();}}
 const g=cx.createRadialGradient(kb.width/2,kb.height*0.8,10,
  kb.width/2,kb.height*0.8,kb.width*0.55);
 g.addColorStop(0,'rgba(10,70,70,0.22)');g.addColorStop(1,'rgba(0,0,0,0)');
 cx.fillStyle=g;cx.fillRect(0,0,kb.width,kb.height);}}
function draw(){{
 plane();
 // contact shadows first
 for(const k of KEYS){{const[x,y,w,h]=keyRect(k);
  cx.save();cx.globalAlpha=0.25;cx.fillStyle='#000';
  rrect(x+3,y+8,w,h*0.5,6);cx.fill();cx.restore();}}
 // floating keycaps
 for(let i=0;i<KEYS.length;i++){{const k=KEYS[i];
  const[x,y,w,h]=keyRect(k); const lift=liftOf(k);
  const ky=y-lift; const fl=flash[i]||0; const hv=(i===hover);
  const glow=0.35+0.4*((lift-10)/8)+(hv?0.4:0)+fl*0.8;
  cx.save();
  cx.shadowColor='rgba(60,255,210,'+Math.min(1,glow)+')';
  cx.shadowBlur=10+18*glow;
  const g=cx.createLinearGradient(x,ky,x,ky+h);
  g.addColorStop(0,'rgba(20,'+Math.round(90+120*glow)+',120,0.95)');
  g.addColorStop(1,'rgba(6,28,40,0.92)');
  cx.fillStyle=g; rrect(x,ky,w,h,6); cx.fill();
  cx.shadowBlur=0;
  cx.strokeStyle='rgba(80,255,220,'+Math.min(1,0.4+glow)+')';
  cx.lineWidth=k.special?1:1.4; cx.stroke();
  // top relief highlight
  cx.strokeStyle='rgba(180,255,240,'+(0.15+0.3*glow)+')';
  cx.beginPath();cx.moveTo(x+5,ky+3);cx.lineTo(x+w-5,ky+3);cx.stroke();
  // label
  cx.fillStyle='rgba(225,255,250,'+Math.min(1,0.7+glow)+')';
  cx.font=(k.special?11:14)+'px monospace';
  cx.textAlign='center';cx.textBaseline='middle';
  cx.fillText(k.label,x+w/2,ky+h/2+1);
  cx.restore();
  if(flash[i]){{flash[i]-=0.06; if(flash[i]<=0)delete flash[i];}}
 }}
}}
document.getElementById('play').onclick=e=>{{playing=!playing;
 e.target.innerHTML=playing?'&#9208; pause':'&#9654; play';}};
setInterval(()=>{{if(playing)t++;draw();}},45);
</script></body></html>"""
