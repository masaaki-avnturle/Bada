/*
 * engine-test.js — クリアキャスト東京 (ClearCast Tokyo) のエンジン単体テスト
 *
 *   node clearcast_tokyo/tools/engine-test.js
 *
 * index.html のインライン <script> を抜き出し、DOM をスタブして
 * 純ロジック部分を検証します:
 *   1. クリーン・シグナル・エンジン — RTT ジッタ統計 (μ / σ / min / max)
 *   2. ITU-T G.107 E モデル — R 値 / MOS 変換 (境界含む) / 単調性
 *   3. 推奨画質 (帯域しきい値) / 推奨バッファ (clamp 2s–30s)
 *   4. YouTube 公式埋め込み URL の生成と入力正規化 (parseYouTubeId)
 *   5. 局カタログの整合性 — 公式配信ドメインの許可リストのみを含むこと
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
  return new Proxy({ style: { setProperty(){} }, classList: { add(){}, remove(){}, toggle(){} },
                     value: "", textContent: "", innerHTML: "", checked: false,
                     children: [], width: 1280, height: 720 }, {
    get(t, p){
      if (p in t) return t[p];
      if (p === "querySelectorAll") return function(){ return []; };
      if (p === "querySelector" || p === "appendChild" || p === "createElement" ||
          p === "getContext" || p === "removeChild" || p === "replaceChildren" ||
          p === "setAttribute" || p === "getAttribute") {
        return function(){ return stubEl(); };
      }
      if (p === "addEventListener" || p === "removeEventListener" || p === "focus" ||
          p === "getBoundingClientRect") {
        return function(){ return { left: 0, top: 0, width: 1280, height: 720 }; };
      }
      return function(){ return stubEl(); };
    },
    set(t, p, v){ t[p] = v; return true; }
  });
}
const sandbox = {
  console, Math, Proxy, String, Number, Object, Array, JSON, Date,
  parseFloat, parseInt, isNaN, isFinite, encodeURIComponent,
  setTimeout: function(fn){ fn(); }, setInterval: function(){ return 0; }, clearInterval: function(){},
  requestAnimationFrame: function(){},
  document: {
    getElementById(){ return stubEl(); }, createElement(){ return stubEl(); },
    querySelectorAll(){ return []; }, addEventListener(){}, removeEventListener(){},
    documentElement: stubEl()
  },
  navigator: {},
  window: {}
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

console.log("1. ジッタ統計 (jitterStats)");
{
  const st = S.jitterStats([10, 20, 30]);
  near(st.mean, 20, 1e-9, "mean μ = 20");
  near(st.sd, Math.sqrt(200 / 3), 1e-9, "sd σ = √(200/3)");
  ok(st.min === 10 && st.max === 30 && st.n === 3, "min/max/n");
  const z = S.jitterStats([]);
  ok(z.n === 0 && z.mean === 0 && z.sd === 0, "空配列は 0 で退化");
}

console.log("2. E モデル (ITU-T G.107) — R 値と MOS");
{
  near(S.emodelR(0, 0, 0), 93.2, 1e-9, "理想回線で R = 93.2 (基準値)");
  const mosBest = S.mosFromR(93.2);
  ok(mosBest > 4.3 && mosBest < 4.5, "R=93.2 → MOS ≈ 4.4");
  ok(S.mosFromR(-10) === 1.0, "R<0 → MOS=1.0 (下限)");
  ok(S.mosFromR(150) === 4.5, "R>100 → MOS=4.5 (上限)");
  ok(S.emodelR(300, 50, 5) < S.emodelR(50, 5, 0), "遅延・損失が増えると R は単調減少");
  // 損失項 Ie,eff = 95·p/(p+10): p=10% で 47.5
  near(S.emodelR(0, 0, 10), 93.2 - 47.5, 1e-9, "損失 10% の Ie,eff = 47.5");
}

console.log("3. 推奨画質・推奨バッファ");
{
  ok(S.recommendQuality(10).indexOf("1080p") === 0, "≥6 Mbps → 1080p");
  ok(S.recommendQuality(4).indexOf("720p") === 0, "≥3 Mbps → 720p");
  ok(S.recommendQuality(2).indexOf("480p") === 0, "≥1.5 Mbps → 480p");
  ok(S.recommendQuality(1).indexOf("360p") === 0, "≥0.7 Mbps → 360p");
  ok(S.recommendQuality(0.1).indexOf("音声") === 0, "低帯域 → 音声のみ");
  near(S.recommendBufferSec(0, 0), 2, 1e-9, "下限 clamp = 2s");
  near(S.recommendBufferSec(5000, 5000), 30, 1e-9, "上限 clamp = 30s");
  near(S.recommendBufferSec(1000, 250), 6, 1e-9, "3·(μ+4σ)/1000 = 6s");
}

console.log("4. YouTube 公式埋め込み URL と入力正規化");
{
  const u = S.ytEmbedURL("UC6AG81pAkf6Lbi_1VC5NmPA");
  ok(u.indexOf("https://www.youtube-nocookie.com/embed/live_stream?channel=UC6AG81pAkf6Lbi_1VC5NmPA") === 0,
     "live_stream 埋め込み URL");
  ok(S.ytStreamsURL("UCabc").indexOf("/channel/UCabc/streams") > 0, "ライブ一覧 URL");
  let p = S.parseYouTubeId("UC6AG81pAkf6Lbi_1VC5NmPA");
  ok(p && p.type === "channel" && p.id === "UC6AG81pAkf6Lbi_1VC5NmPA", "生のチャンネル ID");
  p = S.parseYouTubeId("https://www.youtube.com/watch?v=Anr15FA9OCI");
  ok(p && p.type === "video" && p.id === "Anr15FA9OCI", "watch URL → video ID");
  p = S.parseYouTubeId("https://youtu.be/Anr15FA9OCI");
  ok(p && p.type === "video" && p.id === "Anr15FA9OCI", "youtu.be 短縮 URL");
  p = S.parseYouTubeId("https://www.youtube.com/channel/UCuTAXTexrhetbOe3zgskJBQ/streams");
  ok(p && p.type === "channel" && p.id === "UCuTAXTexrhetbOe3zgskJBQ", "channel URL");
  ok(S.parseYouTubeId("こんにちは") === null, "不正入力は null");
}

console.log("5. 局カタログの整合性 (公式配信ドメインのみ)");
{
  const live = S.liveCatalog();
  ok(live.length === 5, "在京キー局系列 5 チャンネル");
  ok(live.every(s => /^UC[0-9A-Za-z_-]{20,}$/.test(s.ch)), "全ライブが正規のチャンネル ID");
  const tv = S.tvCatalog();
  const tvAllow = ["tver.jp", "plus.nhk.jp", "abema.tv", "s.mxtv.jp", "www3.nhk.or.jp"];
  ok(tv.every(s => s.url.startsWith("https://") && tvAllow.some(d => s.url.indexOf("://" + d + "/") > 0)),
     "テレビ公式リンクは許可ドメインのみ (" + tvAllow.join(", ") + ")");
  const radio = S.radioCatalog();
  ok(radio.length === 10, "東京のラジオ 10 局");
  ok(radio.every(s => s.url.startsWith("https://radiko.jp/") || s.url.startsWith("https://www.nhk.or.jp/radio/")),
     "ラジオは radiko / らじる★らじる の公式のみ");
  const lab = S.mosLabel(4.2);
  ok(lab.cls === "mos-ok", "MOS 4.2 → 優秀");
  ok(S.mosLabel(3.5).cls === "mos-warn" && S.mosLabel(2.0).cls === "mos-bad", "MOS ラベル境界");
}

console.log("");
console.log("結果: " + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
