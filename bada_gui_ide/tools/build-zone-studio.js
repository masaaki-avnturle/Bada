#!/usr/bin/env node
/* ============================================================================
 * build-zone-studio.js — build "Zone Studio", a single self-contained HTML app
 * for AUTHORING YOUR OWN WWW addressed by zone:// URIs and publishing it into
 * the ultra-network (projected onto the NTT NGN line): each page is replicated
 * across the UltraDatabase quorum and sealed with the Jones quantum cipher.
 *
 * You write pages (path + title + body markup), assign zone://<host><path>
 * URIs, publish over "NTT NGN", and preview the decrypted result with its
 * quorum / Jones-key / AEAD-tag security panel. The whole site persists in
 * localStorage and can be exported/imported as a .zonesite JSON.
 *
 * Output: ../dist/zone-studio.html   (offline, no dependencies)
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

/* self-check: author -> publish -> serve returns 200 */
(function () {
  const prog = runtime +
    '\nNET := zone_boot()\n' +
    'zone_publish(NET, "zone://url.or.jp/hello", "# Hello\\nmy first zone page")\n' +
    'zone_serve(NET, "zone://url.or.jp/hello")\n';
  let out = [];
  Bada.run(prog, { maxSteps: 200000000, out: s => out.push(s) });
  if (!/@@STATUS 200/.test(out.join("\n"))) { console.error("self-check failed:\n" + out.join("\n")); process.exit(1); }
  console.log("self-check OK: author a page, publish, serve -> 200");
})();

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Zone Studio — zone:// で自分の WWW を作る</title>
<style>
  :root{color-scheme:light dark;--bg:#04060a;--panel:#0a1220;--line:#1c2838;--ink:#d6e2ee;
        --dim:#8aa0b8;--gold:#c8a44a;--green:#2e9e57;--red:#d0574a;--blue:#4a80d0;}
  *{box-sizing:border-box;} html,body{height:100%;}
  body{margin:0;background:var(--bg);color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}
  header{padding:12px 18px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#0a1220,#04060a);
         display:flex;gap:14px;align-items:center;flex-wrap:wrap;}
  h1{margin:0;font-size:18px;} h1 .a{color:var(--gold);}
  header .host{display:flex;align-items:center;gap:6px;margin-left:auto;font-size:13px;color:var(--dim);}
  header input.host-in{background:#020407;border:1px solid var(--line);border-radius:7px;padding:6px 10px;color:var(--ink);font-family:"SFMono-Regular",Consolas,monospace;width:150px;}
  main{display:grid;grid-template-columns:230px 1fr 1fr;height:calc(100% - 56px);}
  @media(max-width:900px){main{grid-template-columns:1fr;}}
  #list{border-right:1px solid var(--line);padding:12px;overflow:auto;}
  #edit{border-right:1px solid var(--line);padding:14px;overflow:auto;}
  #view{padding:18px 20px;overflow:auto;}
  h3{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--dim);margin:0 0 8px;}
  label{display:block;font-size:12px;color:var(--dim);margin:8px 0 3px;}
  input,textarea{width:100%;background:#020407;border:1px solid var(--line);border-radius:8px;padding:8px 10px;color:var(--ink);font-size:13px;font-family:"SFMono-Regular",Consolas,monospace;}
  textarea{min-height:220px;resize:vertical;line-height:1.5;}
  button{font:inherit;border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:8px;padding:8px 12px;cursor:pointer;}
  button.act{border:0;background:var(--green);color:#eafff0;font-weight:600;}
  .btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;}
  .pageitem{border:1px solid var(--line);border-radius:8px;padding:8px 10px;margin-bottom:8px;cursor:pointer;font-family:"SFMono-Regular",Consolas,monospace;font-size:12.5px;}
  .pageitem:hover{background:#101d2e;} .pageitem.on{border-color:#38537a;background:#12233a;}
  .pageitem .z{color:var(--blue);font-size:11px;word-break:break-all;}
  .pageitem .t{color:var(--ink);}
  .pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:10px;margin:0 6px 6px 0;}
  .ok{background:#123a24;color:#7ce0a3;} .bad{background:#3a1614;color:#f2a49b;} .info{background:#12233a;color:#8fb6ff;}
  .doc h1{font-size:22px;margin:0 0 6px;} .doc h2{font-size:17px;color:var(--gold);margin:16px 0 6px;}
  .doc p{margin:7px 0;max-width:62ch;} .doc a{color:var(--blue);text-decoration:none;border-bottom:1px solid #24405f;cursor:pointer;}
  .kv{display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-bottom:1px dashed #16222f;font-size:12.5px;}
  .kv b{color:var(--dim);font-weight:500;} .kv span{font-family:monospace;text-align:right;word-break:break-all;}
  .note{color:var(--dim);font-size:12px;} code{color:var(--gold);}
  .hint{color:var(--dim);font-size:11.5px;margin-top:6px;line-height:1.5;}
</style>
</head>
<body>
<header>
  <h1>Zone <span class="a">Studio</span> <span class="note">v${VERSION}</span></h1>
  <span class="note">zone:// で自分の WWW を作り、NTT NGN 経由でウルトラネットワークに公開</span>
  <span class="host">host: zone:// <input id="host" class="host-in" value="url.or.jp"/></span>
</header>
<main>
  <nav id="list">
    <h3>ページ</h3>
    <div id="pages"></div>
    <div class="btns">
      <button class="act" id="newPage">＋ 新規</button>
      <button id="publishAll">全公開</button>
    </div>
    <div class="btns">
      <button id="exportBtn">書き出し</button>
      <label style="margin:0"><input id="importFile" type="file" accept=".zonesite,application/json" style="display:none"/>
        <button id="importBtn">読み込み</button></label>
    </div>
    <div class="hint">サイトはブラウザ内(localStorage)に保存されます。<br>書き出し(.zonesite)で持ち運べます。</div>
  </nav>

  <section id="edit">
    <h3>編集</h3>
    <label>パス (zone://<span id="hostEcho">url.or.jp</span> の後)</label>
    <input id="e_path" placeholder="/  または /blog/1"/>
    <label>タイトル</label>
    <input id="e_title" placeholder="My Zone Home"/>
    <label>本文 (マークアップ)</label>
    <textarea id="e_body" placeholder="# 見出し&#10;段落テキスト&#10;## セクション&#10;-> zone://url.or.jp/next | 次のページへ"></textarea>
    <div class="hint"><code># 見出し</code> / <code>## セクション</code> / 段落 / リンク <code>-&gt; zone://... | ラベル</code></div>
    <div class="btns">
      <button class="act" id="savePublish">保存して公開 (NTT NGN)</button>
      <button id="savePage">保存のみ</button>
      <button id="delPage">削除</button>
    </div>
  </section>

  <aside id="view">
    <h3>プレビュー(公開結果を復号)</h3>
    <div id="preview"><span class="note">ページを保存して公開すると、ウルトラネットワークから復号したページを表示します。</span></div>
  </aside>
</main>

<script>
/* ==== Bada core (inlined) ==== */
${badaCore}
</script>
<script>
var ZONE_RUNTIME = ${JSON.stringify(runtime)};
</script>
<script>
(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  var KEY="zonestudio.v1";
  var sel=null;

  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
  function J(s){return JSON.stringify(String(s));}
  function host(){ return ($("host").value.trim()||"url.or.jp"); }
  function load(){ try{return JSON.parse(localStorage.getItem(KEY)||'{"pages":[]}');}catch(e){return {pages:[]};} }
  function save(s){ try{localStorage.setItem(KEY,JSON.stringify(s));}catch(e){alert("保存失敗: "+e);} }
  function normPath(p){ p=String(p||"/").trim(); if(p[0]!=="/")p="/"+p; return p; }
  function uriOf(p){ return "zone://"+host()+normPath(p.path); }

  /* build the per-op Bada program: boot + publish all pages + serve target */
  function run(targetUri){
    var s=load();
    var prog=ZONE_RUNTIME+"\\nNET := zone_boot()\\n";
    s.pages.forEach(function(p){
      var body="# "+(p.title||p.path)+"\\n"+(p.body||"");
      prog+="zone_publish(NET, "+J(uriOf(p))+", "+J(body)+")\\n";
    });
    prog+="zone_serve(NET, "+J(targetUri)+")\\n";
    var out=[];
    BadaLang.run(prog,{maxSteps:200000000,out:function(x){out.push(x);}});
    return out.join("\\n");
  }
  function parse(t){
    var m={status:"?",quorum:"",jones:"",tag:"",node:"",key:"",path:"",body:""};
    var ls=t.split("\\n"),body=[],inB=false;
    ls.forEach(function(l){ if(l==="@@BODY_BEGIN"){inB=true;return;} if(l==="@@BODY_END"){inB=false;return;}
      if(inB){body.push(l);return;} if(l.indexOf("@@")!==0)return;
      var sp=l.indexOf(" "),k=(sp<0?l:l.slice(0,sp)).slice(2),v=sp<0?"":l.slice(sp+1);
      if(k==="STATUS")m.status=v;else if(k==="QUORUM")m.quorum=v;else if(k==="JONESKEY")m.jones=v;
      else if(k==="TAG")m.tag=v;else if(k==="NODE")m.node=v;else if(k==="KEY")m.key=v;else if(k==="PATH")m.path=v; });
    m.body=body.join("\\n"); return m;
  }

  function renderList(){
    var s=load(),box=$("pages");
    $("hostEcho").textContent=host();
    if(!s.pages.length){ box.innerHTML='<p class="note">まだページがありません。「＋ 新規」で作成。</p>'; return; }
    box.innerHTML="";
    s.pages.forEach(function(p,i){
      var d=document.createElement("div"); d.className="pageitem"+(sel===i?" on":"");
      d.innerHTML='<div class="t">'+esc(p.title||"(無題)")+(p.published?' <span class="pill ok" style="padding:1px 6px">公開</span>':'')+
        '</div><div class="z">'+esc(uriOf(p))+'</div>';
      d.addEventListener("click",function(){ selectPage(i); });
      box.appendChild(d);
    });
  }
  function selectPage(i){
    sel=i; var p=load().pages[i]; if(!p)return;
    $("e_path").value=p.path; $("e_title").value=p.title||""; $("e_body").value=p.body||"";
    renderList();
    preview(uriOf(p));
  }
  function currentFromForm(){
    return { path:normPath($("e_path").value), title:$("e_title").value.trim(), body:$("e_body").value };
  }
  function savePage(publish){
    var s=load(), p=currentFromForm();
    if(sel===null || sel>=s.pages.length){ p.published=false; s.pages.push(p); sel=s.pages.length-1; }
    else { p.published=s.pages[sel].published||false; s.pages[sel]=p; }
    if(publish) s.pages[sel].published=true;
    save(s); renderList();
    if(publish) preview(uriOf(s.pages[sel]));
  }
  function delPage(){
    if(sel===null)return; if(!confirm("このページを削除しますか?"))return;
    var s=load(); s.pages.splice(sel,1); sel=null; save(s);
    $("e_path").value=$("e_title").value=$("e_body").value=""; renderList();
    $("preview").innerHTML='<span class="note">削除しました。</span>';
  }

  function preview(uri){
    var t=run(uri); var m=parse(t); var v=$("preview");
    if(m.status!=="200"){ v.innerHTML='<span class="pill bad">'+esc(m.status)+'</span><p class="note">まだ公開されていないか、URIが不正です。「保存して公開」を押してください。</p>'; return; }
    var bodyHtml="",h1=false;
    m.body.split("\\n").forEach(function(ln){ ln=ln.replace(/\\s+$/,""); if(!ln)return; var mm;
      if((mm=/^##\\s+(.*)$/.exec(ln)))bodyHtml+='<h2>'+esc(mm[1])+'</h2>';
      else if((mm=/^#\\s+(.*)$/.exec(ln))){ if(!h1){bodyHtml+='<h1>'+esc(mm[1])+'</h1>';h1=true;} else bodyHtml+='<h2>'+esc(mm[1])+'</h2>'; }
      else if((mm=/^->\\s*(\\S+)\\s*\\|\\s*(.*)$/.exec(ln)))bodyHtml+='<p><a data-z="'+esc(mm[1])+'">'+esc(mm[2])+'</a> <small class="note">'+esc(mm[1])+'</small></p>';
      else bodyHtml+='<p>'+esc(ln)+'</p>';
    });
    v.innerHTML='<div class="doc"><p><span class="pill ok">🔒 200 zone-delivered</span>'+
      '<span class="pill ok">Jones-AEAD verified</span><span class="pill ok">UltraDB quorum '+esc(m.quorum||"—")+'</span></p>'+
      bodyHtml+'<hr style="border-color:#16222f;margin:14px 0"/>'+
      '<div class="kv"><b>URI</b><span>'+esc(uri)+'</span></div>'+
      '<div class="kv"><b>owner局(NGN)</b><span>'+esc(m.node)+'</span></div>'+
      '<div class="kv"><b>DHT key</b><span>'+esc(m.key)+'</span></div>'+
      '<div class="kv"><b>Jones鍵</b><span>'+esc(m.jones)+'</span></div>'+
      '<div class="kv"><b>AEADタグ</b><span>'+esc(m.tag)+'</span></div></div>';
    v.querySelectorAll("a[data-z]").forEach(function(a){ a.addEventListener("click",function(e){e.preventDefault();
      var z=this.getAttribute("data-z"); openUri(z); }); });
  }
  function openUri(uri){
    /* if it's one of our pages, select it; else just preview */
    var s=load(); var idx=-1;
    s.pages.forEach(function(p,i){ if(uriOf(p)===uri) idx=i; });
    if(idx>=0) selectPage(idx); else preview(uri);
  }

  $("newPage").addEventListener("click",function(){ sel=null; $("e_path").value="/"; $("e_title").value=""; $("e_body").value=""; renderList(); $("e_path").focus(); });
  $("savePage").addEventListener("click",function(){ savePage(false); });
  $("savePublish").addEventListener("click",function(){ savePage(true); });
  $("delPage").addEventListener("click",delPage);
  $("publishAll").addEventListener("click",function(){ var s=load(); s.pages.forEach(function(p){p.published=true;}); save(s); renderList(); if(s.pages[0])preview(uriOf(s.pages[0])); });
  $("host").addEventListener("input",function(){ renderList(); });
  $("exportBtn").addEventListener("click",function(){
    var blob=new Blob([JSON.stringify({host:host(),site:load()},null,2)],{type:"application/json"});
    var a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download="my.zonesite"; a.click();
    setTimeout(function(){URL.revokeObjectURL(a.href);},2000);
  });
  $("importBtn").addEventListener("click",function(){ $("importFile").click(); });
  $("importFile").addEventListener("change",function(){ var f=this.files&&this.files[0]; if(!f)return;
    var rd=new FileReader(); rd.onload=function(){ try{ var j=JSON.parse(String(rd.result));
      if(j.host)$("host").value=j.host; save(j.site||{pages:[]}); sel=null; renderList();
      $("preview").innerHTML='<span class="pill info">読み込みました('+(load().pages.length)+' ページ)</span>';
    }catch(e){ alert(".zonesite の読み込みに失敗しました"); } }; rd.readAsText(f); });

  /* seed a starter site on first run */
  (function seed(){ var s=load(); if(s.pages.length)return;
    s.pages=[
      {path:"/",title:"My Zone Home",published:true,body:"私の zone:// サイトへようこそ。\\n## お品書き\\n-> zone://url.or.jp/about | このサイトについて\\n-> zone://url.or.jp/blog/1 | 最初の記事"},
      {path:"/about",title:"About",published:true,body:"これは Zone Studio で作った、URI が zone:// の独自 WWW です。\\nNTT NGN 経由でウルトラネットワークに公開され、Jones量子暗号で守られています。\\n-> zone://url.or.jp/ | ホームへ"},
      {path:"/blog/1",title:"最初の記事",published:true,body:"## zone:// で発信する\\nhttp も DNS も無い、P2P のウルトラネットワークに自分のページを置きました。\\n-> zone://url.or.jp/ | ホームへ"}
    ];
    save(s);
  })();
  renderList();
  if(load().pages.length) selectPage(0);
})();
</script>
</body>
</html>
`;
fs.writeFileSync(path.join(IDE, "dist", "zone-studio.html"), html);
console.log("built dist/zone-studio.html (" + fs.statSync(path.join(IDE, "dist", "zone-studio.html")).size + " bytes)");
