/*
 * vfx.js — 動画リストア (Video Restore Studio) の映像補正コア(純粋関数)
 *
 * 編集(色調・明るさ・彩度・色相・反転・回転・ズーム・速度)された動画を、
 * 逆補正して元の映像へ近づけるためのパラメータ計算とフィルタ生成。
 * 実際の描画は Canvas 側で行い、ここでは Web API に依存しない部分だけを扱う
 * ので単体テストが可能。UMD(ブラウザ global `VFX` / Node default import)。
 */
(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.VFX = api;
})(typeof self !== "undefined" ? self : (typeof globalThis !== "undefined" ? globalThis : this), function () {
  "use strict";

  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }

  /**
   * CSS filter 文字列を組み立てる。編集を「打ち消す」逆補正値を渡す想定。
   * p: { brightness, contrast, saturate, hue(deg), invert(0..1), grayscale(0..1), sepia(0..1) }
   */
  function buildFilter(p) {
    p = p || {};
    const b = p.brightness == null ? 1 : p.brightness;
    const c = p.contrast == null ? 1 : p.contrast;
    const s = p.saturate == null ? 1 : p.saturate;
    const h = p.hue == null ? 0 : p.hue;
    const inv = p.invert == null ? 0 : p.invert;
    const gray = p.grayscale == null ? 0 : p.grayscale;
    const sep = p.sepia == null ? 0 : p.sepia;
    const parts = [
      `brightness(${b.toFixed(3)})`,
      `contrast(${c.toFixed(3)})`,
      `saturate(${s.toFixed(3)})`,
      `hue-rotate(${h.toFixed(1)}deg)`,
    ];
    if (inv > 0) parts.push(`invert(${clamp(inv, 0, 1).toFixed(3)})`);
    if (gray > 0) parts.push(`grayscale(${clamp(gray, 0, 1).toFixed(3)})`);
    if (sep > 0) parts.push(`sepia(${clamp(sep, 0, 1).toFixed(3)})`);
    return parts.join(" ");
  }

  /**
   * RGBA ピクセル配列(Uint8ClampedArray/配列, 長さ 4*画素数)を統計する。
   * 返り値は 0..1 正規化: { lumaMean, satMean, rMean, gMean, bMean }
   */
  function analyzePixels(rgba) {
    const n = Math.floor(rgba.length / 4);
    if (n === 0) return { lumaMean: 0, satMean: 0, rMean: 0, gMean: 0, bMean: 0 };
    let lr = 0, lg = 0, lb = 0, lum = 0, sat = 0;
    for (let i = 0; i < n; i++) {
      const r = rgba[i * 4] / 255, g = rgba[i * 4 + 1] / 255, b = rgba[i * 4 + 2] / 255;
      lr += r; lg += g; lb += b;
      lum += 0.2126 * r + 0.7152 * g + 0.0722 * b;
      const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
      sat += mx <= 0 ? 0 : (mx - mn) / mx; // HSV 彩度
    }
    return { lumaMean: lum / n, satMean: sat / n, rMean: lr / n, gMean: lg / n, bMean: lb / n };
  }

  /**
   * フレーム統計から、中庸(明るさ0.5・彩度targetSat・グレーバランス)へ戻す
   * 逆補正パラメータの初期値を提案する。あくまで目安。
   */
  function suggestCorrection(stats, targetLuma, targetSat) {
    targetLuma = targetLuma == null ? 0.5 : targetLuma;
    targetSat = targetSat == null ? 0.35 : targetSat;
    const luma = Math.max(0.02, stats.lumaMean);
    const sat = Math.max(0.02, stats.satMean);
    const brightness = clamp(targetLuma / luma, 0.3, 3);
    const saturate = clamp(targetSat / sat, 0.2, 3);
    // カラーキャスト補正の目安(色相回転の代替として彩度側で吸収するので0基準)
    return { brightness, contrast: 1, saturate, hue: 0 };
  }

  /** 回転(度)を反転して打ち消す量にする。90刻みに丸め。 */
  function inverseRotation(appliedDeg) {
    const r = ((Math.round(appliedDeg / 90) * 90) % 360 + 360) % 360;
    return (360 - r) % 360;
  }

  /** 速度倍率の逆数(clamp) */
  function inverseSpeed(applied) {
    if (!applied || applied <= 0) return 1;
    return clamp(1 / applied, 0.1, 8);
  }

  return { clamp, buildFilter, analyzePixels, suggestCorrection, inverseRotation, inverseSpeed };
});
