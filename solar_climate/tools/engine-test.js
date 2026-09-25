/*
 * engine-test.js — Bada SolarCast のエンジン単体テスト
 *
 *   node solar_climate/tools/engine-test.js
 *
 * index.html の <script id="engine"> (DOM 非依存) を抜き出して検証します:
 *   1. Γ 関数 (Lanczos) と部分積分の関数等式 Γ(z+1) = zΓ(z)
 *   2. Jones 多項式 (三葉結び目) の熱感知 — 既知値と範囲
 *   3. フレアクラス / フレア指数 / Kp ラベル
 *   4. NOAA 形式のパーサ (X 線 JSON, Kp 新旧形式, daily-solar-indices, 27-day outlook)
 *   5. 統計 — Pearson / 線形回帰 / トレンド除去 / ラグ相関 / 置換検定
 *   6. 日付・スコトーマ (予報の地平線) と確率の混合
 *   7. 気候値 (同じ月日 ±窓) とアンサンブル集計
 * UI 側のインライン JS は構文チェックのみ行います。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const eng = src.match(/<script id="engine">([\s\S]*?)<\/script>/);
if (!eng) { console.error("no <script id=\"engine\"> in index.html"); process.exit(1); }
const ui = src.match(/<script>([\s\S]*?)<\/script>/);
if (!ui) { console.error("no UI <script> in index.html"); process.exit(1); }
new vm.Script(ui[1], { filename: "ui.js" });           // 構文チェック

const ctx = { module: { exports: {} } };
vm.createContext(ctx);
vm.runInContext(eng[1], ctx, { filename: "engine.js" });
const SC = ctx.module.exports;

let pass = 0, fail = 0;
function ok(cond, msg){ if (cond){ pass++; } else { fail++; console.error("FAIL: " + msg); } }
function near(a, b, eps, msg){ ok(Math.abs(a - b) <= eps, msg + " (got " + a + ", want " + b + ")"); }

/* 1. Γ */
near(SC.gammaFn(1), 1, 1e-10, "Γ(1)=1");
near(SC.gammaFn(5), 24, 1e-8, "Γ(5)=24");
near(SC.gammaFn(0.5) ** 2, Math.PI, 1e-10, "Γ(0.5)²=π");
near(SC.gammaFn(0.25), 3.6256099082219083, 1e-9, "Γ(0.25) (反射公式側)");
[0.57, 0.70, 5.58, 2.3, 10.1].forEach(w => near(SC.gammaCheck(w), 1, 1e-10, "Γ(z+1)=zΓ(z) at " + w));

/* 2. Jones 熱感知: V(1) = -1+1+1 = 1,  V(-1) = -1-1-1 = -3 */
near(SC.jonesAbs(0), 1, 1e-12, "|V(e^{i0})| = 1");
near(SC.jonesAbs(Math.PI), 3, 1e-12, "|V(e^{iπ})| = 3");
near(SC.heatTheta(-40), 0, 1e-12, "θ(-40°C) = 0");
near(SC.heatTheta(50), Math.PI, 1e-12, "θ(50°C) = π");
near(SC.heatTheta(99), Math.PI, 1e-12, "θ はクランプされる");
for (let t = -60; t <= 70; t += 0.5){
  const h = SC.jonesHeat(t);
  ok(h >= 0 && h <= 1 + 1e-12, "熱感知指数は 0..1: " + t);
}
ok(isNaN(SC.jonesHeat(NaN)), "NaN 気温は NaN");
// 直接計算との一致 (複素数で V を評価)
for (const th of [0.3, 1.1, 2.2]){
  let re = 0, im = 0;
  [[-4, -1], [-3, 1], [-1, 1]].forEach(([k, c]) => { re += c * Math.cos(k * th); im += c * Math.sin(k * th); });
  near(SC.jonesAbs(th), Math.hypot(re, im), 1e-12, "jonesAbs = |V(e^{iθ})| at " + th);
}

/* 3. フレア */
ok(SC.flareClass(2.3e-5) === "M2.3", "M2.3");
ok(SC.flareClass(1e-4) === "X1.0", "X1.0");
ok(SC.flareClass(1.2e-3) === "X12.0", "X12");
ok(SC.flareClass(5e-7) === "B5.0", "B5.0");
ok(SC.flareClass(3e-9) === "A0.3", "A 未満も A 表記");
ok(SC.flareClass(0) === "—", "0 は —");
ok(SC.flareIndex(3, 1, 0) === 13, "フレア指数 C+10M+100X");
ok(isNaN(SC.flareIndex(NaN, 0, 0)), "欠測は NaN");
ok(SC.kpLabel(5.3) === "G1 (小)" && SC.kpLabel(2) === "静穏" && SC.kpLabel(9) === "G5 (極端)", "Kp ラベル");

/* 4. パーサ */
const xr = SC.parseXrays([
  { time_tag: "2025-09-20T00:01:00Z", energy: "0.05-0.4nm", flux: 1e-8 },
  { time_tag: "2025-09-20T00:02:00Z", energy: "0.1-0.8nm", flux: 2e-6 },
  { time_tag: "2025-09-20T00:00:00Z", energy: "0.1-0.8nm", flux: 1e-6 },
  { time_tag: "2025-09-20T00:03:00Z", energy: "0.1-0.8nm", flux: 0 }
]);
ok(xr.length === 2 && xr[0].flux === 1e-6 && xr[1].flux === 2e-6, "X 線: 長波長チャネルのみ・時刻順・0 除外");
const kpOld = SC.parseKp([["time_tag", "Kp", "a_running", "station_count"],
  ["2025-09-20 00:00:00.000", "3.33", "18", "8"], ["2025-09-20 03:00:00.000", "5.00", "48", "8"]]);
ok(kpOld.length === 2 && kpOld[1].kp === 5 && kpOld[0].t === Date.UTC(2025, 8, 20, 0), "Kp 旧形式");
const kpNew = SC.parseKp([{ time_tag: "2025-09-20T00:00:00", Kp: 2.67 }, { time_tag: "2025-09-20T03:00:00", Kp: 4 }]);
ok(kpNew.length === 2 && kpNew[0].kp === 2.67 && kpNew[0].t === Date.UTC(2025, 8, 20, 0), "Kp 新形式");
const daily = SC.parseDailySolar([
  ":Product: Daily Solar Data            DSD.txt",
  "#  Date     Radio  SESC     Area  New   Mean  Bkgd  X-Ray Flares         Optical Flares",
  "2025 09 01  158    103     680     1     -999  B7.0    5  1  0   8  1  0  0",
  "2025 09 02  149     87     420     0     -999  B5.4    2  0  1   3  0  0  0",
  "2025 09 03   -1     -1      -1     0     -999     *   -1 -1 -1  -1 -1 -1 -1"
].join("\n"));
ok(daily.length === 3, "daily-solar-indices 3 行");
ok(daily[0].date === "2025-09-01" && daily[0].f107 === 158 && daily[0].ssn === 103, "日付・F10.7・黒点数");
ok(daily[0].c === 5 && daily[0].m === 1 && daily[0].x === 0 && daily[1].x === 1, "C/M/X 数");
ok(isNaN(daily[2].f107) && isNaN(daily[2].c), "欠測 (-1) は NaN");
const ol = SC.parseOutlook([
  ":Product: 27-day Space Weather Outlook Table 27DO.txt",
  "#  Date       10.7 cm      A Index    Kp Index",
  "2025 Sep 22     140           8          3",
  "2025 Oct 01     155          12          4"
].join("\n"));
ok(ol.length === 2 && ol[0].date === "2025-09-22" && ol[1].date === "2025-10-01" && ol[1].kp === 4 && ol[0].f107 === 140, "27 日見通し");

/* 5. 統計 */
near(SC.pearson([1, 2, 3, 4], [2, 4, 6, 8]).r, 1, 1e-12, "完全正相関");
near(SC.pearson([1, 2, 3, 4], [8, 6, 4, 2]).r, -1, 1e-12, "完全負相関");
ok(SC.pearson([1, 2, NaN, 4, 5], [1, 2, 99, 4, 5]).n === 4, "NaN の組は除外");
ok(isNaN(SC.pearson([1, 1, 1], [1, 2, 3]).r), "分散 0 は NaN");
const lf = SC.linfit([0, 1, 2, 3], [1, 3, 5, 7]);
near(lf.a, 1, 1e-12, "切片"); near(lf.b, 2, 1e-12, "傾き");
ok(SC.detrend([1, 3, 5, 7]).every(v => Math.abs(v) < 1e-12), "直線はトレンド除去で 0");
near(SC.quantile([1, 2, 3, 4, 5], 0.5), 3, 1e-12, "中央値");
near(SC.quantile([1, 2, 3, 4, 5], 0.1), 1.4, 1e-12, "10% 分位 (線形補間)");

// 既知のラグ: w[t] = s[t-3] → ラグ 3 で r = 1
const R = SC.rng(7);
const s = Array.from({ length: 40 }, () => R());
const w = s.map((_, i) => i >= 3 ? s[i - 3] : R());
const lc = SC.laggedCorr(s, w, 6);
near(lc[3].r, 1, 1e-12, "ラグ 3 で r=1");
ok(lc[3].n === 37, "ラグ 3 の重なりは n-3");
const pt = SC.permutationTest(s, w, 6, 500, 1);
ok(pt.p < 0.01, "埋め込んだ信号は有意 (p=" + pt.p + ")");
// 無関係な系列は多くの場合有意にならない: 50 試行で偽陽性率を確認
let fp = 0;
for (let k = 0; k < 50; k++){
  const r2 = SC.rng(100 + k);
  const a = Array.from({ length: 30 }, () => r2()), b = Array.from({ length: 30 }, () => r2());
  if (SC.permutationTest(a, b, 14, 200, k).p < 0.05) fp++;
}
ok(fp <= 8, "独立系列の偽陽性は約 5% (50 試行中 " + fp + ")");
const bs = SC.blockShuffle([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 5, SC.rng(3));
ok(bs.length === 11 && bs.slice().sort((a, b) => a - b).join() === "1,2,3,4,5,6,7,8,9,10,11", "ブロック置換は並べ替えのみ");
ok([0, 5, 10].some(i => bs[i] === 1) && bs[bs.indexOf(1) + 1] === 2, "ブロック内の順序は保存");
// 自己相関のある独立系列 (AR(1), φ=0.7) でも偽陽性が大きく膨らまないこと
let fpAr = 0;
for (let k = 0; k < 60; k++){
  const r3 = SC.rng(900 + k);
  const ar = () => { const o = []; let v = 0; for (let i = 0; i < 30; i++){ v = 0.7 * v + (r3() - 0.5); o.push(v); } return o; };
  if (SC.permutationTest(ar(), SC.detrend(ar()), 14, 200, k).p < 0.05) fpAr++;
}
ok(fpAr <= 9, "AR(1) 独立系列の偽陽性 (60 試行中 " + fpAr + ")");
console.log("  偽陽性: iid " + fp + "/50, AR(1) " + fpAr + "/60");
// 決定性 (同じ seed → 同じ p)
ok(SC.permutationTest(s, w, 6, 200, 9).p === SC.permutationTest(s, w, 6, 200, 9).p, "置換検定は seed で再現可能");

/* 6. 日付・スコトーマ */
ok(SC.leadDays("2025-12-25", "2025-12-10") === 15, "リード日数");
ok(SC.leadDays("2026-01-01", "2025-12-31") === 1, "年跨ぎ");
ok(SC.leadDays("2025-03-30", "2025-03-29") === 1, "夏時間でもずれない (UTC 計算)");
ok(SC.doy("2025-01-01") === 1 && SC.doy("2025-12-31") === 365 && SC.doy("2024-02-29") === SC.doy("2024-02-28"), "通日");
ok(SC.doyDist("2025-12-30", "2025-01-02") === 3, "年末年始の距離は巡回");
ok(SC.nextChristmas("2026-09-25") === 2026 && SC.nextChristmas("2026-12-25") === 2026 && SC.nextChristmas("2026-12-26") === 2027, "次のクリスマス");
ok(SC.forecastWeight(0) === 1 && SC.forecastWeight(8) === 0.5 && SC.forecastWeight(16) === 0 && SC.forecastWeight(400) === 0, "予報の重み");
ok(!SC.inScotoma(15) && SC.inScotoma(16) && SC.inScotoma(91), "スコトーマの境界");
near(SC.blend(1, 0, 8), 0.5, 1e-12, "混合: 半々");
near(SC.blend(0.9, 0.2, 100), 0.2, 1e-12, "スコトーマ内は気候値そのもの");
near(SC.blend(NaN, 0.3, 2), 0.3, 1e-12, "予報欠測は気候値");

/* 7. 気候値 */
const time = [], tmax = [], tmin = [], pr = [], sn = [];
for (let y = 1991; y <= 2020; y++){
  for (const md of ["12-22", "12-23", "12-24", "12-25", "12-26", "12-27", "12-28", "07-01"]){
    time.push(y + "-" + md);
    const warm = md === "07-01";
    tmax.push(warm ? 25 : 6 + (y - 1991) * 0.03);   // 30 年で +0.87 °C
    tmin.push(warm ? 15 : (y % 4 === 0 ? -2 : 2));  // 4 年に 1 回霜
    pr.push(y % 2 === 0 ? 3 : 0);                   // 2 年に 1 回雨
    sn.push(y % 10 === 0 ? 1 : 0);                  // 10 年に 1 回雪
  }
}
const daily2 = { time, temperature_2m_max: tmax, temperature_2m_min: tmin, precipitation_sum: pr, snowfall_sum: sn };
const c3 = SC.climatology(daily2, "2030-12-25", 3);
ok(c3.n === 30 * 7, "±3 日窓で 7 日 × 30 年 (7 月は除外)");
near(c3.pRain, 0.5, 1e-12, "雨の確率");
near(c3.pSnow, 0.1, 1e-12, "雪の確率");
near(c3.pFrost, 8 / 30, 1e-12, "霜の確率 (1992..2020 の 4 の倍数年 = 8 年)");
near(c3.trendPerDecade, 0.3, 1e-9, "温暖化傾向 +0.3 °C/10 年");
ok(c3.firstYear === 1991 && c3.lastYear === 2020, "期間");
const c0 = SC.climatology(daily2, "2030-12-25", 0);
ok(c0.n === 30 && c0.rows.every(r => r.date.endsWith("12-25")), "窓 0 は当日のみ");
const cNull = SC.climatology({ time: ["2000-12-25"], temperature_2m_max: [null], temperature_2m_min: [null], precipitation_sum: [null], snowfall_sum: [null] }, "2030-12-25", 0);
ok(isNaN(cNull.pRain) && isNaN(cNull.tmaxMean), "欠測のみなら NaN");

const hourly = {
  time: ["2025-12-24T22:00", "2025-12-25T00:00", "2025-12-25T12:00", "2025-12-26T00:00"],
  precipitation: [9, 0.5, 1.0, 9],
  precipitation_member01: [9, 0, 0, 9],
  precipitation_member02: [9, 2, null, 9],
  temperature_2m: [0, 3, 7, 0],
  temperature_2m_member01: [0, 1, 4, 0],
  temperature_2m_mean: [0, 99, 99, 0]      // メンバーではない派生キーは含めない
};
const ep = SC.ensembleDaily(hourly, "precipitation", "2025-12-25", "sum");
ok(ep.length === 3 && ep[0] === 1.5 && ep[1] === 0 && ep[2] === 2, "アンサンブル日降水 (null 無視)");
const et = SC.ensembleDaily(hourly, "temperature_2m", "2025-12-25", "max");
ok(et.length === 2 && et[0] === 7 && et[1] === 4, "アンサンブル日最高 (派生キー除外)");
near(SC.fracWhere(ep, v => v >= 1), 2 / 3, 1e-12, "メンバー割合 = 確率");
ok(SC.ensembleDaily(hourly, "precipitation", "2030-01-01", "sum").length === 0, "該当日なしは空");
ok(SC.wmoText(71) === "弱い雪" && SC.wmoText(1234) === "コード 1234", "WMO コード");

/* 8. 地域検索 / 複数地点 */
const gu = SC.geocodeUrl(" 北海道 ", "jp");
ok(gu.includes("name=%E5%8C%97%E6%B5%B7%E9%81%93&") || gu.endsWith("name=%E5%8C%97%E6%B5%B7%E9%81%93&countryCode=JP"), "地名は trim + URL エンコード");
ok(gu.includes("countryCode=JP") && gu.includes("count=10") && gu.includes("language=ja"), "国コード・件数・言語");
ok(!SC.geocodeUrl("Paris", "").includes("countryCode") && !SC.geocodeUrl("Paris", "x;y").includes("countryCode"), "全世界 / 不正な国コードは付けない");
const geo = SC.parseGeocode({ results: [
  { name: "札幌市", latitude: 43.06, longitude: 141.35, country: "日本", country_code: "JP", admin1: "北海道", admin2: "札幌市", feature_code: "PPLA", population: 1973395, elevation: 29 },
  { name: "Yorkshire", latitude: 54, longitude: -1.5, country: "イギリス", country_code: "GB", admin1: "England", feature_code: "ADM2" },
  { name: "bad", latitude: null, longitude: 1 }
] });
ok(geo.length === 2, "座標のない結果は除外");
ok(geo[0].region === "北海道" && geo[0].kind === "州都・県庁所在地" && geo[0].pop === 1973395, "地域名 (地名と同じ admin2 は省く)・種類・人口");
ok(geo[0].label === "日本 · 北海道 · 札幌市", "ラベル = 国 · 地域 · 地名");
ok(geo[1].kind === "郡・地方" && geo[1].label === "イギリス · England · Yorkshire", "行政区画の検索");
ok(SC.parseGeocode({}).length === 0 && SC.parseGeocode(null).length === 0, "結果なし");
const pts = [{ lat: 35.68, lon: 139.69 }, { lat: 34.69, lon: 135.5 }];
const mu = SC.multiForecastUrl(pts);
ok(mu.includes("latitude=35.68,34.69") && mu.includes("longitude=139.69,135.5") && mu.includes("forecast_days=3"), "複数地点 URL");
const day = t => ({ daily: { time: ["2026-09-25", "2026-09-26"], weather_code: [0, 61], temperature_2m_max: [25, t], temperature_2m_min: [18, null],
  precipitation_sum: [0, 5], precipitation_probability_max: [10, 80] } });
const pm = SC.parseMulti([day(22), day(27)], pts);
ok(pm.length === 2 && pm[1].days[1].tmax === 27 && isNaN(pm[0].days[1].tmin) && pm[0].days[1].pp === 80, "複数地点の配列応答");
const p1 = SC.parseMulti(day(20), [pts[0]]);
ok(p1.length === 1 && p1[0].days.length === 2, "1 地点ならオブジェクト応答");
ok(SC.parseMulti([day(1)], pts)[1].days.length === 0, "欠けた地点は空");
ok(SC.wmoIcon(0) === "☀️" && SC.wmoIcon(73) === "❄️" && SC.wmoIcon(63) === "🌧️" && SC.wmoIcon(95) === "⛈️" && SC.wmoIcon(3) === "☁️", "天気アイコン");

console.log(`SolarCast engine tests: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
