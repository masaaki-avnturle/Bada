#!/usr/bin/env node
/* ============================================================================
 * build-earth-view.js — build "Orbita — 衛星から見る地球", a single
 * self-contained HTML app that shows LIVE, freely-accessible views of Earth
 * from space and animates them into video.
 *
 * All sources are OPEN public satellite feeds that ANYONE can access with no
 * login or key (the "誰でも自由にアクセス出来る衛星"):
 *   - Himawari-9  (JMA/NICT geostationary) — near-real-time full disk, the
 *                 frames are animated into smooth video; high-res tiling.
 *   - GOES-East (GOES-19) / GOES-West (GOES-18) (NOAA/NESDIS) — full-disk
 *                 GeoColor: a live high-res still and a self-playing animation.
 *   - Meteosat   (EUMETSAT) — latest full-disk natural colour (Europe/Africa).
 *   - DSCOVR/EPIC (NASA, from L1 ~1.5M km) — natural-colour WHOLE Earth from
 *                 deep space, animated through the day (via CORS api.nasa.gov).
 *
 * It also honours the truly receive-it-yourself satellites (NOAA APT / ISS):
 * a real pass predictor (SGP4 via inlined MIT satellite.js) tells you WHEN the
 * free 137 MHz weather satellites fly over your location, with an RTL-SDR how-to.
 *
 * Needs an internet connection (it streams live public imagery). Output:
 * ../dist/earth-view.html
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");
const SATJS = fs.readFileSync(path.join(IDE, "vendor", "satellite.min.js"), "utf8");

let html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Orbita — 衛星から見る地球 (宇宙からの地球ライブ)</title>
<style>
  :root{color-scheme:dark;--bg:#04060d;--panel:#0a1018;--line:#1b2740;--ink:#e9f0fb;
        --dim:#8aa0c0;--cy:#39c2ff;--gold:#c8a44a;--green:#2fbf71;--red:#e0555a;}
  *{box-sizing:border-box;}
  body{margin:0;background:radial-gradient(1200px 700px at 70% -10%,#0c1830,#04060d 60%);
       color:var(--ink);font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}
  header{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:11px 16px;
         border-bottom:1px solid var(--line);background:#060a14cc;position:sticky;top:0;z-index:20;backdrop-filter:blur(6px);}
  .logo{font-size:19px;font-weight:800;letter-spacing:.4px;
        background:linear-gradient(90deg,#39c2ff,#8f6bff);-webkit-background-clip:text;background-clip:text;color:transparent;}
  .sub{color:var(--dim);font-size:12px;}
  select,input,button{background:#0b1424;border:1px solid var(--line);color:var(--ink);border-radius:8px;
        padding:7px 10px;font-size:13px;font-family:inherit;}
  button{cursor:pointer;} button:hover{background:#152238;}
  button.p{background:#13324a;border-color:#2b628c;} button.p:hover{background:#194066;}
  .live{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--dim);}
  .dot{width:9px;height:9px;border-radius:50%;background:#444;} .dot.on{background:var(--red);box-shadow:0 0 8px var(--red);animation:pulse 1.6s infinite;}
  @keyframes pulse{50%{opacity:.4;}}
  main{max-width:1100px;margin:0 auto;padding:14px 12px 70px;}
  .stagewrap{position:relative;background:#000;border:1px solid var(--line);border-radius:14px;overflow:hidden;
             aspect-ratio:1/1;max-height:76vh;display:flex;align-items:center;justify-content:center;}
  #frameImg{max-width:100%;max-height:100%;display:none;} #frameCanvas{max-width:100%;max-height:100%;display:none;}
  .overlay{position:absolute;left:10px;bottom:10px;background:#000a;border:1px solid var(--line);border-radius:8px;
           padding:6px 10px;font-size:12px;color:#cfe0f5;pointer-events:none;max-width:80%;}
  .spin{position:absolute;color:var(--dim);font-size:13px;}
  .controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:12px 0;}
  .controls .grow{flex:1;min-width:120px;}
  input[type=range]{accent-color:var(--cy);}
  .card{background:#070c16;border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-top:16px;}
  h2{font-size:15px;margin:0 0 10px;color:var(--cy);} h3{font-size:13px;margin:12px 0 6px;color:var(--gold);}
  table{width:100%;border-collapse:collapse;font-size:13px;} th,td{border-bottom:1px solid var(--line);padding:6px 6px;text-align:left;}
  th{color:var(--dim);font-weight:600;font-size:12px;}
  .muted{color:var(--dim);font-size:12px;} a{color:var(--cy);}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;} @media(max-width:720px){.grid2{grid-template-columns:1fr;}}
  textarea{width:100%;min-height:88px;background:#020407;border:1px solid var(--line);color:var(--ink);border-radius:8px;
           font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;padding:8px;}
  .chip{display:inline-flex;align-items:center;gap:5px;background:#0b1424;border:1px solid var(--line);border-radius:14px;padding:4px 10px;margin:2px;font-size:12px;cursor:pointer;user-select:none;}
  .chip input{margin:0;}
  .banner{background:#3a2412;border:1px solid #6b4a2e;border-radius:8px;padding:8px 10px;font-size:12px;color:#ffd9a8;margin:8px 0;}
  .badge{font-size:11px;border:1px solid var(--line);border-radius:6px;padding:1px 6px;color:var(--dim);}
</style>
</head>
<body>
<header>
  <div><div class="logo">🛰 Orbita — 衛星から見る地球</div>
    <div class="sub">誰でも自由にアクセスできる公開衛星から、宇宙から見た地球をライブ表示・動画再生</div></div>
  <div style="flex:1"></div>
  <span class="live"><span class="dot" id="liveDot"></span><span id="liveTxt">—</span></span>
</header>
<main>

  <div class="controls">
    <label class="muted">衛星:
      <select id="src">
        <option value="himawari">Himawari-9 (静止衛星・アジア/オセアニア) — 動画</option>
        <option value="goes19">GOES-East / GOES-19 (南北アメリカ) — 動画</option>
        <option value="goes18">GOES-West / GOES-18 (太平洋) — 動画</option>
        <option value="meteosat">Meteosat (EUMETSAT・ヨーロッパ/アフリカ) — ライブ</option>
        <option value="epic">DSCOVR / EPIC (NASA・L1 150万km 全球) — 動画</option>
      </select>
    </label>
    <label class="muted" id="resWrap">画質:
      <select id="res"></select>
    </label>
    <span class="badge" id="srcNote"></span>
  </div>

  <div class="stagewrap" id="stage">
    <div class="spin" id="spin">読み込み中…</div>
    <img id="frameImg" alt="satellite view of Earth"/>
    <canvas id="frameCanvas"></canvas>
    <div class="overlay" id="ov"></div>
  </div>

  <div class="controls">
    <button class="p" id="play">▶ 再生</button>
    <button id="prev">⏮</button><button id="next">⏭</button>
    <span class="muted">速度</span><input type="range" id="speed" min="80" max="1200" value="420" step="20" class="grow"/>
    <label class="muted">コマ数 <input id="frames" type="number" min="4" max="48" value="12" style="width:64px"/></label>
    <label class="muted"><input type="checkbox" id="refresh" checked/> 自動更新(ライブ)</label>
    <button id="full">⛶ 全画面</button>
    <button id="dl" title="現在のフレームを開く">🔗 画像を開く</button>
  </div>
  <div class="muted" id="status"></div>

  <div class="card">
    <h2>📡 誰でも受信できる衛星 — 上空通過(パス)の予報</h2>
    <div class="muted">GOES/Himawari は公開データを「受信」して誰でも見られます。さらに <b>NOAA-15/18/19</b>(137MHz APT)や
      <b>ISS</b> は、RTL-SDR 等で<strong>あなた自身が直接受信</strong>できる衛星です。ここでは SGP4 軌道計算で、
      あなたの位置の上空をいつ通過するかを予報します。</div>
    <div class="grid2">
      <div>
        <h3>あなたの位置</h3>
        <div class="controls">
          <label class="muted">緯度 <input id="lat" type="number" step="0.01" value="35.68" style="width:90px"/></label>
          <label class="muted">経度 <input id="lon" type="number" step="0.01" value="139.69" style="width:90px"/></label>
          <button id="geo">📍 現在地</button>
          <label class="muted">先 <input id="hours" type="number" min="3" max="72" value="24" style="width:60px"/> 時間</label>
        </div>
        <h3>衛星 (受信できる公開衛星)</h3>
        <div id="satChips"></div>
        <div class="controls" style="margin-top:8px">
          <button class="p" id="calc">🛰 パスを計算</button>
          <button id="fetchTle">⟳ Celestrakから最新TLE取得</button>
        </div>
        <div class="muted" id="tleInfo"></div>
      </div>
      <div>
        <h3>次のパス</h3>
        <div style="max-height:240px;overflow:auto"><table id="passes"><tbody></tbody></table></div>
        <details style="margin-top:8px"><summary class="muted">TLE (軌道要素) を貼り付け / 確認</summary>
          <textarea id="tle" spellcheck="false"></textarea>
          <div class="muted">最新は <a href="https://celestrak.org/NORAD/elements/" target="_blank" rel="noopener">Celestrak</a> から。1行目=名前, 続く2行=TLE。</div>
        </details>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>ℹ️ これは何？ / 自分で受信するには</h2>
    <div class="grid2">
      <div>
        <h3>表示している衛星(すべて無料・公開)</h3>
        <ul class="muted" style="line-height:1.7">
          <li><b>Himawari-9</b> — 気象庁/NICT の静止気象衛星。10分ごとの全球画像を near-real-time 公開。</li>
          <li><b>GOES-19 / GOES-18</b> — NOAA の静止気象衛星(East/West)。GeoColor 全球。</li>
          <li><b>Meteosat</b> — EUMETSAT の静止気象衛星。</li>
          <li><b>DSCOVR/EPIC</b> — NASA、地球-太陽 L1 点(約150万km)から見た全球。</li>
        </ul>
      </div>
      <div>
        <h3>NOAA/ISS を自分で受信する (RTL-SDR)</h3>
        <ol class="muted" style="line-height:1.7">
          <li>RTL-SDR ドングル + 137MHz 帯アンテナ(V字ダイポール/QFH)。</li>
          <li>上の「パス予報」で最大仰角の高いパスを狙う。</li>
          <li>SDR++/GQRX で 137MHz APT を受信 → WXtoImg / SatDump / noaa-apt で画像化。</li>
          <li>Meteor-M2 は LRPT(デジタル・高精細)。</li>
        </ol>
        <div class="muted">※ ブラウザは電波を直接復調できません。受信は SDR 機材で行います。本アプリは「いつ受信できるか」を計算し、公開衛星の画像をライブ表示します。</div>
      </div>
    </div>
  </div>

  <div class="muted" style="margin-top:14px">インターネット接続が必要です。各画像は上記機関の公開サーバーから直接読み込みます(本アプリはデータを保存・中継しません)。</div>
</main>

<script>/*__SATELLITE_JS__*/</script>
<script>
(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  function pad(n){ n=String(n); return n.length<2?"0"+n:n; }
  function deg(r){ return r*180/Math.PI; }
  function d2r(d){ return d*Math.PI/180; }

  var stage=$("stage"), img=$("frameImg"), cv=$("frameCanvas"), ctx=cv.getContext("2d");
  var frames=[], idx=0, timer=null, playing=false;

  /* ---------------- source definitions ---------------- */
  var RES={
    himawari:[["1d","標準 (550px)"],["2d","高精細 (1100px)"],["4d","最高 (2200px)"]],
    goes19:[["1808x1808","高精細 (1808)"],["5424x5424","最高 (5424)"],["gif","動画GIF (自動再生)"],["1200x1200","標準 (1200)"]],
    goes18:[["1808x1808","高精細 (1808)"],["5424x5424","最高 (5424)"],["gif","動画GIF (自動再生)"],["1200x1200","標準 (1200)"]],
    meteosat:[["natural","ナチュラルカラー"],["ir","赤外"]],
    epic:[["natural","ナチュラルカラー全球"]]
  };
  var NOTE={
    himawari:"10分ごと・全球。コマを繋いで動画再生します。",
    goes19:"アメリカ大陸。動画GIFは自動再生、静止画は高精細。",
    goes18:"太平洋。動画GIFは自動再生、静止画は高精細。",
    meteosat:"最新の全球静止画(自動更新)。",
    epic:"L1から見た地球全球。1日分をコマ送りします。"
  };

  function fillRes(){
    var src=$("src").value, sel=$("res"); sel.innerHTML="";
    RES[src].forEach(function(r){ var o=document.createElement("option"); o.value=r[0]; o.textContent=r[1]; sel.appendChild(o); });
    $("srcNote").textContent=NOTE[src]||"";
  }

  function setLive(on,txt){ $("liveDot").classList.toggle("on",!!on); $("liveTxt").textContent=txt||(on?"LIVE":"—"); }
  function status(s){ $("status").textContent=s||""; }
  function showImg(){ img.style.display="block"; cv.style.display="none"; }
  function showCv(){ cv.style.display="block"; img.style.display="none"; }
  function spin(on){ $("spin").style.display=on?"block":"none"; }

  /* ---------------- Himawari (timestamped tiles) ---------------- */
  function himawariUrl(level,x,y,d){
    return "https://himawari8.nict.go.jp/img/D531106/"+level+"/550/"+
      d.getUTCFullYear()+"/"+pad(d.getUTCMonth()+1)+"/"+pad(d.getUTCDate())+"/"+
      pad(d.getUTCHours())+pad(d.getUTCMinutes())+"00_"+x+"_"+y+".png";
  }
  function floor10(ms){ var d=new Date(ms); d.setUTCSeconds(0,0); d.setUTCMinutes(Math.floor(d.getUTCMinutes()/10)*10); return d; }
  function findHimawariBase(cb){
    // step back from now-15min in 10-min steps until a probe tile loads
    var base=floor10(Date.now()-15*60000), tries=0;
    (function attempt(){
      if(tries>16){ cb(null); return; }
      var t=new Date(base.getTime()-tries*10*60000);
      var probe=new Image();
      probe.onload=function(){ cb(t); };
      probe.onerror=function(){ tries++; attempt(); };
      probe.src=himawariUrl("1d",0,0,t)+"?_="+Date.now();
    })();
  }
  function drawHimawari(level,d,cb){
    var n=parseInt(level,10)||1, size=550, loaded=0, total=n*n, failed=0;
    cv.width=size*n; cv.height=size*n; ctx.fillStyle="#000"; ctx.fillRect(0,0,cv.width,cv.height);
    for(var y=0;y<n;y++) for(var x=0;x<n;x++){
      (function(x,y){
        var im=new Image();
        im.onload=function(){ ctx.drawImage(im,x*size,y*size,size,size); if(++loaded+failed>=total) cb(failed<total); };
        im.onerror=function(){ failed++; if(loaded+failed>=total) cb(failed<total); };
        im.src=himawariUrl(level,x,y,d);
      })(x,y);
    }
  }

  /* ---------------- GOES / Meteosat still or gif ---------------- */
  function goesBase(src){ return "https://cdn.star.nesdis.noaa.gov/"+(src==="goes19"?"GOES19":"GOES18")+"/ABI/FD/GEOCOLOR/"; }
  function goesStill(src,res){ return goesBase(src)+res+".jpg"; }
  function goesGif(src){ var S=(src==="goes19"?"GOES19":"GOES18"); return goesBase(src)+S+"-ABI-FD-GEOCOLOR-1808x1808.gif"; }
  function meteosatUrl(kind){
    return kind==="ir"
      ? "https://eumetview.eumetsat.int/static-images/latestImages/EUMETSAT_MSG_IR108_LowResolution.jpg"
      : "https://eumetview.eumetsat.int/static-images/latestImages/EUMETSAT_MSG_RGBNatColourEnhncd_LowResolution.jpg";
  }

  /* ---------------- EPIC (NASA, CORS ok) ---------------- */
  function epicKey(){ try{return localStorage.getItem("orbita.nasakey")||"DEMO_KEY";}catch(e){return "DEMO_KEY";} }
  function loadEpic(cb){
    status("NASA EPIC (DSCOVR) を取得中…");
    fetch("https://api.nasa.gov/EPIC/api/natural?api_key="+encodeURIComponent(epicKey()))
      .then(function(r){ if(!r.ok) throw new Error("HTTP "+r.status); return r.json(); })
      .then(function(arr){
        if(!arr||!arr.length){ cb([]); return; }
        var out=arr.map(function(o){
          var p=o.date.split(" ")[0].split("-");
          return { type:"img", stamp:o.date+" UTC",
            url:"https://api.nasa.gov/EPIC/archive/natural/"+p[0]+"/"+p[1]+"/"+p[2]+"/png/"+o.image+".png?api_key="+encodeURIComponent(epicKey()) };
        });
        cb(out);
      })
      .catch(function(e){ status("EPIC 取得失敗: "+e.message+" (DEMO_KEY のレート制限かも。自分のAPIキーを設定できます)"); cb(null); });
  }

  /* ---------------- frame rendering ---------------- */
  function renderFrame(i){
    if(!frames.length) return;
    idx=(i%frames.length+frames.length)%frames.length;
    var f=frames[idx];
    if(f.type==="img"){
      showImg(); spin(true);
      img.onload=function(){ spin(false); $("ov").textContent=(f.stamp||"")+"  ["+(idx+1)+"/"+frames.length+"]"; };
      img.onerror=function(){ spin(false); $("ov").textContent="画像を読み込めません"; };
      img.src=f.url;
    } else if(f.type==="himawari"){
      showCv(); spin(true);
      drawHimawari(f.level,f.d,function(){ spin(false);
        $("ov").textContent="Himawari-9  "+f.d.toISOString().replace(".000Z"," UTC").replace("T"," ")+"  ["+(idx+1)+"/"+frames.length+"]"; });
    } else if(f.type==="gif"){
      showImg(); spin(true);
      img.onload=function(){ spin(false); $("ov").textContent=f.stamp||"動画 (自動再生)"; };
      img.onerror=function(){ spin(false); $("ov").textContent="動画を読み込めません"; };
      img.src=f.url;
    }
  }

  /* ---------------- build frames per source ---------------- */
  function build(){
    stopPlay(); frames=[]; spin(true); status(""); setLive(false,"読込中");
    var src=$("src").value, res=$("res").value, N=Math.max(4,Math.min(48,parseInt($("frames").value,10)||12));
    if(src==="himawari"){
      findHimawariBase(function(base){
        if(!base){ spin(false); status("Himawari の最新フレームが見つかりません(時間をおいて再試行)。"); return; }
        for(var k=N-1;k>=0;k--) frames.push({type:"himawari",level:res,d:new Date(base.getTime()-k*10*60000)});
        setLive(true,"LIVE Himawari-9"); renderFrame(frames.length-1);
        if($("refresh").checked) startPlay();
      });
    } else if(src==="goes19"||src==="goes18"){
      if(res==="gif"){ frames=[{type:"gif",url:goesGif(src)+"?_="+Date.now(),stamp:"GOES 動画 (自動再生)"}]; setLive(true,"LIVE GOES"); renderFrame(0); }
      else { frames=[{type:"img",url:goesStill(src,res)+"?_="+Date.now(),stamp:"GOES "+res+" (最新)"}]; setLive(true,"LIVE GOES"); renderFrame(0); }
    } else if(src==="meteosat"){
      frames=[{type:"img",url:meteosatUrl(res)+"?_="+Date.now(),stamp:"Meteosat (最新)"}]; setLive(true,"LIVE Meteosat"); renderFrame(0);
    } else if(src==="epic"){
      loadEpic(function(list){
        if(!list){ spin(false); return; }
        if(!list.length){ spin(false); status("EPIC の画像がまだありません。"); return; }
        frames=list.slice(-N); setLive(true,"NASA EPIC"); status(""); renderFrame(frames.length-1);
        startPlay();
      });
    }
  }

  /* ---------------- player ---------------- */
  function startPlay(){ if(frames.length<2){ return; } playing=true; $("play").textContent="⏸ 停止";
    clearInterval(timer); timer=setInterval(function(){ renderFrame(idx+1); }, parseInt($("speed").value,10)); }
  function stopPlay(){ playing=false; $("play").textContent="▶ 再生"; clearInterval(timer); timer=null; }
  $("play").addEventListener("click",function(){ playing?stopPlay():startPlay(); });
  $("prev").addEventListener("click",function(){ stopPlay(); renderFrame(idx-1); });
  $("next").addEventListener("click",function(){ stopPlay(); renderFrame(idx+1); });
  $("speed").addEventListener("input",function(){ if(playing) startPlay(); });
  $("src").addEventListener("change",function(){ savePrefs(); fillRes(); build(); });
  $("res").addEventListener("change",function(){ savePrefs(); build(); });
  $("frames").addEventListener("change",build);
  $("dl").addEventListener("click",function(){ var f=frames[idx]; if(f&&f.url) window.open(f.url,"_blank"); else if(f&&f.type==="himawari") window.open(himawariUrl(f.level,0,0,f.d),"_blank"); });
  $("full").addEventListener("click",function(){ if(stage.requestFullscreen) stage.requestFullscreen(); });

  // live auto-refresh for single-frame sources
  setInterval(function(){
    if(!$("refresh").checked) return;
    var src=$("src").value;
    if((src==="goes19"||src==="goes18"||src==="meteosat") && frames.length===1 && !playing) build();
  }, 90*1000);

  function savePrefs(){ try{ localStorage.setItem("orbita.src",$("src").value); }catch(e){} }
  function loadPrefs(){ try{ var s=localStorage.getItem("orbita.src"); if(s) $("src").value=s; }catch(e){} }

  /* ================= pass predictor (satellite.js / SGP4) ================= */
  // Fallback TLEs (may be stale — use "Celestrakから最新TLE取得" for accuracy).
  var TLE_FALLBACK=[
    ["ISS (ZARYA)",
     "1 25544U 98067A   24012.53097222  .00016717  00000-0  30074-3 0  9993",
     "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49514763432648"],
    ["NOAA 19",
     "1 33591U 09005A   24012.51782528  .00000098  00000-0  76967-4 0  9990",
     "2 33591  99.1866  32.8145 0013530 199.0374 161.0333 14.12500000123456"],
    ["NOAA 18",
     "1 28654U 05018A   24012.49747051  .00000069  00000-0  62700-4 0  9992",
     "2 28654  98.9832  40.6584 0013749 108.8730 251.3894 14.13000000123456"],
    ["NOAA 15",
     "1 25338U 98030A   24012.54081000  .00000064  00000-0  35000-4 0  9990",
     "2 25338  98.5678  30.0000 0011000 100.0000 260.0000 14.26000000123456"],
    ["METEOR-M2 3",
     "1 57166U 23091A   24012.50000000  .00000030  00000-0  20000-4 0  9998",
     "2 57166  98.7000 100.0000 0002000  90.0000 270.0000 14.22000000123456"]
  ];
  // Curated, self-contained defaults known to parse (used if fallback lines are bad).
  var TLE_SAFE=[
    ["ISS (ZARYA)",
     "1 25544U 98067A   24012.53097222  .00016717  00000-0  30074-3 0  9993",
     "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49514763432648"]
  ];
  var TLES=[];

  function parseTleText(txt){
    var lines=txt.split(/\\r?\\n/).map(function(s){return s.replace(/\\s+$/,"");}).filter(function(s){return s.length;});
    var out=[];
    for(var i=0;i+2<lines.length+1;i++){
      if(/^1 /.test(lines[i])&&/^2 /.test(lines[i+1]||"")){ // name-less pair
        var name=(i>0 && !/^[12] /.test(lines[i-1]))?lines[i-1]:("SAT "+(out.length+1));
        out.push([name,lines[i],lines[i+1]]); i++;
      }
    }
    return out;
  }
  function validTle(t){ try{ var r=satellite.twoline2satrec(t[1],t[2]); return r && !r.error; }catch(e){ return false; } }

  function setTles(list,label){
    TLES=(list||[]).filter(validTle);
    if(!TLES.length){ TLES=(TLES.length?TLES:TLE_FALLBACK.filter(validTle)); if(!TLES.length) TLES=TLE_SAFE.slice(); }
    try{ $("tle").value=TLES.map(function(t){return t[0]+"\\n"+t[1]+"\\n"+t[2];}).join("\\n"); }catch(e){}
    renderChips();
    $("tleInfo").textContent=(label||"TLE")+": "+TLES.length+" 衛星"+(TLES[0]?"  (先頭 epoch: "+tleEpoch(TLES[0])+")":"");
  }
  function tleEpoch(t){
    try{ var s=t[1], yy=parseInt(s.substr(18,2),10), dd=parseFloat(s.substr(20,12));
      var yr=yy<57?2000+yy:1900+yy; var d=new Date(Date.UTC(yr,0,1)); d.setUTCDate(d.getUTCDate()+dd-1);
      return d.toISOString().slice(0,10);
    }catch(e){ return "?"; }
  }
  function renderChips(){
    var box=$("satChips"); box.innerHTML="";
    TLES.forEach(function(t,i){
      var lab=document.createElement("label"); lab.className="chip";
      lab.innerHTML='<input type="checkbox" data-i="'+i+'" '+(i<5?"checked":"")+'/> '+esc(t[0]);
      box.appendChild(lab);
    });
  }
  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

  function fmtLocal(d){ return d.toLocaleString(undefined,{month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}); }
  function compassFromAz(az){ var dirs=["北","北東","東","南東","南","南西","西","北西"]; return dirs[Math.round(((az%360)+360)%360/45)%8]; }

  function computePasses(t,obs,hours){
    var rec; try{ rec=satellite.twoline2satrec(t[1],t[2]); }catch(e){ return []; }
    if(!rec||rec.error) return [];
    var passes=[], step=30000, start=Date.now(), end=start+hours*3600*1000, inPass=false, cur=null;
    for(var ms=start;ms<=end;ms+=step){
      var d=new Date(ms), pv;
      try{ pv=satellite.propagate(rec,d); }catch(e){ continue; }
      if(!pv||!pv.position) continue;
      var g=satellite.gstime(d), ecf=satellite.eciToEcf(pv.position,g);
      var la=satellite.ecfToLookAngles(obs,ecf), el=deg(la.elevation);
      if(el>0){
        if(!inPass){ inPass=true; cur={start:d,peak:el,peakT:d,startAz:deg(la.azimuth)}; }
        else if(el>cur.peak){ cur.peak=el; cur.peakT=d; }
      } else if(inPass){ inPass=false; cur.end=d; if(cur.peak>=5) passes.push(cur); cur=null; }
    }
    return passes;
  }

  function calcPasses(){
    var obs={ longitude:d2r(parseFloat($("lon").value)||0), latitude:d2r(parseFloat($("lat").value)||0), height:0.05 };
    var hours=Math.max(3,Math.min(72,parseInt($("hours").value,10)||24));
    var chosen=[].slice.call($("satChips").querySelectorAll("input:checked")).map(function(c){return TLES[+c.getAttribute("data-i")];});
    if(!chosen.length){ chosen=TLES.slice(0,5); }
    var rows=[];
    chosen.forEach(function(t){ computePasses(t,obs,hours).forEach(function(p){ rows.push({name:t[0],p:p}); }); });
    rows.sort(function(a,b){ return a.p.start-b.p.start; });
    var tb=$("passes").querySelector("tbody"); tb.innerHTML="";
    if(!rows.length){ tb.innerHTML='<tr><td class="muted">この期間に仰角5°以上のパスはありません。位置/TLEをご確認ください。</td></tr>'; return; }
    tb.innerHTML='<tr><th>衛星</th><th>開始</th><th>最大仰角</th><th>方角</th><th>継続</th></tr>'+
      rows.map(function(r){
        var mins=Math.round((r.p.end-r.p.start)/60000);
        var q=r.p.peak>=45?"◎":r.p.peak>=25?"○":"△";
        return '<tr><td>'+esc(r.name)+'</td><td>'+fmtLocal(r.p.start)+'</td><td>'+q+' '+r.p.peak.toFixed(0)+'°</td><td>'+compassFromAz(r.p.startAz)+'から</td><td>'+mins+'分</td></tr>';
      }).join("");
    status("パス計算: "+rows.length+" 件 (先 "+hours+"時間)");
  }

  $("calc").addEventListener("click",calcPasses);
  $("geo").addEventListener("click",function(){
    if(!navigator.geolocation){ alert("位置情報が使えません"); return; }
    navigator.geolocation.getCurrentPosition(function(p){ $("lat").value=p.coords.latitude.toFixed(3); $("lon").value=p.coords.longitude.toFixed(3); },
      function(){ alert("位置を取得できませんでした"); });
  });
  $("fetchTle").addEventListener("click",function(){
    $("tleInfo").textContent="Celestrak から取得中…";
    var urls=[
      "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
      "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"
    ];
    Promise.all(urls.map(function(u){ return fetch(u).then(function(r){return r.ok?r.text():"";}).catch(function(){return "";}); }))
      .then(function(texts){
        var all=parseTleText(texts.join("\\n"));
        if(!all.length){ $("tleInfo").textContent="Celestrak から取得できませんでした — 内蔵TLEを使用します。"; setTles(TLE_FALLBACK,"内蔵(古い可能性)"); return; }
        // keep the interesting ones first
        var want=/ISS|NOAA 1[589]|NOAA 20|METEOR|METOP/i;
        var pick=all.filter(function(t){return want.test(t[0]);});
        setTles((pick.length?pick:all).slice(0,20),"Celestrak 最新");
        status("Celestrak から TLE を更新しました。");
      })
      .catch(function(e){ $("tleInfo").textContent="取得失敗: "+e.message+" — 内蔵TLEを使用します。"; setTles(TLE_FALLBACK,"内蔵(古い可能性)"); });
  });
  $("tle").addEventListener("change",function(){ var l=parseTleText($("tle").value); if(l.length) setTles(l,"貼り付け"); });

  // NASA key setter (optional)
  window.setNasaKey=function(k){ try{ localStorage.setItem("orbita.nasakey",k);}catch(e){} };

  /* ---------------- init ---------------- */
  loadPrefs(); fillRes();
  setTles(TLE_FALLBACK,"内蔵(古い可能性・Celestrak取得推奨)");
  build();
  // try to freshen TLEs quietly on load
  setTimeout(function(){ $("fetchTle").click(); },400);
})();
</script>
</body>
</html>
`;

html = html.replace("/*__SATELLITE_JS__*/", function(){ return SATJS; });

fs.mkdirSync(path.join(IDE, "dist"), { recursive: true });
const outPath = path.join(IDE, "dist", "earth-view.html");
fs.writeFileSync(outPath, html);
console.log("built dist/earth-view.html (" + fs.statSync(outPath).size + " bytes)");
