/*
 * engine-test.js — エアシャトル・ゴーグル (AirShuttle Goggle) のエンジン単体テスト
 *
 *   node airshuttle_goggle/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブして純ロジックを検証します:
 *   1. 肌色判定 (YCbCr クロマ帯) と RGB→YCbCr 変換
 *   2. ハンド・セグメンテーション (動きエネルギーによる背景除去)
 *   3. 連結成分ラベリング / ブロブ→手 (位置・充填率・鏡像) / ポーズ判定
 *   4. One Euro Filter (収束・追従・dt=0 の安全性)
 *   5. シャトル則 (不感帯・べき乗カーブ・デテント吸着・高さによる精度スケール)
 *   6. スワイプ / フリック検出 (移動量・ピーク速度・方向一貫率) と跳躍量
 *   7. トランスポート状態機械 (HOLD / SHUTTLE / FLICK / LOST) と時刻更新・再生駆動方式
 *   8. 表示ヘルパ (タイムコード / フィルムストリップ / かき分け変位 / ゾーン)
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
  return new Proxy({ style: {}, classList: { add(){}, remove(){}, toggle(){}, contains(){ return false; } },
                     value: "", textContent: "", innerHTML: "", className: "",
                     width: 900, height: 300, readyState: 0, paused: true, currentTime: 0, duration: 0 }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "getBoundingClientRect") return function(){ return { left: 0, top: 0, width: 900, height: 300 }; };
      if (p === "addEventListener" || p === "removeEventListener") return function(){};
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const sandbox = {
  console, Math, Proxy, String, Number, Object, Array, JSON, Date, Infinity,
  parseFloat, parseInt, isNaN, isFinite, encodeURIComponent,
  performance: { now(){ return 0; } },
  setTimeout(fn){ return 0; }, setInterval(){ return 0; }, clearInterval(){},
  requestAnimationFrame(){ return 0; },
  document: {
    getElementById(){ return stubEl(); }, createElement(){ return stubEl(); },
    querySelectorAll(){ return []; }, addEventListener(){}, removeEventListener(){},
    documentElement: stubEl(), fullscreenElement: null
  },
  navigator: {}, window: { addEventListener(){}, devicePixelRatio: 1 }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });

let pass = 0, fail = 0;
function ok(cond, label){
  if (cond) { pass++; console.log("  ✓ " + label); }
  else      { fail++; console.error("  ✗ " + label); }
}
function near(a, b, eps, label){ ok(Math.abs(a - b) <= (eps || 1e-9), label + " (" + a + " ≈ " + b + ")"); }
const S = sandbox;

/* 肌色 (r,g,b) の矩形を描いた RGBA バッファを作る */
function makeFrame(w, h, bg, rect, fg){
  const px = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++){
    const i = (y * w + x) * 4;
    const inR = rect && x >= rect.x0 && x <= rect.x1 && y >= rect.y0 && y <= rect.y1;
    const c = inR ? fg : bg;
    px[i] = c[0]; px[i + 1] = c[1]; px[i + 2] = c[2]; px[i + 3] = 255;
  }
  return px;
}
const SKIN = [222, 171, 140], SKIN2 = [214, 163, 133], WALL = [150, 150, 150];

console.log("1. 肌色判定 (YCbCr クロマ帯)");
{
  const c = S.rgbToYCbCr(222, 171, 140);
  near(c.y, 0.299 * 222 + 0.587 * 171 + 0.114 * 140, 1e-9, "Y = BT.601 の重み付き和");
  ok(c.cb > 77 && c.cb < 133 && c.cr > 133 && c.cr < 177, "肌色は Cb/Cr が肌色帯に入る");
  ok(S.isSkinPixel(222, 171, 140) === true, "典型的な肌色 → 肌");
  ok(S.isSkinPixel(150, 150, 150) === false, "無彩色のグレー壁 → 非肌 (彩度条件)");
  ok(S.isSkinPixel(40, 180, 60) === false, "緑 → 非肌 (Cr が下限未満)");
  ok(S.isSkinPixel(40, 60, 200) === false, "青 → 非肌");
  ok(S.isSkinPixel(12, 9, 8) === false, "暗部 → 非肌 (Y 下限)");
  ok(S.isSkinPixel(252, 250, 248) === false, "白飛び → 非肌");
}

console.log("2. ハンド・セグメンテーション (動きによる背景除去)");
{
  const w = 16, h = 12, rect = { x0: 4, y0: 3, x1: 9, y1: 8 };
  const cur = makeFrame(w, h, WALL, rect, SKIN);
  const noMotion = S.segmentHand(cur, null, w, h, { motionThreshold: 0 });
  let count = 0; for (let i = 0; i < noMotion.length; i++) count += noMotion[i];
  ok(count === 36, "動き条件なし: 肌色矩形 6×6 = 36 画素を抽出");
  const still = S.segmentHand(cur, cur, w, h, { motionThreshold: 14 });
  let c2 = 0; for (let i = 0; i < still.length; i++) c2 += still[i];
  ok(c2 === 0, "静止した肌色 (背景の肌色壁) は動き条件で全棄却");
  const prev = makeFrame(w, h, WALL, rect, [110, 70, 55]);
  const moved = S.segmentHand(cur, prev, w, h, { motionThreshold: 14 });
  let c3 = 0; for (let i = 0; i < moved.length; i++) c3 += moved[i];
  ok(c3 === 36, "直前フレームと変化した肌色は手として残る");
  near(S.frameMotion(cur, cur), 0, 1e-9, "同一フレームの動きエネルギー = 0");
  ok(S.frameMotion(cur, prev) > 0, "異なるフレームの動きエネルギー > 0");
  ok(S.frameMotion(cur, null) === 255, "直前フレーム無し → 最大値 (初回は動き扱い)");
}

console.log("3. 連結成分ラベリングとブロブ→手");
{
  const w = 10, h = 10;
  const mask = new Uint8Array(w * h);
  for (let y = 1; y <= 4; y++) for (let x = 1; x <= 4; x++) mask[y * w + x] = 1;   // 4×4 = 16
  for (let y = 7; y <= 8; y++) for (let x = 7; x <= 8; x++) mask[y * w + x] = 1;   // 2×2 = 4
  const blobs = S.labelBlobs(mask, w, h, 1);
  ok(blobs.length === 2, "2 つの連結成分を検出");
  ok(blobs[0].area === 16 && blobs[1].area === 4, "面積降順 (16 → 4)");
  near(blobs[0].cx, 2.5, 1e-9, "最大ブロブの重心 x");
  near(blobs[0].cy, 2.5, 1e-9, "最大ブロブの重心 y");
  ok(S.labelBlobs(mask, w, h, 8).length === 1, "minArea で小ブロブ (ノイズ) を除去");

  const hand = S.handFromBlob(blobs[0], w, h, true);
  near(hand.x, 1 - 0.3, 1e-9, "鏡像 ON: x は左右反転 (カメラは鏡像のため)");
  near(hand.y, 0.3, 1e-9, "y は反転しない");
  near(S.handFromBlob(blobs[0], w, h, false).x, 0.3, 1e-9, "鏡像 OFF: そのまま");
  near(hand.fill, 1.0, 1e-9, "矩形ブロブの充填率 = 1");
  near(hand.size, Math.sqrt(16 / 100), 1e-9, "size = √(面積比)");
  ok(S.handFromBlob(null, w, h, true) === null, "ブロブ無し → null");

  ok(S.classifyPose({ present: true, fill: 0.9 }) === "grab", "充填率 0.9 → 握り (HOLD)");
  ok(S.classifyPose({ present: true, fill: 0.45 }) === "open", "充填率 0.45 → 開いた手");
  ok(S.classifyPose({ present: true, fill: 0.65 }) === "half", "中間 → half");
  ok(S.classifyPose(null) === "none", "手なし → none");
}

console.log("4. One Euro Filter");
{
  const f = S.oneEuroFilter({ minCutoff: 1.0, beta: 0.35 });
  ok(f.filter(0.5, 1 / 60) === 0.5, "初回はそのまま通す");
  let v = 0.5;
  for (let i = 0; i < 200; i++) v = f.filter(0.5, 1 / 60);
  near(v, 0.5, 1e-6, "定常入力に収束");
  const g = S.oneEuroFilter({ minCutoff: 1.0, beta: 0.35 });
  g.filter(0.2, 1 / 60);
  const step = g.filter(0.8, 1 / 60);
  ok(step > 0.2 && step < 0.8, "ステップ入力は行き過ぎずに追従 (平滑化)");
  ok(isFinite(g.filter(0.8, 0)), "dt = 0 でも NaN/Infinity にならない");
  let slow = 0.5, fastV = 0.5;
  const a = S.oneEuroFilter({ beta: 0 }), b = S.oneEuroFilter({ beta: 1.0 });
  a.filter(0, 1 / 60); b.filter(0, 1 / 60);
  for (let i = 1; i <= 5; i++){ slow = a.filter(i * 0.1, 1 / 60); fastV = b.filter(i * 0.1, 1 / 60); }
  ok(fastV > slow, "β が大きいほど素早い動きに追従する (適応カットオフ)");
  a.reset(); ok(a.value() === null, "reset で内部状態が消える");
}

console.log("5. シャトル則 (かき分け → 速度)");
{
  ok(S.shuttleRate(0, {}) === 0, "中立点 → 停止");
  ok(S.shuttleRate(0.05, {}) === 0, "不感帯の内側 → 停止 (誤爆防止)");
  ok(S.shuttleRate(0.45, {}) === 16, "右端まで押し切ると ×16 (最大)");
  ok(S.shuttleRate(-0.45, {}) === -16, "左端まで押し切ると ×-16 (巻き戻し最大)");
  ok(S.shuttleRate(0.9, {}) === 16, "span を超えても上限で飽和");
  const mid = S.shuttleRate(0.30, { detent: false });
  ok(mid > 0 && mid < 16, "中間変位は中間速度");
  ok(S.shuttleRate(0.30, {}) === S.snapRate(mid, 16), "デテント ON で最寄りの目盛に吸着");
  ok(S.shuttleDetents().indexOf(1) >= 0 && S.shuttleDetents()[0] === 0, "デテントは 0 と ×1 を含む");
  ok(S.snapRate(3.4, 16) === 4 && S.snapRate(1.2, 16) === 1, "最寄りデテントへ吸着");
  ok(S.snapRate(30, 16) === 16, "上限 max を超えるデテントは選ばれない");
  const a1 = S.shuttleRate(0.20, { detent: false, gamma: 1 });
  const a2 = S.shuttleRate(0.20, { detent: false, gamma: 3 });
  ok(a2 < a1, "γ が大きいほど中央付近は繊細 (低速)");
  near(S.precisionScale(0), 1.0, 1e-9, "手を上げる (y=0) → 最大速度");
  near(S.precisionScale(1), 0.15, 1e-9, "手を下げる (y=1) → 微調整 (15%)");
  ok(S.precisionScale(0.5) > S.precisionScale(0.9), "高さに対して単調");
}

console.log("6. スワイプ / フリック検出");
{
  const sweep = [];
  for (let i = 0; i <= 10; i++) sweep.push({ t: 1000 + i * 20, x: 0.2 + i * 0.06 });  // 200ms で +0.6
  const sw = S.detectSwipe(sweep, {});
  ok(!!sw && sw.dir === 1, "右への素早い払い → 早送り方向のスワイプ");
  near(sw.travel, 0.6, 1e-9, "移動量 = 0.6");
  ok(sw.speed > 2.9 && sw.speed < 3.1, "ピーク速度 ≈ 3.0 /s");
  const back = sweep.map(s => ({ t: s.t, x: 1 - s.x }));
  ok(S.detectSwipe(back, {}).dir === -1, "左への払い → 巻き戻し方向");
  const slow = [];
  for (let i = 0; i <= 10; i++) slow.push({ t: 1000 + i * 100, x: 0.4 + i * 0.01 });
  ok(S.detectSwipe(slow, {}) === null, "ゆっくりした移動はスワイプではない");
  const shaky = [];
  for (let i = 0; i <= 10; i++) shaky.push({ t: 1000 + i * 20, x: 0.5 + (i % 2 ? 0.25 : -0.25) });
  ok(S.detectSwipe(shaky, {}) === null, "往復する震えは方向一貫率で棄却");
  ok(S.detectSwipe([{ t: 0, x: 0 }], {}) === null, "サンプル不足 → null");

  near(S.flickJumpSeconds(0, {}), 2, 1e-9, "速度 0 → 下限 2 秒");
  ok(S.flickJumpSeconds(3, {}) > S.flickJumpSeconds(1.5, {}), "速いほど大きく跳ぶ");
  ok(S.flickJumpSeconds(1000, {}) === 120, "上限 120 秒でクランプ");
  ok(S.flickJumpSeconds(3, { flickGain: 12 }) > S.flickJumpSeconds(3, { flickGain: 6 }), "感度設定が効く");
}

console.log("7. トランスポート状態機械");
{
  const base = { time: 50, rate: 0, hold: false };
  const cfg = { duration: 100 };
  const lost = S.nextTransport(base, { present: false }, 0.1, cfg);
  ok(lost.event === "lost" && lost.rate === 0 && lost.time === 50, "手を見失ったら安全側で停止");
  const hold = S.nextTransport(base, { present: true, x: 0.9, y: 0.2, pose: "grab" }, 0.1, cfg);
  ok(hold.event === "hold" && hold.hold === true && hold.rate === 0, "握り → HOLD (位置に関係なく停止)");
  const neutral = S.nextTransport(base, { present: true, x: 0.5, y: 0.5, pose: "open" }, 0.1, cfg);
  ok(neutral.event === "neutral" && neutral.rate === 0, "中立位置 → NEUTRAL");
  const ff = S.nextTransport(base, { present: true, x: 0.95, y: 0, pose: "open" }, 0.1, cfg);
  ok(ff.event === "shuttle" && ff.rate === 16, "右へかき分け + 手を上げる → ×16 早送り");
  near(ff.time, 50 + 16 * 0.1, 1e-9, "時刻が rate·Δt だけ進む");
  const rew = S.nextTransport(base, { present: true, x: 0.05, y: 0, pose: "open" }, 0.1, cfg);
  ok(rew.rate === -16 && rew.time < 50, "左へかき分け → 巻き戻し");
  const fine = S.nextTransport(base, { present: true, x: 0.95, y: 1, pose: "open" }, 0.1, cfg);
  ok(fine.rate === 2, "同じ変位でも手を下げると微速 (×16·0.15 → デテント ×2)");
  const flick = S.nextTransport(base, { present: true, x: 0.5, y: 0.5, pose: "open",
                                        swipe: { dir: 1, speed: 3 } }, 0.1, cfg);
  ok(flick.event === "flick" && flick.jump > 0 && flick.time > 50, "フリックで前方へ跳躍");
  const clampEnd = S.nextTransport({ time: 99, rate: 0, hold: false },
                                   { present: true, x: 0.95, y: 0, pose: "open" }, 1, cfg);
  ok(clampEnd.time === 100, "終端でクランプ (duration を超えない)");
  ok(S.nextTransport({ time: 1, rate: 0 }, { present: true, x: 0.05, y: 0, pose: "open" }, 1, cfg).time === 0,
     "先頭でクランプ (負の時刻にならない)");

  near(S.advanceTime(10, -4, 0.5, 100, false), 8, 1e-9, "advanceTime: 巻き戻し");
  ok(S.advanceTime(99, 4, 1, 100, true) === 3, "loop: 終端を超えたら先頭へ回り込む");
  ok(S.advanceTime(1, -4, 1, 100, true) === 97, "loop: 先頭を割ったら末尾へ");
  ok(S.advanceTime(5, -100, 1, 0, false) === 0, "duration 不明でも負にならない");

  ok(S.effectiveRate({ rate: 0, hold: false }, true) === 1, "中立 + 再生中 → ×1 で流れる");
  ok(S.effectiveRate({ rate: 0, hold: false }, false) === 0, "中立 + 停止中 → 止まったまま");
  ok(S.effectiveRate({ rate: -8, hold: false }, true) === -8, "シャトル中は基本再生より優先");
  ok(S.effectiveRate({ rate: 8, hold: true }, true) === 0, "HOLD は何よりも優先して停止");

  ok(S.videoDriveMode(0).mode === "paused", "速度 0 → 一時停止");
  const nat = S.videoDriveMode(2);
  ok(nat.mode === "native" && nat.playbackRate === 2, "×2 は playbackRate で再生");
  ok(S.videoDriveMode(8).mode === "manual", "×8 は手動シーク (playbackRate は不安定)");
  ok(S.videoDriveMode(-2).mode === "manual", "巻き戻しは必ず手動シーク (負の playbackRate は不可)");
  ok(S.videoDriveMode(6, { nativeMax: 8 }).mode === "native", "nativeMax 設定を尊重");
}

console.log("8. 表示ヘルパ (タイムコード / フィルムストリップ / かき分け)");
{
  ok(S.formatTimecode(0, 30) === "00:00:00:00", "0 秒");
  ok(S.formatTimecode(3661.5, 30) === "01:01:01:15", "1h01m01s+15フレーム");
  ok(S.formatTimecode(1.999, 30) === "00:00:01:29", "フレーム番号は fps-1 でクランプ");
  ok(S.formatTimecode(-2, 30).charAt(0) === "-", "負の時刻は符号付き");
  ok(S.rateLabel(0, true) === "⏸ HOLD" && S.rateLabel(0, false) === "⏸ STOP", "停止表示");
  ok(S.rateLabel(-2, false).indexOf("⏪") === 0 && S.rateLabel(4, false).indexOf("⏩") === 0, "方向記号");
  ok(S.rateClass(-2, false) === "rose" && S.rateClass(2, false) === "green" &&
     S.rateClass(0, true) === "amber", "色クラス");

  const times = S.filmstripTimes(100, 4);
  ok(times.length === 4, "フィルムストリップ 4 コマ");
  near(times[0], 12.5, 1e-9, "各コマは区間中央の時刻");
  ok(S.filmstripTimes(0, 10).length === 0, "尺不明ならコマ無し");
  ok(S.stripCellIndex(55, 100, 10) === 5, "現在時刻 → コマ番号");
  ok(S.stripCellIndex(100, 100, 10) === 9, "終端は最終コマにクランプ");
  ok(S.stripCellIndex(5, 0, 10) === 0, "尺 0 は 0 番");

  near(S.partOffset(0.5, 0.5, 1, 0.18), 0, 1e-12, "手の真下のコマは動かない (押し退けの中心)");
  const right = S.partOffset(0.6, 0.5, 1, 0.18), left = S.partOffset(0.4, 0.5, 1, 0.18);
  ok(right > 0 && left < 0, "手の右のコマは右へ、左のコマは左へ “かき分け” られる");
  near(right, -left, 1e-12, "かき分けは左右対称");
  ok(Math.abs(S.partOffset(0.9, 0.5, 1, 0.18)) < Math.abs(right), "遠いコマほど影響が小さい (ガウス窓)");

  ok(S.zoneLabel(0.5, {}) === "NEUTRAL" && S.zoneLabel(0.1, {}) === "REW" && S.zoneLabel(0.9, {}) === "FF",
     "HUD ゾーン表示");

  const s0 = S.demoSceneState(0, 150), s1 = S.demoSceneState(75, 150);
  ok(s1.sun.x > s0.sun.x, "デモ映像: 時刻に対して太陽が移動 (巻き戻し可能な純関数)");
  ok(S.demoSceneState(10, 150).tick === 300, "デモ映像のフレーム番号 = t·30");
  ok(S.clamp(5, 0, 1) === 1 && S.clamp(-5, 0, 1) === 0, "clamp");
}

console.log("");
console.log("結果: " + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
