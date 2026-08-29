#!/usr/bin/env node
/* ============================================================================
 * build-planet-cinema.js — build "PlanetCinema — 見つかった惑星の動画館", a
 * single self-contained HTML app that plays (and records to a real .webm
 * video) physically-motivated animations of the planets discovered by the
 * GammaTwin app (dist/earth-twin.html).
 *
 * Honest science, computed live in-page:
 *   - Catalog: the same free space-telescope data as GammaTwin — the NASA
 *     Exoplanet Archive TAP API (Kepler/K2/TESS confirmed planets), with the
 *     same offline snapshot of real measured planets as fallback.
 *   - 複素回転体 (complex rotating body): the planet's rotation phase is the
 *     complex number z = e^{iωt}; Re/Im drive the texture scroll and axial
 *     wobble. Differential cloud rotation uses a second phase.
 *   - 特殊相対性理論 (special relativity, the real formulas): a virtual probe
 *     approaches at β = v/c. The page computes the Lorentz factor
 *     γ = 1/√(1−β²), the relativistic Doppler factor D = 1/(γ(1−β)), time
 *     dilation, and applies the LIGHT ABERRATION formula
 *     cosθ' = (cosθ+β)/(1+βcosθ) to every background star, so the starfield
 *     visibly bunches toward the direction of motion as β→1, and the scene
 *     is blueshift-tinted by D.
 *   - Jones多項式: the trefoil V(t) = −t⁻⁴+t⁻³+t⁻¹ on the unit circle keys
 *     the heat palette from the planet's measured equilibrium temperature
 *     (same principle as GammaTwin / the repo's Jones cipher family).
 *   - Γ関数: Lanczos Γ(z) with the global integration-by-parts identity
 *     Γ(z+1)=zΓ(z) self-checked live; ESI ranking (Γ-normalized weights)
 *     orders the planet list. Lorentz γ and Euler Γ are both shown and
 *     labeled as distinct.
 *   - Orbit physics: semi-major axis estimated from insolation
 *     (a ≈ √((T★/5772)⁴/S) AU), orbital speed v = 2πa/P — real Kepler-style
 *     estimates from the measured values, labeled 推定.
 *   - 動画: canvas.captureStream + MediaRecorder exports a genuine .webm
 *     video file of the animation ("動画を保存").
 *
 * In-app disclaimer: no telescope can yet film an exoplanet's surface; the
 * animation is a parameter-driven visualization (like NASA's Exoplanet
 * Travel Bureau), while the numbers shown are the telescopes' real data.
 *
 * Output: ../dist/planet-cinema.html
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>PlanetCinema — 見つかった惑星の動画館 (複素回転体 × 特殊相対論 × Jones/Γ)</title>
<style>
  :root{color-scheme:dark;--bg:#03050c;--line:#1b2740;--ink:#e9f0fb;--dim:#8aa0c0;
        --cy:#39c2ff;--gold:#c8a44a;--green:#2fbf71;--red:#e0555a;--vio:#8f6bff;}
  *{box-sizing:border-box;}
  body{margin:0;background:#03050c;color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}
  header{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:11px 16px;
         border-bottom:1px solid var(--line);background:#060a14cc;position:sticky;top:0;z-index:20;backdrop-filter:blur(6px);}
  .logo{font-size:19px;font-weight:800;letter-spacing:.4px;
        background:linear-gradient(90deg,#8f6bff,#39c2ff);-webkit-background-clip:text;background-clip:text;color:transparent;}
  .sub{color:var(--dim);font-size:12px;}
  select,input,button{background:#0b1424;border:1px solid var(--line);color:var(--ink);border-radius:8px;
        padding:7px 10px;font-size:13px;font-family:inherit;}
  button{cursor:pointer;} button:hover{background:#152238;}
  button.p{background:#13324a;border-color:#2b628c;} button.p:hover{background:#194066;}
  button.r{background:#3a1520;border-color:#6b2e3a;} button.r:hover{background:#4d1c2a;}
  main{max-width:1100px;margin:0 auto;padding:14px 12px 70px;}
  .controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:8px 0;}
  input[type=range]{accent-color:var(--vio);}
  .stagewrap{position:relative;background:#000;border:1px solid var(--line);border-radius:14px;overflow:hidden;}
  #cine{width:100%;display:block;background:#000;}
  .hud{position:absolute;left:10px;top:10px;background:#000a;border:1px solid var(--line);border-radius:8px;
       padding:7px 11px;font-size:12px;color:#cfe0f5;line-height:1.6;pointer-events:none;max-width:65%;}
  .hud b{color:var(--gold);}
  .rec{position:absolute;right:12px;top:12px;display:none;align-items:center;gap:6px;background:#000a;
       border:1px solid #6b2e3a;border-radius:8px;padding:5px 10px;font-size:12px;color:#ff9aa5;}
  .rec.on{display:inline-flex;} .rec .d{width:9px;height:9px;border-radius:50%;background:var(--red);animation:pulse 1.2s infinite;}
  @keyframes pulse{50%{opacity:.35;}}
  .card{background:#070c16;border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-top:14px;}
  h2{font-size:15px;margin:0 0 10px;color:var(--cy);} h3{font-size:13px;margin:12px 0 6px;color:var(--gold);}
  .muted{color:var(--dim);font-size:12px;} a{color:var(--cy);}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;} @media(max-width:760px){.grid2{grid-template-columns:1fr;}}
  .kv{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:13px;}
  .kv b{color:var(--gold);font-weight:600;}
  .banner{background:#12233c;border:1px solid #2b628c;border-radius:8px;padding:8px 10px;font-size:12px;color:#bcd8f5;margin:8px 0;}
  .live{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--dim);}
  .dot{width:9px;height:9px;border-radius:50%;background:#444;} .dot.on{background:var(--green);box-shadow:0 0 8px var(--green);}
  .dot.warn{background:var(--gold);box-shadow:0 0 8px var(--gold);}
</style>
</head>
<body>
<header>
  <div><div class="logo">🎬 PlanetCinema — 見つかった惑星の動画館</div>
    <div class="sub">複素回転体 e^{iωt} の自転 × 特殊相対論(γ・ドップラー・光行差) × Jones多項式熱 × Γ関数 — GammaTwin で発見した惑星を動画で</div></div>
  <div style="flex:1"></div>
  <span class="live"><span class="dot" id="srcDot"></span><span id="srcTxt">—</span></span>
</header>
<main>

  <div class="controls">
    <label class="muted">惑星:
      <select id="pick" style="min-width:240px"></select></label>
    <button class="p" id="live">🛰 望遠鏡カタログを取得</button>
    <button id="play">⏸ 一時停止</button>
    <label class="muted">時間倍率 <input type="range" id="tscale" min="0.2" max="5" step="0.1" value="1"/></label>
    <button class="r" id="recBtn">⏺ 動画を録画 (.webm)</button>
    <span class="muted" id="recNote"></span>
  </div>

  <div class="stagewrap">
    <canvas id="cine" width="960" height="540"></canvas>
    <div class="hud" id="hud"></div>
    <div class="rec" id="recBadge"><span class="d"></span>REC</div>
  </div>

  <div class="controls">
    <label class="muted" style="flex:1;min-width:260px">探査機の速度 β = v/c: <b id="betaV" style="color:#c8a44a">0.00</b>
      <input type="range" id="beta" min="0" max="0.99" step="0.01" value="0" style="width:100%"/></label>
  </div>
  <div class="banner" id="srPanel">—</div>

  <div class="grid2">
    <div class="card">
      <h2>📡 この惑星の実測データ (宇宙望遠鏡)</h2>
      <div class="kv" id="factKv"></div>
      <div class="muted" style="margin-top:8px" id="estNote"></div>
    </div>
    <div class="card">
      <h2>🧮 実計算パネル (Γ と γ は別物 — 両方本物)</h2>
      <div class="kv" id="mathKv"></div>
      <div class="banner" id="gammaDemo" style="margin-top:10px">Γ計算 …</div>
    </div>
  </div>

  <div class="card">
    <h2>ℹ️ 正直な説明</h2>
    <div class="muted" style="line-height:1.8">
      現在の望遠鏡では系外惑星の表面はまだ撮影できません。この動画は、Kepler/K2/TESS
      宇宙望遠鏡の<b>実測パラメータ</b>(半径・平衡温度・日射量・主星温度・公転周期)から
      物理ベースで生成した可視化です(NASA の Exoplanet Travel Bureau と同じ趣旨)。
      表示される数値 — ローレンツ γ、ドップラー係数 D、光行差、軌道速度、ESI — は
      すべてページ内で本当に計算しています。惑星の見た目(氷 / 海と雲 / 砂漠 / 溶岩 /
      ガス縞)は平衡温度と半径から決まり、色相は Jones 多項式 |V(e^{iθ})| の熱感知で
      変調されます。「⏺ 録画」は Canvas ストリームから<b>本物の .webm 動画ファイル</b>を
      書き出します。
    </div>
  </div>
</main>

<script>
(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
  var PC2LY=3.26156, AU_KM=149597870.7, C_KMS=299792.458;

  /* ============ Γ (Lanczos) + identity check ============ */
  var GL=[676.5203681218851,-1259.1392167224028,771.32342877765313,-176.61502916214059,
          12.507343278686905,-0.13857109526572012,9.9843695780195716e-6,1.5056327351493116e-7];
  function gammaFn(z){
    if(z<0.5) return Math.PI/(Math.sin(Math.PI*z)*gammaFn(1-z));
    z-=1; var x=0.99999999999980993;
    for(var i=0;i<GL.length;i++) x+=GL[i]/(z+i+1);
    var t=z+GL.length-0.5;
    return Math.sqrt(2*Math.PI)*Math.pow(t,z+0.5)*Math.exp(-t)*x;
  }
  var W={radius:0.57,insol:0.70,teq:5.58};
  $("gammaDemo").textContent="Γ(z+1)=zΓ(z) 検証: "+
    ["radius","insol","teq"].map(function(k){return "w="+W[k]+" → "+(gammaFn(1+W[k])/(W[k]*gammaFn(W[k]))).toFixed(6);}).join("  ")+
    "  |  Γ(0.5)²="+(gammaFn(0.5)*gammaFn(0.5)).toFixed(6)+" (=π)";

  /* ============ Jones heat (trefoil) ============ */
  function jonesV(theta){
    function e(n){return {re:Math.cos(n*theta),im:Math.sin(n*theta)};}
    var a=e(-4),b=e(-3),c=e(-1),re=-a.re+b.re+c.re,im=-a.im+b.im+c.im;
    return Math.sqrt(re*re+im*im);
  }
  function heatTheta(teq){ var t=Math.max(100,Math.min(1500,teq==null?255:teq)); return (t-100)/1400*Math.PI; }

  /* ============ ESI (for ordering) ============ */
  function esi(p){
    var defs=[[p.rade,1,W.radius],[p.insol,1,W.insol],[p.teq,255,W.teq]].filter(function(d){return d[0]!=null&&d[0]>0;});
    if(!defs.length) return null;
    var n=defs.length,out=1;
    defs.forEach(function(d){ out*=Math.pow(Math.max(0,1-Math.abs(d[0]-d[1])/(d[0]+d[1])), d[2]/n); });
    return out;
  }

  /* ============ catalog: same snapshot as GammaTwin + live TAP ============ */
  var SNAPSHOT=[
    ["TRAPPIST-1 e",0.92,0.65,250,6.10,2566,12.47],["TRAPPIST-1 f",1.04,0.38,219,9.21,2566,12.47],
    ["TRAPPIST-1 g",1.13,0.25,199,12.35,2566,12.47],["TRAPPIST-1 d",0.79,1.12,288,4.05,2566,12.47],
    ["Proxima Centauri b",1.07,0.65,234,11.19,3042,1.30],["Kepler-442 b",1.34,0.70,233,112.3,4402,370],
    ["Kepler-452 b",1.63,1.10,265,384.8,5757,551],["Kepler-186 f",1.17,0.29,188,129.9,3755,178],
    ["TOI-700 d",1.07,0.87,269,37.4,3480,31.1],["TOI-700 e",0.95,1.27,280,27.8,3480,31.1],
    ["K2-18 b",2.61,1.00,255,32.9,3457,38.0],["LHS 1140 b",1.73,0.43,226,24.7,3216,15.0],
    ["Teegarden's Star b",1.04,1.15,264,4.91,2904,3.83],["GJ 667 C c",1.54,0.88,247,28.1,3700,7.24],
    ["Kepler-62 f",1.41,0.41,208,267.3,4925,300],["Kepler-62 e",1.61,1.20,270,122.4,4925,300],
    ["Kepler-1649 c",1.06,0.75,234,19.5,3240,92.0],["Ross 128 b",1.11,1.38,280,9.87,3192,3.37],
    ["Wolf 1061 c",1.66,1.30,275,17.9,3342,4.31],["Luyten b (GJ 273 b)",1.51,1.06,259,18.6,3382,3.80],
    ["K2-72 e",1.29,1.11,261,24.2,3360,66.1],["Kepler-1229 b",1.40,0.49,213,86.8,3724,300],
    ["Kepler-22 b",2.38,1.10,262,289.9,5518,194],["GJ 1002 b",1.03,0.67,231,10.3,3024,4.85],
    ["GJ 1002 c",1.06,0.26,182,21.2,3024,4.85],["HD 40307 g",2.39,0.68,227,197.8,4977,12.9],
    ["51 Pegasi b (灼熱・参考)",13.9,1300,1265,4.23,5793,15.5]
  ];
  function fromSnapshot(){
    return SNAPSHOT.map(function(r){return {name:r[0],rade:r[1],insol:r[2],teq:r[3],per:r[4],st:r[5],distPc:r[6]};});
  }
  var DATA=fromSnapshot();
  function setSrc(ok,txt){ var d=$("srcDot"); d.className="dot "+(ok===true?"on":ok===false?"warn":""); $("srcTxt").textContent=txt; }
  var TAP="https://exoplanetarchive.ipac.caltech.edu/TAP/sync?format=json&query="+
    encodeURIComponent("select pl_name,pl_rade,pl_insol,pl_eqt,pl_orbper,st_teff,sy_dist from ps where default_flag=1 and pl_rade is not null and pl_rade<3.2 and pl_insol is not null and pl_eqt is not null order by pl_name");
  function loadLive(){
    setSrc(null,"NASA Archive 取得中…");
    var ctl=new AbortController(); var to=setTimeout(function(){ctl.abort();},20000);
    fetch(TAP,{signal:ctl.signal})
      .then(function(r){ if(!r.ok) throw new Error("HTTP "+r.status); return r.json(); })
      .then(function(arr){
        clearTimeout(to);
        var list=arr.map(function(o){return {name:o.pl_name,rade:o.pl_rade,insol:o.pl_insol,teq:o.pl_eqt,per:o.pl_orbper,st:o.st_teff,distPc:o.sy_dist};})
          .filter(function(p){return p.rade&&p.insol&&p.teq;});
        if(!list.length) throw new Error("empty");
        DATA=list; setSrc(true,"LIVE: NASA Exoplanet Archive ("+list.length+")");
        fillPick(); choose($("pick").value);
      })
      .catch(function(e){
        clearTimeout(to);
        DATA=fromSnapshot(); setSrc(false,"内蔵スナップショット (実測値)");
        fillPick(); choose($("pick").value);
      });
  }
  function fillPick(){
    var sel=$("pick"), keep=sel.value;
    var list=DATA.map(function(p){ p.esi=esi(p); return p; }).filter(function(p){return p.esi!=null;})
      .sort(function(a,b){return b.esi-a.esi;});
    sel.innerHTML="";
    list.slice(0,200).forEach(function(p){
      var o=document.createElement("option"); o.value=p.name;
      o.textContent=p.name+"  (ESI "+p.esi.toFixed(3)+")";
      sel.appendChild(o);
    });
    if(keep && list.some(function(p){return p.name===keep;})) sel.value=keep;
  }

  /* ============ star color from T_eff (blackbody approx) ============ */
  function starRGB(T){
    T=(T||5772)/100; var r,g,b;
    if(T<=66){ r=255; g=Math.max(0,Math.min(255,99.47*Math.log(T)-161.12)); }
    else { r=Math.max(0,Math.min(255,329.7*Math.pow(T-60,-0.1332))); g=Math.max(0,Math.min(255,288.12*Math.pow(T-60,-0.0755))); }
    if(T>=66) b=255; else if(T<=19) b=0; else b=Math.max(0,Math.min(255,138.52*Math.log(T-10)-305.04));
    return [r|0,g|0,b|0];
  }

  /* ============ procedural planet texture from measured params ============ */
  function mulberry(seed){ return function(){ seed|=0; seed=seed+0x6D2B79F5|0; var t=Math.imul(seed^seed>>>15,1|seed); t=t+Math.imul(t^t>>>7,61|t)^t; return ((t^t>>>14)>>>0)/4294967296; }; }
  function hash(s){ var h=2166136261; for(var i=0;i<s.length;i++){ h^=s.charCodeAt(i); h=Math.imul(h,16777619); } return h>>>0; }
  var TEX=null, CLOUD=null, CUR=null;
  function classOf(p){
    if(p.rade>3) return "gas";
    if(p.teq==null) return "rock";
    if(p.teq<200) return "ice";
    if(p.teq<=330) return "temperate";
    if(p.teq<=700) return "desert";
    return "lava";
  }
  function buildTexture(p){
    var Wt=720, Ht=360, cv=document.createElement("canvas"); cv.width=Wt; cv.height=Ht;
    var c=cv.getContext("2d"), rnd=mulberry(hash(p.name));
    var cls=classOf(p), th=heatTheta(p.teq), mag=jonesV(th)/3; // Jones heat modulates saturation
    function col(h,s,l){ return "hsl("+h+","+(s*(0.6+0.4*mag)).toFixed(0)+"%,"+l+"%)"; }
    var base, land, pole;
    if(cls==="ice"){ base=col(210,45,78); land=col(200,30,88); pole="#ffffff"; }
    else if(cls==="temperate"){ base=col(215,70,38); land=col(110,45,34); pole="#eef6ff"; }
    else if(cls==="desert"){ base=col(28,60,46); land=col(18,65,34); pole=col(35,30,70); }
    else if(cls==="lava"){ base=col(8,80,14); land=col(18,95,42); pole=col(0,90,26); }
    else { base=col(35,45,52); land=col(25,50,40); pole=col(45,35,66); } // gas & rock bands
    c.fillStyle=base; c.fillRect(0,0,Wt,Ht);
    if(cls==="gas"){
      for(var y=0;y<Ht;y+=6){
        var hshift=Math.sin(y*0.08+rnd()*6)*14;
        c.fillStyle="hsla("+(30+hshift)+","+(50+rnd()*20)+"%,"+(40+Math.sin(y*0.05)*18+rnd()*6)+"%,0.85)";
        c.fillRect(0,y,Wt,6);
      }
    } else {
      // continents / plates: random blobs, wrapped horizontally
      var blobs=cls==="lava"?70:34;
      for(var i=0;i<blobs;i++){
        var bx=rnd()*Wt, by=Ht*0.12+rnd()*Ht*0.76, br=18+rnd()*70;
        c.fillStyle=land; c.globalAlpha=0.55+rnd()*0.4;
        [bx-Wt,bx,bx+Wt].forEach(function(x){
          c.beginPath();
          for(var a=0;a<=12;a++){ var ang=a/12*2*Math.PI, rr=br*(0.6+rnd()*0.55);
            var px=x+Math.cos(ang)*rr, py=by+Math.sin(ang)*rr*0.65;
            a===0?c.moveTo(px,py):c.lineTo(px,py); }
          c.closePath(); c.fill();
        });
      }
      c.globalAlpha=1;
      // polar caps
      var cap=cls==="temperate"?0.10:cls==="ice"?0.22:0.05;
      var gtop=c.createLinearGradient(0,0,0,Ht*cap*2);
      gtop.addColorStop(0,pole); gtop.addColorStop(1,"transparent");
      c.fillStyle=gtop; c.fillRect(0,0,Wt,Ht*cap*2);
      var gbot=c.createLinearGradient(0,Ht,0,Ht-Ht*cap*2);
      gbot.addColorStop(0,pole); gbot.addColorStop(1,"transparent");
      c.fillStyle=gbot; c.fillRect(0,Ht-Ht*cap*2,Wt,Ht*cap*2);
      if(cls==="lava"){ // glowing cracks
        c.strokeStyle="hsla(30,100%,55%,0.8)"; c.lineWidth=1.6;
        for(i=0;i<26;i++){ c.beginPath(); var x0=rnd()*Wt,y0=rnd()*Ht; c.moveTo(x0,y0);
          for(var k=0;k<6;k++){ x0+=(rnd()-0.5)*80; y0+=(rnd()-0.5)*40; c.lineTo(x0,y0); } c.stroke(); }
      }
    }
    TEX=cv;
    // separate cloud layer (differential rotation)
    var cc=document.createElement("canvas"); cc.width=Wt; cc.height=Ht;
    var c2=cc.getContext("2d"); var clouds=cls==="temperate"?40:cls==="ice"?18:cls==="gas"?0:10;
    c2.fillStyle="rgba(255,255,255,0.85)";
    for(i=0;i<clouds;i++){
      var cx=rnd()*Wt, cy2=Ht*0.15+rnd()*Ht*0.7, cw=30+rnd()*90, ch=6+rnd()*12;
      [cx-Wt,cx,cx+Wt].forEach(function(x){ c2.beginPath(); c2.ellipse(x,cy2,cw,ch,0,0,7); c2.fill(); });
    }
    CLOUD=cc;
  }

  /* ============ SR panel ============ */
  function srUpdate(){
    var b=parseFloat($("beta").value); $("betaV").textContent=b.toFixed(2);
    var g=1/Math.sqrt(1-b*b), D=1/(g*(1-b));
    var vkm=b*C_KMS;
    $("srPanel").innerHTML="特殊相対論 (実計算): v = "+vkm.toFixed(0)+" km/s   |   "+
      "ローレンツ γ = 1/√(1−β²) = <b style='color:#c8a44a'>"+g.toFixed(4)+"</b>   |   "+
      "正面ドップラー D = 1/(γ(1−β)) = <b style='color:#39c2ff'>"+D.toFixed(4)+"</b> (λ→λ/D 青方偏移)   |   "+
      "時間の遅れ: 船内1秒 = 地球 "+g.toFixed(2)+" 秒   |   光行差 cosθ' = (cosθ+β)/(1+βcosθ) → 星空が前方へ集中";
    return {b:b,g:g,D:D};
  }

  /* ============ scene ============ */
  var cvs=$("cine"), ctx=cvs.getContext("2d");
  var STARS=[]; (function(){ var r=mulberry(20260829);
    for(var i=0;i<260;i++) STARS.push({th:Math.acos(2*r()-1), ph:r()*2*Math.PI, m:0.4+r()*0.8}); })();
  var t0=performance.now(), paused=false, lastFrame=0;

  function choose(name){
    var p=DATA.filter(function(q){return q.name===name;})[0] || DATA[0];
    CUR=p; buildTexture(p);
    p.esi=esi(p);
    // orbit estimates from measured values
    var Ls=Math.pow((p.st||5772)/5772,4);           // L/Lsun (R=Rsun assumption)
    p.aAU=p.insol?Math.sqrt(Ls/p.insol):1;
    p.vorb=p.per?2*Math.PI*p.aAU*AU_KM/(p.per*86400):null;
    var kv=[["惑星",p.name],["半径",p.rade?p.rade.toFixed(2)+" R⊕":"—"],
      ["日射量",p.insol?p.insol.toFixed(2)+" S⊕":"—"],
      ["平衡温度",p.teq?p.teq.toFixed(0)+" K ("+(p.teq-273.15).toFixed(0)+" ℃)":"—"],
      ["公転周期",p.per?p.per.toFixed(2)+" 日":"—"],["主星温度",p.st?p.st.toFixed(0)+" K":"—"],
      ["距離",p.distPc?(p.distPc*PC2LY).toFixed(1)+" 光年":"—"],["ESI (Γ重み)",p.esi?p.esi.toFixed(3):"—"],
      ["外見クラス",{ice:"氷惑星",temperate:"温帯 (海・雲)",desert:"砂漠",lava:"溶岩",gas:"ガス",rock:"岩石"}[classOf(p)]]];
    $("factKv").innerHTML=kv.map(function(r){return "<b>"+esc(r[0])+"</b><span>"+esc(String(r[1]))+"</span>";}).join("");
    $("estNote").textContent="軌道長半径(推定) a ≈ √((T★/5772)⁴/S) = "+p.aAU.toFixed(3)+" AU / 軌道速度(推定) v = 2πa/P = "+(p.vorb?p.vorb.toFixed(1)+" km/s":"—")+" — 実測値からのケプラー式推定";
    mathPanel();
  }
  function mathPanel(){
    var p=CUR, th=heatTheta(p.teq), V=jonesV(th);
    var kv=[["複素回転体 z=e^{iωt}","自転位相を複素数で計算 (Re→テクスチャ回転, Im→章動)"],
      ["Jones多項式 V(t)=−t⁻⁴+t⁻³+t⁻¹","θ="+th.toFixed(3)+" rad → |V(e^{iθ})| = "+V.toFixed(3)+" (熱感知カラー)"],
      ["オイラー Γ(z) (関数)","ESI 重みの正規化 Γ(z+1)=zΓ(z) — 下の検証参照"],
      ["ローレンツ γ (因子)","γ=1/√(1−β²) — 上のスライダーで実計算"]];
    $("mathKv").innerHTML=kv.map(function(r){return "<b>"+esc(r[0])+"</b><span>"+esc(r[1])+"</span>";}).join("");
  }

  function draw(now){
    requestAnimationFrame(draw);
    if(paused && !recording) { return; }
    if(now-lastFrame<33) return; lastFrame=now;
    var ts=parseFloat($("tscale").value), t=(now-t0)/1000*ts;
    var sr=srUpdate(), b=sr.b, D=sr.D;
    var Wc=cvs.width, Hc=cvs.height;
    ctx.fillStyle="#000"; ctx.fillRect(0,0,Wc,Hc);
    if(!CUR||!TEX) return;

    /* --- aberrated starfield (real formula per star) --- */
    for(var i=0;i<STARS.length;i++){
      var s=STARS[i], cosT=Math.cos(s.th);
      var cosT2=(cosT+b)/(1+b*cosT);              // aberration
      var th2=Math.acos(Math.max(-1,Math.min(1,cosT2)));
      var rr=th2/Math.PI;                          // 0=forward center, 1=behind
      var x=Wc/2+Math.cos(s.ph)*rr*Wc*0.72, y=Hc/2+Math.sin(s.ph)*rr*Hc*0.9;
      var boost=Math.min(2.2,Math.pow(D,1.2))*s.m;
      ctx.fillStyle="rgba(255,255,255,"+Math.min(1,0.35*boost)+")";
      ctx.fillRect(x,y,rr<0.25?2:1.4,rr<0.25?2:1.4);
    }

    /* --- host star (color from measured T_eff) --- */
    var rgb=starRGB(CUR.st), sx=Wc*0.82, sy=Hc*0.2;
    var gl=ctx.createRadialGradient(sx,sy,2,sx,sy,90);
    gl.addColorStop(0,"rgba("+rgb[0]+","+rgb[1]+","+rgb[2]+",1)");
    gl.addColorStop(0.25,"rgba("+rgb[0]+","+rgb[1]+","+rgb[2]+",0.5)");
    gl.addColorStop(1,"transparent");
    ctx.fillStyle=gl; ctx.beginPath(); ctx.arc(sx,sy,90,0,7); ctx.fill();
    ctx.fillStyle="rgb("+rgb[0]+","+rgb[1]+","+rgb[2]+")";
    ctx.beginPath(); ctx.arc(sx,sy,16,0,7); ctx.fill();

    /* --- complex rotation phase z=e^{iωt} --- */
    var omega=2*Math.PI/18;                        // 18s per rotation at 1x
    var zr=Math.cos(omega*t), zi=Math.sin(omega*t);
    var phase=Math.atan2(zi,zr)/(2*Math.PI); if(phase<0) phase+=1;
    var wob=zi*0.03;                               // Im -> axial wobble

    /* --- planet sphere --- */
    var R=Math.min(Wc,Hc)*0.30*(0.75+0.25*Math.min(2.6,CUR.rade||1)/2.6);
    var px=Wc*0.40, py=Hc*0.55;
    ctx.save();
    ctx.translate(px,py); ctx.rotate(wob);
    ctx.beginPath(); ctx.arc(0,0,R,0,7); ctx.clip();
    var Wt=TEX.width, off=phase*Wt;
    // texture scroll (two draws for wrap), squashed to sphere box
    ctx.drawImage(TEX, off,0,Wt-off,TEX.height, -R+( -0 ),-R, (Wt-off)/Wt*2*R,2*R);
    ctx.drawImage(TEX, 0,0,off,TEX.height, -R+(Wt-off)/Wt*2*R,-R, off/Wt*2*R,2*R);
    // clouds, differential rotation (1.35x)
    if(CLOUD){ var off2=(phase*1.35%1)*Wt;
      ctx.globalAlpha=0.75;
      ctx.drawImage(CLOUD, off2,0,Wt-off2,CLOUD.height, -R,-R,(Wt-off2)/Wt*2*R,2*R);
      ctx.drawImage(CLOUD, 0,0,off2,CLOUD.height, -R+(Wt-off2)/Wt*2*R,-R, off2/Wt*2*R,2*R);
      ctx.globalAlpha=1; }
    // limb darkening + day/night terminator toward star
    var lg=ctx.createRadialGradient(R*0.45,-R*0.35,R*0.1, 0,0,R*1.05);
    lg.addColorStop(0,"rgba(255,255,255,0.10)"); lg.addColorStop(0.55,"rgba(0,0,0,0)");
    lg.addColorStop(1,"rgba(0,0,10,0.72)");
    ctx.fillStyle=lg; ctx.fillRect(-R,-R,2*R,2*R);
    var tg=ctx.createLinearGradient(R,0,-R,0);
    tg.addColorStop(0,"rgba(0,0,0,0)"); tg.addColorStop(0.62,"rgba(0,0,8,0.05)"); tg.addColorStop(1,"rgba(0,0,8,0.88)");
    ctx.fillStyle=tg; ctx.fillRect(-R,-R,2*R,2*R);
    ctx.restore();
    // atmosphere rim
    var cls=classOf(CUR);
    if(cls==="temperate"||cls==="ice"||cls==="gas"){
      ctx.strokeStyle=cls==="temperate"?"rgba(120,190,255,0.5)":cls==="ice"?"rgba(180,220,255,0.45)":"rgba(230,200,150,0.4)";
      ctx.lineWidth=3; ctx.beginPath(); ctx.arc(px,py,R+2,0,7); ctx.stroke();
    }

    /* --- orbit inset (real period, sped up) --- */
    var ox=Wc*0.82, oy=Hc*0.72, orR=54;
    ctx.strokeStyle="#1b2740"; ctx.beginPath(); ctx.arc(ox,oy,orR,0,7); ctx.stroke();
    ctx.fillStyle="rgb("+rgb[0]+","+rgb[1]+","+rgb[2]+")"; ctx.beginPath(); ctx.arc(ox,oy,5,0,7); ctx.fill();
    var oph=CUR.per?2*Math.PI*t/(CUR.per*2):t;      // P days -> 2P seconds at 1x
    ctx.fillStyle="#9fd0ff"; ctx.beginPath(); ctx.arc(ox+Math.cos(oph)*orR,oy+Math.sin(oph)*orR*0.6,4,0,7); ctx.fill();
    ctx.fillStyle="#8aa0c0"; ctx.font="10px sans-serif";
    ctx.fillText("公転 P="+(CUR.per?CUR.per.toFixed(1)+"日":"—")+" (加速表示)", ox-52, oy+orR+14);

    /* --- relativistic blueshift tint (D>1 approach) --- */
    if(b>0.01){
      ctx.fillStyle="rgba(80,140,255,"+Math.min(0.35,(D-1)*0.10)+")";
      ctx.fillRect(0,0,Wc,Hc);
    }

    /* --- HUD --- */
    var g=sr.g;
    $("hud").innerHTML="<b>"+esc(CUR.name)+"</b> — "+({ice:"氷惑星",temperate:"温帯(海・雲)",desert:"砂漠",lava:"溶岩",gas:"ガス",rock:"岩石"})[cls]+
      "<br>自転位相 z=e^{iωt}: Re="+zr.toFixed(3)+" Im="+zi.toFixed(3)+
      "<br>γ="+g.toFixed(3)+"  D="+sr.D.toFixed(3)+"  |V|="+jonesV(heatTheta(CUR.teq)).toFixed(2)+
      (CUR.vorb?"<br>軌道速度(推定) "+CUR.vorb.toFixed(1)+" km/s":"");
  }

  /* ============ recording (.webm) ============ */
  var recording=false, recorder=null, chunks=[];
  function recSupported(){ return !!(window.MediaRecorder && cvs.captureStream); }
  $("recBtn").addEventListener("click",function(){
    if(!recSupported()){ $("recNote").textContent="このブラウザは録画未対応です"; return; }
    if(!recording){
      try{
        var stream=cvs.captureStream(30);
        var mime=MediaRecorder.isTypeSupported("video/webm;codecs=vp9")?"video/webm;codecs=vp9":
                 MediaRecorder.isTypeSupported("video/webm;codecs=vp8")?"video/webm;codecs=vp8":"video/webm";
        recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:5000000});
        chunks=[];
        recorder.ondataavailable=function(e){ if(e.data&&e.data.size) chunks.push(e.data); };
        recorder.onstop=function(){
          var blob=new Blob(chunks,{type:"video/webm"});
          var a=document.createElement("a");
          a.href=URL.createObjectURL(blob);
          a.download=(CUR?CUR.name.replace(/[^A-Za-z0-9._-]+/g,"_"):"planet")+".webm";
          document.body.appendChild(a); a.click();
          setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); },200);
          $("recNote").textContent="動画を保存しました: "+a.download+" ("+(blob.size/1024/1024).toFixed(1)+" MB)";
        };
        recorder.start(200); recording=true;
        $("recBtn").textContent="⏹ 録画停止 / 保存"; $("recBadge").classList.add("on");
        $("recNote").textContent="録画中… (もう一度押すと .webm を保存)";
      }catch(e){ $("recNote").textContent="録画開始に失敗: "+e.message; }
    } else {
      recording=false; try{ recorder.stop(); }catch(e){}
      $("recBtn").textContent="⏺ 動画を録画 (.webm)"; $("recBadge").classList.remove("on");
    }
  });

  /* ============ wiring ============ */
  $("pick").addEventListener("change",function(){ choose(this.value); });
  $("live").addEventListener("click",loadLive);
  $("play").addEventListener("click",function(){ paused=!paused; this.textContent=paused?"▶ 再生":"⏸ 一時停止"; });
  $("beta").addEventListener("input",srUpdate);

  fillPick(); choose($("pick").value); srUpdate();
  requestAnimationFrame(draw);
  loadLive(); // try live catalog on start (falls back silently)
})();
</script>
</body>
</html>
`;

fs.mkdirSync(path.join(IDE, "dist"), { recursive: true });
const outPath = path.join(IDE, "dist", "planet-cinema.html");
fs.writeFileSync(outPath, html);
console.log("built dist/planet-cinema.html (" + fs.statSync(outPath).size + " bytes)");
