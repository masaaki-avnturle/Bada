#!/usr/bin/env node
/* ============================================================================
 * build-anomaly-map.js — build "AnomalyMap — 宇宙人らしき信号の場所特定アトラス",
 * a single self-contained HTML app.
 *
 * The honest version of "宇宙人らしき人が使っている場所の特定": history's REAL
 * signals and events that were seriously considered as possibly alien, each
 * with its real coordinates and, crucially, the real OUTCOME of pinpointing
 * the source:
 *   - Wow! signal (1977)      : still UNRESOLVED — the one that never repeated
 *   - BLC1 (2020, Proxima 方向): pinpointed → human-made radio interference
 *   - LGM-1 (1967)            : pinpointed → the first pulsar (natural)
 *   - Parkes perytons         : pinpointed → the observatory's MICROWAVE OVEN
 *   - 'Oumuamua, Tabby's star, FRB 121102 / 20200120E, SHGb02+14a, 1991 VG…
 *
 * 場所の特定ビュー: sky events get a real DSS2 survey cutout at their RA/Dec
 * (CDS hips2fits, no key) plus a clickable all-sky atlas; ground events get a
 * public map/aerial tile view (Esri/OSM) at their lat/lon. Verdict badges:
 * 🟢未解決 / 🟡人工と判明 / 🔵自然と判明, with a Rio-scale-inspired attention
 * score. Marker colors use the trefoil Jones |V(e^{iθ})| keyed by frequency,
 * keeping the repo's Γ/Jones flavour. Works offline (fallback drawings).
 *
 * Pinned honest banner: as of 2026 there is NO confirmed alien-used site,
 * anywhere. This is the real map of the candidates and how each was resolved.
 *
 * Output: ../dist/anomaly-map.html
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");

let html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>AnomalyMap — 宇宙人らしき信号の場所特定アトラス</title>
<style>
  :root{color-scheme:dark;--bg:#03050c;--line:#1b2740;--ink:#e9f0fb;--dim:#8aa0c0;
        --cy:#39c2ff;--gold:#c8a44a;--green:#2fbf71;--red:#e0555a;--vio:#8f6bff;}
  *{box-sizing:border-box;}
  body{margin:0;background:#03050c;color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}
  header{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:11px 16px;
         border-bottom:1px solid var(--line);background:#060a14cc;position:sticky;top:0;z-index:20;backdrop-filter:blur(6px);}
  .logo{font-size:19px;font-weight:800;letter-spacing:.4px;
        background:linear-gradient(90deg,#8f6bff,#2fbf71);-webkit-background-clip:text;background-clip:text;color:transparent;}
  .sub{color:var(--dim);font-size:12px;}
  main{max-width:1100px;margin:0 auto;padding:14px 12px 70px;}
  .banner{background:#3a2412;border:1px solid #6b4a2e;border-radius:10px;padding:10px 13px;font-size:12.5px;color:#ffd9a8;margin-bottom:12px;line-height:1.7;}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;} @media(max-width:860px){.grid{grid-template-columns:1fr;}}
  .card{background:#070c16;border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-top:14px;}
  h2{font-size:15px;margin:0 0 10px;color:var(--cy);}
  .muted{color:var(--dim);font-size:12px;} a{color:var(--cy);}
  #atlas{width:100%;border:1px solid var(--line);border-radius:10px;background:#020409;display:block;cursor:crosshair;}
  .events{max-height:400px;overflow:auto;border:1px solid var(--line);border-radius:10px;margin-top:10px;}
  .ev{padding:9px 12px;border-bottom:1px solid var(--line);cursor:pointer;font-size:13px;}
  .ev:hover{background:#0d1626;} .ev.sel{background:#12233c;}
  .ev .t{color:var(--dim);font-size:11.5px;margin-top:2px;}
  .badge{font-size:11px;border-radius:6px;padding:1px 7px;margin-left:6px;font-weight:600;}
  .b-open{background:#173a29;color:#7fe0a8;border:1px solid #2e6b46;}
  .b-human{background:#3a3212;color:#ffd97a;border:1px solid #6b5a2e;}
  .b-nat{background:#12283a;color:#8fc8ff;border:1px solid #2e4d6b;}
  #cutout{width:100%;aspect-ratio:1/1;object-fit:cover;border:1px solid var(--line);border-radius:10px;background:#020409;display:none;}
  #groundmap{width:100%;aspect-ratio:1/1;border:1px solid var(--line);border-radius:10px;background:#020409;display:none;}
  .kv{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;font-size:13px;margin-top:10px;}
  .kv b{color:var(--gold);font-weight:600;}
  .score{height:8px;border-radius:4px;background:#0b1424;overflow:hidden;margin-top:4px;}
  .score i{display:block;height:100%;}
</style>
</head>
<body>
<header>
  <div><div class="logo">👽 AnomalyMap — 宇宙人らしき信号の場所特定アトラス</div>
    <div class="sub">「宇宙人では?」と真剣に検討された実在の信号・事象の、実座標と特定結果の全記録</div></div>
</header>
<main>

  <div class="banner">
    <b>正直な前提</b>: 2026年時点で、宇宙人が使っていると確認された場所は宇宙のどこにも<b>ゼロ</b>です。
    このアトラスに載っているのは、科学者が「宇宙人らしき」候補として実際に調査した<b>実在の信号・事象</b>と、
    その<b>発生源を特定した結果</b>(多くは人工・自然と判明。<b>Wow! 信号だけは今も未解決</b>)。
    「場所の特定」こそが SETI の実務であり、その全履歴を実座標で見られます。
  </div>

  <div class="grid">
    <div>
      <h2 style="margin-top:0">🌌 全天アトラス (クリックで選択)</h2>
      <canvas id="atlas" width="520" height="300"></canvas>
      <div class="events" id="events"></div>
    </div>
    <div>
      <h2 style="margin-top:0">📍 場所の特定ビュー</h2>
      <img id="cutout" alt="DSS2 sky survey cutout"/>
      <canvas id="groundmap" width="480" height="480"></canvas>
      <div class="muted" id="viewNote"></div>
      <div class="kv" id="kv"></div>
    </div>
  </div>

  <div class="card">
    <h2>ℹ️ 読み方</h2>
    <div class="muted" style="line-height:1.8">
      <span class="badge b-open">🟢 未解決</span> 宇宙人説をまだ否定できない(=最も注目) /
      <span class="badge b-human">🟡 人工と判明</span> 場所を特定した結果、人間の技術だった /
      <span class="badge b-nat">🔵 自然と判明</span> 特定の結果、新しい自然現象だった(パルサー・FRB など、それ自体が大発見)。
      注目度は IAA の <b>Rio スケール</b>(SETI 検出の重要度 0-10)を参考にした目安。
      マーカー色はリポジトリ共通の <b>Jones 多項式 |V(e^{iθ})|</b> を周波数で評価した熱感知カラー。
      天球の特定ビューは <b>CDS hips2fits の実サーベイ画像 (DSS2)</b>、地上は <b>Esri/OSM 公開タイル</b>
      (どちらも鍵不要・オフライン時は簡易表示)。
    </div>
  </div>
</main>

<script>
(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

  /* ============ Jones heat by frequency (repo flavour) ============ */
  function jonesV(th){
    function e(n){return {re:Math.cos(n*th),im:Math.sin(n*th)};}
    var a=e(-4),b=e(-3),c=e(-1),re=-a.re+b.re+c.re,im=-a.im+b.im+c.im;
    return Math.sqrt(re*re+im*im);
  }
  function heatByFreq(mhz){
    if(mhz==null) return "#8f6bff";
    var t=Math.max(100,Math.min(10000,mhz));
    var th=Math.log(t/100)/Math.log(100)*Math.PI;
    var m=jonesV(th)/3;
    var hue=200-Math.log(t/100)/Math.log(100)*160;
    return "hsl("+hue.toFixed(0)+","+(50+m*40).toFixed(0)+"%,55%)";
  }

  /* ============ 実在の「宇宙人らしき」事象カタログ ============ */
  // verdict: open=未解決 / human=人工と判明 / natural=自然と判明
  // kind: sky (RA/Dec) / ground (lat/lon) / sol (太陽系内)
  var EVENTS=[
    {n:"Wow! シグナル (1977)", kind:"sky", ra:291.38, dec:-26.95, mhz:1420.456, v:"open", rio:4,
     d:"オハイオ州立大 Big Ear が受信した72秒の狭帯域強信号。いて座方向。一度きりで再現されず、発生源は今も未特定 — 宇宙人説を否定しきれない唯一級の事例。",
     res:"未解決 — 2017年の彗星説は反論多数。座標は2つの候補ビームのうち負角側。"},
    {n:"BLC1 (2020, プロキシマ・ケンタウリ方向)", kind:"sky", ra:217.393, dec:-62.676, mhz:982.002, v:"human", rio:1,
     d:"Breakthrough Listen が検出した 982.002 MHz の狭帯域ドリフト信号。最も近い恒星の方向で「宇宙人らしき」候補筆頭に。",
     res:"特定完了 (2021): 地上の人工電波干渉 (RFI) と結論。"},
    {n:"LGM-1 / PSR B1919+21 (1967)", kind:"sky", ra:290.437, dec:21.897, mhz:81.5, v:"natural", rio:2,
     d:"ベル・バーネルが発見した1.337秒周期の規則正しいパルス。あまりに規則的で 'Little Green Men' と呼ばれた。",
     res:"特定完了: 史上初のパルサー(中性子星)— 自然現象だが大発見。"},
    {n:"パークスのペリュトン (1998-2015)", kind:"ground", lat:-32.9984, lon:148.2635, mhz:1400, v:"human", rio:0,
     d:"パークス64m望遠鏡が受信し続けた謎のミリ秒バースト。宇宙起源かと17年議論された。",
     res:"特定完了 (2015): 天文台の休憩室の電子レンジ(扉を早開けした時)と判明 — 場所の特定の傑作例。"},
    {n:"オウムアムア 1I/2017 U1", kind:"sol", ra:279.8, dec:33.99, mhz:null, v:"open", rio:2,
     d:"史上初の恒星間天体。細長い形状と非重力加速から「宇宙人の探査機では」(ローブ説)と議論。こと座方向から飛来。",
     res:"多数派は自然天体(水素/窒素氷など)説だが、確定はしていない。既に太陽系を離脱。"},
    {n:"タビーの星 KIC 8462852", kind:"sky", ra:301.564, dec:44.457, mhz:null, v:"natural", rio:2,
     d:"最大22%の不規則な減光。「エイリアンの巨大構造物 (ダイソン球)では」と話題に。はくちょう座。",
     res:"特定進展: 波長依存の減光からダストが主因とほぼ判明。"},
    {n:"FRB 121102 (反復する高速電波バースト)", kind:"sky", ra:82.995, dec:33.148, mhz:1400, v:"natural", rio:2,
     d:"繰り返す数ミリ秒の強烈な電波爆発。人工ビーコン説も検討された。",
     res:"場所の特定成功: 30億光年先の矮小銀河に局在化 — マグネター説が有力。"},
    {n:"FRB 20200120E (M81方向)", kind:"sky", ra:149.5, dec:68.8, mhz:1400, v:"natural", rio:1,
     d:"最も近い銀河系外FRBのひとつ。",
     res:"場所の特定成功: M81 の球状星団に局在化 — 自然起源(古い星の系)。"},
    {n:"SHGb02+14a (2003, SETI@home)", kind:"sky", ra:25.5, dec:9.0, mhz:1420, v:"natural", rio:1,
     d:"SETI@home の分散解析が拾った候補。うお座-おひつじ座の間(座標は概略)。",
     res:"再観測で微弱・ドリフト大 — 雑音/機器起源とみなされている。"},
    {n:"1991 VG", kind:"sol", ra:0, dec:0, mhz:null, v:"natural", rio:1,
     d:"地球類似軌道の小天体。「異星の探査機では」と論文で議論された。",
     res:"2017年の再観測で自然の小惑星と結論。"},
    {n:"Big Ear 受信地跡 (オハイオ州デラウェア)", kind:"ground", lat:40.2506, lon:-83.0567, mhz:1420, v:"open", rio:0,
     d:"Wow! 信号を受信した Big Ear 電波望遠鏡の跡地。望遠鏡は1998年に解体され、現在はゴルフ場。",
     res:"受信した「場所」は特定済みだが、信号の発生源は未解決のまま。"}
  ];
  function badge(v){ return v==="open"?'<span class="badge b-open">🟢 未解決</span>':
    v==="human"?'<span class="badge b-human">🟡 人工と判明</span>':'<span class="badge b-nat">🔵 自然と判明</span>'; }

  /* ============ atlas (RA/Dec all-sky) ============ */
  var atlas=$("atlas"), ac=atlas.getContext("2d"), CUR=EVENTS[0];
  function drawAtlas(){
    var W=atlas.width,H=atlas.height;
    ac.fillStyle="#020409"; ac.fillRect(0,0,W,H);
    ac.strokeStyle="#141d33"; ac.lineWidth=24; ac.beginPath();
    for(var x=0;x<=W;x+=8){ var ra=x/W*360, y=H/2-Math.sin((ra-90)*Math.PI/180)*H*0.31;
      x===0?ac.moveTo(x,y):ac.lineTo(x,y); }
    ac.stroke();
    ac.fillStyle="#2a3a5a"; ac.font="10px sans-serif"; ac.fillText("天の川",10,14);
    ac.strokeStyle="#0d1626"; ac.lineWidth=1;
    for(var g=0;g<=4;g++){ ac.beginPath(); ac.moveTo(0,g*H/4); ac.lineTo(W,g*H/4); ac.stroke(); }
    for(g=0;g<=6;g++){ ac.beginPath(); ac.moveTo(g*W/6,0); ac.lineTo(g*W/6,H); ac.stroke(); }
    EVENTS.forEach(function(e){
      if(e.kind==="ground") return;
      var x=(360-e.ra)/360*W, y=(90-e.dec)/180*H;
      ac.beginPath(); ac.arc(x,y,e===CUR?6:4,0,7);
      ac.fillStyle=heatByFreq(e.mhz); ac.fill();
      if(e.v==="open"){ ac.strokeStyle="#7fe0a8"; ac.lineWidth=1.6; ac.beginPath(); ac.arc(x,y,(e===CUR?9:7),0,7); ac.stroke(); }
      if(e===CUR){ ac.strokeStyle="#fff"; ac.lineWidth=1.2; ac.beginPath(); ac.arc(x,y,11,0,7); ac.stroke(); }
    });
    ac.fillStyle="#8aa0c0"; ac.fillText("RA 360°→0° / Dec +90°(上)→−90°  🟢=未解決", 10, H-8);
  }
  atlas.addEventListener("click",function(ev){
    var r=this.getBoundingClientRect();
    var mx=(ev.clientX-r.left)*(atlas.width/r.width), my=(ev.clientY-r.top)*(atlas.height/r.height);
    var best=null,bd=1e9;
    EVENTS.forEach(function(e){ if(e.kind==="ground") return;
      var x=(360-e.ra)/360*atlas.width, y=(90-e.dec)/180*atlas.height;
      var d=(x-mx)*(x-mx)+(y-my)*(y-my); if(d<bd){bd=d;best=e;} });
    if(best&&bd<900) select(best);
  });

  /* ============ ground tile view ============ */
  function tXY(lat,lon,z){ var n=Math.pow(2,z);
    var x=(lon+180)/360*n, la=lat*Math.PI/180;
    var y=(1-Math.log(Math.tan(la)+1/Math.cos(la))/Math.PI)/2*n;
    return {x:x,y:y}; }
  function drawGround(e){
    var cv=$("groundmap"), c=cv.getContext("2d"), W=cv.width,H=cv.height, z=13;
    c.fillStyle="#06111e"; c.fillRect(0,0,W,H);
    var ct=tXY(e.lat,e.lon,z), loaded=0;
    for(var dx=-1;dx<=1;dx++) for(var dy=-1;dy<=1;dy++){
      (function(dx,dy){
        var im=new Image(); im.crossOrigin="anonymous";
        im.onload=function(){ loaded++;
          c.drawImage(im, W/2+((Math.floor(ct.x)+dx-ct.x))*256, H/2+((Math.floor(ct.y)+dy-ct.y))*256, 256.8,256.8);
          mark(); };
        im.src="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/"+z+"/"+(Math.floor(ct.y)+dy)+"/"+(Math.floor(ct.x)+dx);
      })(dx,dy);
    }
    function mark(){
      c.strokeStyle="#7fe0a8"; c.lineWidth=2;
      c.beginPath(); c.arc(W/2,H/2,26,0,7); c.stroke();
      c.beginPath(); c.moveTo(W/2-38,H/2); c.lineTo(W/2-14,H/2); c.moveTo(W/2+14,H/2); c.lineTo(W/2+38,H/2);
      c.moveTo(W/2,H/2-38); c.lineTo(W/2,H/2-14); c.moveTo(W/2,H/2+14); c.lineTo(W/2,H/2+38); c.stroke();
    }
    setTimeout(function(){ if(!loaded){
      c.strokeStyle="#12314a"; for(var gx=0;gx<W;gx+=40){c.beginPath();c.moveTo(gx,0);c.lineTo(gx,H);c.stroke();}
      for(var gy=0;gy<H;gy+=40){c.beginPath();c.moveTo(0,gy);c.lineTo(W,gy);c.stroke();}
      c.fillStyle="#28527a"; c.font="12px sans-serif";
      c.fillText("(オフライン: タイル未取得 — 座標は実データ)",16,H-16); mark(); } },2500);
    mark();
  }

  /* ============ selection / 特定ビュー ============ */
  function select(e){
    CUR=e; drawAtlas(); renderList();
    var img=$("cutout"), gm=$("groundmap");
    if(e.kind==="ground"){
      img.style.display="none"; gm.style.display="block"; drawGround(e);
      $("viewNote").textContent="地上の実座標 ("+e.lat.toFixed(4)+"°, "+e.lon.toFixed(4)+") — 公開航空写真タイル (Esri)";
    } else {
      gm.style.display="none"; img.style.display="block";
      $("viewNote").textContent="実サーベイ画像 (DSS2 / CDS hips2fits) を取得中…";
      img.onload=function(){ $("viewNote").textContent="その座標の実際の空 (DSS2 color・視野1°) — RA "+e.ra.toFixed(2)+"° Dec "+e.dec.toFixed(2)+"°"+(e.n.indexOf("SHGb")>=0?" (概略座標)":""); };
      img.onerror=function(){ img.style.display="none"; $("viewNote").textContent="オフラインのためサーベイ画像は取得できません (座標は実データ: RA "+e.ra.toFixed(2)+"° Dec "+e.dec.toFixed(2)+"°)"; };
      img.src="https://alasky.cds.unistra.fr/hips-image-services/hips2fits?hips="+encodeURIComponent("CDS/P/DSS2/color")+
        "&ra="+e.ra+"&dec="+e.dec+"&fov=1.0&width=480&height=480&format=jpg";
    }
    var kv=[["事象",e.n],["何が起きたか",e.d],["特定の結果",e.res],
      ["判定",e.v==="open"?"🟢 未解決 — 宇宙人説を否定できていない":e.v==="human"?"🟡 場所を特定 → 人間の技術だった":"🔵 場所を特定 → 自然現象だった"],
      ["周波数",e.mhz?e.mhz+" MHz":"—"],
      ["注目度 (Rioスケール参考)",e.rio+" / 10"]];
    $("kv").innerHTML=kv.map(function(r){return "<b>"+esc(r[0])+"</b><span>"+esc(r[1])+"</span>";}).join("")+
      '<b>スコア</b><span><span class="score"><i style="width:'+(e.rio*10)+'%;background:'+heatByFreq(e.mhz)+'"></i></span></span>';
  }
  function renderList(){
    var box=$("events"); box.innerHTML="";
    var order=EVENTS.slice().sort(function(a,b){ return (b.v==="open")-(a.v==="open") || b.rio-a.rio; });
    order.forEach(function(e){
      var d=document.createElement("div"); d.className="ev"+(e===CUR?" sel":"");
      d.innerHTML="<div>"+esc(e.n)+badge(e.v)+"</div><div class='t'>"+esc(e.d)+"</div>";
      d.addEventListener("click",function(){ select(e); });
      box.appendChild(d);
    });
  }

  renderList(); select(EVENTS[0]); drawAtlas();
})();
</script>
</body>
</html>
`;

fs.mkdirSync(path.join(IDE, "dist"), { recursive: true });
const outPath = path.join(IDE, "dist", "anomaly-map.html");
fs.writeFileSync(outPath, html);
console.log("built dist/anomaly-map.html (" + fs.statSync(outPath).size + " bytes)");

/* Stage as the native app's www/index.html */
const appWww = path.join(IDE, "anomalymap-app", "www");
fs.mkdirSync(appWww, { recursive: true });
fs.writeFileSync(path.join(appWww, "index.html"), html);
console.log("staged anomalymap-app/www/index.html");
