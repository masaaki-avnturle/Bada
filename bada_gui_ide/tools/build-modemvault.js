#!/usr/bin/env node
/* ============================================================================
 * build-modemvault.js — build "Modem Vault", a single self-contained HTML app:
 *   1) a quantum-cipher password vault for YOUR OWN network gear (the Jones
 *      cipher from modemvault/modemvault-lib.bada; stores only what you type),
 *   2) LAN modem detection helpers (your PC IP via WebRTC, suggested gateway
 *      + admin URLs, MAC->vendor OUI lookup) — no passwords are ever handled.
 *
 * Output: ../dist/modem-vault.html  (offline, no dependencies).
 * A companion real detector is modemvault/cli/modem-scan.js (Node).
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");
const WWW = path.join(IDE, "www");
const MV = path.join(IDE, "modemvault");
const DIST = path.join(IDE, "dist");
fs.mkdirSync(DIST, { recursive: true });

const badaCore = fs.readFileSync(path.join(WWW, "bada.js"), "utf8");
const vaultLib = fs.readFileSync(path.join(MV, "modemvault-lib.bada"), "utf8");
const oui = JSON.parse(fs.readFileSync(path.join(MV, "oui.json"), "utf8")).prefixes || {};
const Bada = require(path.join(WWW, "bada.js"));
const VERSION = Bada.VERSION;

/* self-check: seal then open must round-trip; wrong master must fail */
(function () {
  const secret = "Aterm admin: p@ss 密2024";
  let out = [];
  Bada.run(vaultLib + '\nvault_seal("m4ster", 1234, ' + JSON.stringify(secret) + ')\n',
    { maxSteps: 20000000, out: s => out.push(s) });
  const txt = out.join("\n");
  const ctm = /@@CT (\[[^\]]*\])/.exec(txt), tagm = /@@TAG (\d+)/.exec(txt);
  if (!ctm || !tagm) { console.error("seal failed:\n" + txt); process.exit(1); }
  const ct = ctm[1], tag = tagm[1];
  let o2 = [];
  Bada.run(vaultLib + '\nvault_open("m4ster", 1234, ' + ct + ', ' + tag + ')\n', { maxSteps: 20000000, out: s => o2.push(s) });
  if (o2.join("\n").indexOf("@@PLAIN " + secret) < 0) { console.error("open(correct) failed:\n" + o2.join("\n")); process.exit(1); }
  let o3 = [];
  Bada.run(vaultLib + '\nvault_open("WRONG", 1234, ' + ct + ', ' + tag + ')\n', { maxSteps: 20000000, out: s => o3.push(s) });
  if (o3.join("\n").indexOf("@@FAIL") < 0) { console.error("open(wrong) should fail:\n" + o3.join("\n")); process.exit(1); }
  console.log("self-check OK: seal/open round-trips, wrong master rejected");
})();

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Modem Vault — 量子暗号パスワード保管庫 + LANモデム検出</title>
<style>
  :root{color-scheme:light dark;--bg:#04060a;--panel:#0a1220;--line:#1c2838;--ink:#d6e2ee;
        --dim:#8aa0b8;--gold:#c8a44a;--green:#2e9e57;--red:#d0574a;--blue:#4a80d0;}
  *{box-sizing:border-box;}
  body{margin:0;background:var(--bg);color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;line-height:1.55;}
  header{padding:16px 22px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#0a1220,#04060a);}
  h1{margin:0;font-size:19px;} h1 .a{color:var(--gold);}
  header p{margin:4px 0 0;color:var(--dim);font-size:12.5px;}
  main{max-width:860px;margin:0 auto;padding:18px 22px 60px;}
  .tabs{display:flex;gap:8px;margin-bottom:16px;}
  .tab{border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:9px;padding:9px 16px;cursor:pointer;}
  .tab.on{background:#1c2f49;border-color:#38537a;}
  .card{background:#070c15;border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px;}
  label{display:block;font-size:12px;color:var(--dim);margin:8px 0 3px;}
  input{width:100%;background:#020407;border:1px solid var(--line);border-radius:8px;padding:9px 11px;color:var(--ink);font-size:14px;}
  input.mono{font-family:"SFMono-Regular",Consolas,monospace;}
  button.act{border:0;background:var(--green);color:#eafff0;border-radius:9px;padding:10px 18px;cursor:pointer;font-weight:600;font-size:14px;}
  button.sec{border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:9px;padding:9px 14px;cursor:pointer;}
  button.mini{border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:7px;padding:5px 10px;cursor:pointer;font-size:12px;}
  .row{display:flex;gap:10px;flex-wrap:wrap;align-items:end;}
  .row>div{flex:1;min-width:150px;}
  .entry{border:1px solid var(--line);border-radius:10px;padding:12px;margin-top:10px;}
  .entry .top{display:flex;justify-content:space-between;gap:8px;align-items:center;}
  .entry .model{font-weight:600;} .entry .meta{color:var(--dim);font-size:12px;font-family:monospace;}
  .pass{font-family:"SFMono-Regular",Consolas,monospace;background:#020407;border:1px solid var(--line);
        border-radius:7px;padding:8px 10px;margin-top:8px;word-break:break-all;}
  .pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:10px;margin-right:6px;}
  .ok{background:#123a24;color:#7ce0a3;} .bad{background:#3a1614;color:#f2a49b;} .info{background:#12233a;color:#8fb6ff;}
  .note{color:var(--dim);font-size:12.5px;}
  .hidden{display:none;}
  code{color:var(--gold);}
  a{color:var(--blue);}
</style>
</head>
<body>
<header>
  <h1>Modem <span class="a">Vault</span> <span class="note">v${VERSION}</span></h1>
  <p>Jones 量子暗号でまもる、<b>あなた自身の</b>モデム認証情報の保管庫 + LANモデム検出。すべてローカル・オフラインで動作します。</p>
</header>
<main>
  <div class="tabs">
    <button class="tab on" data-tab="vault">🔐 保管庫</button>
    <button class="tab" data-tab="lan">🛰 LAN検出</button>
  </div>

  <!-- ================= VAULT ================= -->
  <section id="tab-vault">
    <div class="card" id="lockCard">
      <div id="createBox" class="hidden">
        <b>マスターパスワードを設定</b>
        <p class="note">保管庫を暗号化する鍵になります。忘れると復号できません(どこにも保存されません)。</p>
        <label>マスターパスワード</label>
        <input id="newMaster" type="password" class="mono" autocomplete="new-password"/>
        <div style="margin-top:12px"><button class="act" id="createBtn">保管庫を作成</button></div>
      </div>
      <div id="unlockBox" class="hidden">
        <b>保管庫を解錠</b>
        <label>マスターパスワード</label>
        <input id="master" type="password" class="mono" autocomplete="current-password"/>
        <div style="margin-top:12px" class="row" style="align-items:center">
          <div style="flex:0"><button class="act" id="unlockBtn">解錠</button></div>
          <div id="unlockMsg" class="note"></div>
        </div>
      </div>
    </div>

    <div id="vaultBox" class="hidden">
      <div class="card">
        <b>モデム認証情報を追加</b>
        <p class="note">あなたが自分で入力した内容だけを暗号化して保存します。型番から割り出すことはしません。</p>
        <div class="row">
          <div><label>モデム型番</label><input id="e_model" class="mono" placeholder="例: Aterm WX3000HP"/></div>
          <div><label>ラベル(任意)</label><input id="e_label" placeholder="例: 自宅ルーター"/></div>
        </div>
        <div class="row">
          <div><label>パスコード(WiFiキー or 管理PW)</label><input id="e_pass" class="mono"/></div>
        </div>
        <div class="row">
          <div><label>ゲートウェイIP(任意)</label><input id="e_gwip" class="mono" placeholder="192.168.0.1"/></div>
          <div><label>MAC(任意)</label><input id="e_gwmac" class="mono" placeholder="AA:BB:CC:DD:EE:FF"/></div>
        </div>
        <div style="margin-top:12px"><button class="act" id="addBtn">暗号化して保存</button>
          <button class="sec" id="lockBtn">ロック</button></div>
      </div>
      <div id="entries"></div>
    </div>
  </section>

  <!-- ================= LAN ================= -->
  <section id="tab-lan" class="hidden">
    <div class="card">
      <b>自分のPC / LAN を検出</b>
      <p class="note">ブラウザからは自分のPCのIPまで確認できます。ゲートウェイ(モデム)のMACや型番の確実な取得は、同梱の CLI <code>node cli/modem-scan.js</code> をお使いください。パスワードは一切扱いません。</p>
      <button class="act" id="detectBtn">自分のIPを検出 (WebRTC)</button>
      <div id="lanOut" style="margin-top:12px"></div>
    </div>
    <div class="card">
      <b>MAC ベンダー照合 (OUI)</b>
      <p class="note">モデム/ルーターの MAC アドレスを入力すると、メーカーを推定します(型番の目安)。</p>
      <div class="row">
        <div><label>MAC アドレス</label><input id="macIn" class="mono" placeholder="00:60:B9:xx:xx:xx"/></div>
        <div style="flex:0"><label>&nbsp;</label><button class="sec" id="ouiBtn">照合</button></div>
      </div>
      <div id="ouiOut" class="note" style="margin-top:10px"></div>
    </div>
    <div class="card">
      <b>確実な検出: CLI</b>
      <p class="note">ゲートウェイIP・MAC・ベンダー・管理URLを実際に読み取ります(パスワードは表示しません):</p>
      <div class="pass">node cli/modem-scan.js</div>
    </div>
  </section>
</main>

<script>
/* ==== Bada language core (inlined) ==== */
${badaCore}
</script>
<script>
var VAULT_LIB = ${JSON.stringify(vaultLib)};
var OUI = ${JSON.stringify(oui)};
</script>
<script>
(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  var KEY="modemvault.v1";
  var master=null;

  function J(s){return JSON.stringify(String(s));}
  function loadVault(){ try{ return JSON.parse(localStorage.getItem(KEY)||"null"); }catch(e){ return null; } }
  function saveVault(v){ try{ localStorage.setItem(KEY, JSON.stringify(v)); }catch(e){ alert("保存に失敗しました: "+e); } }

  function badaRun(prog){ var out=[]; BadaLang.run(prog,{maxSteps:20000000,out:function(s){out.push(s);}}); return out.join("\\n"); }
  function seal(m, plain){
    var salt=Math.floor(Math.random()*4000)+1;
    var t=badaRun(VAULT_LIB+"\\nvault_seal("+J(m)+", "+salt+", "+J(plain)+")\\n");
    var ct=/@@CT (\\[[^\\]]*\\])/.exec(t), tag=/@@TAG (\\d+)/.exec(t);
    if(!ct||!tag) return null;
    return { salt:salt, ct:JSON.parse(ct[1]), tag:parseInt(tag[1],10) };
  }
  function open(m, rec){
    var t=badaRun(VAULT_LIB+"\\nvault_open("+J(m)+", "+rec.salt+", ["+rec.ct.join(",")+"], "+rec.tag+")\\n");
    var pm=t.indexOf("@@PLAIN ");
    if(pm<0) return null;
    /* @@PLAIN may be followed by the rest of that line only */
    var line=t.slice(pm).split("\\n")[0];
    return line.slice(8);
  }

  /* ---------- lock/unlock/create ---------- */
  function refreshLock(){
    var v=loadVault();
    $("createBox").classList.toggle("hidden", !!v);
    $("unlockBox").classList.toggle("hidden", !v);
    $("vaultBox").classList.add("hidden");
    $("lockCard").classList.remove("hidden");
  }
  $("createBtn").addEventListener("click", function(){
    var m=$("newMaster").value;
    if(m.length<4){ alert("マスターパスワードは4文字以上にしてください"); return; }
    var chk=seal(m,"modemvault-ok");
    saveVault({ check:chk, entries:[] });
    master=m; $("newMaster").value="";
    openVault();
  });
  $("unlockBtn").addEventListener("click", function(){
    var v=loadVault(); if(!v) return refreshLock();
    var m=$("master").value;
    var r=open(m, v.check);
    if(r==="modemvault-ok"){ master=m; $("master").value=""; $("unlockMsg").textContent=""; openVault(); }
    else { $("unlockMsg").innerHTML='<span class="pill bad">マスターパスワードが違います</span>'; }
  });
  $("lockBtn").addEventListener("click", function(){ master=null; refreshLock(); });

  function openVault(){
    $("lockCard").classList.add("hidden");
    $("vaultBox").classList.remove("hidden");
    renderEntries();
  }

  /* ---------- entries ---------- */
  function renderEntries(){
    var v=loadVault(); var box=$("entries"); box.innerHTML="";
    if(!v || !v.entries.length){ box.innerHTML='<p class="note">まだ登録がありません。</p>'; return; }
    v.entries.forEach(function(e){
      var d=document.createElement("div"); d.className="entry";
      var meta=[];
      if(e.gwip) meta.push("IP "+e.gwip);
      if(e.gwmac) meta.push("MAC "+e.gwmac);
      d.innerHTML=
        '<div class="top"><div><span class="model">'+esc(e.model||"(型番なし)")+'</span> '+
        (e.label?'<span class="note">'+esc(e.label)+'</span>':'')+
        '<div class="meta">'+esc(meta.join("  "))+'</div></div>'+
        '<div><button class="mini" data-act="show" data-id="'+e.id+'">パスコード表示</button> '+
        '<button class="mini" data-act="del" data-id="'+e.id+'">削除</button></div></div>'+
        '<div class="pass hidden" id="p_'+e.id+'"></div>';
      box.appendChild(d);
    });
    box.querySelectorAll("button[data-act]").forEach(function(b){
      b.addEventListener("click", function(){
        var id=this.getAttribute("data-id"), act=this.getAttribute("data-act");
        if(act==="del"){ delEntry(id); }
        else { toggleShow(id, this); }
      });
    });
  }
  function toggleShow(id, btn){
    var v=loadVault(); var e=v.entries.filter(function(x){return String(x.id)===String(id);})[0];
    var box=$("p_"+id);
    if(!box.classList.contains("hidden")){ box.classList.add("hidden"); btn.textContent="パスコード表示"; return; }
    var pt=open(master, e);
    box.textContent = pt===null ? "(復号に失敗しました)" : pt;
    box.classList.remove("hidden"); btn.textContent="隠す";
  }
  function delEntry(id){
    if(!confirm("この登録を削除しますか?")) return;
    var v=loadVault(); v.entries=v.entries.filter(function(x){return String(x.id)!==String(id);}); saveVault(v); renderEntries();
  }
  $("addBtn").addEventListener("click", function(){
    if(master===null){ alert("先に解錠してください"); return; }
    var model=$("e_model").value.trim(), pass=$("e_pass").value;
    if(!model && !pass){ alert("型番かパスコードを入力してください"); return; }
    var rec=seal(master, pass);
    if(!rec){ alert("暗号化に失敗しました"); return; }
    var v=loadVault();
    v.entries.push({ id:Date.now()+"_"+Math.floor(Math.random()*1e6),
      model:model, label:$("e_label").value.trim(),
      gwip:$("e_gwip").value.trim(), gwmac:$("e_gwmac").value.trim().toUpperCase(),
      salt:rec.salt, ct:rec.ct, tag:rec.tag });
    saveVault(v);
    $("e_model").value=$("e_label").value=$("e_pass").value=$("e_gwip").value=$("e_gwmac").value="";
    renderEntries();
  });

  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

  /* ---------- tabs ---------- */
  document.querySelectorAll(".tab").forEach(function(t){
    t.addEventListener("click", function(){
      document.querySelectorAll(".tab").forEach(function(x){x.classList.remove("on");});
      this.classList.add("on");
      var name=this.getAttribute("data-tab");
      $("tab-vault").classList.toggle("hidden", name!=="vault");
      $("tab-lan").classList.toggle("hidden", name!=="lan");
    });
  });

  /* ---------- LAN detection ---------- */
  function ouiVendor(mac){
    var p=String(mac).toUpperCase().replace(/-/g,":").split(":").slice(0,3).join(":");
    return OUI[p]||"";
  }
  $("ouiBtn").addEventListener("click", function(){
    var mac=$("macIn").value.trim();
    if(!/^([0-9a-fA-F]{2}[:-]){2}[0-9a-fA-F]{2}/.test(mac)){ $("ouiOut").textContent="MACの先頭3オクテット(例 00:60:B9)を含めて入力してください。"; return; }
    var v=ouiVendor(mac);
    $("ouiOut").innerHTML = v ? '推定メーカー: <b>'+esc(v)+'</b>' : '<span class="pill bad">未知のOUI</span> この表には登録がありません。';
  });
  $("detectBtn").addEventListener("click", function(){
    var outEl=$("lanOut"); outEl.innerHTML='<span class="note">検出中…</span>';
    var ips={};
    var pc;
    try{ pc=new RTCPeerConnection({iceServers:[]}); }catch(e){ outEl.innerHTML='<span class="pill bad">WebRTC利用不可</span> ゲートウェイIPを手動で入力してください。'; return; }
    pc.createDataChannel("x");
    pc.onicecandidate=function(ev){
      if(!ev||!ev.candidate){ finish(); return; }
      var m=/(\\d+\\.\\d+\\.\\d+\\.\\d+)/.exec(ev.candidate.candidate);
      if(m && !/^0\\./.test(m[1])) ips[m[1]]=1;
    };
    pc.createOffer().then(function(o){return pc.setLocalDescription(o);});
    setTimeout(finish, 1200);
    var done=false;
    function finish(){
      if(done) return; done=true; try{pc.close();}catch(e){}
      var list=Object.keys(ips);
      if(!list.length){ outEl.innerHTML='<span class="pill info">IPを自動取得できませんでした</span><p class="note">最近のブラウザはプライバシー保護でローカルIPを隠します。下でゲートウェイIPを手動入力してください。</p>'+gwManual(); return; }
      var h='<div><span class="pill ok">検出したPCのIP</span></div>';
      list.forEach(function(ip){
        var parts=ip.split("."); var g1=parts.slice(0,3).join(".")+".1"; var g254=parts.slice(0,3).join(".")+".254";
        h+='<div class="pass">'+esc(ip)+'  <span class="note">→ 推定ゲートウェイ: '+
           '<a href="http://'+g1+'/" target="_blank">'+g1+'</a> / '+
           '<a href="http://'+g254+'/" target="_blank">'+g254+'</a></span></div>';
      });
      h+=gwManual();
      outEl.innerHTML=h;
      wireManual();
    }
  });
  function gwManual(){
    return '<div class="row" style="margin-top:12px"><div><label>ゲートウェイIPを開く</label>'+
      '<input id="gwManual" class="mono" placeholder="192.168.0.1"/></div>'+
      '<div style="flex:0"><label>&nbsp;</label><button class="sec" id="gwOpen">管理ページを開く</button></div></div>';
  }
  function wireManual(){
    var b=$("gwOpen"); if(!b) return;
    b.addEventListener("click", function(){
      var ip=$("gwManual").value.trim(); if(!/^\\d+\\.\\d+\\.\\d+\\.\\d+$/.test(ip)){ alert("IPv4アドレスを入力してください"); return; }
      window.open("http://"+ip+"/","_blank");
    });
  }

  /* boot */
  refreshLock();
})();
</script>
</body>
</html>
`;

fs.writeFileSync(path.join(DIST, "modem-vault.html"), html);
console.log("built dist/modem-vault.html (" + fs.statSync(path.join(DIST, "modem-vault.html")).size + " bytes)");
