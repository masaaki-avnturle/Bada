#!/usr/bin/env node
/* ============================================================================
 * build-migemo-media.js — build "Migemogram Media", a single self-contained
 * HTML app: an Instagram-like gallery of YOUR OWN photos/videos (from your PC
 * via a file picker, and from your cloud via a direct media URL), with:
 *   - hover to POP OUT big ("どアップ") — the tile lifts and zooms;
 *   - hover a video to auto-play a muted CM-style preview (motion);
 *   - click for a full lightbox ("どアップ") with sound;
 *   - migemo-style romaji incremental search over titles/captions;
 *   - "zone:// に取り込む" — register each item into the ultra-network
 *     zone://url.or.jp/media/<id> (UltraDatabase quorum + Jones quantum
 *     cipher), showing 200 / quorum / Jones key / AEAD tag.
 *
 * Local image thumbnails + all metadata persist in localStorage. Video blobs
 * live for the session (browsers can't persist blobs) and are re-added by
 * re-picking the file. Output: ../dist/migemo-media.html
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

/* self-check: publish a media item to zone and read it back */
(function () {
  const prog = runtime + '\nNET := zone_boot()\nzone_publish(NET,"zone://url.or.jp/media/m1","# clip\\ntype video")\nzone_serve(NET,"zone://url.or.jp/media/m1")\n';
  let out = [];
  Bada.run(prog, { maxSteps: 200000000, out: s => out.push(s) });
  if (!/@@STATUS 200/.test(out.join("\n"))) { console.error("self-check failed:\n" + out.join("\n")); process.exit(1); }
  console.log("self-check OK: a media item publishes to zone:// and reads back 200");
})();

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Migemogram Media — 写真/動画ギャラリー + zone:// 取り込み</title>
<style>
  :root{color-scheme:light dark;--bg:#04060a;--panel:#0a1220;--line:#1c2838;--ink:#e6edf5;
        --dim:#8aa0b8;--gold:#c8a44a;--pink:#e1306c;--blue:#4a80d0;--green:#2e9e57;}
  *{box-sizing:border-box;}
  body{margin:0;background:var(--bg);color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}
  header{position:sticky;top:0;z-index:10;background:linear-gradient(180deg,#0a1220,#060a12);
         border-bottom:1px solid var(--line);padding:10px 14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;}
  .logo{font-size:19px;font-weight:800;background:linear-gradient(90deg,#f09433,#e1306c,#bc1888);
        -webkit-background-clip:text;background-clip:text;color:transparent;}
  #searchwrap{flex:1;display:flex;align-items:center;gap:8px;background:#020407;border:1px solid var(--line);
              border-radius:20px;padding:7px 14px;min-width:180px;max-width:360px;}
  #search{flex:1;background:transparent;border:0;outline:0;color:var(--ink);font-size:14px;}
  .btn{border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:9px;padding:8px 12px;cursor:pointer;font-size:13px;}
  .btn.go{border:0;background:linear-gradient(135deg,#f09433,#e1306c);color:#fff;font-weight:600;}
  main{max-width:1000px;margin:0 auto;padding:14px 12px 60px;}
  .hint{color:var(--dim);font-size:12px;text-align:center;margin:2px 0 12px;}
  .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;}
  @media(max-width:720px){.grid{grid-template-columns:repeat(2,1fr);}}
  .tile{position:relative;aspect-ratio:1;border-radius:12px;overflow:hidden;background:#0c1420;border:1px solid var(--line);
        cursor:zoom-in;transition:transform .22s cubic-bezier(.2,.8,.2,1),box-shadow .22s,z-index 0s;transform-origin:center;}
  .tile:hover{transform:scale(1.32);z-index:5;box-shadow:0 18px 50px #000c;cursor:zoom-in;}
  .tile img,.tile video{width:100%;height:100%;object-fit:cover;display:block;background:#0c1420;}
  .tile .ph{width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#6b86a8;font-size:12px;
            background:linear-gradient(135deg,#12233a,#241a3a);}
  .tile .meta{position:absolute;left:0;right:0;bottom:0;padding:6px 8px;font-size:11px;color:#eef;
              background:linear-gradient(0deg,#000b,#0000);opacity:0;transition:opacity .2s;}
  .tile:hover .meta{opacity:1;}
  .tile .badge{position:absolute;top:6px;left:6px;font-size:10px;padding:1px 6px;border-radius:8px;background:#000a;color:#cfe;}
  .tile .zpill{position:absolute;top:6px;right:6px;font-size:10px;padding:1px 6px;border-radius:8px;background:#123a24;color:#7ce0a3;display:none;}
  .tile.zoned .zpill{display:inline-block;}
  .tile .play{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:34px;color:#fff;text-shadow:0 2px 8px #000;pointer-events:none;opacity:.9;}
  .tile:hover .play{opacity:0;}
  .empty{color:var(--dim);text-align:center;padding:48px 0;}
  /* lightbox どアップ */
  #lb{position:fixed;inset:0;background:#000d;display:none;align-items:center;justify-content:center;z-index:30;padding:16px;}
  #lb.on{display:flex;}
  #lb .inner{max-width:96vw;max-height:88vh;display:flex;flex-direction:column;align-items:center;gap:10px;}
  #lb img,#lb video{max-width:96vw;max-height:78vh;border-radius:12px;box-shadow:0 20px 70px #000;}
  #lb .cap{color:#e6edf5;font-size:14px;text-align:center;max-width:70ch;}
  #lb .bar{display:flex;gap:8px;}
  #lb .x{position:fixed;top:14px;right:16px;font-size:26px;color:#fff;cursor:pointer;}
  /* composer for cloud URL */
  #modal{position:fixed;inset:0;background:#000a;display:none;align-items:center;justify-content:center;z-index:20;padding:14px;}
  #modal.on{display:flex;}
  .sheet{background:#0a1220;border:1px solid var(--line);border-radius:14px;width:100%;max-width:440px;padding:16px;}
  .sheet h3{margin:0 0 10px;} label{display:block;font-size:12px;color:var(--dim);margin:8px 0 3px;}
  .sheet input{width:100%;background:#020407;border:1px solid var(--line);border-radius:8px;padding:8px 10px;color:var(--ink);font-size:14px;}
  .sheet .row{display:flex;gap:8px;margin-top:12px;}
  .sheet button.add{flex:1;border:0;background:var(--green);color:#eafff0;font-weight:600;border-radius:8px;padding:10px;cursor:pointer;}
  .sheet button.cancel{border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:8px;padding:10px 14px;cursor:pointer;}
  mark{background:#5a4a12;color:#ffe9a8;border-radius:3px;padding:0 1px;}
</style>
</head>
<body>
<header>
  <span class="logo">Migemogram Media</span>
  <div id="searchwrap"><span style="opacity:.6">🔎</span><input id="search" placeholder="ローマ字で検索 (例: sora, neko)"/></div>
  <label class="btn go">＋ PCから追加<input id="file" type="file" accept="image/*,video/*" multiple hidden/></label>
  <button class="btn" id="cloudBtn">☁ クラウドURL</button>
  <button class="btn" id="zoneAll">zone:// に全取込</button>
</header>
<main>
  <div class="hint">タイルにポイントすると<strong>どアップ</strong>に浮き出ます。動画はポイントで<strong>CM風プレビュー(ミュート)</strong>が再生、クリックで<strong>音声つきどアップ</strong>。「zone:// 取込」でウルトラネットワークに登録。</div>
  <div id="grid" class="grid"></div>
  <div id="emptyMsg" class="empty">まだメディアがありません。「＋ PCから追加」で写真/動画を選ぶか、「☁ クラウドURL」で直接URLを追加してください。</div>
</main>

<div id="lb"><span class="x" id="lbx">✕</span><div class="inner" id="lbInner"></div></div>

<div id="modal">
  <div class="sheet">
    <h3>クラウド / URL から追加</h3>
    <label>メディアの直接URL(画像 or 動画)</label>
    <input id="c_url" placeholder="https://.../photo.jpg または .../clip.mp4"/>
    <label>タイトル / キャプション(日本語OK)</label>
    <input id="c_title" placeholder="例: 京都旅行 そら sora"/>
    <div class="row"><button class="add" id="c_add">追加</button><button class="cancel" id="c_cancel">キャンセル</button></div>
  </div>
</div>

<script>
/* ==== Bada core (inlined) — for zone:// import ==== */
${badaCore}
</script>
<script>
var ZONE_RUNTIME = ${JSON.stringify(runtime)};
</script>
<script>
/* ==== migemo-lite (romaji -> kana incremental match) ==== */
var MIGEMO=(function(){
  var T={"kya":"きゃ","kyu":"きゅ","kyo":"きょ","sha":"しゃ","shu":"しゅ","sho":"しょ","cha":"ちゃ","chu":"ちゅ","cho":"ちょ","nya":"にゃ","nyu":"にゅ","nyo":"にょ","hya":"ひゃ","hyu":"ひゅ","hyo":"ひょ","mya":"みゃ","myu":"みゅ","myo":"みょ","rya":"りゃ","ryu":"りゅ","ryo":"りょ","gya":"ぎゃ","gyu":"ぎゅ","gyo":"ぎょ","ja":"じゃ","ju":"じゅ","jo":"じょ","jya":"じゃ","jyu":"じゅ","jyo":"じょ","bya":"びゃ","byu":"びゅ","byo":"びょ","pya":"ぴゃ","pyu":"ぴゅ","pyo":"ぴょ","tsu":"つ","shi":"し","chi":"ち",
    "ka":"か","ki":"き","ku":"く","ke":"け","ko":"こ","sa":"さ","si":"し","su":"す","se":"せ","so":"そ","ta":"た","ti":"ち","tu":"つ","te":"て","to":"と","na":"な","ni":"に","nu":"ぬ","ne":"ね","no":"の","ha":"は","hi":"ひ","fu":"ふ","hu":"ふ","he":"へ","ho":"ほ","ma":"ま","mi":"み","mu":"む","me":"め","mo":"も","ya":"や","yu":"ゆ","yo":"よ","ra":"ら","ri":"り","ru":"る","re":"れ","ro":"ろ","wa":"わ","wo":"を","ga":"が","gi":"ぎ","gu":"ぐ","ge":"げ","go":"ご","za":"ざ","zi":"じ","ji":"じ","zu":"ず","ze":"ぜ","zo":"ぞ","da":"だ","de":"で","do":"ど","ba":"ば","bi":"び","bu":"ぶ","be":"べ","bo":"ぼ","pa":"ぱ","pi":"ぴ","pu":"ぷ","pe":"ぺ","po":"ぽ","a":"あ","i":"い","u":"う","e":"え","o":"お","n":"ん","-":"ー"};
  function toHira(s){ s=String(s).toLowerCase(); var o="",i=0; while(i<s.length){ var c=s[i];
    if(c===s[i+1] && "kstpgzdbhmyrwcfj".indexOf(c)>=0){o+="っ";i++;continue;}
    var m=null; for(var L=3;L>=1;L--){var seg=s.substr(i,L); if(T[seg]){m=seg;break;}}
    if(m){o+=T[m];i+=m.length;} else {o+=c;i++;} } return o; }
  function kata(s){ return String(s).replace(/[\\u30a1-\\u30f6]/g,function(ch){return String.fromCharCode(ch.charCodeAt(0)-0x60);}); }
  function match(hay,q){ if(!q)return true; q=String(q).toLowerCase().trim(); var h=String(hay),hl=h.toLowerCase();
    if(hl.indexOf(q)>=0)return true; var qh=toHira(q),hh=kata(h);
    if(qh&&hh.indexOf(qh)>=0)return true; if(qh&&h.indexOf(qh)>=0)return true; return false; }
  return {match:match,toHira:toHira};
})();

(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  var KEY="migemomedia.v1";
  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
  function J(s){return JSON.stringify(String(s));}
  function load(){ try{return JSON.parse(localStorage.getItem(KEY)||'{"items":[]}');}catch(e){return {items:[]};} }
  function save(s){ try{
      // persist metadata + image thumbs only (videos/blob urls are session)
      var copy={items:s.items.map(function(m){ return {id:m.id,title:m.title,type:m.type,src:(m.persist?m.src:""),source:m.source,zoned:m.zoned}; })};
      localStorage.setItem(KEY,JSON.stringify(copy));
    }catch(e){}
  }
  var state=load();

  /* ---- zone import (Bada zone-lib) ---- */
  function zurl(m){ return "zone://url.or.jp/media/"+m.id; }
  function zoneImport(ids){
    var prog=ZONE_RUNTIME+"\\nNET := zone_boot()\\n";
    state.items.forEach(function(m){
      if(ids && ids.indexOf(m.id)<0) return;
      var body="# "+(m.title||m.id)+"\\ntype "+m.type+"\\nsource "+(m.source||"local");
      prog+="zone_publish(NET, "+J(zurl(m))+", "+J(body)+")\\n";
    });
    var target=(ids&&ids.length===1)?ids[0]:null;
    var one=null; state.items.forEach(function(m){ if(target&&m.id===target)one=m; });
    if(one) prog+="zone_serve(NET, "+J(zurl(one))+")\\n";
    var out=[]; BadaLang.run(prog,{maxSteps:200000000,out:function(s){out.push(s);}});
    var t=out.join("\\n");
    (ids||state.items.map(function(m){return m.id;})).forEach(function(id){ var m=byId(id); if(m)m.zoned=true; });
    save(state);
    var q=/@@QUORUM (\\d+ \\d+)/.exec(t), jk=/@@JONESKEY (\\d+)/.exec(t), st=/@@STATUS (\\S+)/.exec(t);
    return { status:st?st[1]:"?", quorum:q?q[1]:"", jones:jk?jk[1]:"" };
  }
  function byId(id){ for(var i=0;i<state.items.length;i++) if(state.items[i].id===id) return state.items[i]; return null; }

  /* ---- add media ---- */
  function addLocalFile(f){
    var isVideo=/^video\\//.test(f.type);
    var url=URL.createObjectURL(f);
    var item={ id:"m"+Date.now()+"_"+Math.floor(Math.random()*1e5), title:f.name.replace(/\\.[^.]+$/,""),
               type:isVideo?"video":"image", src:url, source:"local", zoned:false, persist:false };
    if(!isVideo){
      // downscale image to a persistable thumbnail dataURL
      var img=new Image();
      img.onload=function(){ var max=800,w=img.width,h=img.height; if(w>max||h>max){var r=Math.min(max/w,max/h);w=Math.round(w*r);h=Math.round(h*r);}
        var cv=document.createElement("canvas"); cv.width=w; cv.height=h; cv.getContext("2d").drawImage(img,0,0,w,h);
        try{ item.src=cv.toDataURL("image/jpeg",0.82); item.persist=true; save(state); render(); }catch(e){}
      };
      img.src=url;
    }
    state.items.push(item);
  }
  $("file").addEventListener("change", function(){
    var fs=this.files; if(!fs||!fs.length)return;
    for(var i=0;i<fs.length;i++) addLocalFile(fs[i]);
    this.value=""; save(state); render();
  });
  $("cloudBtn").addEventListener("click", function(){ $("modal").classList.add("on"); });
  $("c_cancel").addEventListener("click", function(){ $("modal").classList.remove("on"); });
  $("c_add").addEventListener("click", function(){
    var u=$("c_url").value.trim(); if(!u){ alert("URLを入力してください"); return; }
    var isVideo=/\\.(mp4|webm|ogg|mov|m4v)(\\?|$)/i.test(u);
    state.items.push({ id:"m"+Date.now(), title:$("c_title").value.trim()||u.split("/").pop(),
      type:isVideo?"video":"image", src:u, source:"cloud", zoned:false, persist:true });
    $("c_url").value=$("c_title").value=""; $("modal").classList.remove("on"); save(state); render();
  });
  $("zoneAll").addEventListener("click", function(){
    if(!state.items.length){ alert("メディアがありません"); return; }
    var r=zoneImport(null); render();
    alert("zone:// に取り込みました: status "+r.status+" quorum "+r.quorum+" jones "+r.jones);
  });

  /* ---- render grid ---- */
  function hi(text,q){ if(!q)return esc(text); var out="",low=text.toLowerCase(),ql=q.toLowerCase(),i=0,idx;
    while((idx=low.indexOf(ql,i))>=0){ out+=esc(text.slice(i,idx))+"<mark>"+esc(text.slice(idx,idx+ql.length))+"</mark>"; i=idx+ql.length; } return out+esc(text.slice(i)); }
  function render(){
    var q=$("search").value.trim();
    var items=state.items.filter(function(m){ return MIGEMO.match((m.title||"")+" "+(m.source||""), q); });
    $("emptyMsg").style.display=items.length?"none":"block";
    var g=$("grid"); g.innerHTML="";
    items.forEach(function(m){
      var d=document.createElement("div"); d.className="tile"+(m.zoned?" zoned":"");
      var media;
      if(m.src){
        if(m.type==="video"){ media='<video src="'+esc(m.src)+'" muted loop preload="metadata" playsinline></video><div class="play">▶</div>'; }
        else { media='<img src="'+esc(m.src)+'"/>'; }
      } else { media='<div class="ph">'+(m.type==="video"?"動画(再選択で表示)":"画像")+'</div>'; }
      d.innerHTML=media+
        '<span class="badge">'+(m.type==="video"?"▶ 動画":"📷 写真")+' · '+esc(m.source||"local")+'</span>'+
        '<span class="zpill">zone取込済</span>'+
        '<div class="meta">'+hi(m.title||"",q)+'</div>';
      // hover CM preview for video
      if(m.type==="video" && m.src){
        var v=d.querySelector("video");
        d.addEventListener("mouseenter",function(){ try{ v.currentTime=0; v.muted=true; var p=v.play(); if(p&&p.catch)p.catch(function(){}); }catch(e){} });
        d.addEventListener("mouseleave",function(){ try{ v.pause(); }catch(e){} });
      }
      // click -> lightbox どアップ (with sound for video)
      d.addEventListener("click",function(e){
        if(e.target && e.target.getAttribute && e.target.getAttribute("data-z")) return;
        openLightbox(m);
      });
      // per-item zone import button in meta (long-press alt: use dblclick)
      d.addEventListener("dblclick",function(){ var r=zoneImport([m.id]); render(); });
      g.appendChild(d);
    });
  }

  /* ---- lightbox どアップ ---- */
  function openLightbox(m){
    var inner=$("lbInner");
    var media;
    if(!m.src){ media='<div style="color:#8aa0b8;padding:40px">このセッションでは表示できません(動画は再選択が必要)。</div>'; }
    else if(m.type==="video"){ media='<video src="'+esc(m.src)+'" controls autoplay playsinline></video>'; }
    else { media='<img src="'+esc(m.src)+'"/>'; }
    inner.innerHTML=media+'<div class="cap">'+esc(m.title||"")+'</div>'+
      '<div class="bar"><button class="btn go" id="lbZone">zone:// に取り込む</button>'+
      '<a class="btn" href="'+esc(m.src||"#")+'" target="_blank">元を開く</a></div>';
    $("lb").classList.add("on");
    var zb=$("lbZone"); if(zb) zb.addEventListener("click",function(){ var r=zoneImport([m.id]); this.textContent="取込済 "+r.quorum+" / jones "+r.jones; render(); });
    // play with sound on user click already granted
    var v=inner.querySelector("video"); if(v){ v.muted=false; }
  }
  function closeLightbox(){ $("lb").classList.remove("on"); $("lbInner").innerHTML=""; }
  $("lbx").addEventListener("click", closeLightbox);
  $("lb").addEventListener("click", function(e){ if(e.target===this) closeLightbox(); });

  $("search").addEventListener("input", render);
  render();
})();
</script>
</body>
</html>
`;

fs.mkdirSync(path.join(IDE, "dist"), { recursive: true });
fs.writeFileSync(path.join(IDE, "dist", "migemo-media.html"), html);
console.log("built dist/migemo-media.html (" + fs.statSync(path.join(IDE, "dist", "migemo-media.html")).size + " bytes)");
