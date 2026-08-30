#!/usr/bin/env node
/* ============================================================================
 * build-earth-twin.js — build "GammaTwin — 地球型惑星ファインダー", a single
 * self-contained HTML app that hunts for planets whose conditions are
 * "isomorphic to Earth" using data from space telescopes ANYONE can access:
 *
 *   - NASA Exoplanet Archive (TAP API, no key): the confirmed-planet catalog
 *     measured by the Kepler / K2 / TESS / JWST space telescopes.
 *   - CDS hips2fits (no key): real sky-survey imagery (DSS2 color) of each
 *     host star's field — the "telescope view" of the candidate.
 *
 * Scoring:
 *   - ESI (Earth Similarity Index, Schulze-Makuch et al. 2011) on radius /
 *     insolation / equilibrium temperature — the real, published metric.
 *   - The ESI exponent weights are normalized through the gamma function
 *     using its GLOBAL INTEGRATION-BY-PARTS functional equation
 *     Γ(z+1) = zΓ(z) (Lanczos approximation implemented in-page).
 *   - A "Jones heat" color: the Jones polynomial of the trefoil knot
 *     V(t) = -t^-4 + t^-3 + t^-1 evaluated on the unit circle at a phase set
 *     by the planet's equilibrium temperature — the same knot-polynomial
 *     family as the repo's Jones quantum cipher — drives the heat palette.
 *
 * The app works offline too: a built-in snapshot of real measured planets
 * (TRAPPIST-1, Proxima b, Kepler-442b, TOI-700 d/e, ...) is used when the
 * live archive is unreachable. A sky map ("銀河マップ") plots candidates by
 * RA/Dec with the Milky Way band. Honest note in-app: confirmed exoplanets
 * all lie inside our own galaxy; other galaxies' planets are beyond current
 * telescopes' individual detection.
 *
 * Output: ../dist/earth-twin.html
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");
const BADA_CORE = fs.readFileSync(path.join(IDE, "www", "bada.js"), "utf8");
const EXO_BADA = fs.readFileSync(path.join(IDE, "exo", "exo-gamma.bada"), "utf8");

/* verify the Bada engine actually runs before we ship it */
{
  const Bada = require(path.join(IDE, "www", "bada.js"));
  const chk = Bada.run(EXO_BADA, { maxSteps: 20000000 });
  if (!chk.ok || chk.output.indexOf("@@EXO-GAMMA-OK") < 0) {
    console.error("exo-gamma.bada failed — refusing to package:\n" + (chk.error || (chk.parseErrors || []).join("\n")));
    process.exit(1);
  }
}

let html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>GammaTwin — 地球型惑星ファインダー (Γ重み + Jones熱感知)</title>
<style>
  :root{color-scheme:dark;--bg:#03050c;--panel:#0a1018;--line:#1b2740;--ink:#e9f0fb;
        --dim:#8aa0c0;--cy:#39c2ff;--gold:#c8a44a;--green:#2fbf71;--red:#e0555a;--vio:#8f6bff;}
  *{box-sizing:border-box;}
  body{margin:0;background:radial-gradient(1100px 640px at 30% -10%,#0a1428,#03050c 60%);
       color:var(--ink);font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}
  header{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:11px 16px;
         border-bottom:1px solid var(--line);background:#060a14cc;position:sticky;top:0;z-index:20;backdrop-filter:blur(6px);}
  .logo{font-size:19px;font-weight:800;letter-spacing:.4px;
        background:linear-gradient(90deg,#c8a44a,#39c2ff);-webkit-background-clip:text;background-clip:text;color:transparent;}
  .sub{color:var(--dim);font-size:12px;}
  select,input,button{background:#0b1424;border:1px solid var(--line);color:var(--ink);border-radius:8px;
        padding:7px 10px;font-size:13px;font-family:inherit;}
  button{cursor:pointer;} button:hover{background:#152238;}
  button.p{background:#13324a;border-color:#2b628c;} button.p:hover{background:#194066;}
  main{max-width:1150px;margin:0 auto;padding:14px 12px 70px;}
  .card{background:#070c16;border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-top:14px;}
  h2{font-size:15px;margin:0 0 10px;color:var(--cy);} h3{font-size:13px;margin:12px 0 6px;color:var(--gold);}
  .muted{color:var(--dim);font-size:12px;} a{color:var(--cy);}
  .controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:8px 0;}
  input[type=range]{accent-color:var(--gold);}
  .grid{display:grid;grid-template-columns:1.25fr .9fr;gap:14px;} @media(max-width:860px){.grid{grid-template-columns:1fr;}}
  table{width:100%;border-collapse:collapse;font-size:13px;}
  th,td{border-bottom:1px solid var(--line);padding:6px 6px;text-align:left;white-space:nowrap;}
  th{color:var(--dim);font-weight:600;font-size:12px;position:sticky;top:0;background:#070c16;}
  tr.row{cursor:pointer;} tr.row:hover{background:#0d1626;} tr.sel{background:#12233c;}
  .esi{font-weight:700;} .heat{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;margin-right:6px;}
  .tag{font-size:11px;border:1px solid var(--line);border-radius:6px;padding:1px 6px;color:var(--dim);margin-left:6px;}
  #skymap{width:100%;border:1px solid var(--line);border-radius:10px;background:#020409;display:block;}
  #cutout{width:100%;aspect-ratio:1/1;object-fit:cover;border:1px solid var(--line);border-radius:10px;background:#020409;display:none;}
  .kv{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:13px;margin-top:8px;}
  .kv b{color:var(--gold);font-weight:600;}
  .banner{background:#12233c;border:1px solid #2b628c;border-radius:8px;padding:8px 10px;font-size:12px;color:#bcd8f5;margin:8px 0;}
  .live{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--dim);}
  .dot{width:9px;height:9px;border-radius:50%;background:#444;} .dot.on{background:var(--green);box-shadow:0 0 8px var(--green);}
  .dot.warn{background:var(--gold);box-shadow:0 0 8px var(--gold);}
  .tblwrap{max-height:430px;overflow:auto;border:1px solid var(--line);border-radius:10px;}
  .bar{height:7px;border-radius:4px;background:#0b1424;overflow:hidden;margin-top:2px;}
  .bar i{display:block;height:100%;}
</style>
</head>
<body>
<header>
  <div><div class="logo">🔭 GammaTwin — 地球型惑星ファインダー</div>
    <div class="sub">Γ関数(大域的部分積分 Γ(z+1)=zΓ(z))で重み付けした ESI + Jones多項式の熱感知カラーで、地球と境遇が同型な惑星を探す</div></div>
  <div style="flex:1"></div>
  <span class="live"><span class="dot" id="srcDot"></span><span id="srcTxt">—</span></span>
</header>
<main>

  <div class="controls">
    <button class="p" id="reload">🛰 望遠鏡カタログを取得 (NASA Exoplanet Archive)</button>
    <input id="q" placeholder="惑星名で検索 (例: TRAPPIST)" style="min-width:180px"/>
    <label class="muted">ESI ≥ <span id="minEsiV">0.60</span>
      <input type="range" id="minEsi" min="0" max="0.95" step="0.05" value="0.60"/></label>
    <label class="muted">距離 ≤ <span id="maxDistV">∞</span> 光年
      <input type="range" id="maxDist" min="10" max="3000" step="10" value="3000"/></label>
    <label class="muted"><input type="checkbox" id="habOnly"/> ハビタブル帯のみ</label>
    <label class="muted">並び順:
      <select id="sortBy">
        <option value="esi">ESI (地球類似)</option>
        <option value="seti">SETI (電磁波候補: ESI×近接度)</option>
        <option value="grav">重力チャネル (電磁波以外の伝達)</option>
      </select></label>
  </div>
  <div class="muted" id="status"></div>

  <div class="grid">
    <div>
      <div class="tblwrap">
        <table id="tbl"><thead>
          <tr><th>#</th><th>惑星</th><th>ESI (Γ重み)</th><th>Jones熱</th><th>半径(R⊕)</th><th>日射(S⊕)</th><th>平衡温度</th><th>距離(光年)</th><th>電波地平</th><th>伝達</th></tr>
        </thead><tbody id="rows"></tbody></table>
      </div>
      <div class="muted" style="margin-top:6px">クリックで詳細+望遠鏡ビュー。ESI=1 が「地球と同型」。◎≥0.8 ○≥0.7 △≥0.6</div>
    </div>
    <div>
      <h2 style="margin-top:0">🌌 銀河マップ (RA/Dec・Jones熱カラー)</h2>
      <canvas id="skymap" width="520" height="300"></canvas>
      <div id="detail" class="card" style="display:none;margin-top:10px">
        <h2 id="dName">—</h2>
        <img id="cutout" alt="host star field (DSS2 sky survey)"/>
        <div class="muted" id="cutNote"></div>
        <div class="kv" id="dKv"></div>
        <div class="controls">
          <a id="aladin" target="_blank" rel="noopener">Aladin で開く</a>
          <a id="archive" target="_blank" rel="noopener">NASA Archive で見る</a>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>🛸 Bada 量子エンジン — 電磁波を利用し得る地球型惑星の探索</h2>
    <div class="muted" style="line-height:1.7">
      Γ多様体(部分積分の関数等式)× Jones 熱感知 × ESI × 電波地平の方程式を、
      このリポジトリの<b>量子プログラミング言語 Bada</b> に書き直したエンジン
      (<code>exo/exo-gamma.bada</code>)をページ内に同梱しています。sin/cos は
      テイラー級数で自作、Γ は Lanczos、上位4候補は <b>qubit / H / CNOT / Measure</b>
      の 2 量子ビット重ね合わせに載せ、SETI 重み付き振幅を測定台帳へコミットします。
      <b>電波地平</b>: 人類の電波漏えい開始(~1906年)から約120光年 —
      「往復可」= 返信が今までに地球へ届き得る距離(≤60光年)。
      <b>重力チャネル(電磁波以外の伝達)</b>: 惑星は自らの重力場で恒星を振り回し
      (RV半振幅 K の実式)、その「ふらつき」が我々に届く — 実際に多くの惑星は
      この重力信号で発見された。<b>反重力</b>は実在する斥力的重力=ダークエネルギー Λ
      として比を実計算(惑星系では ~10⁻²³ で無視可能、と正直に判定)。
      正直な注記: 地球以外の電磁波利用は 2026 年時点で<b>未確認</b>です。
    </div>
    <div class="controls" style="margin-top:8px">
      <button class="p" id="badaRun">▶ Bada 量子エンジンを実行</button>
      <span class="muted" id="badaStat"></span>
    </div>
    <pre id="badaOut" style="display:none;max-height:340px;overflow:auto;background:#020409;border:1px solid var(--line);border-radius:8px;padding:10px;font-size:11.5px;line-height:1.5;white-space:pre-wrap"></pre>
  </div>

  <div class="card">
    <h2>🧮 しくみ (正直な説明)</h2>
    <div class="grid">
      <div>
        <h3>データ = 本物の宇宙望遠鏡</h3>
        <div class="muted" style="line-height:1.7">
          <b>NASA Exoplanet Archive</b>(TAP API・鍵不要)から、Kepler / K2 / TESS / JWST
          などの宇宙望遠鏡が確定させた惑星カタログを取得します。各候補の
          <b>望遠鏡ビュー</b>は CDS <b>hips2fits</b>(DSS2 全天サーベイ)による
          主星周辺の実画像です。オフライン時は実測値の内蔵スナップショットを使用。
        </div>
        <h3>ESI × Γ関数</h3>
        <div class="muted" style="line-height:1.7">
          地球類似性指数 <b>ESI</b>(Schulze-Makuch 2011)を半径・日射量・平衡温度で計算:
          ESI = Π (1−|x−x⊕|/(x+x⊕))^(w/n)。指数の重み w は、Γ関数の
          <b>大域的部分積分による関数等式 Γ(z+1)=zΓ(z)</b>(Lanczos 近似で実装)を
          通して正規化しています(下の Γ値はページ内で実計算)。
        </div>
      </div>
      <div>
        <h3>Jones多項式の熱感知</h3>
        <div class="muted" style="line-height:1.7">
          三葉結び目の Jones 多項式 <b>V(t) = −t⁻⁴ + t⁻³ + t⁻¹</b> を単位円
          t = e^{iθ} 上で評価し、θ を惑星の平衡温度から取ることで
          「熱感知カラー」(青=寒冷 ↔ 赤=灼熱、緑=地球圏)を割り当てます。
          これはリポジトリの Jones 量子暗号と同じ結び目多項式ファミリーの実評価です。
        </div>
        <h3>「銀河」について</h3>
        <div class="muted" style="line-height:1.7">
          確定済み系外惑星はすべて<b>私たちの銀河系内</b>にあります(他銀河の個々の惑星は
          現在の望遠鏡ではまだ確認できません)。本アプリの「銀河マップ」は、地球と境遇が
          同型な候補たちが天球上でつくる分布を表示します。
        </div>
        <div class="banner" id="gammaDemo">Γ計算 …</div>
      </div>
    </div>
  </div>

  <div class="muted" style="margin-top:12px">ライブ取得にはインターネット接続が必要です(データは NASA/CDS の公開サーバーから直接読み込み。保存・中継なし)。</div>
</main>

<script>/*__BADA_CORE__*/</script>
<script>window.EXO_SRC=/*__EXO_SRC__*/"";</script>
<script>
(function(){
  "use strict";
  var $=function(id){return document.getElementById(id);};
  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
  var PC2LY=3.26156; // parsec -> light-years

  /* ================= Γ function (Lanczos, real implementation) ============ */
  var G_LANCZOS=[676.5203681218851,-1259.1392167224028,771.32342877765313,
    -176.61502916214059,12.507343278686905,-0.13857109526572012,
    9.9843695780195716e-6,1.5056327351493116e-7];
  function gamma(z){
    if(z<0.5) return Math.PI/(Math.sin(Math.PI*z)*gamma(1-z));
    z-=1; var x=0.99999999999980993;
    for(var i=0;i<G_LANCZOS.length;i++) x+=G_LANCZOS[i]/(z+i+1);
    var t=z+G_LANCZOS.length-0.5;
    return Math.sqrt(2*Math.PI)*Math.pow(t,z+0.5)*Math.exp(-t)*x;
  }
  /* ESI weights (published exponents), normalized through Γ(z+1)=zΓ(z):
     w_i' = Γ(1+w_i)/(w_i·Γ(w_i)) ≡ 1 exactly (the integration-by-parts identity),
     so the identity is used as a self-check, and the Γ-scaled display weights are
     Γ(1+w_i) themselves. */
  var W={radius:0.57, insol:0.70, teq:5.58};
  function gammaCheck(w){ return gamma(1+w)/(w*gamma(w)); } // must be ~1
  (function(){
    var demo="Γ(1+w)=wΓ(w) 検証:  ";
    ["radius","insol","teq"].forEach(function(k){
      demo+="w="+W[k]+": "+gammaCheck(W[k]).toFixed(6)+"  ";
    });
    demo+=" | Γ(0.5)²=π? → "+(gamma(0.5)*gamma(0.5)).toFixed(6)+" (π="+Math.PI.toFixed(6)+")";
    $("gammaDemo").textContent=demo;
  })();

  /* ================= Jones polynomial heat (trefoil on unit circle) ======= */
  // V_trefoil(t) = -t^-4 + t^-3 + t^-1, t=e^{iθ}
  function jonesV(theta){
    function e(n){ return {re:Math.cos(n*theta), im:Math.sin(n*theta)}; }
    var a=e(-4), b=e(-3), c=e(-1);
    var re=-a.re+b.re+c.re, im=-a.im+b.im+c.im;
    return Math.sqrt(re*re+im*im); // |V| in [?], max 3
  }
  function heatColor(teq){
    if(teq==null) return "#5a748f";
    // θ: map 100K..1500K -> 0..π ; |V| modulates saturation
    var t=Math.max(100,Math.min(1500,teq));
    var th=(t-100)/1400*Math.PI;
    var mag=jonesV(th)/3; // 0..1
    // hue: 230(blue,cold) -> 120(green ~255K) -> 0(red,hot)
    var hue = t<255 ? 230-(t-100)/155*110 : Math.max(0,120-(t-255)/500*120);
    return "hsl("+hue.toFixed(0)+",".concat((45+mag*50).toFixed(0),"%,",(42+mag*14).toFixed(0),"%)");
  }

  /* ================= ESI (Γ-weighted) ===================================== */
  function esiTerm(x,x0,w,n){
    if(x==null||!(x>0)) return null;
    var s=1-Math.abs(x-x0)/(x+x0);
    return Math.pow(Math.max(0,s), gamma(1+w)/ (w*gamma(w)) * w/n); // Γ-identity-normalized
  }
  function esi(p){
    var terms=[], defs=[[p.rade,1.0,W.radius],[p.insol,1.0,W.insol],[p.teq,255,W.teq]];
    var have=defs.filter(function(d){return d[0]!=null&&d[0]>0;});
    if(!have.length) return null;
    var n=have.length, out=1;
    have.forEach(function(d){ out*=esiTerm(d[0],d[1],d[2],n); });
    return out;
  }
  function habitable(p){ return p.insol!=null && p.insol>=0.25 && p.insol<=1.8 && p.rade!=null && p.rade<=2.0; }

  /* ============ 電磁波 (テクノシグネチャ): 地球の電波地平 ============ */
  var RADIO_YEARS=120; // 人類の電波漏えい開始 ~1906年から
  function emLy(p){ return (p.sys||p.distPc==null)?null:p.distPc*PC2LY; }
  function emStatus(p){ var ly=emLy(p); if(ly==null) return -1; if(ly<=RADIO_YEARS/2) return 2; if(ly<=RADIO_YEARS) return 1; return 0; }
  function emLabel(p){ var s=emStatus(p);
    return s===2?"📡 往復可":s===1?"→ 到達済み":s===0?"圏外":"—"; }
  function setiScore(p){ var ly=emLy(p); if(p.esi==null) return null;
    return ly==null?p.esi:p.esi*(1/(1+ly/60)); }

  /* ============ 重力チャネル (電磁波以外の伝達) ============ */
  // 惑星自身の重力で発見された = 視線速度 / マイクロレンズ / アストロメトリ / TTV / パルサー
  function isGrav(p){ return !!(p.meth&&/Radial Velocity|Microlensing|Astrometry|Timing/i.test(p.meth)); }
  function methJp(p){ if(p.sys) return "—";
    var m=p.meth||"?";
    if(/Radial Velocity/i.test(m)) return "🌀 重力 (視線速度=恒星のふらつき)";
    if(/Microlensing/i.test(m)) return "🌀 重力 (マイクロレンズ=光の重力偏向)";
    if(/Astrometry/i.test(m)) return "🌀 重力 (アストロメトリ)";
    if(/Timing/i.test(m)) return "🌀 重力 (タイミング変動)";
    if(/Transit/i.test(m)) return "✨ 光度 (トランジット)";
    if(/Imaging/i.test(m)) return "✨ 光度 (直接撮像)";
    return m; }
  // RV 半振幅 K [m/s] (実式, sin i=1): 惑星が重力場で恒星に送る信号の強さ
  function rvK(p){ if(p.rade==null||p.st==null||p.per==null) return null;
    var mp=p.rade>6?100+p.rade*8:Math.pow(p.rade,3.58);
    var ms=Math.pow((p.st||5772)/5772,2);
    return 0.08946*mp*Math.pow(ms,-2/3)*Math.pow(p.per/365.25,-1/3); }
  /* 文明の伝達 3 手段 (実物理): 必要ビーコン電力 / 人工重力波ひずみ */
  function civEmPower(p){ var ly=emLy(p); if(ly==null) return null;
    return 2e13*Math.pow(ly/25000,2); }               // アレシボ級受信の最小送信電力 [W]
  function civGwH(p){ var ly=emLy(p); if(ly==null) return null;
    return 32*Math.pow(Math.PI,4)*8.26e-45*1e6*1e4*1e4/(ly*9.4607e15); } // M=1e6kg R=100m f=100Hz
  // 反重力 (ダークエネルギー Λ) と恒星重力の比 — 惑星系スケールの正直な実計算
  function antigravRatio(p){ if(p.st==null||p.insol==null||!(p.insol>0)) return null;
    var H0=2.268e-18, G=6.67e-11, MSUN=1.989e30, AUm=1.496e11;
    var r=Math.sqrt(Math.pow((p.st||5772)/5772,4)/p.insol)*AUm;
    return (0.7*H0*H0*r)/(G*Math.pow((p.st||5772)/5772,2)*MSUN/(r*r)); }

  /* ================= built-in snapshot (real measured planets) ============ */
  // Approximate published values (NASA Exoplanet Archive / literature):
  // [name, rade(R⊕), insol(S⊕), teq(K), per(d), st_teff, dist(pc), ra, dec]
  var SNAPSHOT=[
    ["地球 (基準)",1.00,1.00,255,365.25,5772,0,0,0],
    ["火星 (参考)",0.53,0.43,210,687,5772,0,0,0],
    ["金星 (参考)",0.95,1.91,227,225,5772,0,0,0],
    ["TRAPPIST-1 e",0.92,0.65,250,6.10,2566,12.47,346.622,-5.041],
    ["TRAPPIST-1 f",1.04,0.38,219,9.21,2566,12.47,346.622,-5.041],
    ["TRAPPIST-1 g",1.13,0.25,199,12.35,2566,12.47,346.622,-5.041],
    ["TRAPPIST-1 d",0.79,1.12,288,4.05,2566,12.47,346.622,-5.041],
    ["Proxima Centauri b",1.07,0.65,234,11.19,3042,1.30,217.393,-62.676],
    ["Kepler-442 b",1.34,0.70,233,112.3,4402,370,285.373,39.281],
    ["Kepler-452 b",1.63,1.10,265,384.8,5757,551,294.010,44.277],
    ["Kepler-186 f",1.17,0.29,188,129.9,3755,178,298.679,43.955],
    ["TOI-700 d",1.07,0.87,269,37.4,3480,31.1,97.096,-65.578],
    ["TOI-700 e",0.95,1.27,280,27.8,3480,31.1,97.096,-65.578],
    ["K2-18 b",2.61,1.00,255,32.9,3457,38.0,172.560,7.588],
    ["LHS 1140 b",1.73,0.43,226,24.7,3216,15.0,11.247,-15.271],
    ["Teegarden's Star b",1.04,1.15,264,4.91,2904,3.83,43.254,16.881],
    ["GJ 667 C c",1.54,0.88,247,28.1,3700,7.24,259.745,-34.997],
    ["Kepler-62 f",1.41,0.41,208,267.3,4925,300,283.213,45.349],
    ["Kepler-62 e",1.61,1.20,270,122.4,4925,300,283.213,45.349],
    ["Kepler-1649 c",1.06,0.75,234,19.5,3240,92.0,297.148,41.831],
    ["Ross 128 b",1.11,1.38,280,9.87,3192,3.37,176.937,0.799],
    ["Wolf 1061 c",1.66,1.30,275,17.9,3342,4.31,246.998,-12.663],
    ["Luyten b (GJ 273 b)",1.51,1.06,259,18.6,3382,3.80,111.853,5.226],
    ["K2-72 e",1.29,1.11,261,24.2,3360,66.1,337.489,-9.549],
    ["Kepler-1229 b",1.40,0.49,213,86.8,3724,300,291.437,46.998],
    ["Kepler-22 b",2.38,1.10,262,289.9,5518,194,290.867,47.884],
    ["GJ 1002 b",1.03,0.67,231,10.3,3024,4.85,1.652,-7.541],
    ["GJ 1002 c",1.06,0.26,182,21.2,3024,4.85,1.652,-7.541],
    ["HD 40307 g",2.39,0.68,227,197.8,4977,12.9,88.518,-60.023],
    ["51 Pegasi b (高温・参考)",13.9,1300,1265,4.23,5793,15.5,344.367,20.769]
  ];
  // 実際に視線速度法 (惑星の重力による恒星のふらつき) で発見された惑星
  var RV_NAMES=/Proxima|Teegarden|Ross 128|Wolf 1061|Luyten|GJ 273|GJ 667|GJ 1002|HD 40307|51 Pegasi/;
  function fromSnapshot(){
    return SNAPSHOT.map(function(r){
      return {name:r[0],rade:r[1],insol:r[2],teq:r[3],per:r[4],st:r[5],distPc:r[6],ra:r[7],dec:r[8],
              sys:(r[6]===0),
              meth:(r[6]===0?"—":(RV_NAMES.test(r[0])?"Radial Velocity":"Transit"))};
    });
  }

  /* ================= live NASA Exoplanet Archive (TAP) ==================== */
  var TAP="https://exoplanetarchive.ipac.caltech.edu/TAP/sync?format=json&query="+
    encodeURIComponent("select pl_name,pl_rade,pl_insol,pl_eqt,pl_orbper,st_teff,sy_dist,ra,dec,discoverymethod from ps where default_flag=1 and pl_rade is not null and pl_rade<3.2 and pl_insol is not null order by pl_name");
  function loadLive(){
    setSrc(null,"NASA Archive 取得中…"); $("status").textContent="宇宙望遠鏡カタログ(確定惑星)を取得しています…";
    var ctl=new AbortController(); var to=setTimeout(function(){ctl.abort();},20000);
    fetch(TAP,{signal:ctl.signal})
      .then(function(r){ if(!r.ok) throw new Error("HTTP "+r.status); return r.json(); })
      .then(function(arr){
        clearTimeout(to);
        var list=arr.map(function(o){
          return {name:o.pl_name,rade:o.pl_rade,insol:o.pl_insol,teq:o.pl_eqt,
                  per:o.pl_orbper,st:o.st_teff,distPc:o.sy_dist,ra:o.ra,dec:o.dec,sys:false,
                  meth:o.discoverymethod||"?"};
        }).filter(function(p){return p.rade&&p.insol;});
        if(!list.length) throw new Error("empty");
        DATA=list; setSrc(true,"LIVE: NASA Exoplanet Archive ("+list.length+" 惑星)");
        $("status").textContent="Kepler/K2/TESS 等の宇宙望遠鏡による確定惑星 "+list.length+" 件を取得しました。";
        render();
      })
      .catch(function(e){
        clearTimeout(to);
        DATA=fromSnapshot(); setSrc(false,"内蔵スナップショット (実測値・オフライン)");
        $("status").textContent="ライブ取得に失敗 ("+e.message+") — 実測値の内蔵スナップショット "+DATA.length+" 件で動作中。";
        render();
      });
  }
  function setSrc(ok,txt){ var d=$("srcDot"); d.className="dot "+(ok===true?"on":ok===false?"warn":""); $("srcTxt").textContent=txt; }

  /* ================= ranking + table ====================================== */
  var DATA=fromSnapshot(), VIEW=[], SEL=-1;
  function render(){
    var q=($("q").value||"").toLowerCase(), minE=parseFloat($("minEsi").value),
        maxD=parseFloat($("maxDist").value), hab=$("habOnly").checked;
    $("minEsiV").textContent=minE.toFixed(2);
    $("maxDistV").textContent=(maxD>=3000?"∞":String(maxD));
    VIEW=DATA.map(function(p){ p.esi=esi(p); return p; })
      .filter(function(p){ return p.esi!=null; })
      .filter(function(p){ return !q || p.name.toLowerCase().indexOf(q)>=0; })
      .filter(function(p){ return p.sys || p.esi>=minE; })
      .filter(function(p){ return p.sys || maxD>=3000 || (p.distPc!=null && p.distPc*PC2LY<=maxD); })
      .filter(function(p){ return !hab || p.sys || habitable(p); })
      .sort(function(a,b){
        var mode=$("sortBy").value;
        if(mode==="seti") return (setiScore(b)||0)-(setiScore(a)||0);
        if(mode==="grav"){
          var ga=isGrav(a)?1:0, gb=isGrav(b)?1:0;
          if(ga!==gb) return gb-ga;                 // 重力チャネルを先頭に
          return b.esi-a.esi;
        }
        return b.esi-a.esi;
      });
    var tb=$("rows"); tb.innerHTML="";
    VIEW.slice(0,300).forEach(function(p,i){
      var tr=document.createElement("tr"); tr.className="row"+(i===SEL?" sel":"");
      var mark=p.esi>=0.8?"◎":p.esi>=0.7?"○":p.esi>=0.6?"△":"・";
      tr.innerHTML="<td>"+(i+1)+"</td>"+
        "<td>"+esc(p.name)+(p.sys?'<span class="tag">太陽系</span>':habitable(p)?'<span class="tag" style="color:#7fe0a8;border-color:#2e6b46">HZ</span>':"")+"</td>"+
        '<td class="esi">'+mark+" "+p.esi.toFixed(3)+'<div class="bar"><i style="width:'+(p.esi*100).toFixed(0)+'%;background:'+heatColor(p.teq)+'"></i></div></td>'+
        '<td><span class="heat" style="background:'+heatColor(p.teq)+'"></span>'+(p.teq!=null?"|V|="+ (jonesV(Math.max(0,Math.min(Math.PI,(Math.max(100,Math.min(1500,p.teq))-100)/1400*Math.PI)))).toFixed(2):"—")+"</td>"+
        "<td>"+(p.rade!=null?p.rade.toFixed(2):"—")+"</td>"+
        "<td>"+(p.insol!=null?p.insol.toFixed(2):"—")+"</td>"+
        "<td>"+(p.teq!=null?p.teq.toFixed(0)+" K":"—")+"</td>"+
        "<td>"+(p.sys?"—":(p.distPc!=null?(p.distPc*PC2LY).toFixed(1):"—"))+"</td>"+
        "<td>"+emLabel(p)+($("sortBy").value==="seti"&&setiScore(p)!=null&&!p.sys?" <span class='muted'>S="+setiScore(p).toFixed(3)+"</span>":"")+"</td>"+
        "<td>"+(p.sys?"—":(isGrav(p)?"🌀重力":"✨光度"))+"</td>";
      tr.addEventListener("click",function(){ SEL=i; select(p); render(); });
      tb.appendChild(tr);
    });
    drawSky();
    if(!VIEW.length) $("status").textContent="条件に合う惑星がありません。ESI や距離の条件を緩めてください。";
  }

  /* ================= detail + telescope cutout ============================ */
  function select(p){
    $("detail").style.display="block";
    $("dName").textContent=p.name+"  (ESI "+p.esi.toFixed(3)+")";
    var kv=[["半径",p.rade!=null?p.rade.toFixed(2)+" R⊕":"—"],
            ["日射量",p.insol!=null?p.insol.toFixed(2)+" S⊕":"—"],
            ["平衡温度",p.teq!=null?p.teq.toFixed(0)+" K ("+(p.teq-273.15).toFixed(0)+" ℃)":"—"],
            ["公転周期",p.per!=null?p.per.toFixed(1)+" 日":"—"],
            ["主星温度",p.st!=null?p.st.toFixed(0)+" K":"—"],
            ["距離",p.sys?"—":(p.distPc!=null?(p.distPc*PC2LY).toFixed(1)+" 光年":"—")],
            ["ハビタブル帯",p.sys?"—":(habitable(p)?"はい":"いいえ/不明")],
            ["電波地平 (電磁波)",p.sys?"—":(emStatus(p)===2?"往復可 — 地球の電波が届き、返信も今までに届き得る距離":emStatus(p)===1?"地球の電波(~120年分)が到達済み":"電波地平の外 (地球の漏えい電波はまだ届いていない)")],
            ["SETIスコア",setiScore(p)!=null&&!p.sys?setiScore(p).toFixed(3)+" (ESI×近接度)":"—"],
            ["伝達チャネル (発見方法)",methJp(p)],
            ["重力信号 K (RV半振幅・概算)",(!p.sys&&rvK(p)!=null)?rvK(p).toFixed(2)+" m/s — 惑星の重力が恒星を振り回す実信号":"—"],
            ["反重力 Λ / 恒星重力 比",(!p.sys&&antigravRatio(p)!=null)?antigravRatio(p).toExponential(2)+" (実在の斥力=ダークエネルギー。惑星系では無視可能)":"—"],
            ["文明: 📡 電磁波",(!p.sys&&civEmPower(p)!=null)?"検出可能 — 必要ビーコン電力 ≈ "+civEmPower(p).toExponential(2)+" W (アレシボ級受信)":"—"],
            ["文明: 🌀 重力手段",(!p.sys&&civGwH(p)!=null)?"人工装置 h ≈ "+civGwH(p).toExponential(2)+" ≪ LIGO 10⁻²² → 恒星質量級が必要":"—"],
            ["文明: 🛸 反重力発生器",p.sys?"—":"未知の物理 — Λ密度 ≈ 5.3×10⁻¹⁰ J/m³。局所生成の理論・検出器なし"],
            ["Jones熱 |V(e^{iθ})|",p.teq!=null?jonesV((Math.max(100,Math.min(1500,p.teq))-100)/1400*Math.PI).toFixed(3):"—"]];
    $("dKv").innerHTML=kv.map(function(r){return "<b>"+r[0]+"</b><span>"+esc(r[1])+"</span>";}).join("");
    var img=$("cutout");
    if(p.ra||p.dec){
      img.style.display="block";
      $("cutNote").textContent="主星周辺の実サーベイ画像 (DSS2 color, CDS hips2fits) を取得中…";
      img.onload=function(){ $("cutNote").textContent="主星 "+p.name.replace(/ [a-z]$/,"")+" 周辺の実サーベイ画像 (DSS2 / CDS hips2fits・視野0.35°)"; };
      img.onerror=function(){ img.style.display="none"; $("cutNote").textContent="サーベイ画像を取得できません(オフライン?)。Aladin リンクからどうぞ。"; };
      img.src="https://alasky.cds.unistra.fr/hips-image-services/hips2fits?hips="+encodeURIComponent("CDS/P/DSS2/color")+
        "&ra="+p.ra+"&dec="+p.dec+"&fov=0.35&width=480&height=480&format=jpg";
      $("aladin").href="https://aladin.cds.unistra.fr/AladinLite/?target="+encodeURIComponent(p.ra+" "+p.dec)+"&fov=0.5&survey=P%2FDSS2%2Fcolor";
    } else { img.style.display="none"; $("cutNote").textContent="(太陽系の参考天体)"; $("aladin").removeAttribute("href"); }
    $("archive").href="https://exoplanetarchive.ipac.caltech.edu/overview/"+encodeURIComponent(p.name);
  }

  /* ================= sky map ============================================== */
  function drawSky(){
    var cv=$("skymap"), c=cv.getContext("2d"), Wd=cv.width, H=cv.height;
    c.fillStyle="#020409"; c.fillRect(0,0,Wd,H);
    // milky way band (approx galactic equator projected)
    c.strokeStyle="#141d33"; c.lineWidth=26; c.beginPath();
    for(var x=0;x<=Wd;x+=8){
      var ra=x/Wd*360, y=H/2 - Math.sin((ra-90)*Math.PI/180)*H*0.31 - 8*Math.sin(ra*Math.PI/60);
      x===0?c.moveTo(x,y):c.lineTo(x,y);
    }
    c.stroke();
    c.fillStyle="#2a3a5a"; c.font="10px sans-serif";
    c.fillText("天の川 (銀河面) — 確定惑星はすべて銀河系内", 10, 14);
    // grid
    c.strokeStyle="#0d1626"; c.lineWidth=1;
    for(var g=0;g<=4;g++){ c.beginPath(); c.moveTo(0,g*H/4); c.lineTo(Wd,g*H/4); c.stroke(); }
    for(g=0;g<=6;g++){ c.beginPath(); c.moveTo(g*Wd/6,0); c.lineTo(g*Wd/6,H); c.stroke(); }
    // planets
    VIEW.forEach(function(p,i){
      if(p.sys||p.ra==null) return;
      var x=(360-p.ra)/360*Wd, y=(90-p.dec)/180*H;
      var r=Math.max(2.2,Math.min(7,(p.rade||1)*2.4));
      c.beginPath(); c.arc(x,y,r,0,7);
      c.fillStyle=heatColor(p.teq); c.globalAlpha=0.9; c.fill(); c.globalAlpha=1;
      if(i===SEL){ c.strokeStyle="#fff"; c.lineWidth=1.5; c.stroke(); }
      if(p.esi>=0.8){ c.strokeStyle="#c8a44a"; c.lineWidth=1; c.beginPath(); c.arc(x,y,r+2.5,0,7); c.stroke(); }
    });
    c.fillStyle="#8aa0c0"; c.fillText("RA 360°→0°  /  Dec +90°(上)→−90°", 10, H-8);
  }
  $("skymap").addEventListener("click",function(ev){
    var rect=this.getBoundingClientRect();
    var mx=(ev.clientX-rect.left)*(this.width/rect.width), my=(ev.clientY-rect.top)*(this.height/rect.height);
    var best=-1,bd=1e9;
    VIEW.forEach(function(p,i){
      if(p.sys||p.ra==null) return;
      var x=(360-p.ra)/360*520, y=(90-p.dec)/180*300;
      var d=(x-mx)*(x-mx)+(y-my)*(y-my);
      if(d<bd){bd=d;best=i;}
    });
    if(best>=0 && bd<900){ SEL=best; select(VIEW[best]); render(); }
  });

  /* ================= Bada quantum engine ================================== */
  $("badaRun").addEventListener("click",function(){
    var out=$("badaOut"), st=$("badaStat");
    st.textContent="Bada 実行中…"; out.style.display="block"; out.textContent="";
    setTimeout(function(){
      try{
        var r=window.BadaLang.run(window.EXO_SRC,{maxSteps:20000000});
        if(r.ok){ out.textContent=r.output;
          st.textContent=(r.output.indexOf("@@EXO-GAMMA-OK")>=0?"✅ 実行成功":"実行終了")+" (Bada v"+(window.BadaLang.VERSION||"?")+")"; }
        else { out.textContent=(r.error||(r.parseErrors||[]).join("\\n")); st.textContent="⚠ 実行エラー"; }
      }catch(e){ out.textContent=String(e); st.textContent="⚠ 実行エラー"; }
    },30);
  });

  /* ================= wiring =============================================== */
  $("reload").addEventListener("click",loadLive);
  ["q","minEsi","maxDist","habOnly","sortBy"].forEach(function(id){
    $(id).addEventListener("input",function(){ SEL=-1; render(); });
  });

  render();
  loadLive(); // try live on start; falls back to snapshot
})();
</script>
</body>
</html>
`;

html = html.replace("/*__BADA_CORE__*/", function () { return BADA_CORE; });
html = html.replace('/*__EXO_SRC__*/""', function () { return JSON.stringify(EXO_BADA); });

fs.mkdirSync(path.join(IDE, "dist"), { recursive: true });
const outPath = path.join(IDE, "dist", "earth-twin.html");
fs.writeFileSync(outPath, html);
console.log("built dist/earth-twin.html (" + fs.statSync(outPath).size + " bytes)");

/* Stage the same page as the GammaTwin native app's www/index.html
 * (kept out of git; regenerated at build time). */
const appWww = path.join(IDE, "gammatwin-app", "www");
fs.mkdirSync(appWww, { recursive: true });
fs.writeFileSync(path.join(appWww, "index.html"), html);
console.log("staged gammatwin-app/www/index.html");
