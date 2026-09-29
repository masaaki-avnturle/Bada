#!/usr/bin/env node
/*
 * engine-test.js — Blueprint Studio の数値テスト (Node, DOM 不要)。
 *   レポート値との一致: Riemann–Siegel θ/Z, Jones V(t*), UFO の揚力比・上昇軌道, 方程式レジストリ件数,
 *   PDF 書き出しの構造, 3 アプリのフレーム関数がモック Canvas で例外なく最後まで描けること。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
let fails = 0;
function ok(cond, msg) { console.log((cond ? "  ok   " : "  FAIL ") + msg); if (!cond) fails++; }
function near(a, b, tol, msg) { ok(Math.abs(a - b) <= tol, msg + "  (" + a + " vs " + b + ")"); }

/* モック Canvas 2D コンテキスト (呼び出しを受け流す) */
function mockCtx() {
  const noop = () => {};
  return new Proxy({}, {
    get(t, k) {
      if (k === "measureText") return s => ({ width: String(s).length * 8 });
      if (k in t) return t[k];
      return noop;
    },
    set(t, k, v) { t[k] = v; return true; }
  });
}

function loadApp(app) {
  const reg = JSON.parse(fs.readFileSync(path.join(ROOT, "..", "data", "equations.json"), "utf8"));
  let registry = reg.map(e => [e.id, e.status, (e.tags && e.tags[0]) || "OTHER", e.eq]);
  if (app === "ufo") registry = registry.filter(r => r[0].startsWith("UFO."));
  if (app === "chatgpt") registry = [];
  const sandbox = { console, Math, Float32Array, Uint8Array, Blob: function (c, o) { this.c = c; this.type = o && o.type; },
                    atob: s => Buffer.from(s, "base64").toString("binary"), BP_REGISTRY: registry };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(ROOT, "src", "engine.js"), "utf8"), sandbox);
  vm.runInContext(fs.readFileSync(path.join(ROOT, "src", app + ".js"), "utf8"), sandbox);
  return sandbox;
}

console.log("[engine] special functions");
const E = loadApp("transporter");
const BP = E.BP;
near(BP.rsTheta(11.7722), -2.58135979084479, 1e-9, "Riemann–Siegel θ(11.7722) = −2.581360");
near(BP.rsZ(11.7722), -1.33415332468586, 1e-8, "Z(11.7722) = −1.334153");
near(BP.rsZ(14.134725142), 0, 1e-6, "Z の第 1 零点 t = 14.1347");
near(BP.zeta({ re: 2, im: 0 }).re, Math.PI * Math.PI / 6, 1e-12, "ζ(2) = π²/6");

console.log("[transporter]");
const TR = E.BP_APP._test;
near(TR.VT["3_1"][0], -0.116342, 2e-5, "V_3_1(t*) 実部 ≈ −0.116342 (レポート値とは 4 桁一致)");
near(TR.VT["3_1"][1], 2.30908, 5e-5, "V_3_1(t*) 虚部 = 2.30908");
near(TR.VT["4_1"][0], 3.56478, 5e-5, "V_4_1(t*) = 3.56478");
near(TR.VT["5_1"][0], -2.81527, 5e-5, "V_5_1(t*) 実部 = −2.81527");
ok(TR.REG.length === 2111, "方程式レジストリ 2111 本");
ok(TR.WINDOWS.length === 10, "共鳴窓 10 箇所");

console.log("[ufo]");
const U = loadApp("ufo").BP_APP._test;
near(U.V.U, 7.50723e11, 1e6, "U = GMm/r = 7.50723e11 J");
near(U.V.L0, 2.125, 1e-12, "L(地表) = cosh(2 log 2) = 2.125");
near(U.V.a0, 11.047, 1e-3, "a = (L−1) g_eff = 11.047");
near(U.V.L1, 2.1245, 1e-5, "L(1 km) = 2.12450");
near(U.V.h10, 607.54, 0.1, "10 ステップ後 高度 607.5 m");
near(U.V.v10, 110.454, 0.01, "10 ステップ後 速度 110.45 m/s");
near(U.V.delta, 0.6815, 1e-4, "Δ = e^π − π^e = 0.6815");
ok(U.EQS.length === 26, "UFO 方程式 26 本");

console.log("[chatgpt]");
const G = loadApp("chatgpt").BP_APP._test;
ok(G.ATTN.length === 8 && G.ATTN[0].length === 10, "注意行列 8 層 × 10×10");
ok(G.ATTN.every(A => A.every((row, i) => Math.abs(row.reduce((a, b) => a + b, 0) - 1) < 1e-9 && row.every((v, j) => j <= i || v < 1e-12))),
   "各行の和 = 1、因果マスクで上三角 = 0");

console.log("[frames + pdf] 全アプリを 0.5 秒刻みでモック描画");
for (const app of ["transporter", "chatgpt", "ufo"]) {
  const S = loadApp(app), A = S.BP_APP, ctx = mockCtx();
  let err = null;
  try {
    for (let t = 0; t < A.timeline.total; t += 0.5) A.frame(ctx, t);
    A.pdfPages.forEach(p => { S.BP.pdfFrame(ctx, 1, 1, A); p(ctx, S.BP.PDF_W, S.BP.PDF_H); });
    const pcm = A.audio(8000);
    if (pcm.length !== Math.floor(A.timeline.total * 8000) || pcm.some(v => !isFinite(v))) throw new Error("audio");
  } catch (e) { err = e; }
  ok(!err, app + ": フレーム・PDF ページ・音声が例外なく生成できる" + (err ? " — " + err.stack : ""));
}

console.log("[pdf] 構造");
const blob = BP.buildPdf([{ jpeg: new Uint8Array([0xff, 0xd8, 0xff, 0xd9]), w: 2, h: 2 }], "t");
const bytes = Buffer.concat(blob.c.map(c => Buffer.from(typeof c === "string" ? c : c)));
const s = bytes.toString("latin1");
ok(s.startsWith("%PDF-1.4") && s.trim().endsWith("%%EOF"), "ヘッダとトレーラ");
const xref = parseInt(s.match(/startxref\n(\d+)/)[1], 10);
ok(s.slice(xref, xref + 4) === "xref", "startxref が xref を指す");
ok(/\/Filter \/DCTDecode/.test(s), "JPEG (DCTDecode) 画像ページ");

console.log(fails ? "\n" + fails + " test(s) FAILED" : "\nall tests passed");
process.exit(fails ? 1 : 0);
