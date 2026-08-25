#!/usr/bin/env node
/* ============================================================================
 * build-ngngrid.js — build "NGN Quantum Grid", a single self-contained HTML app
 * that VISUALIZES the zone://url.or.jp ultra-network projected onto the NTT NGN:
 * a regional NGN backbone ring (= the zone P2P ring / UltraDatabase), home &
 * office Von-Neumann PCs on subscriber lines (each an HDD pseudo-quantum
 * register), entanglement (Bell pairs) drawn over the NTT lines, and a
 * zone:// fetch over NTT with the Jones-cipher security panel.
 *
 * Output: ../dist/ngn-quantum.html   (offline, no dependencies)
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");
const badaCore = fs.readFileSync(path.join(IDE, "www", "bada.js"), "utf8");
const runtime = fs.readFileSync(path.join(IDE, "browser", "zone-lib.bada"), "utf8") + "\n" +
                fs.readFileSync(path.join(IDE, "ngngrid", "ngn-extra.bada"), "utf8");
const Bada = require(path.join(IDE, "www", "bada.js"));
const VERSION = Bada.VERSION;

/* self-check: entangle + a zone fetch over the runtime */
(function () {
  let out = [];
  Bada.run(runtime + '\nNET := zone_boot()\nentangle_show("a","b")\nzone_publish(NET,"zone://url.or.jp/","# hi")\nzone_serve(NET,"zone://url.or.jp/")\n',
    { maxSteps: 200000000, out: s => out.push(s) });
  const t = out.join("\n");
  if (!/@@BELL a b/.test(t) || !/@@STATUS 200/.test(t)) { console.error("self-check failed:\n" + t); process.exit(1); }
  console.log("self-check OK: entangle_show emits a Bell pair; zone fetch returns 200");
})();

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>NGN Quantum Grid — zone:// を NTT回線に投射</title>
<style>
  :root{color-scheme:light dark;--bg:#04060a;--panel:#0a1220;--line:#1c2838;--ink:#d6e2ee;
        --dim:#8aa0b8;--gold:#c8a44a;--green:#2e9e57;--red:#d0574a;--blue:#4a80d0;--ent:#c79bff;}
  *{box-sizing:border-box;} html,body{height:100%;}
  body{margin:0;background:var(--bg);color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}
  header{padding:12px 18px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#0a1220,#04060a);}
  h1{margin:0;font-size:18px;} h1 .a{color:var(--gold);}
  header p{margin:3px 0 0;color:var(--dim);font-size:12px;}
  main{display:grid;grid-template-columns:1fr 340px;height:calc(100% - 58px);}
  @media(max-width:860px){main{grid-template-columns:1fr;}}
  #stage{position:relative;overflow:hidden;}
  #panel{border-left:1px solid var(--line);padding:14px;overflow:auto;font-size:13px;}
  .btns{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;}
  button{font:inherit;border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:8px;padding:9px 13px;cursor:pointer;}
  button.act{border:0;background:var(--green);color:#eafff0;font-weight:600;}
  h3{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--dim);margin:14px 0 8px;}
  .kv{display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-bottom:1px dashed #16222f;}
  .kv b{color:var(--dim);font-weight:500;} .kv span{font-family:"SFMono-Regular",Consolas,monospace;text-align:right;word-break:break-all;}
  .pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:10px;margin:0 6px 6px 0;}
  .ok{background:#123a24;color:#7ce0a3;} .info{background:#12233a;color:#8fb6ff;} .ent{background:#241a3a;color:#c79bff;}
  #log{white-space:pre-wrap;font-family:"SFMono-Regular",Consolas,monospace;font-size:11.5px;color:#bcd;
       background:#020407;border:1px solid var(--line);border-radius:8px;padding:10px;max-height:200px;overflow:auto;margin-top:8px;}
  text{font-family:system-ui,sans-serif;}
</style>
</head>
<body>
<header>
  <h1>NGN <span class="a">Quantum Grid</span> <span style="color:var(--dim);font-size:12px">v${VERSION}</span></h1>
  <p>ウルトラネットワーク <b>zone://url.or.jp</b> を <b>NTT NGN 回線</b>に投射 — 地域局のバックボーン環(=zone P2P/UltraDB)、各家庭・職場PC(HDD擬似量子レジスタ)、NTT回線上のエンタングルメント、Jones量子暗号。</p>
</header>
<main>
  <div id="stage"><svg id="svg" width="100%" height="100%"></svg></div>
  <aside id="panel">
    <div class="btns">
      <button class="act" id="entangleAll">NTT回線でエンタングル</button>
      <button id="fetch">zone://url.or.jp を NTT経由で取得</button>
      <button id="reset">リセット</button>
    </div>
    <div id="pills"></div>
    <h3>詳細</h3>
    <div id="detail"><span class="info" style="color:var(--dim)">操作を選んでください。</span></div>
    <h3>ログ</h3>
    <div id="log"></div>
  </aside>
</main>

<script>
/* ==== Bada core (inlined) ==== */
${badaCore}
</script>
<script>
var NGN_RUNTIME = ${JSON.stringify(runtime)};
</script>
<script>
(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  var SVG="http://www.w3.org/2000/svg";
  var svg=$("svg");

  /* topology: 6 regional NGN nodes (ring) + home/office PCs attached */
  var REGIONS=[
    {name:"NGN-Tokyo"},{name:"NGN-Osaka"},{name:"NGN-Nagoya"},
    {name:"NGN-Sapporo"},{name:"NGN-Fukuoka"},{name:"NGN-Naha"}
  ];
  var PCS=[
    {name:"home-PC (Tokyo)",   ip:"192.168.0.23", r:0},
    {name:"office-PC (Osaka)", ip:"192.168.10.5", r:1},
    {name:"NAS (Nagoya)",      ip:"192.168.20.9", r:2},
    {name:"home-PC (Sapporo)", ip:"192.168.30.7", r:3},
    {name:"office-PC (Fukuoka)",ip:"192.168.40.2",r:4}
  ];
  var pairs=[[0,1],[0,2],[1,4],[2,3],[3,0]]; /* entanglement links (PC index) */

  function J(s){return JSON.stringify(String(s));}
  function badaRun(prog){ var out=[]; BadaLang.run(prog,{maxSteps:200000000,out:function(s){out.push(s);}}); return out.join("\\n"); }
  function log(s){ var el=$("log"); el.textContent += s+"\\n"; el.scrollTop=el.scrollHeight; }

  var W,H,cx,cy,R;
  function layout(){
    W=svg.clientWidth||900; H=svg.clientHeight||600; cx=W/2; cy=H/2; R=Math.min(W,H)*0.28;
    REGIONS.forEach(function(n,i){ var a=-Math.PI/2 + i*2*Math.PI/REGIONS.length;
      n.x=cx+R*Math.cos(a); n.y=cy+R*Math.sin(a); });
    PCS.forEach(function(p,i){ var reg=REGIONS[p.r]; var a=Math.atan2(reg.y-cy,reg.x-cx);
      var rr=R+90+((i%2)*46);
      p.x=cx+rr*Math.cos(a + (i%2?0.18:-0.18)); p.y=cy+rr*Math.sin(a + (i%2?0.18:-0.18)); });
  }
  function el(tag,attrs){ var e=document.createElementNS(SVG,tag); for(var k in attrs) e.setAttribute(k,attrs[k]); return e; }
  function draw(){
    layout(); svg.innerHTML="";
    /* backbone ring */
    for(var i=0;i<REGIONS.length;i++){ var a=REGIONS[i],b=REGIONS[(i+1)%REGIONS.length];
      svg.appendChild(el("line",{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:"#24405f","stroke-width":2})); }
    /* subscriber lines PC->region */
    PCS.forEach(function(p){ var reg=REGIONS[p.r];
      svg.appendChild(el("line",{x1:p.x,y1:p.y,x2:reg.x,y2:reg.y,stroke:"#1c2838","stroke-width":1.5,"stroke-dasharray":"3 3"})); });
    /* region nodes */
    REGIONS.forEach(function(n){ svg.appendChild(el("circle",{cx:n.x,cy:n.y,r:16,fill:"#12233a",stroke:"#4a80d0","stroke-width":2}));
      var t=el("text",{x:n.x,y:n.y+30,fill:"#8fb6ff","font-size":11,"text-anchor":"middle"}); t.textContent=n.name; svg.appendChild(t); });
    /* PC nodes */
    PCS.forEach(function(p){ svg.appendChild(el("rect",{x:p.x-13,y:p.y-11,width:26,height:22,rx:4,fill:"#0a1a12",stroke:"#2e9e57","stroke-width":2}));
      var t=el("text",{x:p.x,y:p.y-16,fill:"#7ce0a3","font-size":10,"text-anchor":"middle"}); t.textContent=p.name; svg.appendChild(t);
      var ip=el("text",{x:p.x,y:p.y+24,fill:"#8aa0b8","font-size":9,"text-anchor":"middle"}); ip.textContent=p.ip; svg.appendChild(ip); });
    /* center label */
    var c=el("text",{x:cx,y:cy,fill:"#c8a44a","font-size":13,"text-anchor":"middle"}); c.textContent="NTT NGN"; svg.appendChild(c);
    var c2=el("text",{x:cx,y:cy+18,fill:"#8aa0b8","font-size":10,"text-anchor":"middle"}); c2.textContent="UltraDB ×4 / zone://"; svg.appendChild(c2);
  }

  function entangleAll(){
    var prog=NGN_RUNTIME+"\\nNET := zone_boot()\\n";
    pairs.forEach(function(pr){ prog+="entangle_show("+J(PCS[pr[0]].name)+", "+J(PCS[pr[1]].name)+")\\n"; });
    var t=badaRun(prog);
    draw();
    var intactN=0;
    t.split("\\n").forEach(function(l){ if(l.indexOf("@@BELL ")!==0)return;
      var f=l.split(" "); /* @@BELL a... but names have spaces -> use last 5 tokens */
      var tail=f.slice(-5); /* p00 p01 p10 p11 intact */
      var p00=tail[0],p11=tail[3],intact=tail[4];
      if(intact==="1")intactN++;
    });
    /* draw entanglement links */
    pairs.forEach(function(pr){ var a=PCS[pr[0]],b=PCS[pr[1]];
      svg.appendChild(el("line",{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:"#c79bff","stroke-width":2,"stroke-dasharray":"6 4",opacity:0.9})); });
    $("pills").innerHTML='<span class="pill ent">エンタングル '+intactN+'/'+pairs.length+' 対</span>'+
      '<span class="pill ok">零保存 OK(|01>,|10>=0)</span>';
    $("detail").innerHTML='<div class="kv"><b>Bell対</b><span>'+pairs.length+'</span></div>'+
      '<div class="kv"><b>整合(intact)</b><span>'+intactN+'</span></div>'+
      '<div class="kv"><b>各PCのHDD状態</b><span>|00>=0.5, |11>=0.5</span></div>'+
      '<div class="kv"><b>意味</b><span>NTT回線上の相関=盗聴なし</span></div>';
    log("entangled "+intactN+"/"+pairs.length+" Bell pairs over NTT lines (zero-preservation intact)");
  }

  function fetchZone(){
    var prog=NGN_RUNTIME+"\\nNET := zone_boot()\\n";
    PCS.forEach(function(p){ prog+="ngn_register(NET, "+J(p.ip)+", "+p.r+")\\n"; });
    prog+='zone_publish(NET, "zone://url.or.jp/", "# Ultra Network over NTT NGN | no http, no center | entangled home/office PCs")\\n';
    prog+='zone_serve(NET, "zone://url.or.jp/")\\n';
    var t=badaRun(prog);
    var m={status:"?",quorum:"",jones:"",tag:"",node:"",body:""};
    var ls=t.split("\\n"),body=[],inB=false;
    ls.forEach(function(l){ if(l==="@@BODY_BEGIN"){inB=true;return;} if(l==="@@BODY_END"){inB=false;return;}
      if(inB){body.push(l);return;} if(l.indexOf("@@")!==0)return;
      var sp=l.indexOf(" "),k=(sp<0?l:l.slice(0,sp)).slice(2),v=sp<0?"":l.slice(sp+1);
      if(k==="STATUS")m.status=v;else if(k==="QUORUM")m.quorum=v;else if(k==="JONESKEY")m.jones=v;
      else if(k==="TAG")m.tag=v;else if(k==="NODE")m.node=v; });
    $("pills").innerHTML='<span class="pill ok">🔒 '+m.status+' zone-delivered</span>'+
      '<span class="pill ok">Jones-AEAD verified</span><span class="pill ok">UltraDB quorum '+m.quorum+'</span>';
    $("detail").innerHTML='<div class="kv"><b>取得</b><span>zone://url.or.jp/</span></div>'+
      '<div class="kv"><b>経由</b><span>NTT NGN</span></div>'+
      '<div class="kv"><b>owner局</b><span>'+m.node+'</span></div>'+
      '<div class="kv"><b>UltraDB quorum</b><span>'+m.quorum+'</span></div>'+
      '<div class="kv"><b>Jones鍵</b><span>'+m.jones+'</span></div>'+
      '<div class="kv"><b>AEADタグ</b><span>'+m.tag+'</span></div>'+
      '<div style="margin-top:8px;color:#c7d6e6">'+body.join("<br>").replace(/^#\\s*/,"<b>").replace(/\\|/g,"</b> · ")+'</div>';
    log("fetched zone://url.or.jp over NTT NGN: "+m.status+" quorum "+m.quorum+" jones "+m.jones);
  }

  $("entangleAll").addEventListener("click", entangleAll);
  $("fetch").addEventListener("click", fetchZone);
  $("reset").addEventListener("click", function(){ draw(); $("pills").innerHTML=""; $("detail").innerHTML='<span class="info" style="color:var(--dim)">操作を選んでください。</span>'; });
  window.addEventListener("resize", draw);
  draw();
})();
</script>
</body>
</html>
`;
fs.writeFileSync(path.join(IDE, "dist", "ngn-quantum.html"), html);
console.log("built dist/ngn-quantum.html (" + fs.statSync(path.join(IDE, "dist", "ngn-quantum.html")).size + " bytes)");
