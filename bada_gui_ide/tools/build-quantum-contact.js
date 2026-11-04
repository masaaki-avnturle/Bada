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
  if (!res.ok || (res.parseErrors && res.parseErrors.length) || !/@@BB84-OK/.test(res.output)) {
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
  p.addEventListener("change",function(){ TI=parseInt(this.value,10); budget(); });

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
  function encrypt(){
    if(!KEY){ $("encInfo").innerHTML="<b>状態</b><span style='color:#ff9aa5'>先に BB84 で鍵を確立してください (盗聴検出時は鍵なし)</span>"; return; }
    var bytes=messageBytes();
    var ks=KEY.kv+KEY.jones*1000, ct=[];
    for(var i=0;i<bytes.length;i++){ ks=lcg(ks); ct.push((bytes[i]+Math.floor(ks))%256); }
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
    var head="QMSG/1 QuantumContact\\n宛先: "+TARGETS[TI][0]+"\\n距離: "+TARGETS[TI][1]+" 光年\\n鍵指紋: kv="+KEY.kv+" |V|="+KEY.jones.toFixed(6)+" QBER="+(KEY.qber*100).toFixed(1)+"%\\n注記: 実送信はしていません (2026年時点で接触実績ゼロ)\\n---\\n";
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

  /* ================= init ================================================= */
  preset(); budget();
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
