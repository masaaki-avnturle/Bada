"""Quantum Cache Disk dashboard.

Renders the hard disk reinterpreted as a quantum cache (bit patterns -> qubit
amplitudes), the Reviser rewriting von-Neumann cache ops into quantum gates, the
Grover a-priori prediction engine amplifying the DNA-telomere "thought pattern",
the Jones-polynomial thermal network, the Gamma integration-by-parts manifold,
and the semiconductor uncertainty bound — all computed in Bada.
"""

from __future__ import annotations

import json


def html_qcache(data: dict) -> str:
    return _TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))


_TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Quantum Cache Disk — Bada</title>
<style>
 body{margin:0;background:#04070e;color:#cfe;font-family:monospace}
 .bar{padding:9px 12px;background:#070c18;border-bottom:2px solid #2a8;
   display:flex;gap:12px;align-items:center;flex-wrap:wrap}
 .bar b{color:#5fe;letter-spacing:1px}
 .wrap{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));
   gap:12px;padding:12px}
 .card{background:#0a1322;border:1px solid #21406a;border-radius:12px;padding:12px;
   box-shadow:0 0 16px #0a6a5522}
 .card h3{margin:0 0 8px;color:#6fe;font-size:13px}
 .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
 .blk{background:#0c1a2e;border:1px solid #1c3a52;border-radius:7px;padding:5px;
   font-size:10px;text-align:center}
 .blk.hot{border-color:#fe6;box-shadow:0 0 12px #fe680;background:#1a2238}
 .blk .a{height:5px;border-radius:3px;background:linear-gradient(90deg,#1aa,#5fe);
   margin-top:4px}
 table{width:100%;border-collapse:collapse;font-size:12px}
 td,th{border:1px solid #1c3a52;padding:3px 6px;text-align:center}
 th{color:#7cd} .gate{color:#fe7}
 .gauge{height:16px;background:#0c1a2e;border:1px solid #1c3a52;border-radius:8px;
   overflow:hidden;margin-top:6px}
 .gauge>div{height:100%;background:linear-gradient(90deg,#1aa,#6fe)}
 canvas{display:block;width:100%;background:#0a1322;border-radius:8px}
 .k{color:#fe7} .s{color:#9ab;font-size:11px}
</style></head><body>
<div class="bar"><b>&#9883; QUANTUM CACHE DISK</b>
 <span class="s">ハードディスク → 量子キャッシュ · Reviserでノイマン型を量子化 · 計算はBada</span></div>
<div class="wrap">
 <div class="card"><h3>量子キャッシュディスク（ビットパターン→量子振幅）</h3>
   <div class="grid" id="disk"></div>
   <div class="s" id="diskcap" style="margin-top:6px"></div></div>
 <div class="card"><h3>Reviser: ノイマン型 → 量子ゲート</h3>
   <table id="rev"><tr><th>von Neumann</th><th>quantum</th></tr></table></div>
 <div class="card"><h3>事前エンジン（DNAテロメア思考パターン予知 / Grover）</h3>
   <div class="s">telomere length</div>
   <div class="gauge"><div id="telo"></div></div>
   <div class="s" style="margin-top:6px">予測ブロック <span class="k" id="pb"></span>
     · 増幅後ヒット確率 <span class="k" id="hp"></span></div>
   <div class="gauge"><div id="hpg"></div></div>
   <canvas id="curve" width="280" height="70"></canvas></div>
 <div class="card"><h3>Jones多項式 熱ネットワーク（t=e<sup>-β</sup>）</h3>
   <canvas id="thermal" width="280" height="90"></canvas></div>
 <div class="card"><h3>Γ 大域的部分積分多様体（Γ(z+1)=z·Γ(z)）</h3>
   <table id="gamma"><tr><th>z</th><th>Γ(z)</th><th>z·Γ(z)</th><th>Γ(z+1)</th></tr></table></div>
 <div class="card"><h3>半導体の不確定性原理</h3>
   <div class="s">Δaddr · Δdata ≥ ħ/2</div>
   <div id="unc" style="margin-top:8px;font-size:13px"></div></div>
</div>
<script>
const D=__DATA__;
// disk grid
const disk=document.getElementById('disk');
function bin(n,w){let s=n.toString(2);while(s.length<w)s='0'+s;return s;}
D.patterns.forEach((p,i)=>{const d=document.createElement('div');d.className='blk';
 d.id='blk'+i;
 d.innerHTML='#'+i+'<br>'+bin(p,D.nbits)
  +'<div class="a" style="width:'+Math.round(D.amps[i]/Math.max.apply(0,D.amps)*100)+'%"></div>';
 disk.appendChild(d);});
document.getElementById('diskcap').textContent=
 '|ψ⟩ = Σ aᵢ|blockᵢ⟩ , Σaᵢ²=1 （ハードディスクが量子コンピュータに）';
// reviser table
const rev=document.getElementById('rev');
D.reviser.forEach(r=>{const tr=document.createElement('tr');
 tr.innerHTML='<td>'+r[0]+'</td><td class="gate">'+r[1]+'</td>';rev.appendChild(tr);});
// gamma table
const gt=document.getElementById('gamma');
D.gamma.forEach(g=>{const tr=document.createElement('tr');
 tr.innerHTML='<td>'+g[0]+'</td><td>'+g[1]+'</td><td>'+g[2]+'</td><td>'+g[2]+'</td>';
 gt.appendChild(tr);});
// uncertainty
document.getElementById('unc').innerHTML=
 'ħ='+D.unc.hbar.toExponential(3)+' , Δaddr='+D.unc.d_addr
 +' ⟹ Δdata ≥ <span class="k">'+D.unc.bound.toExponential(3)+'</span>';
// thermal curve
(function(){const c=document.getElementById('thermal'),x=c.getContext('2d');
 const T=D.thermal,mx=Math.max.apply(0,T.map(p=>p[1]))||1;
 x.strokeStyle='#5fe';x.lineWidth=2;x.beginPath();
 T.forEach((p,i)=>{const px=i/(T.length-1)*c.width,py=c.height-p[1]/mx*(c.height-10)-5;
  i?x.lineTo(px,py):x.moveTo(px,py);});x.stroke();
 x.fillStyle='#7cd';x.font='10px monospace';x.fillText('Z(β)=|V(e^-β)|',6,12);})();
// prediction animation over telomere division steps
const curve=document.getElementById('curve'),cx=curve.getContext('2d');
let t=0;
function frame(){
 const T=D.predicted.length;
 const pb=D.predicted[t%T], hp=D.curve[t%T];
 for(let i=0;i<D.patterns.length;i++){
  document.getElementById('blk'+i).classList.toggle('hot', i===pb);}
 document.getElementById('pb').textContent='#'+pb;
 document.getElementById('hp').textContent=(hp*100).toFixed(1)+'%';
 document.getElementById('hpg').style.width=Math.round(hp*100)+'%';
 const telo=D.teloMax-(t%T);
 document.getElementById('telo').style.width=
  Math.round(Math.max(0,telo)/D.teloMax*100)+'%';
 // curve of hit prob
 cx.clearRect(0,0,curve.width,curve.height);
 cx.strokeStyle='#6fe';cx.lineWidth=2;cx.beginPath();
 D.curve.forEach((p,i)=>{const px=i/(D.curve.length-1)*curve.width,
  py=curve.height-p*(curve.height-10)-5; i?cx.lineTo(px,py):cx.moveTo(px,py);});
 cx.stroke();
 cx.fillStyle='#fe7';const cxp=(t%T)/(D.curve.length-1)*curve.width;
 cx.beginPath();cx.arc(cxp,curve.height-D.curve[t%T]*(curve.height-10)-5,3,0,7);cx.fill();
 cx.fillStyle='#7cd';cx.font='10px monospace';cx.fillText('prefetch hit prob',6,12);
 t++;
}
setInterval(frame,700);frame();
</script></body></html>"""
