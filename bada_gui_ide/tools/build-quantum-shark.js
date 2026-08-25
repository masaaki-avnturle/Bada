#!/usr/bin/env node
/* ============================================================================
 * build-quantum-shark.js — build "QuantumShark", a single self-contained HTML
 * packet viewer/analyzer (Wireshark-style) whose capture files are ENCRYPTED
 * with the Jones-polynomial quantum cipher.
 *
 * The viewer loads a .qcap (produced by netcapture/cli/qshark-capture.js),
 * decrypts it with your master password (Jones cipher), and shows a
 * Wireshark-like packet table with a display filter and a details pane.
 * A small demo capture is inlined (master: "demo") so it opens alive.
 *
 * Output: ../dist/quantum-shark.html   (offline, no dependencies)
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");
const WWW = path.join(IDE, "www");
const DIST = path.join(IDE, "dist");
fs.mkdirSync(DIST, { recursive: true });

const badaCore = fs.readFileSync(path.join(WWW, "bada.js"), "utf8");
const cipherLib = fs.readFileSync(path.join(IDE, "modemvault", "modemvault-lib.bada"), "utf8");
const Bada = require(path.join(WWW, "bada.js"));
const VERSION = Bada.VERSION;

/* seal a demo capture (master "demo") to inline, and self-check open */
function seal(master, plain) {
  let out = [];
  Bada.run(cipherLib + "\nvault_seal(" + JSON.stringify(master) + ", 1717, " + JSON.stringify(plain) + ")\n",
    { maxSteps: 200000000, out: s => out.push(s) });
  const t = out.join("\n");
  const ct = /@@CT (\[[^\]]*\])/.exec(t), tag = /@@TAG (\d+)/.exec(t), sm = /@@SALT (\d+)/.exec(t);
  if (!ct || !tag || !sm) { console.error("seal failed:\n" + t); process.exit(1); }
  return { salt: parseInt(sm[1], 10), ct: JSON.parse(ct[1]), tag: parseInt(tag[1], 10) };
}
const demoRecords = [
  { no:1, time:"0.000000", src:"192.168.0.23", dst:"192.168.0.1",   proto:"DNS",     len:74,  info:"Standard query A example.com" },
  { no:2, time:"0.004120", src:"192.168.0.1",  dst:"192.168.0.23",  proto:"DNS",     len:90,  info:"Standard query response A 93.184.216.34" },
  { no:3, time:"0.005001", src:"192.168.0.23", dst:"93.184.216.34", proto:"TCP",     len:74,  info:"49832 > 443 [SYN] Seq=0 Win=64240" },
  { no:4, time:"0.028744", src:"93.184.216.34",dst:"192.168.0.23",  proto:"TCP",     len:74,  info:"443 > 49832 [SYN, ACK] Seq=0 Ack=1" },
  { no:5, time:"0.029001", src:"192.168.0.23", dst:"93.184.216.34", proto:"TLSv1.3", len:583, info:"Client Hello" },
  { no:6, time:"0.052210", src:"192.168.0.23", dst:"192.168.0.1",   proto:"ARP",     len:42,  info:"Who has 192.168.0.1? Tell 192.168.0.23" }
];
const demoQcap = {
  magic: "QCAP1", tool: "demo", count: demoRecords.length,
  check: seal("demo", "qshark-ok"),
  cap: seal("demo", JSON.stringify(demoRecords))
};
/* self-check: open with correct + wrong master */
(function () {
  const openProg = (m, r) => cipherLib + "\nvault_open(" + JSON.stringify(m) + ", " + r.salt + ", [" + r.ct.join(",") + "], " + r.tag + ")\n";
  let a = []; Bada.run(openProg("demo", demoQcap.cap), { maxSteps: 200000000, out: s => a.push(s) });
  if (a.join("\n").indexOf("@@PLAIN [") < 0) { console.error("demo open failed"); process.exit(1); }
  let b = []; Bada.run(openProg("nope", demoQcap.check), { maxSteps: 200000000, out: s => b.push(s) });
  if (b.join("\n").indexOf("@@FAIL") < 0) { console.error("wrong-master should fail"); process.exit(1); }
  console.log("self-check OK: demo .qcap decrypts with master \"demo\"; wrong master rejected");
})();

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>QuantumShark — 量子暗号つきパケット アナライザ</title>
<style>
  :root{color-scheme:light dark;--bg:#04060a;--panel:#0a1220;--line:#1c2838;--ink:#d6e2ee;
        --dim:#8aa0b8;--gold:#c8a44a;--green:#2e9e57;--red:#d0574a;--blue:#4a80d0;}
  *{box-sizing:border-box;} html,body{height:100%;}
  body{margin:0;background:var(--bg);color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}
  header{padding:12px 18px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#0a1220,#04060a);
         display:flex;gap:14px;align-items:center;flex-wrap:wrap;}
  h1{margin:0;font-size:17px;} h1 .a{color:var(--gold);}
  header .note{color:var(--dim);font-size:12px;}
  .bar{display:flex;gap:8px;align-items:center;padding:8px 18px;border-bottom:1px solid var(--line);background:#070c15;flex-wrap:wrap;}
  input,button{font:inherit;}
  input{background:#020407;border:1px solid var(--line);border-radius:7px;padding:7px 10px;color:var(--ink);}
  #filter{flex:1;min-width:200px;font-family:"SFMono-Regular",Consolas,monospace;}
  button.act{border:0;background:var(--green);color:#eafff0;border-radius:7px;padding:8px 14px;cursor:pointer;font-weight:600;}
  button.sec{border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:7px;padding:7px 12px;cursor:pointer;}
  main{height:calc(100% - 108px);display:flex;flex-direction:column;}
  #lock{padding:30px 18px;max-width:520px;}
  #lock .card{background:#070c15;border:1px solid var(--line);border-radius:12px;padding:18px;}
  label{display:block;font-size:12px;color:var(--dim);margin:8px 0 3px;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;font-family:"SFMono-Regular",Consolas,monospace;}
  thead th{position:sticky;top:0;background:#0c1626;color:var(--dim);text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);font-weight:600;}
  tbody td{padding:4px 8px;border-bottom:1px solid #0e1826;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  tbody tr{cursor:pointer;} tbody tr:hover{background:#0e1a2b;} tbody tr.sel{background:#13294a;}
  td.info{white-space:normal;color:#c7d6e6;}
  .p-DNS{color:#7ac0ff;} .p-TCP{color:#8fe0a8;} .p-ARP{color:#e0c07a;} .p-UDP{color:#c79bff;}
  .p-TLSv13,.p-TLS{color:#f0a3d0;} .p-ICMP{color:#f2a49b;} .p-HTTP{color:#9fe0ff;}
  #tablewrap{flex:1;overflow:auto;}
  #details{height:180px;border-top:1px solid var(--line);background:#020407;overflow:auto;padding:10px 14px;
           font-family:"SFMono-Regular",Consolas,monospace;font-size:12px;white-space:pre-wrap;}
  .pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:10px;margin-right:6px;}
  .ok{background:#123a24;color:#7ce0a3;} .bad{background:#3a1614;color:#f2a49b;} .info2{background:#12233a;color:#8fb6ff;}
  .hidden{display:none;} code{color:var(--gold);}
</style>
</head>
<body>
<header>
  <h1>Quantum<span class="a">Shark</span></h1>
  <span class="note">量子暗号(Jones)で暗号化されたパケット キャプチャを復号して解析 — 自分の通信の防御的分析用</span>
</header>

<div id="lockbar" class="bar">
  <span class="note">🔒 マスターパスワードで .qcap を復号します</span>
</div>

<main>
  <section id="lock">
    <div class="card">
      <b>キャプチャを開く</b>
      <p class="note">同梱デモを開くか(マスター: <code>demo</code>)、<code>qshark-capture.js</code> で作った自分の <code>.qcap</code> を選択してください。</p>
      <label>マスターパスワード</label>
      <input id="master" type="password" class="mono" value="demo"/>
      <div style="margin-top:12px">
        <button class="act" id="openDemo">デモを開く</button>
        <label style="display:inline-block;margin:0 0 0 8px">
          <input id="file" type="file" accept=".qcap,application/json" class="hidden"/>
          <button class="sec" id="pick">.qcap を選択</button>
        </label>
      </div>
      <div id="lockMsg" class="note" style="margin-top:10px"></div>
    </div>
  </section>

  <section id="app" class="hidden" style="display:flex;flex-direction:column;flex:1;min-height:0;">
    <div class="bar">
      <input id="filter" placeholder="表示フィルタ: proto/ip/文字列 (例: TCP, 192.168, Client Hello)"/>
      <span id="stat" class="note"></span>
      <button class="sec" id="close">閉じる</button>
    </div>
    <div id="tablewrap">
      <table>
        <thead><tr><th>No.</th><th>Time</th><th>Source</th><th>Destination</th><th>Protocol</th><th>Len</th><th>Info</th></tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </div>
    <div id="details">パケットを選択すると詳細を表示します。</div>
  </section>
</main>

<script>
/* ==== Bada core (inlined) ==== */
${badaCore}
</script>
<script>
var CIPHER_LIB = ${JSON.stringify(cipherLib)};
var DEMO_QCAP  = ${JSON.stringify(demoQcap)};
</script>
<script>
(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  var packets=[], filtered=[];

  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
  function openRec(master, rec){
    var out=[];
    BadaLang.run(CIPHER_LIB+"\\nvault_open("+JSON.stringify(master)+", "+rec.salt+", ["+rec.ct.join(",")+"], "+rec.tag+")\\n",
      {maxSteps:200000000,out:function(s){out.push(s);}});
    var t=out.join("\\n"),i=t.indexOf("@@PLAIN ");
    if(i<0) return null;
    return t.slice(i).split("\\n")[0].slice(8);
  }

  function loadQcap(qcap, master){
    /* verify master via the check record */
    var chk=openRec(master, qcap.check);
    if(chk!=="qshark-ok"){ return { ok:false, err:"マスターパスワードが違います(または破損しています)" }; }
    var plain=openRec(master, qcap.cap);
    if(plain===null){ return { ok:false, err:"復号に失敗しました" }; }
    var recs; try{ recs=JSON.parse(plain); }catch(e){ return { ok:false, err:"キャプチャの解析に失敗しました" }; }
    return { ok:true, records:recs };
  }

  function show(recs){
    packets=recs;
    $("lock").classList.add("hidden"); $("lockbar").classList.add("hidden");
    $("app").classList.remove("hidden");
    applyFilter();
  }
  function applyFilter(){
    var q=$("filter").value.trim().toLowerCase();
    filtered = !q ? packets : packets.filter(function(p){
      return (p.proto||"").toLowerCase().indexOf(q)>=0 ||
             (p.src||"").toLowerCase().indexOf(q)>=0 ||
             (p.dst||"").toLowerCase().indexOf(q)>=0 ||
             (p.info||"").toLowerCase().indexOf(q)>=0;
    });
    renderRows();
    $("stat").textContent = filtered.length+" / "+packets.length+" packets";
  }
  function protoClass(p){ return "p-"+String(p||"").replace(/[^A-Za-z0-9]/g,""); }
  function renderRows(){
    var tb=$("rows"); tb.innerHTML="";
    filtered.forEach(function(p,idx){
      var tr=document.createElement("tr");
      tr.innerHTML='<td>'+esc(p.no)+'</td><td>'+esc(p.time)+'</td><td>'+esc(p.src)+'</td><td>'+esc(p.dst)+
        '</td><td class="'+protoClass(p.proto)+'">'+esc(p.proto)+'</td><td>'+esc(p.len)+'</td><td class="info">'+esc(p.info)+'</td>';
      tr.addEventListener("click",function(){
        Array.prototype.forEach.call(tb.children,function(x){x.classList.remove("sel");});
        tr.classList.add("sel");
        $("details").textContent =
          "Frame "+p.no+":  "+p.len+" bytes\\n"+
          "Time (relative): "+p.time+"\\n"+
          "Source:      "+p.src+"\\n"+
          "Destination: "+p.dst+"\\n"+
          "Protocol:    "+p.proto+"\\n"+
          "Info:        "+p.info+"\\n\\n"+
          "(このキャプチャは Jones 量子暗号で暗号化された .qcap から復号されました)";
      });
      tb.appendChild(tr);
    });
  }

  function tryOpen(qcap){
    var m=$("master").value;
    var r=loadQcap(qcap, m);
    if(!r.ok){ $("lockMsg").innerHTML='<span class="pill bad">'+esc(r.err)+'</span>'; return; }
    $("lockMsg").textContent=""; show(r.records);
  }

  $("openDemo").addEventListener("click", function(){ tryOpen(DEMO_QCAP); });
  $("pick").addEventListener("click", function(){ $("file").click(); });
  $("file").addEventListener("change", function(){
    var f=this.files && this.files[0]; if(!f) return;
    var rd=new FileReader();
    rd.onload=function(){ try{ var q=JSON.parse(String(rd.result)); tryOpen(q); }
      catch(e){ $("lockMsg").innerHTML='<span class="pill bad">.qcap の読み込みに失敗しました</span>'; } };
    rd.readAsText(f);
  });
  $("filter").addEventListener("input", applyFilter);
  $("close").addEventListener("click", function(){
    $("app").classList.add("hidden"); $("lock").classList.remove("hidden"); $("lockbar").classList.remove("hidden");
  });
})();
</script>
</body>
</html>
`;

fs.writeFileSync(path.join(DIST, "quantum-shark.html"), html);
console.log("built dist/quantum-shark.html (" + fs.statSync(path.join(DIST, "quantum-shark.html")).size + " bytes)");
