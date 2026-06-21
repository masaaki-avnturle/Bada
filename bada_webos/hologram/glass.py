"""Fully transparent holographic display + Japanese HHKB keyboard.

No video content: the holographic display and the keyboard are rendered as
*glass* (outlines + faint tint + reflections) over a **camera passthrough**
background, so you see straight through them to the world behind the tablet —
and it stays see-through even while the app runs.  The keyboard is the Happy
Hacking layout with **Japanese input** (romaji -> kana), using the conversion
table defined in Bada (apps/hologram/lib/romaji_kana.bada).
"""

from __future__ import annotations

import json

from .keyboard import keys_with_labels


def html_glass(keys: list, kbd_width: int, kana_table: dict) -> str:
    return _TEMPLATE.format(
        keys=json.dumps(keys_with_labels(keys)), kw=kbd_width,
        kana=json.dumps(kana_table, ensure_ascii=False))


_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>透過ホログラフィー — 日本語HHKB</title>
<style>
 html,body{{margin:0;height:100%;overflow:hidden;background:
   radial-gradient(circle at 50% 35%,#0b1822,#05080e 70%);
   color:#dff;font-family:monospace}}
 /* camera passthrough — you see the world behind the transparent UI */
 #cam{{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;
   z-index:0;opacity:0.9}}
 #ui{{position:fixed;inset:0;z-index:1}}
 #bar{{position:fixed;left:0;right:0;top:0;z-index:2;display:flex;gap:12px;
   align-items:center;padding:8px 12px;font-size:13px;
   background:linear-gradient(#0008,#0000)}}
 #bar b{{color:#6fe}} .btn{{border:1px solid #6fe9;border-radius:8px;
   padding:3px 10px;color:#dff;background:#0a1a2a55;cursor:pointer}}
 #hint{{color:#9cc;font-size:12px}}
</style></head><body>
<video id="cam" autoplay playsinline muted></video>
<div id="bar"><b>&#x1F52E; 透過ホログラフィー</b>
 <span class="btn" id="mode">あ かな</span>
 <span class="btn" id="clear">クリア</span>
 <span id="hint">ローマ字で入力 → かな。 透明な表示とキーボードの向こうに背景が透けます。</span>
</div>
<canvas id="ui"></canvas>
<script>
const KEYS={keys}, KW={kw}, KANA={kana};
let kata=false, romaji="", committed="";
const cv=document.getElementById('ui'), cx=cv.getContext('2d');
function fit(){{cv.width=innerWidth;cv.height=innerHeight;}}
addEventListener('resize',fit); fit();

// --- camera passthrough (graceful fallback to the room gradient) ----------
(async()=>{{ try{{
  const st=await navigator.mediaDevices.getUserMedia(
    {{video:{{facingMode:{{ideal:'environment'}}}},audio:false}});
  document.getElementById('cam').srcObject=st;
}}catch(e){{ document.getElementById('cam').style.display='none'; }} }})();

// --- romaji -> kana (mirrors apps/hologram/lib/romaji_kana.bada) ----------
function isV(c){{return 'aiueo'.indexOf(c)>=0;}}
function toHira(s){{let out='',i=0;
 while(i<s.length){{let m=false;
  for(let L=3;L>=1&&!m;L--){{ if(i+L<=s.length){{const sub=s.slice(i,i+L);
   if(KANA[sub]!==undefined){{out+=KANA[sub];i+=L;m=true;}}}}}}
  if(!m){{const ch=s[i];
   if(ch!=='n'&&!isV(ch)&&i+1<s.length&&s[i+1]===ch){{out+='っ';i++;m=true;}}}}
  if(!m&&s[i]==='n'){{out+='ん';i++;m=true;}}
  if(!m){{out+=s[i];i++;}}
 }} return out;}}
function toKata(s){{return [...s].map(c=>{{const o=c.charCodeAt(0);
  return (o>=0x3041&&o<=0x3096)?String.fromCharCode(o+0x60):c;}}).join('');}}
function conv(s){{const h=toHira(s);return kata?toKata(h):h;}}

// --- input handling: hardware keys + on-screen glass keys -----------------
function feed(ch){{ romaji+=ch; }}
function commit(){{ committed+=conv(romaji); romaji=''; }}
function backspace(){{ if(romaji)romaji=romaji.slice(0,-1);
  else committed=committed.slice(0,-1); }}
addEventListener('keydown',e=>{{
 if(e.key.length===1&&/[a-zA-Z-]/.test(e.key)){{feed(e.key.toLowerCase());e.preventDefault();}}
 else if(e.key==='Backspace'){{backspace();e.preventDefault();}}
 else if(e.key===' '||e.key==='Enter'){{commit();
   if(e.key==='Enter')committed+='\\n'; e.preventDefault();}}
}});
document.getElementById('mode').onclick=()=>{{kata=!kata;
 document.getElementById('mode').textContent=kata?'ア カナ':'あ かな';}};
document.getElementById('clear').onclick=()=>{{romaji='';committed='';}};

// on-screen key geometry (Happy Hacking layout, from Bada)
function kbGeom(){{
 const U=Math.min((cv.width-24)/KW, 46);
 const w=KW*U, ox=(cv.width-w)/2, oy=cv.height-6*U;
 return {{U,ox,oy}};
}}
cv.addEventListener('click',e=>{{
 const r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;
 const {{U,ox,oy}}=kbGeom();
 for(const k of KEYS){{const x=ox+k.x*U+2,y=oy+k.y*U+2,kw=k.w*U-4,kh=U-4;
  if(mx>=x&&mx<=x+kw&&my>=y&&my<=y+kh){{press(k);return;}}}}
}});
function press(k){{
 const L=k.label;
 if(!k.special&&L.length===1&&/[a-z0-9-]/i.test(L)) feed(L.toLowerCase());
 else if(L==='del') backspace();
 else if(L==='⏎') {{commit();committed+='\\n';}}
 else if(L==='fn') {{kata=!kata;
   document.getElementById('mode').textContent=kata?'ア カナ':'あ かな';}}
 else if(L===''||L==='tab') commit();   // spacebar commits the preedit
}}

// --- glass rendering -------------------------------------------------------
function rrect(x,y,w,h,r){{cx.beginPath();cx.moveTo(x+r,y);
 cx.arcTo(x+w,y,x+w,y+h,r);cx.arcTo(x+w,y+h,x,y+h,r);
 cx.arcTo(x,y+h,x,y,r);cx.arcTo(x,y,x+w,y,r);cx.closePath();}}
function glassPanel(x,y,w,h,r){{
 cx.save();
 cx.fillStyle='rgba(120,220,255,0.06)';     // faint tint — still see-through
 rrect(x,y,w,h,r);cx.fill();
 cx.lineWidth=1.5;cx.strokeStyle='rgba(130,240,255,0.55)';
 cx.shadowColor='rgba(80,230,255,0.5)';cx.shadowBlur=14;cx.stroke();
 cx.shadowBlur=0;
 // top reflection streak
 cx.strokeStyle='rgba(220,255,255,0.18)';
 cx.beginPath();cx.moveTo(x+10,y+6);cx.lineTo(x+w-10,y+6);cx.stroke();
 cx.restore();
}}
function cornerTicks(x,y,w,h){{cx.strokeStyle='rgba(150,255,235,0.8)';
 cx.lineWidth=2;const s=14;
 const seg=(ax,ay,bx,by,cxp,cyp)=>{{cx.beginPath();cx.moveTo(ax,ay);
  cx.lineTo(bx,by);cx.moveTo(bx,by);cx.lineTo(cxp,cyp);cx.stroke();}};
 seg(x,y+s,x,y,x+s,y); seg(x+w-s,y,x+w,y,x+w,y+s);
 seg(x,y+h-s,x,y+h,x+s,y+h); seg(x+w-s,y+h,x+w,y+h,x+w,y+h-s);}}
function display(t){{
 const w=Math.min(cv.width-40,560),h=Math.min(cv.height*0.34,260);
 const x=(cv.width-w)/2,y=64;
 glassPanel(x,y,w,h,16); cornerTicks(x,y,w,h);
 // faint internal grid (still transparent)
 cx.strokeStyle='rgba(120,220,255,0.10)';cx.lineWidth=1;
 for(let i=1;i<6;i++){{cx.beginPath();cx.moveTo(x+i*w/6,y);cx.lineTo(x+i*w/6,y+h);cx.stroke();}}
 for(let j=1;j<4;j++){{cx.beginPath();cx.moveTo(x,y+j*h/4);cx.lineTo(x+w,y+j*h/4);cx.stroke();}}
 cx.fillStyle='rgba(180,245,255,'+(0.30+0.12*Math.sin(t*0.05))+')';
 cx.font='14px monospace';cx.textAlign='center';cx.textBaseline='middle';
 cx.fillText('ホログラフィーディスプレイ（透過）',cv.width/2,y+h/2-10);
 cx.fillStyle='rgba(150,220,235,0.5)';cx.font='11px monospace';
 cx.fillText('背景が透けて見えます — 動画なし',cv.width/2,y+h/2+12);
}}
function textbar(){{
 const w=Math.min(cv.width-40,560),h=44,x=(cv.width-w)/2,y=64+Math.min(cv.height*0.34,260)+12;
 glassPanel(x,y,w,h,10);
 cx.textAlign='left';cx.textBaseline='middle';cx.font='18px monospace';
 cx.fillStyle='rgba(225,255,250,0.95)';
 const pre=conv(romaji);
 const shown=committed.replace(/\\n/g,'  ');
 cx.fillText(shown,x+12,y+h/2);
 const cw=cx.measureText(shown).width;
 // preedit (underlined)
 cx.fillStyle='rgba(120,255,220,0.95)';
 cx.fillText(pre,x+12+cw,y+h/2);
 const pw=cx.measureText(pre).width;
 cx.strokeStyle='rgba(120,255,220,0.8)';cx.lineWidth=1.5;
 cx.beginPath();cx.moveTo(x+12+cw,y+h/2+12);cx.lineTo(x+12+cw+pw,y+h/2+12);cx.stroke();
 // caret
 if(Math.floor(Date.now()/500)%2===0){{cx.fillStyle='rgba(200,255,240,0.9)';
  cx.fillRect(x+12+cw+pw+1,y+h/2-10,2,20);}}
}}
function keyboard(t){{
 const {{U,ox,oy}}=kbGeom();
 for(const k of KEYS){{const x=ox+k.x*U+2,y=oy+k.y*U+2,w=k.w*U-4,h=U-4;
  const wave=0.5+0.5*Math.sin((k.x/KW)*6.283-t*0.05);
  cx.save();
  cx.fillStyle='rgba(120,220,255,'+(0.05+0.05*wave)+')';   // transparent cap
  rrect(x,y,w,h,5);cx.fill();
  cx.lineWidth=1;cx.strokeStyle='rgba(130,240,255,'+(0.35+0.3*wave)+')';
  cx.shadowColor='rgba(80,230,255,0.4)';cx.shadowBlur=6;cx.stroke();cx.shadowBlur=0;
  cx.fillStyle='rgba(220,255,250,0.85)';
  cx.font=(k.special?9:13)+'px monospace';
  cx.textAlign='center';cx.textBaseline='middle';
  cx.fillText(k.label,x+w/2,y+h/2);
  cx.restore();}}
 const {{U:UU}}=kbGeom();
 cx.fillStyle='rgba(150,220,235,0.6)';cx.font='11px monospace';cx.textAlign='center';
 cx.fillText('Happy Hacking Keyboard — 日本語（ローマ字）入力 · タップ／物理キー対応',
  cv.width/2, oy-10);
}}
let t=0;
function frame(){{ cx.clearRect(0,0,cv.width,cv.height);
 display(t); textbar(); keyboard(t); t++; requestAnimationFrame(frame); }}
frame();
</script></body></html>"""
