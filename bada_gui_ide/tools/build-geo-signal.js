#!/usr/bin/env node
/* ============================================================================
 * build-geo-signal.js — build "GeoSignal — 地球の伝達使用地点シアター", a
 * single self-contained HTML app: the companion of GammaTwin/PlanetCinema
 * turned toward EARTH. Earth is the one planet where a civilization is
 * CONFIRMED to use the transmission channels those apps hunt for — and the
 * places where it does so are real, with real coordinates:
 *
 *   📡 EM sites   : deep-space transmitters and radio telescopes
 *                   (臼田 64m, 野辺山 45m, Goldstone DSN, FAST, Green Bank,
 *                    Parkes, Effelsberg, ALMA, Arecibo site…)
 *   🌀 GW sites   : the gravity-channel detectors (KAGRA 神岡, LIGO Hanford /
 *                    Livingston, Virgo) — h ~ 1e-21 spacetime strain.
 *   🛸 anti-grav  : no such facility exists anywhere on Earth (honest note).
 *
 * 「場所の特定地域を動画で見る」— selecting a site plays a continuous
 * ZOOM MOVIE from space down to the facility, rendered from real public
 * map/aerial tiles (Esri World Imagery / OpenStreetMap, no key) with the
 * site's "usage pattern" animated on top (EM rings from transmitters,
 * spacetime ripples from GW detectors). The movie is recordable to a real
 * .webm file. 「周辺」— a world overview shows every site, and the ISS's
 * LIVE position (open wheretheiss API) is plotted as the nearest
 * "surrounding place" using the channels right now. Works offline with a
 * procedural fallback when tiles are unreachable.
 *
 * Output: ../dist/geo-signal.html
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
<title>GeoSignal — 地球の伝達使用地点シアター (特定地域ズーム動画)</title>
<style>
  :root{color-scheme:dark;--bg:#03050c;--line:#1b2740;--ink:#e9f0fb;--dim:#8aa0c0;
        --cy:#39c2ff;--gold:#c8a44a;--green:#2fbf71;--red:#e0555a;}
  *{box-sizing:border-box;}
  body{margin:0;background:#03050c;color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}
  header{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:11px 16px;
         border-bottom:1px solid var(--line);background:#060a14cc;position:sticky;top:0;z-index:20;backdrop-filter:blur(6px);}
  .logo{font-size:19px;font-weight:800;letter-spacing:.4px;
        background:linear-gradient(90deg,#2fbf71,#39c2ff);-webkit-background-clip:text;background-clip:text;color:transparent;}
  .sub{color:var(--dim);font-size:12px;}
  select,input,button{background:#0b1424;border:1px solid var(--line);color:var(--ink);border-radius:8px;
        padding:7px 10px;font-size:13px;font-family:inherit;}
  button{cursor:pointer;} button:hover{background:#152238;}
  button.p{background:#13324a;border-color:#2b628c;} button.r{background:#3a1520;border-color:#6b2e3a;}
  main{max-width:1100px;margin:0 auto;padding:14px 12px 70px;}
  .controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:8px 0;}
  .grid{display:grid;grid-template-columns:2fr 1fr;gap:14px;} @media(max-width:860px){.grid{grid-template-columns:1fr;}}
  .stagewrap{position:relative;background:#000;border:1px solid var(--line);border-radius:14px;overflow:hidden;}
  #stage{width:100%;display:block;background:#000;}
  .hud{position:absolute;left:10px;top:10px;background:#000b;border:1px solid var(--line);border-radius:8px;
       padding:7px 11px;font-size:12px;color:#cfe0f5;line-height:1.6;pointer-events:none;max-width:72%;}
  .hud b{color:var(--gold);}
  .rec{position:absolute;right:12px;top:12px;display:none;align-items:center;gap:6px;background:#000a;
       border:1px solid #6b2e3a;border-radius:8px;padding:5px 10px;font-size:12px;color:#ff9aa5;}
  .rec.on{display:inline-flex;} .rec .d{width:9px;height:9px;border-radius:50%;background:var(--red);animation:pulse 1.2s infinite;}
  @keyframes pulse{50%{opacity:.35;}}
  .card{background:#070c16;border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-top:14px;}
  h2{font-size:15px;margin:0 0 10px;color:var(--cy);}
  .muted{color:var(--dim);font-size:12px;} a{color:var(--cy);}
  .sites{max-height:330px;overflow:auto;border:1px solid var(--line);border-radius:10px;}
  .site{padding:8px 11px;border-bottom:1px solid var(--line);cursor:pointer;font-size:13px;}
  .site:hover{background:#0d1626;} .site.sel{background:#12233c;}
  .site .t{color:var(--dim);font-size:11.5px;}
  #wmap{width:100%;border:1px solid var(--line);border-radius:10px;background:#020409;display:block;cursor:crosshair;}
  .kv{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:13px;margin-top:8px;}
  .kv b{color:var(--gold);font-weight:600;}
  .banner{background:#12233c;border:1px solid #2b628c;border-radius:8px;padding:8px 10px;font-size:12px;color:#bcd8f5;margin-top:8px;}
</style>
</head>
<body>
<header>
  <div><div class="logo">🗼 GeoSignal — 地球の伝達使用地点シアター</div>
    <div class="sub">地球上(+周辺)で電磁波・重力チャネルが実際に使われている実在の地点を、特定地域ズーム動画で見る</div></div>
  <div style="flex:1"></div>
  <span class="muted" id="tileStat">—</span>
</header>
<main>

  <div class="controls">
    <label class="muted">地点:
      <select id="pick" style="min-width:250px"></select></label>
    <label class="muted">地図:
      <select id="layer">
        <option value="sat">航空写真 (Esri World Imagery)</option>
        <option value="map">地図 (OpenStreetMap)</option>
      </select></label>
    <button id="play">⏸ 一時停止</button>
    <label class="muted">速度 <input type="range" id="speed" min="0.3" max="2.5" step="0.1" value="1"/></label>
    <button class="r" id="recBtn">⏺ 動画を録画 (.webm)</button>
    <span class="muted" id="recNote"></span>
  </div>

  <div class="grid">
    <div>
      <div class="stagewrap">
        <canvas id="stage" width="820" height="560"></canvas>
        <div class="hud" id="hud"></div>
        <div class="rec" id="recBadge"><span class="d"></span>REC</div>
      </div>
      <div class="kv" id="kv"></div>
    </div>
    <div>
      <h2 style="margin-top:2px">🌍 地点一覧 + 周辺</h2>
      <canvas id="wmap" width="360" height="180"></canvas>
      <div class="muted" style="margin:4px 0 8px" id="issLine">🛰 ISS (周辺・軌道上): 位置取得中…</div>
      <div class="sites" id="sites"></div>
    </div>
  </div>

  <div class="card">
    <h2>ℹ️ 正直な説明</h2>
    <div class="muted" style="line-height:1.8">
      GammaTwin / PlanetCinema が探す伝達チャネルを<b>地球側から見た</b>アプリです。
      地球は「文明が伝達手段を使っている」ことが確認できる唯一の惑星で、その
      「使っている模様」は実在の施設として地図上にあります — <b>📡 電磁波</b>は
      深宇宙送信局・電波望遠鏡(臼田 64m は 20kW 級の X 帯を惑星間へ実送信)、
      <b>🌀 重力チャネル</b>は重力波検出器(KAGRA・LIGO・Virgo が h~10⁻²¹ の時空
      ひずみを実検出)。<b>🛸 反重力発生器は地球上に存在しません</b>(既知の物理に
      理論なし)。ズーム動画は Esri / OpenStreetMap の公開タイルから合成し
      (オフライン時は簡易描画に自動切替)、⏺ で本物の .webm に保存できます。
      🛰 ISS の現在位置は公開 API (wheretheiss.at) のライブ実データです。
    </div>
  </div>
</main>

<script>
(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

  /* ============ 実在の伝達使用地点 (実座標) ============ */
  // type: em-tx=送信+受信, em-rx=受信, gw=重力波検出
  var SITES=[
    {n:"臼田宇宙空間観測所 64m (JAXA)", c:"日本・長野", lat:36.1292, lon:138.3625, t:"em-tx",
     use:"深宇宙探査機へ X帯 ~20kW を実送信・受信 (はやぶさ等)"},
    {n:"野辺山宇宙電波観測所 45m", c:"日本・長野", lat:35.9411, lon:138.4761, t:"em-rx",
     use:"ミリ波電波望遠鏡 — 宇宙からの電磁波を受信"},
    {n:"KAGRA 重力波望遠鏡", c:"日本・岐阜 神岡 (地下)", lat:36.4119, lon:137.3106, t:"gw",
     use:"🌀 重力チャネル検出器 — 3km レーザー干渉計で h~10⁻²¹ を実測"},
    {n:"Goldstone 深宇宙通信施設 (NASA DSN)", c:"アメリカ・カリフォルニア", lat:35.4267, lon:-116.8900, t:"em-tx",
     use:"70m アンテナ — 惑星間探査機へ最大 ~400kW 送信"},
    {n:"Green Bank 100m 望遠鏡", c:"アメリカ・ウェストバージニア", lat:38.4331, lon:-79.8397, t:"em-rx",
     use:"世界最大の可動電波望遠鏡 — SETI 観測 (Breakthrough Listen) の主力"},
    {n:"LIGO Hanford", c:"アメリカ・ワシントン州", lat:46.4551, lon:-119.4077, t:"gw",
     use:"🌀 4km 干渉計 — 2015年 GW150914 を初検出"},
    {n:"LIGO Livingston", c:"アメリカ・ルイジアナ州", lat:30.5629, lon:-90.7742, t:"gw",
     use:"🌀 4km 干渉計 — Hanford と同時検出で方向を決定"},
    {n:"FAST 500m 球面電波望遠鏡", c:"中国・貴州", lat:25.6529, lon:106.8566, t:"em-rx",
     use:"世界最大の単一開口 — SETI/パルサー受信"},
    {n:"Parkes 64m 'The Dish'", c:"オーストラリア", lat:-32.9984, lon:148.2635, t:"em-rx",
     use:"アポロ11号の映像を受信した歴史的アンテナ"},
    {n:"Effelsberg 100m", c:"ドイツ", lat:50.5248, lon:6.8836, t:"em-rx",
     use:"欧州最大級の電波望遠鏡"},
    {n:"Virgo 重力波検出器", c:"イタリア・ピサ近郊", lat:43.6314, lon:10.5045, t:"gw",
     use:"🌀 3km 干渉計 — LIGO と国際ネットワークを構成"},
    {n:"ALMA (アタカマ大型ミリ波干渉計)", c:"チリ・標高5000m", lat:-23.0290, lon:-67.7550, t:"em-rx",
     use:"66台のアンテナ群 — ミリ波/サブミリ波受信"},
    {n:"アレシボ天文台跡 305m", c:"プエルトリコ", lat:18.3464, lon:-66.7528, t:"em-tx",
     use:"1974年 アレシボ・メッセージを M13 へ実送信 (2020年に崩落・歴史地点)"}
  ];
  function typeJp(t){ return t==="gw"?"🌀 重力チャネル (検出)":t==="em-tx"?"📡 電磁波 (送信+受信)":"📡 電磁波 (受信)"; }

  /* ============ slippy tile math ============ */
  function tXY(lat,lon,z){
    var n=Math.pow(2,z);
    var x=(lon+180)/360*n;
    var la=lat*Math.PI/180;
    var y=(1-Math.log(Math.tan(la)+1/Math.cos(la))/Math.PI)/2*n;
    return {x:x,y:y};
  }
  function tileUrl(z,x,y){
    var n=Math.pow(2,z); x=((x%n)+n)%n;
    if(y<0||y>=n) return null;
    if($("layer").value==="map") return "https://tile.openstreetmap.org/"+z+"/"+x+"/"+y+".png";
    return "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/"+z+"/"+y+"/"+x;
  }
  var CACHE={}, okTiles=0, badTiles=0;
  function getTile(z,x,y){
    var u=tileUrl(z,Math.floor(x),Math.floor(y));
    if(!u) return null;
    var k=$("layer").value+"|"+z+"|"+Math.floor(x)+"|"+Math.floor(y);
    if(CACHE[k]) return CACHE[k];
    var im=new Image();
    im.crossOrigin="anonymous";
    im._ok=false;
    im.onload=function(){ im._ok=true; okTiles++; tileStat(); };
    im.onerror=function(){ badTiles++; tileStat(); };
    im.src=u;
    CACHE[k]=im;
    return im;
  }
  function tileStat(){
    $("tileStat").textContent=okTiles>0?("タイル "+okTiles+" 枚取得"):(badTiles>8?"オフライン (簡易描画)":"タイル取得中…");
  }

  /* ============ zoom movie ============ */
  var cvs=$("stage"), ctx=cvs.getContext("2d");
  var CUR=SITES[0], t0=performance.now(), paused=false, lastF=0;
  var ZMIN=3, ZMAX=16, CYCLE=26;      // seconds per zoom cycle at 1x

  function drawLevel(z,alpha){
    var c=tXY(CUR.lat,CUR.lon,Math.floor(z));
    var scale=Math.pow(2,z-Math.floor(z));       // 1..2 within a level
    var px=256*scale;
    var W=cvs.width,H=cvs.height;
    var drew=0;
    ctx.globalAlpha=alpha;
    for(var dx=-2;dx<=2;dx++) for(var dy=-2;dy<=2;dy++){
      var tx=Math.floor(c.x)+dx, ty=Math.floor(c.y)+dy;
      var im=getTile(Math.floor(z),tx,ty);
      if(!im||!im._ok) continue;
      var sx=W/2+((tx-c.x))*px, sy=H/2+((ty-c.y))*px;
      try{ ctx.drawImage(im,sx,sy,px+0.8,px+0.8); drew++; }catch(e){}
    }
    ctx.globalAlpha=1;
    return drew;
  }
  function fallbackScene(z){
    var W=cvs.width,H=cvs.height;
    var g=ctx.createRadialGradient(W/2,H/2,10,W/2,H/2,W*0.7);
    g.addColorStop(0,"#0d2418"); g.addColorStop(0.5,"#08131f"); g.addColorStop(1,"#02040a");
    ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
    ctx.strokeStyle="#12314a"; ctx.lineWidth=1;
    var step=40*Math.pow(2,(z%1));
    for(var x=W/2%step;x<W;x+=step){ ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }
    for(var y=H/2%step;y<H;y+=step){ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }
    ctx.fillStyle="#28527a"; ctx.font="12px sans-serif";
    ctx.fillText("(オフライン: タイル未取得のため簡易表示 — 座標は実データ)",14,H-14);
  }

  function draw(now){
    requestAnimationFrame(draw);
    if(paused&&!recording) return;
    if(now-lastF<33) return; lastF=now;
    var sp=parseFloat($("speed").value);
    var tt=((now-t0)/1000*sp)%CYCLE;
    // ease: dive from ZMIN to ZMAX then hold + loop
    var f=tt/CYCLE;
    var z=f<0.8 ? ZMIN+(ZMAX-ZMIN)*(f/0.8) : ZMAX;
    var W=cvs.width,H=cvs.height;
    ctx.fillStyle="#000"; ctx.fillRect(0,0,W,H);
    var drew=drawLevel(z,1);
    if(z-Math.floor(z)>0.6) drew+=drawLevel(z+1,(z-Math.floor(z)-0.6)/0.4*0.9);
    if(drew===0) fallbackScene(z);

    /* usage-pattern overlay at the exact site */
    var cx=W/2, cy=H/2;
    var k=((now-t0)/1000*sp*40)%120;
    if(CUR.t==="gw"){
      ctx.strokeStyle="rgba(200,164,74,0.65)"; ctx.lineWidth=1.6;
      ctx.beginPath(); ctx.ellipse(cx,cy,k,k*0.62,0,0,7); ctx.stroke();
      ctx.strokeStyle="rgba(200,164,74,0.3)";
      ctx.beginPath(); ctx.ellipse(cx,cy,(k+60)%120,((k+60)%120)*0.62,0,0,7); ctx.stroke();
    } else {
      ctx.strokeStyle="rgba(80,220,255,0.65)"; ctx.lineWidth=1.6;
      ctx.beginPath(); ctx.arc(cx,cy,k,0,7); ctx.stroke();
      ctx.strokeStyle="rgba(80,220,255,0.3)";
      ctx.beginPath(); ctx.arc(cx,cy,(k+60)%120,0,7); ctx.stroke();
    }
    ctx.strokeStyle="#fff"; ctx.lineWidth=1.4;
    ctx.beginPath(); ctx.moveTo(cx-12,cy); ctx.lineTo(cx-4,cy); ctx.moveTo(cx+4,cy); ctx.lineTo(cx+12,cy);
    ctx.moveTo(cx,cy-12); ctx.lineTo(cx,cy-4); ctx.moveTo(cx,cy+4); ctx.lineTo(cx,cy+12); ctx.stroke();

    $("hud").innerHTML="<b>"+esc(CUR.n)+"</b> — "+esc(CUR.c)+
      "<br>"+typeJp(CUR.t)+"  |  緯度 "+CUR.lat.toFixed(4)+"° 経度 "+CUR.lon.toFixed(4)+"°"+
      "<br>ズーム z="+z.toFixed(1)+" (宇宙→地表の連続ズーム動画・ループ)";
  }

  /* ============ world overview + ISS (周辺) ============ */
  var wm=$("wmap"), wc=wm.getContext("2d"), ISS=null;
  function drawWorld(){
    var W=wm.width,H=wm.height;
    wc.fillStyle="#020409"; wc.fillRect(0,0,W,H);
    // background: z=2 tiles (equirect approx via mercator rows 0..3)
    var drew=0;
    for(var x=0;x<4;x++) for(var y=0;y<4;y++){
      var im=getTile(2,x,y);
      if(im&&im._ok){ try{ wc.drawImage(im,x*W/4,y*H/4,W/4,H/4); drew++; }catch(e){} }
    }
    if(!drew){
      wc.strokeStyle="#0f2237";
      for(var gx=0;gx<=6;gx++){ wc.beginPath(); wc.moveTo(gx*W/6,0); wc.lineTo(gx*W/6,H); wc.stroke(); }
      for(var gy=0;gy<=3;gy++){ wc.beginPath(); wc.moveTo(0,gy*H/3); wc.lineTo(W,gy*H/3); wc.stroke(); }
    }
    function pt(lat,lon){ var p=tXY(lat,lon,2); return {x:p.x/4*W, y:p.y/4*H}; }
    SITES.forEach(function(s){
      var p=pt(s.lat,s.lon);
      wc.fillStyle=s.t==="gw"?"#c8a44a":"#39c2ff";
      wc.beginPath(); wc.arc(p.x,p.y,s===CUR?5:3,0,7); wc.fill();
      if(s===CUR){ wc.strokeStyle="#fff"; wc.lineWidth=1.2; wc.beginPath(); wc.arc(p.x,p.y,7,0,7); wc.stroke(); }
    });
    if(ISS){
      var q=pt(ISS.lat,ISS.lon);
      wc.fillStyle="#7fe0a8"; wc.beginPath(); wc.arc(q.x,q.y,4,0,7); wc.fill();
      wc.fillStyle="#7fe0a8"; wc.font="9px sans-serif"; wc.fillText("ISS",q.x+6,q.y+3);
    }
  }
  setInterval(drawWorld,900);
  wm.addEventListener("click",function(ev){
    var r=this.getBoundingClientRect();
    var mx=(ev.clientX-r.left)*(wm.width/r.width), my=(ev.clientY-r.top)*(wm.height/r.height);
    var best=null,bd=1e9;
    SITES.forEach(function(s){ var p=tXY(s.lat,s.lon,2), x=p.x/4*wm.width, y=p.y/4*wm.height;
      var d=(x-mx)*(x-mx)+(y-my)*(y-my); if(d<bd){bd=d;best=s;} });
    if(best&&bd<600) select(best);
  });

  function pollIss(){
    fetch("https://api.wheretheiss.at/v1/satellites/25544")
      .then(function(r){ return r.ok?r.json():null; })
      .then(function(j){ if(!j) return;
        ISS={lat:j.latitude,lon:j.longitude,alt:j.altitude};
        $("issLine").textContent="🛰 ISS (周辺・軌道上 LIVE): 緯度 "+j.latitude.toFixed(2)+"° 経度 "+j.longitude.toFixed(2)+"° 高度 "+j.altitude.toFixed(0)+" km — 電磁波チャネルを常時使用中";
      })
      .catch(function(){ $("issLine").textContent="🛰 ISS (周辺・軌道上): オフラインのため位置は取得できません (公開API: wheretheiss.at)"; });
  }
  pollIss(); setInterval(pollIss,15000);

  /* ============ selection ============ */
  function select(s){
    CUR=s; t0=performance.now(); okTiles=0; badTiles=0;
    $("pick").value=s.n;
    var kv=[["地点",s.n+" ("+s.c+")"],["チャネル",typeJp(s.t)],
            ["使っている模様",s.use],
            ["座標",s.lat.toFixed(4)+"°, "+s.lon.toFixed(4)+"°"],
            ["反重力発生器","🛸 地球上に存在しません (既知の物理に理論なし・正直)"]];
    $("kv").innerHTML=kv.map(function(r){return "<b>"+esc(r[0])+"</b><span>"+esc(r[1])+"</span>";}).join("");
    renderList();
  }
  function renderList(){
    var box=$("sites"); box.innerHTML="";
    SITES.forEach(function(s){
      var d=document.createElement("div"); d.className="site"+(s===CUR?" sel":"");
      d.innerHTML="<div>"+(s.t==="gw"?"🌀 ":"📡 ")+esc(s.n)+"</div><div class='t'>"+esc(s.c)+" — "+esc(s.use)+"</div>";
      d.addEventListener("click",function(){ select(s); });
      box.appendChild(d);
    });
  }
  var sel=$("pick");
  SITES.forEach(function(s){ var o=document.createElement("option"); o.value=s.n; o.textContent=(s.t==="gw"?"🌀 ":"📡 ")+s.n; sel.appendChild(o); });
  sel.addEventListener("change",function(){ var s=SITES.filter(function(q){return q.n===sel.value;})[0]; if(s) select(s); });
  $("layer").addEventListener("change",function(){ okTiles=0; badTiles=0; CACHE={}; });
  $("play").addEventListener("click",function(){ paused=!paused; this.textContent=paused?"▶ 再生":"⏸ 一時停止"; });

  /* ============ .webm recording ============ */
  var recording=false, recorder=null, chunks=[];
  $("recBtn").addEventListener("click",function(){
    if(!(window.MediaRecorder&&cvs.captureStream)){ $("recNote").textContent="録画未対応のブラウザです"; return; }
    if(!recording){
      try{
        var stream=cvs.captureStream(30);
        var mime=MediaRecorder.isTypeSupported("video/webm;codecs=vp9")?"video/webm;codecs=vp9":"video/webm";
        recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:5000000});
        chunks=[];
        recorder.ondataavailable=function(e){ if(e.data&&e.data.size) chunks.push(e.data); };
        recorder.onstop=function(){
          var blob=new Blob(chunks,{type:"video/webm"});
          var a=document.createElement("a");
          a.href=URL.createObjectURL(blob);
          a.download="geosignal-"+CUR.n.replace(/[^A-Za-z0-9._-]+/g,"_").replace(/^_+|_+$/g,"")+".webm";
          document.body.appendChild(a); a.click();
          setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); },200);
          $("recNote").textContent="動画を保存しました ("+(blob.size/1024/1024).toFixed(1)+" MB)";
        };
        recorder.start(200); recording=true;
        $("recBtn").textContent="⏹ 停止 / 保存"; $("recBadge").classList.add("on");
        $("recNote").textContent="録画中…";
      }catch(e){ $("recNote").textContent="録画開始に失敗: "+e.message; }
    } else {
      recording=false; try{ recorder.stop(); }catch(e){}
      $("recBtn").textContent="⏺ 動画を録画 (.webm)"; $("recBadge").classList.remove("on");
    }
  });

  /* ============ init ============ */
  renderList(); select(SITES[0]); tileStat();
  requestAnimationFrame(draw);
})();
</script>
</body>
</html>
`;

fs.mkdirSync(path.join(IDE, "dist"), { recursive: true });
const outPath = path.join(IDE, "dist", "geo-signal.html");
fs.writeFileSync(outPath, html);
console.log("built dist/geo-signal.html (" + fs.statSync(outPath).size + " bytes)");

/* Stage the same page as the GeoSignal native app's www/index.html */
const appWww = path.join(IDE, "geosignal-app", "www");
fs.mkdirSync(appWww, { recursive: true });
fs.writeFileSync(path.join(appWww, "index.html"), html);
console.log("staged geosignal-app/www/index.html");
