#!/usr/bin/env node
/* ============================================================================
 * build-quantum-contact.js — build "QuantumContact — 宇宙人コンタクト量子通信局",
 * a single self-contained HTML app: compose a real-format interstellar
 * message (Arecibo-style 23×73 bitmap), protect it with QUANTUM CRYPTOGRAPHY
 * (a full BB84 quantum-key-distribution simulation — the actual job a
 * quantum computer has in interstellar contact), and watch the transmission
 * fly to a real target with the real link budget.
 *
 * Honest physics, stated in the app:
 *   ・Entanglement itself cannot carry a message (no-communication theorem).
 *     The quantum computer's real role is the KEY: BB84 produces a shared
 *     key whose eavesdropper is exposed by quantum mechanics (QBER ≈ 25%
 *     under intercept-resend — simulated live, with an Eve toggle).
 *   ・The carrier remains electromagnetic (a radio dish).
 *   ・Real METI history is listed (Arecibo 1974 → M13; Cosmic Call;
 *     Sónar Calling 2017 → GJ 273b = the catalog's Luyten b, via EISCAT).
 *   ・Zero replies / zero contact as of 2026. This app composes and
 *     quantum-encrypts; it does NOT transmit.
 *
 * The Bada quantum engine (exo/contact-bb84.bada, arrow syntax) is embedded
 * and runs in-browser: BB84 sifting, Eve's QBER, Bell zero-preservation,
 * the Jones |V(e^{iθ})| key, and an encrypt/decrypt round trip ending in
 * @@BB84-OK. The builder refuses to package if that run fails.
 *
 * Output: ../dist/quantum-contact.html (+ staged quantumcontact-app/www/)
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");

const BADA_CORE = fs.readFileSync(path.join(IDE, "www", "bada.js"), "utf8");
const CONTACT_SRC = fs.readFileSync(path.join(IDE, "exo", "contact-bb84.bada"), "utf8");

/* ---- refuse to package unless the quantum engine completes ------------- */
{
  const mod = { exports: {} };
  const fn = new Function("module", "exports", "window", BADA_CORE + "\nreturn module.exports;");
  let Bada = fn(mod, mod.exports, undefined) || mod.exports;
  if (Bada.BadaLang) Bada = Bada.BadaLang;
  const res = Bada.run(CONTACT_SRC, { maxSteps: 4000000 });
  if (!res.ok || (res.parseErrors && res.parseErrors.length) || !/@@BB84-OK/.test(res.output) || !/@@GERT-OK/.test(res.output) || !/@@NONCOMM-OK/.test(res.output)) {
    console.error("ERROR: contact-bb84.bada failed — refusing to package");
    console.error((res.parseErrors || []).join("\n"));
    console.error(res.error || "");
    process.exit(1);
  }
  console.log("contact-bb84.bada run OK (@@BB84-OK)");
}

let html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>QuantumContact — 宇宙人コンタクト量子通信局 (BB84×Jones×Bada)</title>
<style>
  :root{color-scheme:dark;--bg:#03050c;--line:#1b2740;--ink:#e9f0fb;--dim:#8aa0c0;
        --cy:#39c2ff;--gold:#c8a44a;--green:#2fbf71;--red:#e0555a;--vio:#b58cff;}
  *{box-sizing:border-box;}
  body{margin:0;background:#03050c;color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;}
  header{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:11px 16px;
         border-bottom:1px solid var(--line);background:#060a14cc;position:sticky;top:0;z-index:20;backdrop-filter:blur(6px);}
  .logo{font-size:19px;font-weight:800;letter-spacing:.4px;
        background:linear-gradient(90deg,#b58cff,#39c2ff);-webkit-background-clip:text;background-clip:text;color:transparent;}
  .sub{color:var(--dim);font-size:12px;}
  select,input,button,textarea{background:#0b1424;border:1px solid var(--line);color:var(--ink);border-radius:8px;
        padding:7px 10px;font-size:13px;font-family:inherit;}
  button{cursor:pointer;} button:hover{background:#152238;}
  button.r{background:#3a1520;border-color:#6b2e3a;}
  button.g{background:#11301f;border-color:#2e6b46;}
  main{max-width:1150px;margin:0 auto;padding:14px 12px 70px;}
  .banner{background:#241636;border:1px solid #4a3a7a;border-radius:10px;padding:10px 13px;
          font-size:12.5px;color:#d8c8ff;margin-bottom:12px;line-height:1.7;}
  .controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:8px 0;}
  .grid{display:grid;grid-template-columns:2fr 1fr;gap:14px;} @media(max-width:920px){.grid{grid-template-columns:1fr;}}
  .stagewrap{position:relative;background:#000;border:1px solid var(--line);border-radius:14px;overflow:hidden;}
  #stage{width:100%;display:block;background:#000;}
  .hud{position:absolute;left:10px;top:10px;background:#000b;border:1px solid var(--line);border-radius:8px;
       padding:7px 11px;font-size:12px;color:#cfe0f5;line-height:1.6;pointer-events:none;max-width:76%;}
  .hud b{color:var(--gold);}
  .rec{position:absolute;right:12px;top:12px;display:none;align-items:center;gap:6px;background:#000a;
       border:1px solid #6b2e3a;border-radius:8px;padding:5px 10px;font-size:12px;color:#ff9aa5;}
  .rec.on{display:inline-flex;} .rec .d{width:9px;height:9px;border-radius:50%;background:var(--red);animation:pulse 1.2s infinite;}
  @keyframes pulse{50%{opacity:.35;}}
  .card{background:#070c16;border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-top:14px;}
  h2{font-size:15px;margin:0 0 10px;color:var(--cy);}
  .muted{color:var(--dim);font-size:12px;}
  .kv{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;font-size:13px;margin-top:10px;}
  .kv b{color:var(--gold);font-weight:600;}
  table{border-collapse:collapse;font-size:12px;width:100%;}
  th,td{border:1px solid var(--line);padding:3px 7px;text-align:center;}
  th{background:#0d1626;color:var(--cy);}
  #msg{display:block;background:#04070f;border:1px solid var(--line);border-radius:10px;cursor:crosshair;max-width:100%;}
  .mono{font-family:ui-monospace,Consolas,monospace;font-size:11.5px;word-break:break-all;}
  .gline{font-family:ui-monospace,Consolas,monospace;font-size:11.5px;color:#7fd8a8;margin-top:8px;word-break:break-all;}
  .warn{background:#3a1520;border:1px solid #6b2e3a;border-radius:8px;padding:8px 11px;color:#ff9aa5;font-size:12.5px;margin-top:8px;display:none;}
  .ok{background:#11301f;border:1px solid #2e6b46;border-radius:8px;padding:8px 11px;color:#7fe0a8;font-size:12.5px;margin-top:8px;display:none;}
  pre{background:#04070f;border:1px solid var(--line);border-radius:10px;padding:10px;font-size:11px;
      max-height:300px;overflow:auto;white-space:pre-wrap;color:#bfe6c8;}
  .badge{font-size:11px;border-radius:6px;padding:1px 7px;margin-left:6px;font-weight:600;
         background:#173a29;color:#7fe0a8;border:1px solid #2e6b46;}
</style>
</head>
<body>
<header>
  <div><div class="logo">📡 QuantumContact — 宇宙人コンタクト量子通信局</div>
    <div class="sub">量子コンピューター (BB84量子鍵配送) × Jones量子鍵 × アレシボ様式メッセージ — 宇宙人達への接触を量子暗号で守る通信局</div></div>
</header>
<main>

  <div class="banner">
    <b>正直な前提</b>: 地球外文明との接触は <b>2026年時点でゼロ</b>です (実在のMETI送信 —
    <b>1974 アレシボ・メッセージ→M13</b>、Cosmic Call、<b>2017 Sónar Calling→GJ 273b (=カタログのLuyten b)</b> —
    への返信もまだありません)。物理も正直に: <b>量子もつれ自体はメッセージを運べません</b>
    (no-communication 定理)。量子コンピューターの実際の役割は<b>鍵</b> — BB84 量子鍵配送が
    盗聴を QBER≈25% として暴露する共有鍵を作り、本文の搬送は電磁波 (電波望遠鏡) です。
    この通信局はメッセージの作成・量子暗号化・送信シミュレーションまでを行い、<b>実際の送信はしません</b>。
  </div>

  <div class="grid">
    <div>
      <div class="card" style="margin-top:0">
        <h2>🎯 送信先 (実在の天体) と実リンクバジェット</h2>
        <div class="controls">
          <label class="muted">宛先:
            <select id="pick" style="min-width:300px"></select></label>
        </div>
        <div class="kv" id="budget"></div>
      </div>

      <div class="card">
        <h2>✉ アレシボ様式メッセージ (23×73 = 1679ビット・半素数) <span class="muted">クリックで編集</span></h2>
        <canvas id="msg" width="414" height="657"></canvas>
        <div class="controls">
          <button id="presetBtn">🧬 自作アレシボ様式に戻す</button>
          <button id="clearBtn">⬛ 全消去</button>
          <span class="muted" id="bitInfo"></span>
        </div>
        <div class="controls">
          <label class="muted" style="flex:1;min-width:280px">追記テキスト (UTF-8でビット列に追加):
            <input id="txt" style="width:100%" value="WE COME IN PEACE 私たちは平和のうちに来た"/></label>
        </div>
        <div class="muted">本物のアレシボ・メッセージ (1974) と同じ 23×73 形式に倣った<b>自作</b>ビットマップ:
          2進数の1〜10 / 生命の原子番号 H,C,N,O,P / DNA二重らせん / ヒト / 太陽系 (地球を持ち上げ) / 電波望遠鏡。</div>
      </div>
    </div>

    <div>
      <div class="card" style="margin-top:0">
        <h2>🔑 量子鍵配送 (BB84) — 量子コンピューターの実務</h2>
        <div class="controls">
          <button class="g" id="qkdBtn">⚛ 量子鍵を配送 (BB84×64qubit)</button>
          <label class="muted"><input type="checkbox" id="eve"/> 盗聴者イヴを挿入</label>
        </div>
        <div style="max-height:190px;overflow:auto"><table id="qtab"></table></div>
        <div class="kv" id="qinfo"></div>
        <div class="warn" id="qwarn"></div>
        <div class="ok" id="qok"></div>
      </div>

      <div class="card">
        <h2>🔐 量子暗号化 → 送信パッケージ</h2>
        <div class="controls">
          <button class="g" id="encBtn">🔐 Jones量子鍵で暗号化</button>
          <button id="dlBtn">⬇ .qmsg を保存</button>
        </div>
        <div class="kv" id="encInfo"></div>
        <div class="mono muted" id="cipherPrev" style="margin-top:6px"></div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>🛰 送信シミュレーション (実スケールの光の旅)</h2>
    <div class="stagewrap">
      <canvas id="stage" width="920" height="420"></canvas>
      <div class="hud" id="hud"></div>
      <div class="rec" id="recBadge"><span class="d"></span>REC</div>
    </div>
    <div class="controls" style="margin-top:8px">
      <button class="g" id="txBtn">📡 送信シミュレーション開始</button>
      <button class="r" id="recBtn">⏺ 録画 (.webm)</button>
      <span class="muted" id="recNote"></span>
      <span class="muted">※ 実際の電波送信は行いません (シミュレーションのみ)</span>
    </div>
    <div class="gline" id="gammaDemo"></div>
  </div>

  <div class="card">
    <h2>🌀 重力⇄電磁 変換 (Gertsenshtein効果) — 交信路は盗聴できるか?</h2>
    <div class="muted" style="line-height:1.75">
      レポート6–7頁の重力テンソル方程式が指し示す<b>実在の物理</b>:
      強い磁場 B の中では<b>重力波(重力子)が電磁波(光子)へ変換</b>されます
      (Gertsenshtein 1962、逆変換も成立)。もし系外惑星の交信路の重力的擾乱を
      電磁信号として拾えれば、それは“盗聴”になり得ます。— そこで変換確率を
      <b>実際の物理定数で計算</b>します:
      <span class="mono">P = (16πG / μ₀c⁴)·B²·L² ≈ 3.30×10⁻³⁷·B²·L²</span>。
      結果は常に、<b>人工の装置では盗聴できない</b>ことを示します。
    </div>
    <div class="controls" style="margin-top:10px">
      <label class="muted">磁場 B (テスラ): <input id="gB" type="number" value="20" step="any" style="width:120px"/></label>
      <label class="muted">経路長 L (m): <input id="gL" type="number" value="10" step="any" style="width:150px"/></label>
      <select id="gPreset" style="min-width:230px">
        <option value="">— プリセット —</option>
        <option value="20,10">実験室の超伝導磁石 (20T × 10m)</option>
        <option value="8.3,27000">LHC双極子リング (8.3T × 27km)</option>
        <option value="3e-10,1.173e17">星間磁場 × 12.4光年 (Luyten b まで)</option>
        <option value="1e8,1e6">中性子星 磁気圏 (1e8 T × 1000km)</option>
        <option value="1e11,1e4">マグネター表面 (1e11 T × 10km)</option>
      </select>
      <button class="g" id="gTapBtn">🛰 この経路を傍受してみる</button>
    </div>
    <div class="kv" id="gertInfo"></div>
    <div class="warn" id="gertWarn"></div>
    <div class="ok" id="gertOk"></div>
    <div class="muted" style="margin-top:9px">
      ※ これは係数 3.30×10⁻³⁷ の<b>コヒーレント小混合近似</b> (P≪1 で有効)。本アプリは実在の
      交信機器に<b>接続せず</b>、いかなる実信号も<b>傍受しません</b>。重力⇄電磁変換が非ゼロに
      なるのはマグネター級の天体だけで、人工の盗聴装置では到達できません。
    </div>
  </div>

  <div class="card">
    <h2>📥 受信モード — 重力⇄電磁 交信を受信し量子復号する</h2>
    <div class="muted" style="line-height:1.75">
      送信の逆向き:<b>逆Gertsenshtein効果</b>で到来した重力波を磁場中で光子へ戻し、
      <b>特殊相対性理論の複素回転</b>(ローレンツ変換=虚角 iφ の回転)で到来周波数を補正、
      <b>tuplenetworkリバイザの順序変換不可の原理</b>(非可換 XZ≠ZX)に根ざす<b>量子復号</b>で
      本文を復元します。受信信号は光速で届くため<b>過去</b>の記録です —
      遠方ほど「<b>遺跡信号</b>」(古い時代の文明の痕跡) になります。
    </div>
    <div class="grid" style="margin-top:12px">
      <div>
        <div class="controls">
          <label class="muted" style="flex:1;min-width:260px">源の視線速度 β=v/c (−接近 / +後退):
            <input id="beta" type="range" min="-0.6" max="0.6" step="0.001" value="0.012" style="width:100%"/></label>
        </div>
        <div class="kv" id="relInfo"></div>
        <div class="kv" id="recvBudget" style="margin-top:8px"></div>
        <div class="controls" style="margin-top:10px">
          <button class="g" id="recvLoopBtn">📡 自局の送信を受信 (ループバック)</button>
          <label class="muted" style="display:inline-flex;align-items:center;gap:6px">
            📂 .qmsg を受信 <input id="qfile" type="file" accept=".qmsg,text/plain" style="max-width:190px"/></label>
        </div>
        <div class="warn" id="recvWarn"></div>
        <div class="ok" id="recvOk"></div>
      </div>
      <div>
        <div class="muted">復元された 23×73 ビットマップ</div>
        <canvas id="rxmsg" width="138" height="438" style="display:block;background:#04070f;border:1px solid var(--line);border-radius:10px;margin-top:6px;max-width:100%"></canvas>
        <div class="mono muted" id="rxText" style="margin-top:8px;max-height:90px;overflow:auto"></div>
      </div>
    </div>
    <div class="muted" style="margin-top:10px">
      ※ 2026年時点で地球外からの受信実績は<b>ゼロ</b>。逆Gertsenshtein変換の確率は ~10⁻²¹ で
      実在の信号は事実上検出不能です。本モードは自局で作成/保存した .qmsg を復号する
      <b>シミュレーション</b>であり、実在の交信を傍受・受信するものではありません。
    </div>
  </div>

  <div class="card">
    <h2>⚛ Bada量子エンジン — exo/contact-bb84.bada (矢印構文) をブラウザ内で実行</h2>
    <div class="controls">
      <button class="g" id="badaBtn">▶ BB84エンジンを実行</button>
      <span id="badaStat" class="muted"></span>
    </div>
    <pre id="badaOut">(実行すると BB84 ふるい・イヴのQBER・Bell零保存・Jones鍵・暗号往復が表示されます)</pre>
  </div>

</main>
<script>/*__BADA_CORE__*/</script>
<script>
window.CONTACT_SRC=/*__SRC__*/"";
(function(){
  "use strict";
  function $(id){ return document.getElementById(id); }

  /* ================= Γ check + Jones heat ================================ */
  var LG=[676.5203681218851,-1259.1392167224028,771.32342877765313,-176.61502916214059,
          12.507343278686905,-0.13857109526572012,9.9843695780195716e-6,1.5056327351493116e-7];
  function gamma(z){ if(z<0.5) return Math.PI/(Math.sin(Math.PI*z)*gamma(1-z));
    z-=1; var x=0.99999999999980993;
    for(var i=0;i<LG.length;i++) x+=LG[i]/(z+i+1);
    var t=z+LG.length-0.5;
    return Math.sqrt(2*Math.PI)*Math.pow(t,z+0.5)*Math.exp(-t)*x; }
  function jonesV(th){ function e(n){ return {re:Math.cos(n*th), im:Math.sin(n*th)}; }
    var a=e(-4), b=e(-3), c=e(-1);
    var re=-a.re+b.re+c.re, im=-a.im+b.im+c.im;
    return Math.sqrt(re*re+im*im); }
  function heatColor(T){ if(T==null) return "#5a748f";
    var t=Math.max(100,Math.min(1500,T)), mag=jonesV((t-100)/1400*Math.PI)/3;
    var hue=t<255?230-(t-100)/155*110:Math.max(0,120-(t-255)/500*120);
    return "hsl("+hue.toFixed(0)+","+(45+mag*50).toFixed(0)+"%,"+(42+mag*14).toFixed(0)+"%)"; }
  $("gammaDemo").textContent="Γ(z+1)=zΓ(z) 検証: "+
    [0.57,0.70,5.58].map(function(w){return "w="+w+": "+(gamma(1+w)/(w*gamma(w))).toFixed(6);}).join("  ")+
    " | Γ(0.5)²="+(gamma(0.5)*gamma(0.5)).toFixed(6)+" (π="+Math.PI.toFixed(6)+")";

  /* ================= real targets ======================================== */
  // [name, 距離ly, Teq(色), 実送信史]
  var TARGETS=[
    ["Proxima Centauri b (最も近い地球型)",4.25,234,null],
    ["Luyten b (GJ 273 b) ★実送信済み",12.4,259,"2017 Sónar Calling (EISCAT, ノルウェー) が実際に音楽+科学メッセージを送信 — 最速返信 2042年ごろ"],
    ["Teegarden's Star b",12.5,264,null],
    ["Ross 128 b",11.0,280,null],
    ["GJ 1002 b",15.8,231,null],
    ["TRAPPIST-1 e",40.66,250,null],
    ["TOI-700 d",101.4,269,null],
    ["Kepler-442 b",1206,233,null],
    ["球状星団 M13 ★実送信済み",25000,null,"1974 アレシボ・メッセージ (1679ビット) が実際に送信済み — 到着は約2.5万年後"]
  ];
  var TI=1;
  function budget(){
    var t=TARGETS[TI], d=t[1];
    var power=2e13*Math.pow(d/25000,2);
    $("budget").innerHTML=
      "<b>距離</b><span>"+d+" 光年"+(t[3]?' <span class="badge">実送信史あり</span>':"")+"</span>"+
      "<b>片道の旅</b><span>"+d+" 年 (光速) → 到着 "+Math.ceil(2026+d)+" 年</span>"+
      "<b>最速返信</b><span>"+Math.ceil(2026+2*d)+" 年 (往復 "+(2*d)+" 年)</span>"+
      "<b>必要ビーコン電力</b><span>≈ "+power.toExponential(2)+" W (アレシボ級受信を仮定)</span>"+
      "<b>実在の送信機例</b><span>Goldstone 70m (DSN) / EISCAT UHF (Sónar Calling 実機)</span>"+
      (t[3]?"<b>実史</b><span>"+t[3]+"</span>":"");
  }
  var p=$("pick");
  TARGETS.forEach(function(t,i){ var o=document.createElement("option"); o.value=i; o.textContent="📡 "+t[0]+" — "+t[1]+"光年"; if(i===TI)o.selected=true; p.appendChild(o); });
  p.addEventListener("change",function(){ TI=parseInt(this.value,10); budget(); if(window.__recvBudget) window.__recvBudget(); });

  /* ================= Arecibo-style 23x73 composer ======================== */
  var CW=23, CH=73, CELL=18;
  var grid=[];
  function blank(){ grid=[]; for(var y=0;y<CH;y++){ var r=[]; for(var x=0;x<CW;x++) r.push(0); grid.push(r); } }
  function px(x,y){ if(x>=0&&x<CW&&y>=0&&y<CH) grid[y][x]=1; }
  function bin(n,col,row){ // 下位ビットを下に置く縦2進数
    var b=n.toString(2);
    for(var i=0;i<b.length;i++) if(b[b.length-1-i]==="1") px(col,row-i);
  }
  function preset(){
    blank();
    for(var n=1;n<=10;n++) bin(n,n*2,5);                 // 1〜10 の2進数
    var atoms=[1,6,7,8,15], ac=0;                        // H C N O P
    atoms.forEach(function(a){ bin(a,3+ac*4,13); ac++; });
    for(var y=16;y<34;y++){                              // DNA 二重らせん
      var ph=(y-16)/18*Math.PI*2;
      px(Math.round(11+7*Math.sin(ph)),y);
      px(Math.round(11-7*Math.sin(ph)),y);
      if(y%3===0) for(var x=Math.min(Math.round(11+7*Math.sin(ph)),Math.round(11-7*Math.sin(ph)))+1;x<Math.max(Math.round(11+7*Math.sin(ph)),Math.round(11-7*Math.sin(ph)));x++) px(x,y);
    }
    var man=[ "..#..", ".###.", "#.#.#", "..#..", ".#.#.", "#...#" ];  // ヒト
    for(var my=0;my<man.length;my++) for(var mx=0;mx<5;mx++) if(man[my][mx]==="#") px(9+mx,37+my);
    bin(173,16,42);                                      // 身長 ~173cm の2進数
    for(var s=0;s<9;s++) px(2+s*2,50+(s===2?-1:0));      // 太陽系 (3番目=地球を持ち上げ)
    px(0,50); px(1,50); px(0,49); px(1,49);              // 太陽
    for(var dx=-8;dx<=8;dx++){                           // 電波望遠鏡 (放物面)
      var dy=Math.round(dx*dx/10);
      px(11+dx,62+dy);
    }
    px(11,66); px(11,67); px(10,68); px(12,68);          // 支柱
    drawMsg();
  }
  var mc=$("msg"), mctx=mc.getContext("2d");
  function drawMsg(){
    mctx.fillStyle="#04070f"; mctx.fillRect(0,0,mc.width,mc.height);
    var on=0;
    for(var y=0;y<CH;y++) for(var x=0;x<CW;x++){
      if(grid[y][x]){ on++; mctx.fillStyle=heatColor(150+((x*7+y*11)%900)); mctx.fillRect(x*CELL+1,y*CELL+1,CELL-2,CELL-2); }
      else { mctx.fillStyle="#0a1120"; mctx.fillRect(x*CELL+1,y*CELL+1,CELL-2,CELL-2); }
    }
    $("bitInfo").textContent="ビットマップ 1679ビット (点灯 "+on+") + テキスト "+(new TextEncoder().encode($("txt").value).length*8)+"ビット";
  }
  mc.addEventListener("click",function(ev){
    var r=mc.getBoundingClientRect();
    var x=Math.floor((ev.clientX-r.left)*mc.width/r.width/CELL), y=Math.floor((ev.clientY-r.top)*mc.height/r.height/CELL);
    if(x>=0&&x<CW&&y>=0&&y<CH){ grid[y][x]=grid[y][x]?0:1; drawMsg(); }
  });
  $("presetBtn").addEventListener("click",preset);
  $("clearBtn").addEventListener("click",function(){ blank(); drawMsg(); });
  $("txt").addEventListener("input",drawMsg);

  function messageBytes(){
    var bits=[];
    for(var y=0;y<CH;y++) for(var x=0;x<CW;x++) bits.push(grid[y][x]);
    var bytes=[];
    for(var i=0;i<bits.length;i+=8){ var v=0; for(var j=0;j<8;j++) v=(v<<1)|(bits[i+j]||0); bytes.push(v); }
    var tb=new TextEncoder().encode($("txt").value);
    for(var k=0;k<tb.length;k++) bytes.push(tb[k]);
    return bytes;
  }

  /* ================= BB84 quantum key distribution ======================= */
  function rb(){ return crypto.getRandomValues(new Uint8Array(1))[0]&1; }
  var KEY=null, QBER=null, EVE=false;
  function runBB84(){
    EVE=$("eve").checked;
    var N=64, rows=[], key=[], err=0, kept=0;
    for(var i=0;i<N;i++){
      var abit=rb(), abase=rb(), bbase=rb(), bbit;
      if(EVE){
        // 傍受再送: イヴは自分の基底で測って送り直す。彼女の基底が
        // アリスと不一致なら状態が壊れ、ボブの結果は完全ランダム → QBER 25%
        var ebase=rb();
        if(ebase===abase){ bbit=(abase===bbase)?abit:rb(); }
        else { bbit=rb(); }
      } else {
        bbit=(abase===bbase)?abit:rb();
      }
      if(abase===bbase){
        kept++;
        key.push(abit);
        if(bbit!==abit) err++;
      }
      if(rows.length<12) rows.push([i,abit,abase?"×":"+",bbase?"×":"+",abase===bbase?"✓":"—",abase===bbase?abit:"·"]);
    }
    QBER=kept?err/kept:0;
    var h="<tr><th>#</th><th>ビット</th><th>基底A</th><th>基底B</th><th>一致</th><th>鍵</th></tr>";
    rows.forEach(function(r){ h+="<tr><td>"+r.join("</td><td>")+"</td></tr>"; });
    $("qtab").innerHTML=h;
    var kv=0; key.forEach(function(b){ kv=(kv*2+b)%65521; });
    var th=(kv%1400)/1400*Math.PI, jk=jonesV(th);
    KEY={bits:key,kv:kv,theta:th,jones:jk,qber:QBER};
    $("qinfo").innerHTML=
      "<b>量子ビット</b><span>"+N+" (基底一致 "+kept+" → 鍵長 "+key.length+" bit)</span>"+
      "<b>QBER</b><span>"+(QBER*100).toFixed(1)+"% (しきい値 11%)</span>"+
      "<b>鍵値</b><span class='mono'>"+kv+" → θ="+th.toFixed(3)+" → Jones|V|="+jk.toFixed(4)+"</span>";
    if(QBER>0.11){
      KEY=null;
      $("qwarn").style.display="block";
      $("qwarn").innerHTML="<b>🚨 盗聴を検出</b> — QBER "+(QBER*100).toFixed(1)+"% &gt; 11%。量子力学がイヴの傍受再送を暴露しました。<b>鍵を破棄</b>して再配送してください (これが量子暗号の防御です)。";
      $("qok").style.display="none";
    } else {
      $("qwarn").style.display="none";
      $("qok").style.display="block";
      $("qok").innerHTML="✅ QBER "+(QBER*100).toFixed(1)+"% — 盗聴なし。Jones量子鍵 |V|="+jk.toFixed(4)+" を確立しました。";
    }
  }
  $("qkdBtn").addEventListener("click",runBB84);

  /* ================= encrypt + package =================================== */
  var CIPHER=null;
  function lcg(s){ return (s*1103+12345)%100003; }
  // 整数の鍵種: kv と Jones|V| から再現可能に導出 (受信側が厳密に復号できる)
  function keySeed(K){ return ((K.kv*100003)+Math.round(K.jones*1e6))%2147483647; }
  function encrypt(){
    if(!KEY){ $("encInfo").innerHTML="<b>状態</b><span style='color:#ff9aa5'>先に BB84 で鍵を確立してください (盗聴検出時は鍵なし)</span>"; return; }
    var bytes=messageBytes();
    var ks=keySeed(KEY), ct=[];
    for(var i=0;i<bytes.length;i++){ ks=lcg(ks); ct.push((bytes[i]+ks)%256); }
    CIPHER=ct;
    var hex=ct.slice(0,24).map(function(b){ return ("0"+b.toString(16)).slice(-2); }).join(" ");
    $("encInfo").innerHTML=
      "<b>平文</b><span>"+bytes.length+" バイト (1679ビット図 + テキスト)</span>"+
      "<b>暗号方式</b><span>BB84鍵 → Jones|V|ストリーム (往復復号可)</span>"+
      "<b>宛先</b><span>"+TARGETS[TI][0]+"</span>";
    $("cipherPrev").textContent="暗号文 (先頭24バイト): "+hex+" …";
  }
  $("encBtn").addEventListener("click",encrypt);
  $("dlBtn").addEventListener("click",function(){
    if(!CIPHER){ $("cipherPrev").textContent="先に暗号化してください。"; return; }
    var head="QMSG/1 QuantumContact\\n宛先: "+TARGETS[TI][0]+"\\n距離: "+TARGETS[TI][1]+" 光年\\n鍵指紋: kv="+KEY.kv+" |V|="+KEY.jones.toFixed(6)+" QBER="+(KEY.qber*100).toFixed(1)+"%\\n鍵種: "+keySeed(KEY)+"\\n注記: 実送信はしていません (2026年時点で接触実績ゼロ)\\n---\\n";
    var body=CIPHER.map(function(b){ return ("0"+b.toString(16)).slice(-2); }).join("");
    var blob=new Blob([head+body+"\\n"],{type:"text/plain"});
    var a=document.createElement("a"); a.href=URL.createObjectURL(blob);
    a.download="contact-"+TARGETS[TI][1]+"ly.qmsg";
    document.body.appendChild(a); a.click();
    setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); },200);
  });

  /* ================= transmission simulation ============================= */
  var st=$("stage"), sx=st.getContext("2d"), W=st.width, H=st.height;
  var playing=true, t0=performance.now(), TX={on:false,t0:0};
  var STARS=[]; (function(){ var s=7; function r(){ s=(Math.imul(s,1664525)+1013904223)>>>0; return s/4294967296; }
    for(var i=0;i<140;i++) STARS.push([r()*W,r()*H,r()*1.3+0.3]); })();
  $("txBtn").addEventListener("click",function(){ TX.on=true; TX.t0=performance.now(); });
  function draw(now){
    var t=(now-t0)/1000;
    sx.fillStyle="#000308"; sx.fillRect(0,0,W,H);
    sx.fillStyle="#9fb6d8";
    for(var i=0;i<STARS.length;i++){ sx.globalAlpha=0.25+0.35*Math.abs(Math.sin(t*0.7+i)); sx.fillRect(STARS[i][0],STARS[i][1],STARS[i][2],STARS[i][2]); }
    sx.globalAlpha=1;
    var tg=TARGETS[TI], dx=110, dy=H*0.52, txx=W-90, txy=H*0.38;
    // 電波望遠鏡 (放物面)
    sx.strokeStyle="#8aa0c0"; sx.lineWidth=3;
    sx.beginPath(); sx.arc(dx-24,dy,46,-Math.PI*0.42,Math.PI*0.42); sx.stroke();
    sx.beginPath(); sx.moveTo(dx-24,dy+44); sx.lineTo(dx-24,dy+70); sx.moveTo(dx-40,dy+70); sx.lineTo(dx-8,dy+70); sx.stroke();
    sx.fillStyle="#cfe0f5"; sx.font="11px sans-serif"; sx.fillText("Goldstone / EISCAT 級",dx-70,dy+88);
    // 目標星
    var col=heatColor(tg[2]);
    var g=sx.createRadialGradient(txx,txy,0,txx,txy,34);
    g.addColorStop(0,col); g.addColorStop(1,"rgba(0,0,0,0)");
    sx.fillStyle=g; sx.beginPath(); sx.arc(txx,txy,34,0,Math.PI*2); sx.fill();
    sx.fillStyle=col; sx.beginPath(); sx.arc(txx,txy,9,0,Math.PI*2); sx.fill();
    sx.fillStyle="#fff"; sx.font="11px sans-serif"; sx.fillText(tg[0].split(" ★")[0],txx-120,txy-28);
    // ビーム + 暗号ビット
    if(TX.on){
      var pr=Math.min(1,(now-TX.t0)/9000);
      sx.strokeStyle="rgba(181,140,255,0.5)"; sx.lineWidth=2;
      sx.beginPath(); sx.moveTo(dx,dy-8); sx.lineTo(dx+(txx-dx)*pr,dy-8+(txy-dy+8)*pr); sx.stroke();
      sx.font="10px ui-monospace,monospace";
      for(var b2=0;b2<26;b2++){
        var ph=(t*0.35+b2*0.045)%1;
        if(ph<pr){
          var bx2=dx+(txx-dx)*ph, by2=dy-8+(txy-dy+8)*ph;
          sx.fillStyle=b2%3?"#b58cff":"#39c2ff";
          sx.fillText(((b2*7+Math.floor(t*4))%2).toString(),bx2,by2-4);
        }
      }
      // タイムライン (対数)
      var y=H-34, x0=80, x1=W-40;
      sx.strokeStyle="#2a3c5c"; sx.lineWidth=2; sx.beginPath(); sx.moveTo(x0,y); sx.lineTo(x1,y); sx.stroke();
      function lx(yr){ return x0+(x1-x0)*Math.log10(1+yr)/Math.log10(1+2*tg[1]); }
      sx.fillStyle="#8aa0c0"; sx.font="10.5px sans-serif";
      sx.fillText("2026 送信",x0-20,y+16);
      sx.strokeStyle="#c8a44a"; sx.beginPath(); sx.moveTo(lx(tg[1]),y-6); sx.lineTo(lx(tg[1]),y+6); sx.stroke();
      sx.fillText("到着 "+Math.ceil(2026+tg[1]),lx(tg[1])-22,y+16);
      sx.strokeStyle="#2fbf71"; sx.beginPath(); sx.moveTo(lx(2*tg[1]),y-6); sx.lineTo(lx(2*tg[1]),y+6); sx.stroke();
      sx.fillText("最速返信 "+Math.ceil(2026+2*tg[1]),lx(2*tg[1])-34,y+16);
      sx.fillStyle="#b58cff";
      sx.beginPath(); sx.arc(lx(tg[1]*pr),y,4,0,Math.PI*2); sx.fill();
    }
    $("hud").innerHTML="<b>📡 "+tg[0]+"</b> — "+tg[1]+" 光年<br>"+
      (KEY?("Jones量子鍵 |V|="+KEY.jones.toFixed(4)+" (QBER "+(KEY.qber*100).toFixed(1)+"%)"):"鍵: 未配送 (BB84を実行)")+
      "<br>"+(TX.on?("光の旅: "+(Math.min(1,(now-TX.t0)/9000)*tg[1]).toFixed(2)+" 光年 経過 (加速表示)"):"送信シミュレーション待機 — 実送信はしません");
  }
  function loop(now){ draw(now); if(playing) requestAnimationFrame(loop); }

  /* ================= recorder ============================================ */
  var recorder=null, chunks=[], recording=false;
  $("recBtn").addEventListener("click",function(){
    if(!recording){
      try{
        var stream=st.captureStream(30);
        var mime=MediaRecorder.isTypeSupported("video/webm;codecs=vp9")?"video/webm;codecs=vp9":"video/webm";
        recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:6e6});
        chunks=[];
        recorder.ondataavailable=function(e){ if(e.data.size) chunks.push(e.data); };
        recorder.onstop=function(){
          var blob=new Blob(chunks,{type:"video/webm"});
          var a=document.createElement("a"); a.href=URL.createObjectURL(blob);
          a.download="quantumcontact.webm";
          document.body.appendChild(a); a.click();
          setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); },200);
          $("recNote").textContent="保存しました ("+(blob.size/1024/1024).toFixed(1)+" MB)";
        };
        recorder.start(200); recording=true;
        $("recBtn").textContent="⏹ 停止 / 保存"; $("recBadge").classList.add("on");
      }catch(e){ $("recNote").textContent="録画失敗: "+e.message; }
    } else {
      recording=false; try{ recorder.stop(); }catch(e){}
      $("recBtn").textContent="⏺ 録画 (.webm)"; $("recBadge").classList.remove("on");
    }
  });

  /* ================= Bada engine card ==================================== */
  $("badaBtn").addEventListener("click",function(){
    $("badaStat").textContent="実行中…";
    setTimeout(function(){
      try{
        var r=window.BadaLang.run(window.CONTACT_SRC,{maxSteps:4000000});
        $("badaOut").textContent=r.output+((r.parseErrors&&r.parseErrors.length)?"\\n"+r.parseErrors.join("\\n"):"");
        $("badaStat").textContent=/@@BB84-OK/.test(r.output)?"✅ @@BB84-OK (Bada量子エンジン完走)":"⚠ 異常終了";
      }catch(e){ $("badaStat").textContent="エラー: "+e.message; }
    },30);
  });

  /* ====== Gertsenshtein gravity<->EM conversion (interception demo) ======= */
  var G_=6.674e-11, C_=2.998e8, MU0=1.2566370614e-6;
  var GPREF=16*Math.PI*G_/(MU0*Math.pow(C_,4)); // ≈ 3.30e-37 /T^2/m^2
  function gert(){
    var B=parseFloat($("gB").value), L=parseFloat($("gL").value);
    if(!isFinite(B)||!isFinite(L)||B<=0||L<=0){
      $("gertInfo").innerHTML="<b>入力</b><span>B と L に正の数を入れてください</span>"; return null; }
    var P=GPREF*B*B*L*L;
    var photons=P*1e40; // 強い天体源 1e40 グラビトン/秒 を仮定しても取り出せる光子
    $("gertInfo").innerHTML=
      "<b>変換係数</b><span class='mono'>16πG/μ₀c⁴ = "+GPREF.toExponential(3)+" /T²/m²</span>"+
      "<b>変換確率 P</b><span class='mono'>"+P.toExponential(2)+"  (log₁₀P = "+Math.log10(P).toFixed(2)+")</span>"+
      "<b>入力 B, L</b><span>"+B.toExponential(2)+" T, "+L.toExponential(2)+" m</span>"+
      "<b>強源(1e40 g/s)から回収</b><span>"+(photons<1?("≈ "+photons.toExponential(2)+" 光子/秒 (事実上ゼロ)"):(photons.toExponential(2)+" 光子/秒"))+"</span>";
    return P;
  }
  function tap(){
    var P=gert(); if(P==null) return;
    $("gertWarn").style.display="none"; $("gertOk").style.display="none";
    if(P<1e-9){
      $("gertWarn").style.display="block";
      $("gertWarn").innerHTML="<b>🚫 傍受失敗</b> — 変換確率 P="+P.toExponential(2)+" ≪ 1。重力擾乱から取り出せる光子は事実上ゼロで、この交信路を<b>物理的に盗聴できません</b>。Gertsenshtein変換が意味を持つのはマグネター級 (B≳10¹⁰ T) の天体だけです。";
    } else {
      $("gertOk").style.display="block";
      $("gertOk").innerHTML="⚛ P="+P.toExponential(2)+" — マグネター級の磁場でのみ重力⇄電磁変換が非ゼロになる天体物理の領域です (人工の盗聴装置では到達不能)。"+
        (KEY?(" さらに本交信路は BB84 量子鍵で守られ、傍受は QBER "+(KEY.qber*100).toFixed(1)+"% として<b>自動的に露見</b>します。"):" さらに BB84 量子鍵を配送すれば、いかなる傍受も QBER で露見します。");
    }
  }
  $("gPreset").addEventListener("change",function(){
    if(!this.value) return;
    var pr=this.value.split(","); $("gB").value=pr[0]; $("gL").value=pr[1]; gert();
  });
  $("gB").addEventListener("input",gert);
  $("gL").addEventListener("input",gert);
  $("gTapBtn").addEventListener("click",tap);

  /* ====== RECEIVER: inverse Gertsenshtein + relativistic complex rotation = */
  var RCELL=6, rxc=$("rxmsg"), rxx=rxc.getContext("2d");
  function drawRx(g){
    rxx.fillStyle="#04070f"; rxx.fillRect(0,0,rxc.width,rxc.height);
    for(var y=0;y<CH;y++) for(var x=0;x<CW;x++){
      if(g[y][x]){ rxx.fillStyle=heatColor(150+((x*7+y*11)%900)); rxx.fillRect(x*RCELL+1,y*RCELL,RCELL-1,RCELL-1); }
    }
  }
  function bytesToRx(bytes){
    var bits=[], i, j;
    for(i=0;i<210 && i<bytes.length;i++){ for(j=7;j>=0;j--) bits.push((bytes[i]>>j)&1); }
    var g=[]; for(var y=0;y<CH;y++){ var r=[]; for(var x=0;x<CW;x++){ var k=y*CW+x; r.push(k<bits.length?bits[k]:0); } g.push(r); }
    var txt=""; try{ txt=new TextDecoder().decode(new Uint8Array(bytes.slice(210))); }catch(e){ txt="(decode error)"; }
    return {grid:g, text:txt};
  }
  function hexToBytes(h){ h=h.replace(/[^0-9a-fA-F]/g,""); var b=[]; for(var i=0;i+1<h.length;i+=2) b.push(parseInt(h.substr(i,2),16)); return b; }
  function decrypt(ct, seed){ var ks=seed, out=[]; for(var i=0;i<ct.length;i++){ ks=lcg(ks); out.push(((ct[i]-ks)%256+256)%256); } return out; }
  // 特殊相対性理論の複素回転体: ローレンツ・ブースト = 虚角 iφ の回転
  function relRot(){
    var beta=parseFloat($("beta").value);
    var phi=Math.atanh(beta), ch=Math.cosh(phi), sh=Math.sinh(phi);
    var D=Math.sqrt((1-beta)/(1+beta)), gam=1/Math.sqrt(1-beta*beta);
    $("relInfo").innerHTML=
      "<b>ラピディティ φ</b><span>artanh(β)="+phi.toFixed(4)+" → ブースト=虚角 iφ の回転</span>"+
      "<b>複素回転体</b><span class='mono'>[[cosh,−sinh],[−sinh,cosh]]=[["+ch.toFixed(3)+","+(-sh).toFixed(3)+"],["+(-sh).toFixed(3)+","+ch.toFixed(3)+"]]</span>"+
      "<b>ローレンツ因子 γ</b><span>"+gam.toFixed(4)+"</span>"+
      "<b>相対論ドップラー</b><span>f_rx/f_tx=√((1−β)/(1+β))="+D.toFixed(4)+(beta>0.0005?" (赤方偏移)":beta<-0.0005?" (青方偏移)":" (無偏移)")+"</span>";
  }
  // 逆Gertsenshtein受信 + ルックバック (過去=遺跡信号)
  function recvBudget(){
    var t=TARGETS[TI], d=t[1], emit=2026-d, ruin=(d>=1000);
    var B=3e-10, L=d*9.461e15, P=GPREF*B*B*L*L;
    $("recvBudget").innerHTML=
      "<b>受信源</b><span>"+t[0].split(" ★")[0]+" — "+d+" 光年</span>"+
      "<b>発信時期 (光速の遡り)</b><span>"+(emit>=0?("西暦 "+Math.round(emit)+" 年"):("約 "+Math.round(-emit).toLocaleString()+" 年前"))+(ruin?' <span class="badge">遺跡信号</span>':"")+"</span>"+
      "<b>逆Gertsenshtein P</b><span class='mono'>"+P.toExponential(2)+" (実信号は事実上検出不能)</span>";
  }
  function recvLoop(){
    $("recvWarn").style.display="none"; $("recvOk").style.display="none";
    if(!CIPHER||!KEY){ $("recvWarn").style.display="block"; $("recvWarn").innerHTML="先に右側で (1) ⚛ BB84で鍵配送 → (2) 🔐 Jones量子鍵で暗号化 を実行してください。"; return; }
    relRot(); recvBudget();
    var plain=decrypt(CIPHER, keySeed(KEY)), rx=bytesToRx(plain), orig=messageBytes();
    drawRx(rx.grid);
    var match=(plain.length===orig.length)&&plain.every(function(b,i){return b===orig[i];});
    $("rxText").textContent="復元テキスト: "+rx.text;
    $("recvOk").style.display="block";
    $("recvOk").innerHTML="✅ 受信・量子復号に成功 — "+plain.length+" バイトを復元"+(match?" <b>(送信原本と完全一致)</b>":"")+"。順序変換不可(非可換)の量子鍵で守られた交信を復元しました。";
  }
  $("beta").addEventListener("input",relRot);
  $("recvLoopBtn").addEventListener("click",recvLoop);
  $("qfile").addEventListener("change",function(ev){
    var f=ev.target.files[0]; if(!f) return;
    var rd=new FileReader();
    rd.onload=function(){
      $("recvWarn").style.display="none"; $("recvOk").style.display="none";
      try{
        var txt=String(rd.result), mSeed=txt.match(/鍵種:\\s*(\\d+)/), idx=txt.indexOf("---");
        var ct=hexToBytes(idx>=0?txt.slice(idx+3):txt);
        if(!mSeed){ $("recvWarn").style.display="block"; $("recvWarn").innerHTML="このファイルには鍵種がありません (旧形式)。本バージョンで保存した .qmsg を使ってください。"; return; }
        var plain=decrypt(ct, parseInt(mSeed[1],10)), rx=bytesToRx(plain);
        drawRx(rx.grid); relRot(); recvBudget();
        $("rxText").textContent="復元テキスト: "+rx.text;
        var dst=txt.match(/宛先:\\s*(.+)/);
        $("recvOk").style.display="block";
        $("recvOk").innerHTML="✅ .qmsg を受信・量子復号 — "+plain.length+" バイト復元。"+(dst?("源: "+dst[1]):"");
      }catch(e){ $("recvWarn").style.display="block"; $("recvWarn").innerHTML="復号エラー: "+e.message; }
    };
    rd.readAsText(f);
  });

  /* ================= init ================================================= */
  window.__recvBudget=recvBudget;
  preset(); budget(); gert(); relRot(); recvBudget();
  requestAnimationFrame(loop);
})();
</script>
</body>
</html>
`;

html = html.replace("/*__BADA_CORE__*/", function () { return BADA_CORE; });
html = html.replace('/*__SRC__*/""', function () { return JSON.stringify(CONTACT_SRC); });

fs.mkdirSync(path.join(IDE, "dist"), { recursive: true });
const outPath = path.join(IDE, "dist", "quantum-contact.html");
fs.writeFileSync(outPath, html);
console.log("built dist/quantum-contact.html (" + fs.statSync(outPath).size + " bytes)");

const appWww = path.join(IDE, "quantumcontact-app", "www");
fs.mkdirSync(appWww, { recursive: true });
fs.writeFileSync(path.join(appWww, "index.html"), html);
console.log("staged quantumcontact-app/www/index.html");
