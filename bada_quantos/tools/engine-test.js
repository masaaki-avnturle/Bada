/*
 * engine-test.js — Bada QuantOS のエンジン単体テスト (Node で実行)
 *
 *   node bada_quantos/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM/localStorage を
 * スタブした上で純ロジック部分を検証します:
 *   1. 擬似量子カーネル (qkInterpret) — ベル状態 / GHZ / エラー / let·print
 *   2. トポロジー不変量 (topoInvariant) — 交点数・ライズ・⟨K⟩、全機能で一意
 *   3. トポロジー写像 (topoMap) — 機能 ↦ 基底状態の単射、準備回路の検算
 *   4. 連続変形 (topoRoute) — ハミング距離と X ゲート列
 *   5. 端末プロファイル (deviceProfile) — スマートフォン / タブレット / デスクトップ
 *   6. 電卓 (calcEval) — 再帰下降パーサ
 *   7. 意図解析 (intentDetect) — 電話番号抽出・各機能への振り分け
 *   8. 生成AIカーネル (aiKernel) — 6 段パイプラインと実行
 *   9. 実行系 (osDispatch) — テスト環境では発行せず記述のみ返す
 *  10. 量子暗号方式 (qcBB84 / qcEncrypt / qcDecrypt) — BB84 鍵配送・
 *      盗聴検出 (QBER)・ワンタイムパッドの往復・鍵違いの棄却
 *  11. アプリランチャー + Play ストア (appLaunch / appCatalogFind) —
 *      カタログ照合・market: インテント・意図解析・実行系
 *  12. フリーフォーム / マルチウィンドウ (wmOpen / wmTile / wmSnap /
 *      wmBraidWord / wmDeviceSupport) — Samsung DeX 判定・分割配置・
 *      ウィンドウの重なりを組み紐不変量として計算
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

/* ── DOM / localStorage スタブ ── */
function stubEl(){
  return new Proxy({ style: {}, classList: { add(){}, remove(){} }, value: "", textContent: "", innerHTML: "" }, {
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
  console: console,
  Math: Math,
  Function: Function,
  setTimeout: function(fn){ fn(); },
  setInterval: function(){ return 0; },
  clearInterval: function(){},
  alert: function(){},
  localStorage: { _d: {}, getItem(k){ return k in this._d ? this._d[k] : null; }, setItem(k, v){ this._d[k] = String(v); } },
  window: {},
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

function get(name){ return vm.runInContext(name, sandbox); }
function assert(cond, msg){ if (!cond){ console.error("FAIL: " + msg); process.exit(1); } console.log("ok - " + msg); }

/* 1. 擬似量子カーネル */
const bell = get("qkInterpret")("qubit q0 q1\nH q0\nCNOT q0 q1\nstate\nmeasure");
assert(/\|00⟩ 0\.707/.test(bell) && /\|11⟩ 0\.707/.test(bell), "bell state amplitudes 1/√2 (|00⟩+|11⟩)");
assert(/measure → \|(00|11)⟩/.test(bell), "measurement collapses to correlated |00⟩ or |11⟩");
const ghz = get("qkInterpret")("qubit q0 q1 q2\nH q0\nCNOT q0 q1\nCNOT q1 q2\nstate");
assert(/\|000⟩ 0\.707/.test(ghz) && /\|111⟩ 0\.707/.test(ghz), "GHZ state has |000⟩ and |111⟩ at 1/√2");
assert(/!!/.test(get("qkInterpret")("H q9")), "interpreter reports errors for undeclared qubits");
assert(/print → 6/.test(get("qkInterpret")("let x = 1 + 2\nlet y = x * 2\nprint y")), "let/print classical arithmetic works");

/* 2. トポロジー不変量 */
const inv3 = get("topoInvariant")([1, 1, 1]);
assert(inv3.crossings === 3 && inv3.writhe === 3 && inv3.aExp === 9, "trefoil-like curl [+1,+1,+1] → c=3, w=3, A-exponent 9");
assert(/\(−A³\)\^3/.test(inv3.bracket), "Kauffman bracket of w=3 curls is (−A³)^3");
const inv0 = get("topoInvariant")([]);
assert(inv0.crossings === 0 && inv0.writhe === 0 && inv0.bracket === "1", "unknot (AI kernel) has trivial bracket 1");
const apps = get("OS_APPS");
const keys = new Set();
for (const a of apps) keys.add(get("topoInvariant")(a.knot).key);
assert(keys.size === apps.length, "invariant (c,w) is distinct for every OS function (injective classification)");

/* 3. トポロジー写像 */
const phone = get("topoMap")("phone");
assert(phone.ket === "|0001⟩", "phone maps to basis |0001⟩");
const camera = get("topoMap")("camera");
assert(camera.ket === "|0101⟩", "camera maps to basis |0101⟩");
const kets = new Set();
for (const a of apps) kets.add(get("topoMap")(a.id).ket);
assert(kets.size === apps.length, "φ is injective: every function gets a unique basis state");
const prep = get("qkInterpret")(camera.program);
assert(/\|0101⟩ 1\.000/.test(prep), "camera's preparation circuit reaches |0101⟩ with amplitude 1.000");
assert(get("topoMap")("nosuch") === null, "unknown function maps to null");

/* 4. 連続変形 */
const route = get("topoRoute")("phone", "camera");
assert(route.hamming === 1 && route.steps.length === 1 && route.steps[0] === "X q1", "phone→camera is one hypercube edge (X q1)");
const far = get("topoRoute")("ai", "settings");
assert(far.hamming === far.steps.length && far.hamming >= 1, "route step count equals Hamming distance");
const self = get("topoRoute")("phone", "phone");
assert(self.hamming === 0 && self.steps.length === 0, "identity deformation has zero steps");

/* 5. 端末プロファイル */
const sp = get("deviceProfile")("Mozilla/5.0 (Linux; Android 14; Pixel 8) Mobile Safari", 412);
assert(sp.kind === "smartphone" && sp.tel === true, "Android Mobile UA → smartphone with tel: capability");
const tb = get("deviceProfile")("Mozilla/5.0 (Linux; Android 14; SM-X910) Safari", 1280);
assert(tb.kind === "tablet" && tb.tel === true, "Android non-Mobile UA → tablet");
const ip = get("deviceProfile")("Mozilla/5.0 (iPad; CPU OS 17_0)", 1024);
assert(ip.kind === "tablet", "iPad UA → tablet");
const dt = get("deviceProfile")("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", 1920);
assert(dt.kind === "desktop" && dt.tel === false, "Windows UA → desktop without phone line");

/* 6. 電卓 */
assert(get("calcEval")("1+2*3") === 7, "calcEval respects operator precedence (1+2*3=7)");
assert(get("calcEval")("(1+2)*3") === 9, "calcEval handles parentheses ((1+2)*3=9)");
assert(Math.abs(get("calcEval")("10/4") - 2.5) < 1e-12, "calcEval divides (10/4=2.5)");
let threw = false;
try { get("calcEval")("1+"); } catch (e) { threw = true; }
assert(threw, "calcEval rejects malformed expressions");

/* 7. 意図解析 */
const it1 = get("intentDetect")("090-1234-5678 に電話をかけて");
assert(it1.intent === "phone" && it1.number === "090-1234-5678", "intent: phone call with extracted number");
assert(get("intentDetect")("写真を撮って").intent === "camera", "intent: 写真 → camera");
const it3 = get("intentDetect")("7時にアラームをかけて起こして");
assert(it3.intent === "clock" && it3.hour === "7", "intent: alarm with extracted hour");
assert(get("intentDetect")("1+2*3").intent === "calc", "intent: bare expression → calc");
assert(get("intentDetect")("qubit q0\nH q0\nmeasure").intent === "quantum_code", "intent: raw quantum code");
assert(get("intentDetect")("トポロジーの写像を見せて").intent === "topo", "intent: 写像 → topo");
assert(get("intentDetect")("こんにちは").intent === "chat", "intent: greeting → chat");

/* 8. 生成AIカーネル */
const k1 = get("aiKernel")("090-1234-5678 に電話をかけて");
assert(k1.stages.length === 6, "kernel pipeline discloses all 6 stages");
assert(k1.stages[2].name.indexOf("トポロジー写像") >= 0 && /\|0001⟩/.test(k1.stages[2].detail), "stage③ shows the topological mapping to |0001⟩");
assert(k1.action.type === "tel" && k1.action.number === "090-1234-5678", "phone request produces a tel: action");
const k2 = get("aiKernel")("1+2*3");
assert(/= 7/.test(k2.reply), "calculator request is evaluated in the reply (=7)");
const k3 = get("aiKernel")("qubit q0 q1\nH q0\nCNOT q0 q1\nstate");
assert(/0\.707/.test(k3.reply), "pasted quantum code is executed by the pseudo-quantum kernel");
const k4 = get("aiKernel")("こんにちは");
assert(k4.reply.length > 0 && k4.intent === "chat", "chat produces a generated reply");

/* 9. 実行系 (テスト環境では location が無い → 発行せず記述を返す) */
const d1 = get("osDispatch")({ action: { type: "tel", number: "0312345678" } });
assert(d1.performed === false && /tel:0312345678/.test(d1.how), "tel dispatch in test env describes the intent without navigating");
const d2 = get("osDispatch")({ action: { type: "open", app: "camera" } });
assert(d2.performed === true && /camera/.test(d2.how), "open dispatch reports the mapped transition");

/* 10. 量子暗号方式 */
const qc = get("topoMap")("qcrypt");
assert(qc !== null && qc.ket === "|1110⟩", "qcrypt is mapped to basis |1110⟩ (existing kets unchanged)");
const bb = get("qcBB84")(64, false);
assert(bb.qber === 0 && bb.eveDetected === false, "BB84 without Eve: QBER is 0 on a noiseless channel");
assert(bb.key.length > 0 && bb.sifted >= 10, "BB84 sifting yields a nonempty shared key");
assert(bb.sifted <= 64 && bb.key.length === bb.sifted - bb.checked, "key = sifted bits minus the check sample");
const bbE = get("qcBB84")(512, true);
assert(bbE.qber > 0.03, "intercept-resend eavesdropping leaves errors in the sifted key (QBER ≈ 25%)");
assert(!bbE.eveDetected || bbE.key.length === 0, "when Eve is detected the key is discarded");
const key = bb.key;
const secret = "量子暗号テスト🔐 QuantOS";
const ct = get("qcEncrypt")(secret, key);
assert(/^[0-9a-f]+$/.test(ct) && ct.indexOf(secret) < 0, "ciphertext is hex and hides the plaintext");
assert(get("qcDecrypt")(ct, key) === secret, "one-time-pad round-trip restores UTF-8 text (Japanese + emoji)");
let leaked = null;
try { leaked = get("qcDecrypt")(ct, key.map(b => 1 - b)); } catch (e) { leaked = null; }
assert(leaked !== secret, "a wrong key never reveals the plaintext");
let noKey = false;
try { get("qcEncrypt")("x", []); } catch (e) { noKey = true; }
assert(noKey, "encrypting without a distributed key is rejected");
const itc = get("intentDetect")("BB84で量子鍵配送して");
assert(itc.intent === "qcrypt", "intent: 鍵配送 → qcrypt (wins over 量子ラボ)");
assert(get("intentDetect")("盗聴されていないか暗号を確認").eve === true, "intent: 盗聴 sets the Eve flag");
const kq = get("aiKernel")("量子暗号の鍵配送をして");
assert(kq.intent === "qcrypt" && /QBER/.test(kq.reply), "AI kernel runs BB84 and reports the QBER");
assert(/\|1110⟩/.test(kq.stages[2].detail), "stage③ maps the request onto qcrypt's basis |1110⟩");

/* 11. アプリランチャー + Play ストア */
const ap = get("topoMap")("apps");
assert(ap !== null && ap.ket === "|1111⟩", "apps launcher is mapped to basis |1111⟩ (register is now fully populated)");
assert(get("deviceProfile")("Mozilla/5.0 (Linux; Android 14; Pixel 8) Mobile Safari", 412).android === true, "Android UA sets the android capability flag");
assert(get("deviceProfile")("Mozilla/5.0 (Windows NT 10.0)", 1920).android === false, "desktop UA has no android capability");
const yt = get("appLaunch")("YouTube");
assert(yt.found && yt.store === "market://details?id=com.google.android.youtube", "YouTube resolves to its Play Store page");
assert(/^vnd\.youtube:/.test(yt.launch), "YouTube launches via its URL scheme");
const unk = get("appLaunch")("謎のアプリ999");
assert(!unk.found && /^market:\/\/search\?q=/.test(unk.store), "unknown apps fall back to a Play Store search");
const home = get("appLaunch")("");
assert(home.found && /play\.google\.com/.test(home.launch), "empty query opens the Play Store itself");
const tk = get("appLaunch")("TikTok");
assert(tk.found && tk.launch === tk.store, "an app without a URL scheme launches via its Play Store page");
assert(get("intentDetect")("YouTubeを開いて").intent === "launch", "intent: YouTubeを開いて → launch");
assert(get("intentDetect")("LINEをインストールして").intent === "store", "intent: インストール → store");
assert(get("intentDetect")("Playストアを開いて").intent === "store", "intent: Play ストア → store");
assert(get("intentDetect")("アプリ一覧を見せて").intent === "apps", "intent: アプリ一覧 → apps panel");
const kl = get("aiKernel")("YouTubeを開いて");
assert(kl.action.type === "launch" && /vnd\.youtube/.test(kl.action.launch.launch), "AI kernel produces a launch action with the app's scheme");
assert(/\|1111⟩/.test(kl.stages[2].detail), "stage③ maps the launch request onto |1111⟩");
const ks = get("aiKernel")("LINEをインストールして");
assert(ks.action.type === "market" && ks.action.launch.store === "market://details?id=jp.naver.line.android", "install request produces a market: action for LINE");
const dl = get("osDispatch")({ action: { type: "launch", app: "apps", launch: yt } });
assert(dl.performed === false && /vnd\.youtube/.test(dl.how), "launch dispatch outside Android describes the intent without navigating");
assert(get("intentDetect")("カメラを起動して").intent === "camera", "built-in functions still win over the app catalog (カメラ → camera)");

/* 12. フリーフォーム / マルチウィンドウ */
const dex = get("deviceProfile")("Mozilla/5.0 (Linux; Android 13; SM-X910) AppleWebKit Chrome/120 Safari", 1920);
assert(dex.samsung && dex.dex && dex.freeform, "Samsung tablet UA without 'Mobile' is detected as DeX with freeform support");
const galaxy = get("deviceProfile")("Mozilla/5.0 (Linux; Android 14; SM-S928B) Mobile Safari", 412);
assert(galaxy.samsung && !galaxy.dex && galaxy.freeform && galaxy.multiWindow, "Galaxy phone: Samsung freeform yes, DeX no");
const pixel = get("deviceProfile")("Mozilla/5.0 (Linux; Android 14; Pixel 8) Mobile Safari", 412);
assert(!pixel.samsung && pixel.multiWindow && !pixel.freeform, "non-Samsung Android: split-screen only, no Samsung freeform");
assert(/DeX/.test(get("wmDeviceSupport")(dex).note), "wmDeviceSupport names DeX when detected");
assert(get("wmDeviceSupport")(get("deviceProfile")("Windows NT 10.0", 1920)).multiWindow === false, "desktop reports no device-side multi-window");

const st = get("wmNewState")(1000, 600);
assert(st.mode === "fullscreen" && st.wins.length === 0, "window manager starts empty in fullscreen mode");
get("wmOpen")(st, "phone"); get("wmOpen")(st, "camera"); get("wmOpen")(st, "qlab");
assert(st.wins.length === 3 && st.focus === st.wins[2].id, "three windows open, the last one holds focus");
get("wmOpen")(st, "phone");
assert(st.wins.length === 3 && get("wmGet")(st, st.focus).appId === "phone", "re-opening an app focuses its existing window instead of duplicating");
const phoneId = st.focus;
get("wmTile")(st, "split2");
const vis = st.wins.slice().sort((a, b) => a.z - b.z);
assert(vis[0].x === 0 && vis[0].w === 500 && vis[1].x === 500 && vis[1].w === 500, "split2 tiles the two lowest windows into left/right halves");
get("wmTile")(st, "grid4");
const cells = st.wins.map(w => w.x + "," + w.y + "," + w.w + "," + w.h);
assert(new Set(cells).size === 3, "grid4 gives every window a distinct cell");
assert(st.wins.every(w => w.w === 500 && w.h === 300), "grid4 cells are quarter-sized");
get("wmSnap")(st, phoneId, "left");
const ph = get("wmGet")(st, phoneId);
assert(ph.x === 0 && ph.y === 0 && ph.w === 500 && ph.h === 600, "snapping to the left edge fills the left half");
get("wmSnap")(st, phoneId, "max");
assert(get("wmGet")(st, phoneId).w === 1000 && get("wmGet")(st, phoneId).h === 600, "maximize fills the viewport");
get("wmResize")(st, phoneId, 10, 10);
assert(get("wmGet")(st, phoneId).w === 260 && get("wmGet")(st, phoneId).h === 180, "windows cannot be resized below the minimum");
get("wmMove")(st, phoneId, -500, -500);
assert(get("wmGet")(st, phoneId).x === 0 && get("wmGet")(st, phoneId).y === 0, "windows cannot be dragged off the top-left");
get("wmMinimize")(st, phoneId);
assert(get("wmGet")(st, phoneId).min === true && st.focus !== phoneId, "minimizing hands focus to another window");
assert(get("wmVisible")(st).length === 2, "minimized windows are not visible");
get("wmFocus")(st, phoneId);
assert(get("wmGet")(st, phoneId).min === false && st.focus === phoneId, "focusing restores a minimized window");

/* 重なり = 組み紐 */
const bs = get("wmNewState")(1200, 700);
get("wmOpen")(bs, "phone"); get("wmOpen")(bs, "camera"); get("wmOpen")(bs, "qlab");
const ws = bs.wins;
ws[0].x = 0; ws[1].x = 100; ws[2].x = 200;          /* x 昇順, z も昇順 → 交差なし */
ws[0].z = 1; ws[1].z = 2; ws[2].z = 3;
let br = get("wmBraidWord")(bs);
assert(br.strands === 3 && br.crossings === 0 && /自明/.test(br.text), "windows stacked in x-order form the trivial braid");
assert(br.invariant.bracket === "1", "the trivial braid closes to the unknot bracket 1");
ws[0].z = 3; ws[1].z = 2; ws[2].z = 1;               /* z を反転 → 転倒数 3 */
br = get("wmBraidWord")(bs);
assert(br.crossings === 3 && br.word.length === 3, "fully reversed stacking gives 3 crossings (n(n-1)/2)");
assert(br.invariant.writhe === 3 && /\(−A³\)\^3/.test(br.invariant.bracket), "the braid's writhe feeds the same Kauffman bracket as the topology mapping");
ws[0].z = 1; ws[1].z = 3; ws[2].z = 2;               /* 1 転倒 */
br = get("wmBraidWord")(bs);
assert(br.crossings === 1 && br.word[0] === "σ₂", "a single overlap is the generator σ₂");

/* 隣接ウィンドウ起動 (Samsung マルチウィンドウ) */
const ytA = get("appLaunch")("YouTube");
assert(/launchFlags=0x10001000/.test(ytA.adjacent) && /package=com\.google\.android\.youtube/.test(ytA.adjacent),
       "adjacent launch builds an intent: URI with FLAG_ACTIVITY_LAUNCH_ADJACENT");
assert(get("appLaunch")("謎のアプリ999").adjacent === null, "unknown apps have no adjacent-launch intent");
const dAdj = get("osDispatch")({ action: { type: "adjacent", app: "apps", launch: ytA } });
assert(dAdj.performed === false && /launchFlags=0x10001000/.test(dAdj.how), "adjacent dispatch outside Android describes the split-screen intent");

/* 意図解析 + AIカーネル */
assert(get("intentDetect")("マルチウィンドウにして").intent === "window", "intent: マルチウィンドウ → window");
assert(get("intentDetect")("ウィンドウを左右に分割して").layout === "split2", "intent: 左右に分割 → split2 layout");
assert(get("intentDetect")("窓を上下に並べて").layout === "vsplit2", "intent: 上下に並べて → vsplit2 layout");
assert(get("intentDetect")("4分割の格子に並べて").layout === "grid4", "intent: 格子4 → grid4 layout");
assert(get("intentDetect")("フリーフォームにして").layout === null, "plain freeform request carries no forced layout");
const kw = get("aiKernel")("ウィンドウを左右に分割して");
assert(kw.action.type === "window" && kw.action.layout === "split2", "AI kernel produces a window action with the split2 layout");
assert(/フリーフォーム/.test(kw.reply) && /左右2分割/.test(kw.reply), "AI kernel explains the freeform switch and the layout");

console.log("\nALL ENGINE TESTS PASSED");
