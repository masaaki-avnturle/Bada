/*
 * engine-test.js — Bada Relativity Lens のエンジン単体テスト (Node で実行)
 *
 *   node relativity_lens/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブした上で
 * 純ロジック部分を検証します:
 *   1. ローレンツ因子・行列ユーティリティ (gammaOf / mat3inv / mat3pinv)
 *   2. 相対論的光行差 (aberrateDir) — 教科書の閉じた式と厳密な可逆性
 *   3. ドップラー因子 (dopplerFactor) — 前方・後方・横方向
 *   4. ローレンツ収縮とテレル回転 (contractDir / terrellAngle)
 *   5. ★ズレ防止 (correctDir) — 光行差の厳密な打ち消し
 *   6. カメラモデル (makeCam / pixelToDir / dirToPixel) — 往復の一致
 *   7. 分光ドップラー (spectralBasis / dopplerMatrix) — 1の分割・単位行列・
 *      灰色不変・条件数が情報損失を正しく報告すること
 *   8. 画像ワープ (warpImage) — observe と correct が互いに逆変換であること
 *   9. ズレ計測 (zureField / zureReport) — 補正後に残差が消えること
 *  10. 光時計 (lightClock / sketchGeometry) — 写真のスケッチの幾何
 *  11. サンプル画像 (sampleImage) — 決定論性と内容
 *  12. 意図解析・応答 (lensIntent / lensReply)
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

/* ── index.html からインラインスクリプトを抽出 ── */
const htmlPath = path.join(__dirname, "..", "index.html");
const src = fs.readFileSync(htmlPath, "utf8");
const m = src.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no inline <script> in index.html"); process.exit(1); }

/* ── DOM スタブ (UI 層は init されないので触られない) ── */
function stubEl(){
  return new Proxy({ style:{}, classList:{ add(){}, remove(){} }, value:"", textContent:"", innerHTML:"", checked:false, width:0, height:0 }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "querySelector" || p === "appendChild" || p === "createElement") return function(){ return stubEl(); };
      if (p === "addEventListener" || p === "removeEventListener" || p === "focus") return function(){};
      if (p === "getAttribute") return function(){ return "0"; };
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const sandbox = {
  console, Math, Map, Object, Number, String, Array, JSON, isFinite, Infinity, NaN,
  Uint8ClampedArray, Image: function(){}, URL: { createObjectURL(){ return ""; }, revokeObjectURL(){} },
  setTimeout: fn => fn(), requestAnimationFrame: fn => fn(),
  document: {
    getElementById(){ return stubEl(); },
    createElement(){ return stubEl(); },
    querySelectorAll(){ return []; },
    addEventListener(){}, removeEventListener(){}
  }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox, { filename: "index.html<script>" });

const get = name => vm.runInContext(name, sandbox);
let passed = 0;
function assert(cond, msg){
  if (!cond){ console.error("FAIL: " + msg); process.exit(1); }
  passed++; console.log("ok - " + msg);
}
const close = (a, b, eps) => Math.abs(a - b) <= (eps === undefined ? 1e-9 : eps);
function dirClose(a, b, eps){
  return close(a.x, b.x, eps) && close(a.y, b.y, eps) && close(a.z, b.z, eps);
}

const gammaOf = get("gammaOf"), aberrateDir = get("aberrateDir"), contractDir = get("contractDir"),
      uncontractDir = get("uncontractDir"), correctDir = get("correctDir"), uncorrectDir = get("uncorrectDir"),
      dopplerFactor = get("dopplerFactor"), terrellAngle = get("terrellAngle"), beamFactor = get("beamFactor"),
      makeCam = get("makeCam"), pixelToDir = get("pixelToDir"), dirToPixel = get("dirToPixel"),
      spectralBasis = get("spectralBasis"), dopplerMatrix = get("dopplerMatrix"), dopplerRGB = get("dopplerRGB"),
      matCond = get("matCond"), mat3inv = get("mat3inv"), mat3pinv = get("mat3pinv"), mat3mul = get("mat3mul"),
      colorReversibility = get("colorReversibility"), warpImage = get("warpImage"),
      zureField = get("zureField"), zureReport = get("zureReport"),
      aberratedFov = get("aberratedFov"),
      lightClock = get("lightClock"), sketchGeometry = get("sketchGeometry"),
      sampleImage = get("sampleImage"), lensIntent = get("lensIntent"), lensReply = get("lensReply");

/* ═══ 1. ローレンツ因子・行列 ═══ */
assert(gammaOf(0) === 1, "gamma(0) = 1");
assert(close(gammaOf(0.6), 1.25), "gamma(0.6) = 1.25 (3-4-5 triangle)");
assert(close(gammaOf(0.8), 5 / 3), "gamma(0.8) = 5/3");
assert(close(gammaOf(-0.6), 1.25), "gamma is even in beta");
assert(gammaOf(0.99) > 7 && gammaOf(0.99) < 7.1, "gamma(0.99) ~ 7.09");

const A = [[2, 0, 1], [1, 3, 2], [1, 1, 4]];   /* det = 18 */
const I3 = mat3mul(A, mat3inv(A));
assert(close(I3[0][0], 1) && close(I3[1][1], 1) && close(I3[2][2], 1) && close(I3[0][1], 0),
       "mat3inv(A)·A = I for a non-singular matrix");
const SING = [[1, 0, 0], [1, 0, 0], [1, 0, 0]];
assert(matCond(SING) === Infinity, "matCond reports Infinity for a singular matrix");
assert(isFinite(matCond(A)), "matCond is finite for a non-singular matrix");
const pinvOK = mat3mul(mat3pinv(A), A);
assert(close(pinvOK[0][0], 1, 1e-6) && close(pinvOK[0][1], 0, 1e-6),
       "mat3pinv equals the true inverse when well-conditioned");
const pinvSing = mat3pinv(SING);
assert(pinvSing.every(r => r.every(v => isFinite(v))),
       "mat3pinv stays finite on a singular matrix (no silent identity, no blow-up)");

/* ═══ 2. 相対論的光行差 ═══ */
const BETAS = [0, 0.1, 0.5, 0.87, 0.99];
for (const b of BETAS){
  /* θ=90° の視線は cosθ' = β へ写る (教科書の特値) */
  const d90 = aberrateDir({ x:1, y:0, z:0 }, b);
  assert(close(d90.z, b, 1e-12), `aberration maps theta=90deg to cos(theta')=beta at beta=${b}`);
  /* 前方・後方は不動点 */
  assert(close(aberrateDir({ x:0, y:0, z:1 }, b).z, 1, 1e-12), `forward axis is a fixed point at beta=${b}`);
  /* β → −β が厳密な逆写像 */
  for (const d of [{x:0.4,y:-0.3,z:0.8}, {x:-0.9,y:0.2,z:0.35}, {x:0.05,y:0.02,z:0.99}]){
    const n = Math.hypot(d.x, d.y, d.z);
    const u = { x:d.x/n, y:d.y/n, z:d.z/n };
    assert(dirClose(aberrateDir(aberrateDir(u, b), -b), u, 1e-12),
           `aberration with -beta inverts aberration with beta (beta=${b}, dir ${d.x},${d.y},${d.z})`);
  }
}
/* 光行差は必ず前方へ寄せる (θ' <= θ) */
{
  const u = { x:0.6, y:0, z:0.8 };
  assert(aberrateDir(u, 0.7).z > 0.8, "aberration pushes the line of sight toward the direction of motion");
  assert(aberrateDir(u, -0.7).z < 0.8, "a backward boost pushes it away");
  assert(close(aberrateDir(u, 0).z, 0.8, 1e-12), "beta=0 leaves the direction untouched");
  /* 方位角 phi は保存される (ブーストは z 軸まわりに対称) */
  const t = aberrateDir({ x:0.3, y:0.4, z:0.866 }, 0.8);
  assert(close(Math.atan2(t.y, t.x), Math.atan2(0.4, 0.3), 1e-12), "aberration preserves the azimuth angle");
}

/* ═══ 3. ドップラー因子 ═══ */
for (const b of [0.1, 0.5, 0.87]){
  assert(close(dopplerFactor(1, b), Math.sqrt((1 + b) / (1 - b)), 1e-12),
         `forward Doppler = sqrt((1+b)/(1-b)) at beta=${b}`);
  assert(close(dopplerFactor(-1, b), Math.sqrt((1 - b) / (1 + b)), 1e-12),
         `backward Doppler = sqrt((1-b)/(1+b)) at beta=${b}`);
  assert(close(dopplerFactor(0, b), gammaOf(b), 1e-12), `transverse Doppler = gamma at beta=${b}`);
  /* 見かけの角度で書いた D = 1/(γ(1−β cosθ')) と一致すること */
  const u = { x:0.5, y:0.2, z:0.84 };
  const n = Math.hypot(u.x, u.y, u.z);
  const uu = { x:u.x/n, y:u.y/n, z:u.z/n };
  const app = aberrateDir(uu, b);
  assert(close(dopplerFactor(uu.z, b), 1 / (gammaOf(b) * (1 - b * app.z)), 1e-12),
         `D = gamma(1+b cos) equals 1/(gamma(1-b cos')) at beta=${b}`);
}
assert(dopplerFactor(1, 0) === 1, "no Doppler shift at rest");
assert(close(beamFactor(2), 16), "beaming is the fourth power of D");

/* ═══ 4. ローレンツ収縮とテレル回転 ═══ */
for (const b of [0.3, 0.75, 0.95]){
  const u = { x:0.6, y:0, z:0.8 };
  assert(dirClose(uncontractDir(contractDir(u, b), b), u, 1e-12), `contract/uncontract round-trip at beta=${b}`);
  /* tan(theta_now) = gamma * tan(theta) */
  const c = contractDir(u, b);
  assert(close(Math.hypot(c.x, c.y) / c.z, gammaOf(b) * (0.6 / 0.8), 1e-12),
         `tan(theta_now) = gamma tan(theta) at beta=${b}`);
  assert(terrellAngle(u, b) > 0, `Terrell rotation is non-zero at beta=${b}`);
}
assert(close(terrellAngle({ x:0.6, y:0, z:0.8 }, 0), 0, 1e-12), "no Terrell rotation at rest");
assert(terrellAngle({ x:0.6, y:0, z:0.8 }, 0.9) > terrellAngle({ x:0.6, y:0, z:0.8 }, 0.4),
       "Terrell rotation grows with speed");

/* ═══ 5. ★ズレ防止 — correctDir ═══ */
for (const b of [0.2, 0.6, 0.95, 0.999]){
  for (const d of [{x:0.4,y:-0.3,z:0.8}, {x:0.02,y:0.9,z:0.44}, {x:0,y:0,z:1}]){
    const n = Math.hypot(d.x, d.y, d.z);
    const u = { x:d.x/n, y:d.y/n, z:d.z/n };
    const seen = aberrateDir(u, b);
    assert(dirClose(correctDir(seen, b, "rest"), u, 1e-11),
           `correctDir(rest) cancels the apparent shift exactly (beta=${b})`);
    assert(dirClose(correctDir(seen, b, "now"), contractDir(u, b), 1e-11),
           `correctDir(now) lands on the simultaneity direction (beta=${b})`);
    assert(dirClose(uncorrectDir(correctDir(seen, b, "rest"), b, "rest"), seen, 1e-11),
           `uncorrectDir undoes correctDir (rest, beta=${b})`);
    assert(dirClose(uncorrectDir(correctDir(seen, b, "now"), b, "now"), seen, 1e-11),
           `uncorrectDir undoes correctDir (now, beta=${b})`);
  }
}
assert(dirClose(correctDir({ x:0.5, y:0.5, z:0.707 }, 0, "rest"),
                (v => { const n = Math.hypot(v.x, v.y, v.z); return { x:v.x/n, y:v.y/n, z:v.z/n }; })({ x:0.5, y:0.5, z:0.707 }), 1e-12),
       "correction is a no-op at rest");

/* ═══ 6. カメラモデル ═══ */
{
  const cam = makeCam(320, 240, 90);
  assert(close(cam.fx, 160, 1e-9), "90deg horizontal FOV puts the focal length at half the width");
  for (const p of [[10, 10], [160, 120], [319, 239], [80, 200]]){
    const back = dirToPixel(pixelToDir(p[0], p[1], cam), cam);
    assert(close(back.x, p[0], 1e-9) && close(back.y, p[1], 1e-9),
           `pixel -> direction -> pixel round-trip at (${p[0]},${p[1]})`);
  }
  assert(close(pixelToDir(160, 120, cam).z, 1, 1e-12), "the image centre looks straight down the optical axis");
  assert(dirToPixel({ x:0, y:0, z:-1 }, cam) === null, "directions behind the camera have no pixel");
}

/* ═══ 7. 分光ドップラー ═══ */
for (const lam of [200, 380, 550, 700, 1200, 4000]){
  const w = spectralBasis(lam);
  assert(close(w[0] + w[1] + w[2], 1, 1e-12), `the spectral basis is a partition of unity at ${lam}nm`);
  assert(w.every(v => v >= 0 && v <= 1), `the spectral basis stays in [0,1] at ${lam}nm`);
}
assert(spectralBasis(4000)[0] > 0.99, "far infrared is carried entirely by the red channel (flat extension)");
assert(spectralBasis(150)[2] > 0.99, "far ultraviolet is carried entirely by the blue channel");
for (const mode of ["spectral", "vivid"]){
  const M1 = dopplerMatrix(1, mode);
  assert(close(M1[0][0], 1, 1e-9) && close(M1[0][1], 0, 1e-9) && close(M1[2][2], 1, 1e-9),
         `the Doppler matrix is exactly the identity at D=1 (${mode})`);
  assert(close(matCond(M1), 1, 1e-6), `the Doppler matrix is perfectly conditioned at D=1 (${mode})`);
}
/* 灰色 = 等エネルギースペクトルなので、厳密モデルでは偏移しても色が変わらない */
{
  const grey = dopplerRGB([128, 128, 128], 1.8, false, "spectral").map(Math.round);
  assert(grey[0] === grey[1] && grey[1] === grey[2],
         "an equal-energy grey stays grey under the exact spectral shift");
  const red = dopplerRGB([255, 40, 40], 1.35, false, "spectral");
  assert(Math.abs(red[2] - 40) > 5 || Math.abs(red[1] - 40) > 5,
         "a saturated colour does shift under the spectral model");
}
/* 可視域ラップは常に良条件 = 完全に可逆、分光は高 D で情報が落ちる */
for (const D of [0.4, 0.8, 1.3, 2.5, 6]){
  assert(matCond(dopplerMatrix(D, "vivid")) < 50,
         `the vivid colour mode stays well-conditioned at D=${D}`);
  assert(colorReversibility(D, "vivid").ok, `the vivid colour mode is reversible at D=${D}`);
}
assert(matCond(dopplerMatrix(2.5, "spectral")) > 50,
       "the exact spectral model becomes ill-conditioned once the visible band comes from the infrared");
assert(!colorReversibility(2.5, "spectral").ok,
       "and colorReversibility reports honestly that the colour cannot be recovered");
assert(colorReversibility(1.02, "spectral").ok, "a mild shift is still fully reversible");
/* 良条件の範囲では色の往復が厳密に戻る */
for (const D of [0.85, 1.15]){
  const back = dopplerRGB(dopplerRGB([210, 90, 160], D, false, "vivid"), D, true, "vivid");
  assert(close(back[0], 210, 0.6) && close(back[1], 90, 0.6) && close(back[2], 160, 0.6),
         `colour survives a Doppler round-trip at D=${D} (vivid)`);
}

/* ═══ 8. 画像ワープ — observe と correct が互いの逆変換 ═══ */
{
  const W = 96, H = 72;
  /* なめらかな勾配画像を使う (再標本化の補間誤差を分離するため) */
  const smooth = { w:W, h:H, data:new Uint8ClampedArray(W * H * 4) };
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++){
    const o = (y * W + x) * 4;
    smooth.data[o]   = 40 + 160 * x / W;
    smooth.data[o+1] = 40 + 160 * y / H;
    smooth.data[o+2] = 128;
    smooth.data[o+3] = 255;
  }
  const opt = { beta:0.5, fov:90, aberration:true, doppler:false, beaming:false, colorMode:"vivid" };
  const obs = warpImage(smooth, Object.assign({ mode:"observe" }, opt));
  const fix = warpImage(obs, Object.assign({ mode:"correct", target:"rest" }, opt));
  assert(obs.w === W && obs.h === H, "warpImage keeps the image size");
  assert(obs.coverage > 0 && obs.coverage <= 1, "warpImage reports the fraction of the frame still in view");

  let n = 0, sum = 0, worst = 0;
  for (let i = 0; i < W * H; i++){
    if (fix.data[i*4+3] < 255) continue;           /* 圏外・境界は比較できない */
    for (let c = 0; c < 3; c++){
      const e = Math.abs(fix.data[i*4+c] - smooth.data[i*4+c]);
      sum += e; n++; worst = Math.max(worst, e);
    }
  }
  assert(n > W * H, "most of the frame survives the observe -> correct round-trip");
  assert(sum / n < 0.6, `observe then correct returns the original image (mean error ${(sum/n).toFixed(3)}/255)`);
  assert(worst <= 2, `no pixel drifts far in the round-trip (worst ${worst}/255)`);
  /* 圏外が「黒い被写体」に化けていないこと */
  let leaked = 0;
  for (let i = 0; i < W * H; i++) if (obs.data[i*4+3] === 0 && obs.data[i*4] !== 0) leaked++;
  assert(leaked === 0, "out-of-frame pixels stay marked as out-of-frame, not turned into black content");

  /* 色と輝度まで入れた完全な往復 (良条件の vivid モード) */
  const full = { beta:0.5, fov:90, aberration:true, doppler:true, beaming:true, colorMode:"vivid" };
  const obs2 = warpImage(smooth, Object.assign({ mode:"observe" }, full));
  const fix2 = warpImage(obs2, Object.assign({ mode:"correct", target:"rest" }, full));
  let s2 = 0, n2 = 0;
  for (let i = 0; i < W * H; i++){
    if (fix2.data[i*4+3] < 255) continue;
    for (let c = 0; c < 3; c++){ s2 += Math.abs(fix2.data[i*4+c] - smooth.data[i*4+c]); n2++; }
  }
  assert(s2 / n2 < 2.0, `the full optical chain (aberration+Doppler+beaming) is invertible (mean ${(s2/n2).toFixed(3)}/255)`);

  /* beta=0 は恒等変換 */
  const still = warpImage(smooth, { mode:"observe", beta:0, fov:90 });
  let same = true;
  for (let i = 0; i < W * H * 4; i += 4) if (Math.abs(still.data[i] - smooth.data[i]) > 1) same = false;
  assert(same, "warpImage at beta=0 is the identity");

  /* 光行差を切ると幾何は動かない */
  const noAber = warpImage(smooth, { mode:"observe", beta:0.8, fov:90, aberration:false, doppler:false, beaming:false });
  let same2 = true;
  for (let i = 0; i < W * H * 4; i += 4) if (Math.abs(noAber.data[i] - smooth.data[i]) > 1) same2 = false;
  assert(same2, "disabling aberration leaves the geometry untouched");

  /* ビーミングは前方を明るくする */
  const beamed = warpImage(smooth, { mode:"observe", beta:0.6, fov:90, aberration:false, doppler:false, beaming:true });
  const ctr = ((H/2|0) * W + (W/2|0)) * 4;
  assert(beamed.data[ctr] >= smooth.data[ctr], "beaming brightens the forward direction");
}

/* ═══ 8b. 観測画角の自動追尾 (2 台のカメラ) ═══ */
{
  assert(close(aberratedFov(90, 0), 90, 1e-9), "at rest the apparent field of view is unchanged");
  assert(aberratedFov(100, 0.6) < 100, "a forward boost squeezes the scene into a narrower apparent field");
  assert(aberratedFov(100, 0.95) < aberratedFov(100, 0.6), "the faster the observer, the tighter the squeeze");
  assert(aberratedFov(100, -0.6) > 100, "a backward boost spreads the scene over a wider field");
  /* 追尾画角にすると、同じ場面がフレームにほぼ収まる */
  const W = 80, H = 60;
  const im = { w:W, h:H, data:new Uint8ClampedArray(W * H * 4) };
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++){
    const o = (y * W + x) * 4;
    im.data[o] = 60 + 120 * x / W; im.data[o+1] = 140; im.data[o+2] = 60 + 120 * y / H; im.data[o+3] = 255;
  }
  const base = { beta:0.6, fov:100, aberration:true, doppler:false, beaming:false, colorMode:"vivid" };
  const same = warpImage(im, Object.assign({ mode:"observe" }, base));
  const auto = warpImage(im, Object.assign({ mode:"observe", fovView: aberratedFov(100, 0.6) }, base));
  assert(same.coverage < 0.3, `keeping the same field of view leaves most of the frame out of shot (${(same.coverage*100).toFixed(1)}%)`);
  assert(auto.coverage > 0.9, `auto-matching the field of view fills the frame (${(auto.coverage*100).toFixed(1)}%)`);

  /* 画角が違っても observe と correct は厳密に逆変換のまま */
  const opt2 = Object.assign({ fovView: aberratedFov(100, 0.6) }, base);
  const back = warpImage(auto, Object.assign({ mode:"correct", target:"rest" }, opt2));
  let sum = 0, n = 0;
  for (let i = 0; i < W * H; i++){
    if (back.data[i*4+3] < 255) continue;
    for (let c = 0; c < 3; c++){ sum += Math.abs(back.data[i*4+c] - im.data[i*4+c]); n++; }
  }
  assert(n > W * H * 2, "the re-framed round-trip still covers most of the image");
  assert(sum / n < 1.0, `observe/correct stay exact inverses across different fields of view (mean ${(sum/n).toFixed(3)}/255)`);

  /* zureField は観測フレームでの位置も返す */
  const camRest = makeCam(W, H, 100), camView = makeCam(W, H, aberratedFov(100, 0.6));
  const fv = zureField(camRest, 0.6, 6, camView);
  assert(fv.every(e => e.pView), "zureField reports a position in the observed frame too");
  assert(fv.some(e => Math.abs(e.pView.x - e.pApp.x) > 1),
         "the observed-frame position differs from the same-field position when the frame is re-matched");
  assert(zureField(camRest, 0.6, 6).every(e => e.pView === e.pApp),
         "without a view camera the two positions coincide");
}

/* ═══ 9. ズレ計測 ═══ */
{
  const cam = makeCam(320, 240, 100);
  const f0 = zureField(cam, 0, 9);
  assert(f0.every(e => e.px < 1e-9), "there is no misalignment at rest");
  const f = zureField(cam, 0.6, 9);
  assert(f.length > 0 && f.some(e => e.px > 10), "at 0.6c features are displaced by many pixels");
  assert(f.every(e => e.D > 0), "the Doppler factor is positive everywhere in the frame");

  for (const b of [0.1, 0.6, 0.9, 0.99]){
    for (const target of ["rest", "now"]){
      const r = zureReport(cam, b, target, "vivid");
      assert(r.before.px > 0, `there is a misalignment to correct at beta=${b} (${target})`);
      assert(r.after.px < 1e-9,
             `★ correction drives the geometric misalignment to zero at beta=${b} (${target}): ` +
             `${r.before.px.toFixed(1)}px -> ${r.after.px.toExponential(1)}px`);
      assert(r.after.deg < 1e-9, `angular residual vanishes at beta=${b} (${target})`);
      assert(r.after.colr < 0.01, `colour residual vanishes in the reversible mode at beta=${b}`);
      assert(r.afterBeamRatio === 1, `brightness is flattened back to 1.00 at beta=${b}`);
    }
  }
  /* 速いほどズレは大きい */
  const slow = zureReport(cam, 0.2, "rest", "vivid"), fast = zureReport(cam, 0.9, "rest", "vivid");
  assert(fast.before.px > slow.before.px, "the faster the observer, the larger the misalignment");
  assert(fast.beforeBeamRatio > slow.beforeBeamRatio, "and the larger the brightness spread");
  /* 静止系整合ではテレル回転が残り、同時刻整合では消える — 正直な報告 */
  const rRest = zureReport(cam, 0.8, "rest", "vivid"), rNow = zureReport(cam, 0.8, "now", "vivid");
  assert(rRest.after.terrDeg > 0.1, "rest-frame alignment honestly reports the Terrell rotation it does not remove");
  assert(rNow.after.terrDeg < 1e-9, "simultaneity alignment does remove the Terrell rotation");
  /* 分光モードでは高速時に色が戻らないことを正しく報告する */
  const rs = zureReport(cam, 0.8, "rest", "spectral");
  assert(!rs.rev.ok && rs.after.colr > 1,
         "the exact spectral mode reports that colour is genuinely lost at high speed");
  assert(rs.after.px < 1e-9, "but the geometric correction is still exact there");
}

/* ═══ 10. 光時計 — 写真のスケッチ ═══ */
for (const b of [0, 0.3, 0.6, 0.9, 0.99]){
  const ck = lightClock(b, 1);
  assert(close(ck.L * ck.L + ck.drift * ck.drift, ck.halfHyp * ck.halfHyp, 1e-9),
         `light-clock triangle closes: L^2 + (b*g*L)^2 = (g*L)^2 at beta=${b}`);
  assert(close(ck.tickMoving / ck.tickRest, gammaOf(b), 1e-12),
         `one tick is dilated by exactly gamma at beta=${b}`);
  assert(close(ck.dilation, gammaOf(b), 1e-12), `the dilation factor is gamma at beta=${b}`);
}
assert(close(lightClock(0, 1).drift, 0), "a clock at rest does not drift sideways");
assert(close(lightClock(0.6, 1).halfHyp, 1.25), "at 0.6c the light path is 1.25 L");
{
  const g = sketchGeometry(0.6);
  assert(g.up.length === 3 && g.down.length === 3, "the sketch has the two three-point light paths");
  assert(g.cross.length === 2, "the two light paths cross twice (the X in the drawing)");
  assert(close(g.cross[0].y, g.cross[1].y, 1e-9), "both crossings sit at the same height (mid-way between the mirrors)");
  /* 交差点が実際に 2 本の線分の交わりであることを確認する */
  const onSeg = (a, b, p) => {
    const t = Math.abs(b.x - a.x) > 1e-12 ? (p.x - a.x) / (b.x - a.x) : (p.y - a.y) / (b.y - a.y);
    return t > -1e-9 && t < 1 + 1e-9 &&
           close(a.x + (b.x - a.x) * t, p.x, 1e-9) && close(a.y + (b.y - a.y) * t, p.y, 1e-9);
  };
  assert(onSeg(g.up[0], g.up[1], g.cross[0]) && onSeg(g.down[0], g.down[1], g.cross[0]),
         "the first crossing really lies on both light paths");
  assert(onSeg(g.up[1], g.up[2], g.cross[1]) && onSeg(g.down[1], g.down[2], g.cross[1]),
         "the second crossing really lies on both light paths");
  assert(close(g.mirror.y0, g.mirror.y1, 1e-12) && g.mirror.y0 < g.floor.y0,
         "the mirror bar is horizontal and sits above the floor mirror");
  const all = [].concat(g.up, g.down, g.cross, [g.apex, g.emit]);
  assert(all.every(p => p.x >= -1e-9 && p.x <= 1 + 1e-9 && p.y >= -1e-9 && p.y <= 1 + 1e-9),
         "the whole sketch auto-fits inside the unit box");
  const wide = sketchGeometry(0.95);
  assert(wide.up[2].x - wide.up[0].x >= g.up[2].x - g.up[0].x - 1e-9,
         "a faster clock draws a wider, more slanted path");
  assert(close(sketchGeometry(0).up[0].x, sketchGeometry(0).up[1].x, 1e-9),
         "at rest the path is exactly vertical (the V collapses)");
}

/* ═══ 11. サンプル画像 ═══ */
for (const kind of ["sketch", "grid", "bars", "stars"]){
  const im = sampleImage(kind, 64, 48);
  assert(im.w === 64 && im.h === 48 && im.data.length === 64 * 48 * 4, `sampleImage('${kind}') has the right shape`);
  assert(im.data.every((v, i) => i % 4 !== 3 || v === 255), `sampleImage('${kind}') is fully opaque`);
  let distinct = new Set();
  for (let i = 0; i < im.data.length; i += 4) distinct.add(im.data[i] + "," + im.data[i+1] + "," + im.data[i+2]);
  assert(distinct.size > 2, `sampleImage('${kind}') actually draws something`);
  const again = sampleImage(kind, 64, 48);
  assert(again.data.every((v, i) => v === im.data[i]), `sampleImage('${kind}') is deterministic`);
}
{
  const sk = sampleImage("sketch", 128, 96);
  assert(sk.data[0] > 200 && sk.data[1] > 200, "the sketch sample is drawn on light notebook paper");
}

/* ═══ 12. 意図解析・応答 ═══ */
assert(lensIntent("0.9c にして").patch.beta === 0.9, "intent: '0.9c にして' sets beta to 0.9");
assert(lensIntent("β=0.42").patch.beta === 0.42, "intent: 'beta=0.42' is parsed");
assert(lensIntent("95% で").patch.beta === 0.95, "intent: a percentage is parsed");
assert(lensIntent("光速の8割").patch.beta === 0.8, "intent: 'eight tenths of light speed' is parsed");
assert(lensIntent("静止して").patch.beta === 0, "intent: 'stop' returns to rest");
assert(lensIntent("ズレは?").intent === "report", "intent: 'how large is the misalignment?' asks for the report");
assert(lensIntent("補正オフ").patch.fix === false, "intent: 'correction off' disables the fix");
assert(lensIntent("ズレ防止オン").patch.fix === true, "intent: 'misalignment prevention on' enables the fix");
assert(lensIntent("ドップラー切って").patch.doppler === false, "intent: 'turn off Doppler'");
assert(lensIntent("光行差を無効に").patch.aberration === false, "intent: 'disable aberration'");
assert(lensIntent("ビーミング入れて").patch.beaming === true, "intent: 'enable beaming'");
assert(lensIntent("画角 130").patch.fov === 130, "intent: 'field of view 130'");
assert(lensIntent("同時刻整合にして").patch.target === "now", "intent: switch to simultaneity alignment");
assert(lensIntent("静止系に戻して").patch.target === "rest", "intent: switch back to rest-frame alignment");
assert(lensIntent("色は厳密な分光で").patch.colorMode === "spectral", "intent: choose the exact spectral colour model");
assert(lensIntent("色を強調して").patch.colorMode === "vivid", "intent: choose the vivid colour model");
assert(lensIntent("γ は?").intent === "clock", "intent: asking for gamma opens the light-clock answer");
assert(lensIntent("格子にして").patch.sample === "grid", "intent: switch the sample image to the grid");
assert(lensIntent("").intent === "none", "an empty command does nothing");
assert(lensIntent("ぬるぽ").intent === "unknown", "an unparsable command is reported as unknown");

{
  const st = { beta:0.6, fov:100, target:"rest", colorMode:"vivid",
               aberration:true, doppler:true, beaming:true, fix:true, w:320, h:240 };
  const r1 = lensReply("0.9c にして", st);
  assert(r1.patch.beta === 0.9 && /β = 0\.900/.test(r1.reply) && /γ = 2\.294/.test(r1.reply),
         "lensReply reports the new beta and gamma");
  assert(/px/.test(r1.reply), "lensReply quotes the misalignment in pixels");
  const r2 = lensReply("ズレは?", st);
  assert(/光行差/.test(r2.reply) && /テレル回転/.test(r2.reply) &&
         /ドップラー/.test(r2.reply) && /ビーミング/.test(r2.reply),
         "the report covers all four kinds of misalignment");
  const r3 = lensReply("γ は?", st);
  assert(/L² \+ \(βγL\)² = \(γL\)²/.test(r3.reply), "the light-clock answer states the triangle identity");
  const r4 = lensReply("補正オフ", st);
  assert(r4.patch.fix === false && /OFF/.test(r4.reply), "turning the correction off is acknowledged");
  const r5 = lensReply("使い方", st);
  assert(/0\.9c/.test(r5.reply), "the help text gives usable examples");
  assert(lensReply("", st).reply === "", "an empty command produces no chatter");
  /* 分光モードでは色が戻らないことを応答でも正直に言う */
  const r6 = lensReply("色は厳密な分光で", Object.assign({}, st, { beta:0.8 }));
  assert(/可逆性/.test(r6.reply), "switching to the exact model warns about colour reversibility");
}

console.log("\nALL " + passed + " ENGINE TESTS PASSED");
