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
 *   6. アル (意図エンジン) の応答
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
sess.feed("12.4V\r>");
assert(writes[writes.length - 1] === "010D" && writes.length === 10,
       "ELM session: poll cycle wraps around (010D 010C 0105 ATRV -> 010D)");
const spd = telemetry.filter(function(e){ return e.type === "speed"; });
const rpm = telemetry.filter(function(e){ return e.type === "rpm"; });
assert(spd.length === 1 && spd[0].kmh === 40, "ELM session: telemetry speed 40 km/h delivered");
assert(rpm.length === 1 && rpm[0].rpm === 1000, "ELM session: telemetry 1000 rpm delivered");
sess.feed("41 0D");        /* 分割パケット前半 */
sess.feed(" 50\r>");       /* 後半 — 結合して 80 km/h */
const spd2 = telemetry.filter(function(e){ return e.type === "speed"; });
assert(spd2.length === 2 && spd2[1].kmh === 80, "ELM session: split BLE packets are reassembled (80 km/h)");

console.log("\nALL ENGINE TESTS PASSED");
