/*
 * engine-test.js — Laevateinn (自動走行アシスタント「アル」) のエンジン単体テスト
 *
 *   node laevateinn/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブして
 * 純ロジック部分を検証します:
 *   1. A* 経路計画 — 道路網上の連結経路
 *   2. アルのトランスフォーマー知覚 — 前方障害物への attention 集中 /
 *      無障害時ゼロ脅威 / attention の softmax 正規化
 *   3. Web地図モード測位 (衛星不使用) — 推測航法のドリフトと
 *      ランドマーク補正による吸着
 *   4. 人工衛星モード測位 — 擬似距離の最小二乗トリラテレーション
 *   5. 地図タイル AEAD — 封緘/開封の往復 (CJK 含む) と改ざん拒否
 *   6. アル (意図エンジン) の応答 / トランスフォーマー制御ヘッド / 車両運動
 *   7. ELM327 (OBD-II) — 外気温 PID 0146 (車の温度計) を含む
 *   8. ガンマ関数・大域的部分積分多様体エントロピー Ξ
 *   9. 熱画像知覚 (赤外線カメラ × 温度計) と 16 レイ融合
 *  10. サイレントトーク (口形 → 口形素 → 走行コマンド) と安全ゲート
 *  11. 目的地リンク (AEAD 封筒 / 地名・座標の解析 / 改ざん拒否)
 *  12. 完全自動走行ミッション (受理 → 計画 → 封鎖・再計画 → 到着 → 次へ / 緊急停止)
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

function stubEl(){
  return new Proxy({ style: {}, classList: { add(){}, remove(){}, toggle(){} }, value: "", textContent: "", innerHTML: "",
                     children: [], width: 720, height: 540 }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "querySelector" || p === "appendChild" || p === "createElement" ||
          p === "getContext" || p === "removeChild") return function(){ return stubEl(); };
      if (p === "addEventListener" || p === "removeEventListener" || p === "focus" ||
          p === "getBoundingClientRect") return function(){ return { left: 0, top: 0, width: 720, height: 540 }; };
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const sandbox = {
  console, Math, Proxy, String, Number, Object, Array, JSON,
  setTimeout: function(fn){ fn(); }, setInterval: function(){ return 0; }, clearInterval: function(){},
  requestAnimationFrame: function(){},
  document: { getElementById(){ return stubEl(); }, createElement(){ return stubEl(); },
              querySelectorAll(){ return []; }, addEventListener(){}, removeEventListener(){} },
  window: {}
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });
const G = function(name){ return vm.runInContext(name, sandbox); };
function assert(cond, msg){ if (!cond){ console.error("FAIL: " + msg); process.exit(1); } console.log("ok - " + msg); }

/* 1. A* 経路計画 */
const route = G("planRoute")([0, 0], [11, 8]);
assert(Array.isArray(route) && route.length > 10, "A* finds a route from (0,0) to (11,8)");
let contiguous = true, onRoad = true;
for (let i = 0; i < route.length; i++){
  if (!G("isRoad")(route[i][0], route[i][1])) onRoad = false;
  if (i > 0 && Math.abs(route[i][0] - route[i-1][0]) + Math.abs(route[i][1] - route[i-1][1]) !== 1) contiguous = false;
}
assert(onRoad && contiguous, "the route stays on roads and moves one cell at a time");
assert(G("planRoute")([1, 0], [1, 0]) !== null && G("planRoute")([0, 0], [5, 1]) === null, "A* rejects off-road destinations");

/* 2. トランスフォーマー知覚 */
const empty = [];
for (let i = 0; i < 16; i++) empty.push({ dist: 9999, type: "none" });
const calm = G("alPerceive")(empty);
assert(calm.threat === 0, "no obstacles -> zero threat");
const front = empty.map(function(r){ return { dist: r.dist, type: r.type }; });
front[8] = { dist: 25, type: "car" };
const alert = G("alPerceive")(front);
assert(alert.threat > 0.5, "a close car dead ahead -> high threat (" + alert.threat.toFixed(2) + ")");
assert(alert.focus === 8, "attention focuses on the front ray (focus=" + alert.focus + ")");
let sum = 0;
for (const w of alert.attn) sum += w;
assert(Math.abs(sum - 1) < 1e-9, "attention weights are a softmax distribution (sum=1)");

/* 3. Web地図モード (衛星不使用): 推測航法 + ランドマーク補正 */
const rnd = G("lvRand")(123);
let est = { x: 30, y: 30 };
for (let i = 0; i < 200; i++) est = G("deadReckonStep")(est, 0, 10, 0.05, rnd);
const trueEnd = { x: 30 + 10 * 0.05 * 200, y: 30 };
const driftErr = Math.hypot(est.x - trueEnd.x, est.y - trueEnd.y);
assert(driftErr > 0.5, "dead reckoning accumulates drift without fixes (" + driftErr.toFixed(1) + " m)");
const fix = G("landmarkFix")(est, { x: 30, y: 30 }, 60);   /* (0,0) は 'L' ランドマーク */
assert(fix.fixed && fix.x === 30 && fix.y === 30, "a landmark intersection snaps the estimate to the known map position");
const nofix = G("landmarkFix")(est, { x: 90, y: 30 }, 60); /* (1,0) は '#' 道路 (非ランドマーク) */
assert(!nofix.fixed, "plain road cells do not snap");

/* 4. 人工衛星モード: トリラテレーション */
const exact = G("gnssFix")({ x: 333, y: 222 }, 0, null);
assert(Math.hypot(exact.x - 333, exact.y - 222) < 0.5, "noise-free satellite fix converges to the true position");
const noisy = G("gnssFix")({ x: 333, y: 222 }, 6, G("lvRand")(7));
assert(Math.hypot(noisy.x - 333, noisy.y - 222) < 30, "noisy satellite fix stays within GNSS-like error");

/* 5. 地図タイル AEAD */
const key = G("lvHash")("laevateinn-map.or.jp");
const env = G("mapSeal")("tile-0-0|L###|#..#|#..# こんにちは", key, 99);
assert(G("mapOpen")(env, key) === "tile-0-0|L###|#..#|#..# こんにちは", "map tile envelope round-trips (CJK preserved)");
env.ct[0] = (env.ct[0] + 1) % 65536;
assert(G("mapOpen")(env, key) === null, "a tampered tile is rejected (AEAD tag mismatch)");
const t00 = G("tileReceive")(G("tileEnvelope")(0, 0));
assert(t00 && t00.id === "tile-0-0" && t00.rows.length === 3 && t00.rows[0] === "L###",
       "website tile delivery decodes to the road map rows");

/* 6. アル (意図エンジン) */
assert(/衛星は使っていません/.test(G("alReply")("状態", { mode: "web", x: 1, y: 2, speed: 3, err: 1.5, tiles: 9 })),
       "Al reports web-map mode as satellite-free positioning");
assert(/人工衛星/.test(G("alReply")("状態", { mode: "sat", x: 1, y: 2, speed: 3, err: 1.5, tiles: 9 })),
       "Al reports satellite mode");
assert(/停止/.test(G("alReply")("停止して", {})), "Al acknowledges a stop command");
assert(/アル/.test(G("alReply")("あなたはだれ?", {})), "Al introduces itself");

/* 6b. トランスフォーマー制御ヘッド — 車両の操縦 */
const clearRays = [];
for (let i = 0; i < 16; i++) clearRays.push({ dist: 9999, type: "none" });
/* 目標が正面 → 直進・加速 */
const cStraight = G("alControl")(clearRays, 0);
assert(Math.abs(cStraight.steer) < 0.05 && cStraight.throttle > 0.8, "control: clear road, goal ahead -> ~straight, accelerate");
/* 目標が左 (負の bearing) → 左へ操舵 */
const cLeft = G("alControl")(clearRays, -0.8);
assert(cLeft.steer < -0.1, "control: goal to the left -> steer left (negative)");
const cRight = G("alControl")(clearRays, 0.8);
assert(cRight.steer > 0.1, "control: goal to the right -> steer right (positive)");
/* 正面に障害物 → 制動 (throttle 負) */
const frontObs = clearRays.map(function(r){ return { dist: r.dist, type: r.type }; });
frontObs[8] = { dist: 22, type: "car" };
const cBrake = G("alControl")(frontObs, 0);
assert(cBrake.throttle < 0, "control: obstacle dead ahead -> brake (throttle<0)");
/* 右前方に障害物・目標は正面 → 左へ回避操舵 */
const rightObs = clearRays.map(function(r){ return { dist: r.dist, type: r.type }; });
rightObs[10] = { dist: 30, type: "walker" };
const cAvoid = G("alControl")(rightObs, 0);
assert(cAvoid.steer < -0.02, "control: obstacle on the right -> steer away to the left");
/* steer は ±maxSteer に飽和 */
const cSat = G("alControl")(clearRays, 3.0);
assert(Math.abs(cSat.steer) <= 0.6 + 1e-9, "control: steering saturates at +/- maxSteer");

/* 6c. 車両運動モデル — 制御出力が実際に車体を動かす */
let car = { x: 100, y: 100, heading: 0, speed: 0 };
for (let i = 0; i < 40; i++) car = G("carStep")(car, { steer: 0, throttle: 1 }, 0.05);
assert(car.speed > 20 && car.x > 100 && Math.abs(car.y - 100) < 1, "kinematics: throttle+straight accelerates forward along x");
const before = car.heading;
for (let i = 0; i < 20; i++) car = G("carStep")(car, { steer: 0.6, throttle: 1 }, 0.05);
assert(car.heading > before + 0.1, "kinematics: positive steer turns heading (right/CW in screen space)");
let braking = { x: 0, y: 0, heading: 0, speed: 40 };
for (let i = 0; i < 40; i++) braking = G("carStep")(braking, { steer: 0, throttle: -1 }, 0.05);
assert(braking.speed < 1, "kinematics: full brake brings the car to a stop");
const parked = G("carStep")({ x: 0, y: 0, heading: 0, speed: 0 }, { steer: 0.6, throttle: 0 }, 0.05);
assert(Math.abs(parked.heading) < 1e-6, "kinematics: steering has little effect at a standstill (speed-dependent)");

/* 7. 実車接続 — ELM327 (OBD-II) プロトコルエンジン */
const P = G("elmParseLine");
assert(P("41 0D 3C").type === "speed" && P("41 0D 3C").kmh === 60, "ELM: '41 0D 3C' -> 60 km/h");
assert(P("410C1AF8").type === "rpm" && P("410C1AF8").rpm === 1726, "ELM: '410C1AF8' -> 1726 rpm");
assert(P("41 05 5A").type === "coolant" && P("41 05 5A").c === 50, "ELM: '41 05 5A' -> coolant 50°C");
assert(P("41 46 3A").type === "ambient" && P("41 46 3A").c === 18, "ELM: '41 46 3A' -> ambient air 18°C (PID 0146)");
assert(P("12.6V").type === "volt" && P("12.6V").v === 12.6, "ELM: 'ATRV' reply '12.6V' -> battery voltage");
assert(P("NO DATA").type === "nodata" && P("UNABLE TO CONNECT").type === "nodata", "ELM: NO DATA / UNABLE TO CONNECT are flagged");
assert(P("010D").type === "echo" && P("ATZ").type === "echo", "ELM: command echoes are ignored as echo");
assert(P("ELM327 v1.5").type === "ok", "ELM: version banner is acknowledged");

const writes = [];
const telemetry = [];
const states = [];
const Session = G("ElmSession");
const sess = new Session(function(c){ writes.push(c.trim()); }, function(ev){ telemetry.push(ev); }, function(st){ states.push(st); });
sess.start();
assert(writes.join(",") === "ATZ", "ELM session: starts with ATZ reset");
sess.feed("ELM327 v1.5\r\r>");
sess.feed("OK\r>");   /* ATE0 */
sess.feed("OK\r>");   /* ATL0 */
sess.feed("OK\r>");   /* ATS0 */
sess.feed("OK\r>");   /* ATSP0 */
assert(writes.join(",") === "ATZ,ATE0,ATL0,ATS0,ATSP0,010D",
       "ELM session: full init sequence then first speed poll");
assert(states.indexOf("ready") >= 0, "ELM session: reports ready after init");
sess.feed("41 0D 28\r>");                       /* 40 km/h */
sess.feed("41 0C 0F A0\r>");                    /* 1000 rpm */
sess.feed("41 05 46\r>");                       /* 30°C */
sess.feed("41 46 3C\r>");                       /* 外気温 20°C */
sess.feed("12.4V\r>");
assert(writes[writes.length - 1] === "010D" && writes.length === 11,
       "ELM session: poll cycle wraps around (010D 010C 0105 0146 ATRV -> 010D)");
const amb = telemetry.filter(function(e){ return e.type === "ambient"; });
assert(amb.length === 1 && amb[0].c === 20, "ELM session: ambient air temperature (PID 0146, the car's thermometer) 20°C delivered");
const spd = telemetry.filter(function(e){ return e.type === "speed"; });
const rpm = telemetry.filter(function(e){ return e.type === "rpm"; });
assert(spd.length === 1 && spd[0].kmh === 40, "ELM session: telemetry speed 40 km/h delivered");
assert(rpm.length === 1 && rpm[0].rpm === 1000, "ELM session: telemetry 1000 rpm delivered");
sess.feed("41 0D");        /* 分割パケット前半 */
sess.feed(" 50\r>");       /* 後半 — 結合して 80 km/h */
const spd2 = telemetry.filter(function(e){ return e.type === "speed"; });
assert(spd2.length === 2 && spd2[1].kmh === 80, "ELM session: split BLE packets are reassembled (80 km/h)");

/* 8. ガンマ関数・大域的部分積分多様体エントロピー Ξ */
const Gm = G("lvGamma"), Bt = G("lvBeta"), MI = G("manifoldInvariant");
assert(Math.abs(Gm(5) - 24) < 1e-9 && Math.abs(Gm(0.5) - Math.sqrt(Math.PI)) < 1e-12, "Gamma (Lanczos): Γ(5)=24, Γ(1/2)=√π");
assert(Math.abs(Gm(0.25) * Gm(0.75) - Math.PI / Math.sin(Math.PI / 4)) < 1e-9, "Gamma reflection formula Γ(x)Γ(1-x)=π/sin(πx)");
assert(Math.abs(Bt(2, 3) - 1 / 12) < 1e-12, "Beta: B(2,3) = 1/12");
assert(Math.abs(G("zetaGauge")(2, 3, Math.E) - 1 / 12) < 1e-12, "zeta gauge = B(p,q)/log x");
assert(Math.abs(G("manifoldElement")(Math.E) - 1 / (Math.E * Math.E)) < 1e-12 && G("manifoldElement")(1) === 1,
       "manifold element dμ = 1/(x log x)^2 (safe at x<=1)");
const uni = MI([10, 10, 10, 10]), peak = MI([40, 0, 0, 0]);
assert(Math.abs(uni.H - 2) < 1e-12 && peak.H === 0, "manifold invariant: Shannon H of a uniform 4-bin measure = 2 bit, a delta = 0");
assert(Math.abs(uni.xi - G("zetaGauge")(uni.H + 1, uni.M + 1, 41)) < 1e-15 && uni.xi > 0,
       "manifold invariant: Xi = zeta_gauge(H+1, M+1, N+1)");
/* Ruby 実装 (bada_ruby Manifold.invariant) と同じ値になること: 分布 [0.5,0.25,0.25], N=4 */
const rb = MI([2, 1, 1]);
const expM = 0.5 / Math.pow(2 * Math.log(2), 2) + 0.25 / Math.pow(3 * Math.log(3), 2) + 0.25 / Math.pow(4 * Math.log(4), 2);
assert(Math.abs(rb.H - 1.5) < 1e-12 && Math.abs(rb.M - expM) < 1e-12, "manifold invariant matches the Ruby definition (H=1.5, M=Σp·dμ(rank+2))");

/* 9. 熱画像知覚 — 赤外線カメラ × 温度計 */
const TW = 64, TH_ = 48;
assert(G("angleToRay")(0) === 8 && G("angleToRay")(-0.05) === 7, "thermal: straight ahead maps to the front rays 7/8");
const d0 = 60, row = G("thermalDistRow")(d0, TH_);
assert(Math.abs(G("thermalRowDist")(row, TH_) - d0) < 4, "thermal: ground-plane row <-> distance mapping round-trips");
const quiet = G("thermalAnalyze")(G("thermalSynth")({ x: 0, y: 0, heading: 0 }, [], 20, TW, TH_, G("lvRand")(1)), TW, TH_, 20);
assert(quiet.sectors.every(function(s){ return s.type === "none"; }), "thermal: an empty (silent) scene has no heat sources");
const walker = { x: 50, y: 0, type: "walker" };
const seen = G("thermalAnalyze")(G("thermalSynth")({ x: 0, y: 0, heading: 0 }, [walker], 20, TW, TH_, G("lvRand")(1)), TW, TH_, 20);
const hit = seen.sectors.filter(function(s){ return s.type !== "none"; });
assert(hit.length >= 1 && hit.every(function(s){ return s.ray === 7 || s.ray === 8; }), "thermal: a silent pedestrian ahead is detected in the front sector");
assert(hit[0].type === "walker" && Math.abs(hit[0].dist - 50) < 12, "thermal: classified as walker (~34°C) at ~50 m (" + hit[0].dist.toFixed(0) + " m)");
const carObs = { x: 0, y: 40, type: "car" };
const seenCar = G("thermalAnalyze")(G("thermalSynth")({ x: 0, y: 0, heading: Math.PI / 2 }, [carObs], 20, TW, TH_, null), TW, TH_, 20);
assert(seenCar.sectors.some(function(s){ return s.type === "car"; }), "thermal: a hot engine/exhaust (>45°C) is classified as a car");
const behind = G("thermalAnalyze")(G("thermalSynth")({ x: 0, y: 0, heading: 0 }, [{ x: -50, y: 0, type: "car" }], 20, TW, TH_, null), TW, TH_, 20);
assert(behind.sectors.every(function(s){ return s.type === "none"; }), "thermal: objects outside the 90° camera FOV are not seen");
assert(seen.xi > 0 && seen.H > quiet.H - 1e-9, "thermal: per-scene Xi is computed; a heat source adds entropy to the temperature measure");
/* 輝度 → 温度 (温度計 = 中央値の基準) */
const lum = new Uint8Array(100); for (let i = 0; i < 100; i++) lum[i] = i < 90 ? 100 : 100 + 51;
const tt = G("lumaToTemps")(lum, 18, 50);
assert(Math.abs(tt[0] - 18) < 1e-6 && Math.abs(tt[99] - 28) < 1e-4, "thermal: white-hot luma is anchored to the thermometer (median = ambient)");
/* 融合: 熱画像でしか見えない無音の歩行者がトランスフォーマーの制動を起こす */
const blind = clearRays.map(function(r){ return { dist: r.dist, type: r.type }; });
const fused = G("fuseRays")(blind, seen);
assert(fused[hit[0].ray].src === "thermal" && fused[hit[0].ray].type === "walker", "fusion: thermal detection fills the ray the LiDAR missed");
const cFused = G("alControl")(G("fuseRays")(blind, G("thermalAnalyze")(G("thermalSynth")({ x: 0, y: 0, heading: 0 }, [{ x: 20, y: 0, type: "walker" }], 20, TW, TH_, null), TW, TH_, 20)), 0);
assert(cFused.throttle < 0, "fusion: a close silent pedestrian seen only by the IR camera makes the transformer brake");
assert(G("bleEssTemp")(new DataView(new Int16Array([2345]).buffer)) === 23.45, "BLE thermometer: ESS 0x2A6E sint16 x 0.01°C");

/* 10. サイレントトーク — 口形 → 口形素 → 走行コマンド */
function mouth(ap, sp){
  const w = 48, h = 32, a = new Uint8Array(w * h).fill(200);
  const rh = Math.round(ap * h), rw = Math.round(sp * w);
  const r0 = Math.floor((h - rh) / 2), c0 = Math.floor((w - rw) / 2);
  for (let r = r0; r < r0 + rh; r++) for (let c = c0; c < c0 + rw; c++) a[r * w + c] = 30;
  return a;
}
const LF = G("stLipFeatures"), CL = G("stClassify");
assert(CL(LF(mouth(0.6, 0.7), 48, 32)) === "A", "silent talk: tall+wide mouth -> A");
assert(CL(LF(mouth(0.25, 0.7), 48, 32)) === "I", "silent talk: flat+wide mouth -> I");
assert(CL(LF(mouth(0.6, 0.3), 48, 32)) === "O", "silent talk: tall+narrow mouth -> O");
assert(CL(LF(mouth(0.16, 0.3), 48, 32)) === "U", "silent talk: small+narrow mouth -> U");
assert(CL(LF(mouth(0, 0), 48, 32)) === "C", "silent talk: closed mouth -> C (rest)");
const Dec = G("StDecoder");
const dec = new Dec({ stable: 3, restFrames: 4 });
function frames(v, n){ let out = null; for (let i = 0; i < n; i++){ const t = dec.push(v); if (t) out = t; } return out; }
frames("C", 5); frames("A", 4); frames("I", 5);
const tk = frames("C", 8);
assert(tk && tk.word === "AI" && tk.cmd === "START", "silent talk: A..A I..I + rest decodes to 'AI' = 発進 (START)");
frames("E", 3); frames("O", 1); frames("E", 2); frames("I", 4);   /* O 1 フレームはノイズとして捨てる */
const tk2 = frames("C", 8);
assert(tk2 && tk2.word === "EI" && tk2.cmd === "STOP", "silent talk: a 1-frame glitch is filtered; 'EI' = 停止 (STOP)");
frames("U", 4); frames("U", 4);
const tk3 = frames("C", 8);
assert(tk3 && tk3.word === "U" && tk3.cmd === null, "silent talk: an unknown mouth word maps to no command");
/* 安全ゲート */
const gate = {}, SG = G("stGate");
assert(SG(gate, "STOP", 0).act === true, "gate: STOP executes immediately");
const g1 = SG(gate, "START", 1000);
assert(!g1.act && g1.needConfirm, "gate: START needs confirmation");
assert(SG(gate, "START", 4000).act === true, "gate: START confirmed by a second identical word within 5 s");
SG(gate, "START", 10000);
assert(SG(gate, "START", 16000).act === false, "gate: confirmation expires after 5 s");
SG(gate, "START", 20000);
assert(SG(gate, "STOP", 21000).act === true && gate.pending === null, "gate: STOP cancels a pending START");
/* 左右指示 → 経路組み替え */
const straight = G("planRoute")([0, 3], [11, 3]);
const tR = G("turnRoute")(straight, 0, 0, "RIGHT");
assert(tR && tR.into[1] === tR.turnAt[1] + 1 && G("isRoad")(tR.into[0], tR.into[1]), "turn: RIGHT while heading east picks the next road branching south");
const tL = G("turnRoute")(straight, 0, 0, "LEFT");
assert(tL && tL.into[1] === tL.turnAt[1] - 1 && G("isRoad")(tL.into[0], tL.into[1]), "turn: LEFT while heading east picks the next road branching north");

/* 11. 目的地リンク */
const DP = G("dstParse"), DD = G("dstDecode"), DS = G("dstSeal");
assert(DP("駅").x === 11 && DP("駅").y === 0 && DP("空港へ").label === "空港", "destination: place names resolve to landmark cells");
assert(DP("3,6").x === 3 && DP("3,6").y === 6 && DP("DST|11,8|空港|7").seq === 7 && DP("DST|11,8|空港|7").label === "空港", "destination: 'x,y' and DST|x,y|label|seq forms parse");
assert(DP("CMD|STOP").cmd === "STOP" && DP("cmd|go").cmd === "GO" && DP("???") === null, "destination: commands parse, garbage is null");
const sealed = DS({ x: 11, y: 8, label: "空港", seq: 3 }, 1234);
assert(/^LVD1\{/.test(sealed), "destination link: sealed envelope carries the LVD1 magic");
const okd = DD(sealed);
assert(okd.ok && okd.msg.signed && okd.msg.x === 11 && okd.msg.y === 8 && okd.msg.seq === 3, "destination link: sealed envelope verifies and decodes (signed)");
const env2 = JSON.parse(sealed.slice(4)); env2.ct[2] = (env2.ct[2] + 1) % 65536;
assert(DD("LVD1" + JSON.stringify(env2)).ok === false && DD("LVD1" + JSON.stringify(env2)).why === "tamper", "destination link: a tampered envelope is rejected (AEAD tag mismatch)");
assert(DD("港").ok && DD("港").msg.signed === false && DD("港").msg.x === 11 && DD("港").msg.y === 6, "destination link: plain text is accepted but marked unsigned");
assert(DD(DS({ cmd: "STOP" }, 5)).msg.cmd === "STOP", "destination link: sealed CMD|STOP decodes");

/* 12. 完全自動走行ミッション */
const PRA = G("planRouteAvoid");
const direct = G("planRoute")([0, 0], [11, 0]);
assert(direct.length === 12, "A*: top road (0,0)->(11,0) is a straight 12-cell route");
const detour = PRA([0, 0], [11, 0], { "5,0": true });
assert(detour && detour.length > 12 && !detour.some(function(p){ return p[0] === 5 && p[1] === 0; }), "A* avoid: a blocked cell forces a detour that never enters it (" + detour.length + " cells)");
assert(PRA([5, 0], [11, 0], { "5,0": true }) !== null, "A* avoid: the start cell itself is never treated as blocked");
assert(G("isRoad")(5, 0) === true, "A* avoid: isRoad is restored after planning");
const M = G("Mission");
const mi = new M();
assert(mi.accept({ x: 1, y: 1, label: "x", seq: 1 }, 0).ok === false, "mission: an off-road destination is rejected");
assert(mi.accept({ x: 11, y: 0, label: "駅", seq: 5, signed: true }, 0).ok && mi.accept({ x: 11, y: 8, label: "空港", seq: 2 }, 0).why === "stale",
       "mission: destinations queue; an older seq than the last accepted is rejected");
assert(mi.accept({ x: 11, y: 8, label: "空港", seq: 6 }, 0).pos === 2 && mi.queue.length === 2, "mission: second destination waits in the queue");
const n1 = mi.next([0, 0], 0);
assert(n1.ok && mi.state === "DRIVING" && mi.current.label === "駅" && mi.path.length === 12, "mission: next() plans the route to the first destination and starts DRIVING (no button)");
/* 封鎖 → 再計画: セル (5,0) の手前で 6 秒以上停止 */
mi.wp = 5;
let ev = null;
for (let i = 0; i < 70; i++){ const e = mi.observe(1000 + i * 100, 0.1, 0, 0.9, [4, 0]); if (e) ev = e; }
assert(ev && ev.type === "replan" && ev.cell[0] === 5 && ev.cell[1] === 0 && mi.path[0][0] === 4 && !mi.path.some(function(p){ return p[0] === 5 && p[1] === 0; }),
       "mission: stuck >6 s at a blocked cell -> that cell is blocked and the route re-planned around it (" + ev.len + " cells)");
assert(mi.observe(9000, 0.1, 20, 0, [4, 1]) === null && mi.stuckT === 0, "mission: moving again clears the stuck timer");
assert(Object.keys(mi.activeBlocked(9000)).length === 1 && Object.keys(mi.activeBlocked(9000 + 60000)).length === 0, "mission: a blocked cell expires after BLOCK_TTL");
/* 緊急停止と再開 */
mi.hold(); assert(mi.state === "HOLD", "mission: hold() -> HOLD (emergency stop)");
mi.resume(); assert(mi.state === "DRIVING", "mission: resume() -> DRIVING again");
/* 到着 → 次へ */
const arrived = mi.arrive(50000);
assert(arrived.label === "駅" && mi.state === "ARRIVED" && mi.done.length === 1 && mi.queue.length === 1, "mission: arrive() records the stop and keeps the queue");
const n2 = mi.next([11, 0], 50000);
assert(n2.ok && mi.current.label === "空港" && mi.path[0][0] === 11 && mi.path[0][1] === 0, "mission: after arrival the next queued destination is dispatched automatically");
mi.arrive(60000);
assert(mi.state === "IDLE" && mi.done.length === 2, "mission: with an empty queue the vehicle returns to IDLE and waits for Bluetooth");
const mu = new M(); mu.accept({ x: 7, y: 4, label: "unreach", seq: null }, 0);   /* (7,4) is '.'? no: row4 '#..#..#..#.#' -> x=7 '.' → offroad */
assert(mu.queue.length === 0, "mission: off-road cells never enter the queue");
const mb = new M(); mb.accept({ x: 11, y: 0, label: "駅" }, 0); mb.blocked["11,0"] = 1e12;
const nb = mb.next([0, 0], 0);
assert(!nb.ok && nb.skipped.length === 1 && mb.state === "IDLE", "mission: an unreachable destination is skipped and reported");

console.log("\nALL ENGINE TESTS PASSED");
