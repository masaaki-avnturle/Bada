#!/usr/bin/env node
/* ============================================================================
 * build-zoneimport.js — build "LAN → zone://", a single self-contained HTML app
 * that imports the IP addresses on YOUR OWN PC / LAN into the ultra-network as
 * encrypted zone:// records under zone://url.or.jp/lan/.
 *
 * Each imported IP becomes a zone page published across the UltraDatabase
 * quorum and sealed with the Jones-polynomial quantum cipher (browser/
 * zone-lib.bada). Reading it back shows 200 + quorum + Jones-AEAD verified.
 *
 * Output: ../dist/lan-to-zone.html   (offline, no dependencies)
 * Companion real detector: ../zoneimport/cli/lan-to-zone.js (Node).
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");
const WWW = path.join(IDE, "www");
const BR = path.join(IDE, "browser");
const DIST = path.join(IDE, "dist");
fs.mkdirSync(DIST, { recursive: true });

const badaCore = fs.readFileSync(path.join(WWW, "bada.js"), "utf8");
const zoneLib = fs.readFileSync(path.join(BR, "zone-lib.bada"), "utf8");
const Bada = require(path.join(WWW, "bada.js"));
const VERSION = Bada.VERSION;

/* self-check: publish a lan page and read it back -> 200 */
(function () {
  const prog = zoneLib +
    '\nNET := zone_boot()\n' +
    'zone_publish(NET, "zone://url.or.jp/lan/192.168.0.2", "# LAN node 192.168.0.2\\nimported")\n' +
    'zone_serve(NET, "zone://url.or.jp/lan/192.168.0.2")\n';
  let out = [];
  Bada.run(prog, { maxSteps: 20000000, out: s => out.push(s) });
  if (!/@@STATUS 200/.test(out.join("\n"))) { console.error("self-check failed:\n" + out.join("\n")); process.exit(1); }
  console.log("self-check OK: a LAN IP publishes to zone:// and reads back 200");
})();

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>LAN → zone:// — 自分のLAN IPをウルトラネットワークに取り込む</title>
<style>
  :root{color-scheme:light dark;--bg:#04060a;--panel:#0a1220;--line:#1c2838;--ink:#d6e2ee;
        --dim:#8aa0b8;--gold:#c8a44a;--green:#2e9e57;--red:#d0574a;--blue:#4a80d0;}
  *{box-sizing:border-box;}
  body{margin:0;background:var(--bg);color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;line-height:1.55;}
  header{padding:16px 22px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#0a1220,#04060a);}
  h1{margin:0;font-size:19px;} h1 .a{color:var(--gold);}
  header p{margin:4px 0 0;color:var(--dim);font-size:12.5px;}
  main{display:grid;grid-template-columns:300px 1fr;gap:0;min-height:calc(100vh - 62px);}
  @media(max-width:820px){main{grid-template-columns:1fr;}}
  #side{border-right:1px solid var(--line);padding:16px;overflow:auto;}
  #view{padding:22px 26px;overflow:auto;}
  h3{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--dim);margin:0 0 10px;}
  label{display:block;font-size:12px;color:var(--dim);margin:8px 0 3px;}
  input{width:100%;background:#020407;border:1px solid var(--line);border-radius:8px;padding:8px 10px;color:var(--ink);font-family:"SFMono-Regular",Consolas,monospace;font-size:13px;}
  button.act{border:0;background:var(--green);color:#eafff0;border-radius:8px;padding:9px 14px;cursor:pointer;font-weight:600;}
  button.sec{border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:8px;padding:8px 12px;cursor:pointer;}
  button.mini{border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:6px;padding:4px 9px;cursor:pointer;font-size:12px;}
  .ipitem{border:1px solid var(--line);border-radius:8px;padding:9px 10px;margin-top:8px;cursor:pointer;font-family:"SFMono-Regular",Consolas,monospace;font-size:13px;}
  .ipitem:hover{background:#101d2e;} .ipitem.on{border-color:#38537a;background:#12233a;}
  .ipitem .z{color:var(--blue);font-size:11px;word-break:break-all;}
  .pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:10px;margin-right:6px;}
  .ok{background:#123a24;color:#7ce0a3;} .bad{background:#3a1614;color:#f2a49b;} .info{background:#12233a;color:#8fb6ff;}
  .doc h1{font-size:24px;margin:0 0 6px;} .doc h2{font-size:18px;color:var(--gold);margin:18px 0 6px;}
  .doc p{margin:8px 0;max-width:60ch;} .doc a{color:var(--blue);text-decoration:none;}
  .kv{display:flex;justify-content:space-between;gap:8px;padding:5px 0;border-bottom:1px dashed #16222f;font-size:12.5px;}
  .kv b{color:var(--dim);font-weight:500;} .kv span{font-family:monospace;text-align:right;word-break:break-all;}
  .note{color:var(--dim);font-size:12.5px;} code{color:var(--gold);}
</style>
</head>
<body>
<header>
  <h1>LAN → <span class="a">zone://</span></h1>
  <p>自分のPC/LANのIPアドレスを、ウルトラネットワーク <code>zone://url.or.jp/lan/</code> に暗号化して取り込みます(P2P DHT + Jones量子暗号)。ローカル・オフライン。</p>
</header>
<main>
  <nav id="side">
    <h3>IP を追加 / 検出</h3>
    <button class="act" id="detect">自分のIPを検出 (WebRTC)</button>
    <div class="row" style="margin-top:10px">
      <label>IP を手動追加</label>
      <input id="ipin" placeholder="192.168.0.23"/>
      <label>ラベル(任意)</label>
      <input id="labelin" placeholder="例: 自分のPC / NAS"/>
      <div style="margin-top:8px"><button class="sec" id="add">追加</button>
        <button class="sec" id="importAll">全て zone:// に取り込む</button></div>
    </div>
    <h3 style="margin-top:18px">取り込んだ LAN ノード</h3>
    <div id="list"></div>
  </nav>
  <section id="view"><p class="note">左でIPを検出/追加し、「取り込む」を押すと zone://url.or.jp/lan/&lt;IP&gt; として暗号化公開されます。</p></section>
</main>

<script>
/* ==== Bada core (inlined) ==== */
${badaCore}
</script>
<script>
var ZONE_LIB = ${JSON.stringify(zoneLib)};
</script>
<script>
(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  var KEY="lan2zone.v1";
  var sel=null;

  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
  function J(s){return JSON.stringify(String(s));}
  function load(){ try{return JSON.parse(localStorage.getItem(KEY)||'{"nodes":[]}');}catch(e){return {nodes:[]};} }
  function save(s){ try{localStorage.setItem(KEY,JSON.stringify(s));}catch(e){} }

  function zurl(ip){ return "zone://url.or.jp/lan/"+ip; }
  function pageFor(n){
    var lines=["# LAN node "+n.ip];
    lines.push(n.label? ("label: "+n.label) : "registered into the ultra-network from my PC");
    lines.push("imported: "+(n.at||""));
    return lines.join("\\n");
  }
  function indexPage(nodes){
    var l=["# LAN zone index","このゾーンに取り込まれた自分のLANノード:"];
    nodes.forEach(function(n){ l.push("-> "+zurl(n.ip)+" | "+n.ip+(n.label?(" ("+n.label+")"):"")); });
    return l.join("\\n");
  }

  /* build the per-op Bada program: boot + publish all imported + serve target */
  function run(target){
    var s=load();
    var prog=ZONE_LIB+"\\nNET := zone_boot()\\n";
    s.nodes.forEach(function(n){ prog+="zone_publish(NET, "+J(zurl(n.ip))+", "+J(pageFor(n))+")\\n"; });
    prog+="zone_publish(NET, "+J("zone://url.or.jp/lan/")+", "+J(indexPage(s.nodes))+")\\n";
    prog+="zone_serve(NET, "+J(target)+")\\n";
    var out=[];
    BadaLang.run(prog,{maxSteps:20000000,out:function(x){out.push(x);}});
    return out.join("\\n");
  }
  function parse(t){
    var m={status:"?",quorum:"",jones:"",tag:"",node:"",key:"",body:""};
    var ls=t.split("\\n"),body=[],inB=false;
    for(var i=0;i<ls.length;i++){var ln=ls[i];
      if(ln==="@@BODY_BEGIN"){inB=true;continue;} if(ln==="@@BODY_END"){inB=false;continue;}
      if(inB){body.push(ln);continue;} if(ln.indexOf("@@")!==0)continue;
      var sp=ln.indexOf(" "),k=(sp<0?ln:ln.slice(0,sp)).slice(2),v=sp<0?"":ln.slice(sp+1);
      if(k==="STATUS")m.status=v; else if(k==="QUORUM")m.quorum=v; else if(k==="JONESKEY")m.jones=v;
      else if(k==="TAG")m.tag=v; else if(k==="NODE")m.node=v; else if(k==="KEY")m.key=v;
    }
    m.body=body.join("\\n"); return m;
  }

  function renderList(){
    var s=load(),box=$("list");
    if(!s.nodes.length){ box.innerHTML='<p class="note">まだありません。</p>'; return; }
    box.innerHTML="";
    s.nodes.forEach(function(n){
      var d=document.createElement("div"); d.className="ipitem"+(sel===n.ip?" on":"");
      d.innerHTML=esc(n.ip)+(n.label?' <span class="note">'+esc(n.label)+'</span>':'')+
        (n.imported?' <span class="pill ok">取込済</span>':' <span class="pill info">未取込</span>')+
        '<div class="z">'+esc(zurl(n.ip))+'</div>'+
        '<div style="margin-top:6px"><button class="mini" data-a="imp" data-ip="'+esc(n.ip)+'">取り込む</button> '+
        '<button class="mini" data-a="open" data-ip="'+esc(n.ip)+'">開く</button> '+
        '<button class="mini" data-a="del" data-ip="'+esc(n.ip)+'">削除</button></div>';
      box.appendChild(d);
    });
    box.querySelectorAll("button[data-a]").forEach(function(b){
      b.addEventListener("click",function(e){ e.stopPropagation();
        var ip=this.getAttribute("data-ip"),a=this.getAttribute("data-a");
        if(a==="del")delNode(ip); else if(a==="imp")importNode(ip); else openNode(ip);
      });
    });
  }

  function addNode(ip,label){
    if(!/^\\d+\\.\\d+\\.\\d+\\.\\d+$/.test(ip)){ alert("IPv4アドレスを入力してください"); return; }
    var s=load(); if(s.nodes.some(function(n){return n.ip===ip;})){ return; }
    s.nodes.push({ip:ip,label:label||"",imported:false,at:""}); save(s); renderList();
  }
  function delNode(ip){ var s=load(); s.nodes=s.nodes.filter(function(n){return n.ip!==ip;}); save(s); if(sel===ip)sel=null; renderList(); }
  function importNode(ip){
    var s=load(),n=s.nodes.filter(function(x){return x.ip===ip;})[0]; if(!n)return;
    n.at=new Date().toISOString().slice(0,19).replace("T"," "); n.imported=true; save(s);
    openNode(ip);
    renderList();
  }
  function openNode(ip){
    sel=ip; renderList();
    var t=run(zurl(ip)); var m=parse(t);
    var v=$("view");
    if(m.status!=="200"){
      v.innerHTML='<div class="doc"><span class="pill bad">'+esc(m.status)+'</span><p>まだ取り込まれていません。「取り込む」を押してください。</p></div>';
      return;
    }
    var bodyHtml="";
    m.body.split("\\n").forEach(function(ln){ ln=ln.replace(/\\s+$/,""); if(!ln)return;
      var mm;
      if((mm=/^#\\s+(.*)$/.exec(ln)))bodyHtml+='<h1>'+esc(mm[1])+'</h1>';
      else if((mm=/^->\\s*(\\S+)\\s*\\|\\s*(.*)$/.exec(ln)))bodyHtml+='<p><a href="#" data-z="'+esc(mm[1])+'">'+esc(mm[2])+'</a></p>';
      else bodyHtml+='<p>'+esc(ln)+'</p>';
    });
    v.innerHTML='<div class="doc">'+
      '<p><span class="pill ok">🔒 200 zone-delivered</span><span class="pill ok">Jones-AEAD verified</span>'+
      '<span class="pill ok">UltraDB quorum '+esc(m.quorum||"—")+'</span></p>'+bodyHtml+
      '<hr style="border-color:#16222f;margin:16px 0"/>'+
      '<div class="kv"><b>zone URL</b><span>'+esc(zurl(ip))+'</span></div>'+
      '<div class="kv"><b>owner node</b><span>'+esc(m.node)+'</span></div>'+
      '<div class="kv"><b>DHT key</b><span>'+esc(m.key)+'</span></div>'+
      '<div class="kv"><b>Jones key</b><span>'+esc(m.jones)+'</span></div>'+
      '<div class="kv"><b>AEAD tag</b><span>'+esc(m.tag)+'</span></div>'+
      '<div class="kv"><b>UltraDB quorum</b><span>'+esc(m.quorum)+'</span></div></div>';
    v.querySelectorAll("a[data-z]").forEach(function(a){ a.addEventListener("click",function(e){e.preventDefault();
      var z=this.getAttribute("data-z"); var ipm=/lan\\/(\\d+\\.\\d+\\.\\d+\\.\\d+)/.exec(z); if(ipm)openNode(ipm[1]); }); });
  }

  $("add").addEventListener("click",function(){ addNode($("ipin").value.trim(),$("labelin").value.trim()); $("ipin").value=$("labelin").value=""; });
  $("importAll").addEventListener("click",function(){ var s=load(); s.nodes.forEach(function(n){ n.imported=true; if(!n.at)n.at=new Date().toISOString().slice(0,19).replace("T"," "); }); save(s); renderList(); if(s.nodes[0])openNode(s.nodes[0].ip); });
  $("detect").addEventListener("click",function(){
    var pc; try{pc=new RTCPeerConnection({iceServers:[]});}catch(e){ alert("WebRTC利用不可。手動で追加してください。"); return; }
    var found={}; pc.createDataChannel("x");
    pc.onicecandidate=function(ev){ if(!ev||!ev.candidate){fin();return;}
      var m=/(\\d+\\.\\d+\\.\\d+\\.\\d+)/.exec(ev.candidate.candidate); if(m&&!/^0\\./.test(m[1]))found[m[1]]=1; };
    pc.createOffer().then(function(o){return pc.setLocalDescription(o);});
    var done=false; setTimeout(fin,1200);
    function fin(){ if(done)return; done=true; try{pc.close();}catch(e){}
      var ips=Object.keys(found);
      if(!ips.length){ alert("自動取得できませんでした(ブラウザのプライバシー保護)。手動で追加してください。"); return; }
      ips.forEach(function(ip){ addNode(ip,"検出したIP"); });
    }
  });

  renderList();
})();
</script>
</body>
</html>
`;

fs.writeFileSync(path.join(DIST, "lan-to-zone.html"), html);
console.log("built dist/lan-to-zone.html (" + fs.statSync(path.join(DIST, "lan-to-zone.html")).size + " bytes)");
