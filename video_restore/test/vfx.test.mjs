/* vfx.js の単体テスト。 node video_restore/test/vfx.test.mjs */
import VFX from "../www/vfx.js";
const { clamp, buildFilter, analyzePixels, suggestCorrection, inverseRotation, inverseSpeed } = VFX;

let passed = 0, failed = 0;
const ok = (name, cond, extra = "") => cond ? (passed++, console.log(`  ✓ ${name}`)) : (failed++, console.log(`  ✗ ${name}  ${extra}`));

console.log("clamp");
ok("範囲内はそのまま", clamp(0.5, 0, 1) === 0.5);
ok("下限でクランプ", clamp(-1, 0, 1) === 0);
ok("上限でクランプ", clamp(9, 0, 1) === 1);

console.log("buildFilter");
{
  const f = buildFilter({ brightness: 1.2, contrast: 0.9, saturate: 1.5, hue: 30 });
  ok("必須4項目を含む", /brightness\(1.200\).*contrast\(0.900\).*saturate\(1.500\).*hue-rotate\(30.0deg\)/.test(f), f);
  ok("invert=0 は出力しない", !buildFilter({}).includes("invert"));
  ok("invert>0 は出力する", buildFilter({ invert: 1 }).includes("invert(1.000)"));
  ok("デフォルトは無変換(全て1/0)", buildFilter({}) === "brightness(1.000) contrast(1.000) saturate(1.000) hue-rotate(0.0deg)");
}

console.log("analyzePixels");
{
  // 中間グレー(128,128,128) 一色
  const gray = new Uint8ClampedArray(4 * 100);
  for (let i = 0; i < 100; i++) { gray[i*4]=128; gray[i*4+1]=128; gray[i*4+2]=128; gray[i*4+3]=255; }
  const gs = analyzePixels(gray);
  ok("グレーの輝度≈0.502", Math.abs(gs.lumaMean - 128/255) < 1e-6, `luma=${gs.lumaMean.toFixed(3)}`);
  ok("グレーの彩度≈0", gs.satMean < 1e-6, `sat=${gs.satMean.toFixed(3)}`);
  // 純赤
  const red = new Uint8ClampedArray(4 * 50);
  for (let i = 0; i < 50; i++) { red[i*4]=255; red[i*4+3]=255; }
  const rs = analyzePixels(red);
  ok("純赤の彩度=1", Math.abs(rs.satMean - 1) < 1e-6, `sat=${rs.satMean.toFixed(3)}`);
  ok("空配列は0統計", analyzePixels(new Uint8ClampedArray(0)).lumaMean === 0);
}

console.log("suggestCorrection");
{
  // 暗い映像(luma 0.2)→ 明るく補正(>1)
  const dark = suggestCorrection({ lumaMean: 0.2, satMean: 0.35 });
  ok("暗い映像は明るさ>1を提案", dark.brightness > 1, `b=${dark.brightness.toFixed(2)}`);
  ok("暗い映像の明るさは 0.5/0.2=2.5", Math.abs(dark.brightness - 2.5) < 1e-6, `b=${dark.brightness}`);
  // 明るすぎる映像 → 暗く(<1)
  const bright = suggestCorrection({ lumaMean: 0.9, satMean: 0.35 });
  ok("明るい映像は明るさ<1を提案", bright.brightness < 1, `b=${bright.brightness.toFixed(2)}`);
  // 彩度過多 → saturate<1
  const oversat = suggestCorrection({ lumaMean: 0.5, satMean: 0.8 });
  ok("彩度過多は saturate<1 を提案", oversat.saturate < 1, `s=${oversat.saturate.toFixed(2)}`);
  ok("補正量はクランプ範囲内", dark.brightness <= 3 && oversat.saturate >= 0.2);
}

console.log("inverseRotation / inverseSpeed");
{
  ok("90° の逆は 270°", inverseRotation(90) === 270);
  ok("180° の逆は 180°", inverseRotation(180) === 180);
  ok("270° の逆は 90°", inverseRotation(270) === 90);
  ok("0° の逆は 0°", inverseRotation(0) === 0);
  ok("2倍速の逆は0.5", Math.abs(inverseSpeed(2) - 0.5) < 1e-9);
  ok("0.5倍速の逆は2", Math.abs(inverseSpeed(0.5) - 2) < 1e-9);
  ok("不正値は1", inverseSpeed(0) === 1);
}

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed === 0 ? 0 : 1);
