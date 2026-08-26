/* test_engines.js — engines.js が Python 版と同じ数値を返すことの照合テスト
 *   実行: node test/test_engines.js
 * 期待値は各 Python パッケージのテスト／実行結果から取っています。
 */
"use strict";
const O = require("../www/engines.js");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("PASS " + name); }
  else { fail++; console.log("FAIL " + name + (extra ? "  → " + extra : "")); }
}
const close = (a, b, tol) => Math.abs(a - b) <= (tol === undefined ? 1e-9 : tol);

// ---- 1. ガンマ多様体 --------------------------------------------------------
ok("gamma: Γ(s+1)=s·Γ(s) 恒等式", O.gammaSelfCheck());
ok("gamma: Γ(5)=24", close(O.gammaFn(5), 24, 1e-6), O.gammaFn(5));
ok("gamma: Γ(0.5)=√π", close(O.gammaFn(0.5), Math.sqrt(Math.PI), 1e-6));
{
  const m = new O.GammaManifold();
  m.register(2.0, "x");
  m.step();
  // Γ(3)=2·Γ(2) なので logWeight = log 2、s は 3 へ
  ok("manifold: 1ステップで logWeight=log2", close(m.states[0].logWeight, Math.log(2)));
  ok("manifold: s が 3 に進む", m.states[0].s === 3);
  const m2 = new O.GammaManifold();
  m2.register(1.0); m2.register(2.0); m2.register(0.5);
  m2.step();
  const dist = m2.softmax();
  ok("manifold: softmax の総和=1", close(dist.reduce((a, b) => a + b, 0), 1));
}

// ---- 2. 擬似量子VM / メビウス ------------------------------------------------
{
  const vm = new O.PseudoQuantumVM(4, 1);
  const out = vm.run([["LOAD", 0, 0], ["X", 0], ["MEASURE", 0], ["HALT"]]);
  ok("vm: X 反転で確実に 1", JSON.stringify(out) === "[1]", JSON.stringify(out));

  const a = new O.PseudoQuantumVM(4, 123)
    .run([["LOAD", 0, 0], ["H", 0], ["MEASURE", 0], ["HALT"]]);
  const b = new O.PseudoQuantumVM(4, 123)
    .run([["LOAD", 0, 0], ["H", 0], ["MEASURE", 0], ["HALT"]]);
  ok("vm: 同一 seed で再現性", JSON.stringify(a) === JSON.stringify(b));

  const d = new O.MobiusDisk(8);
  d.write(0b10101010);
  d.seek(8);
  ok("mobius: 1周で裏面", d.face === -1);
  ok("mobius: 裏面ではビット反転", d.read() === ((~0b10101010) & 0xff), d.read());
  d.seek(8);
  ok("mobius: 2周で表に復帰", d.face === 1 && d.read() === 0b10101010);
  ok("mobius: 二重被覆の判定", d.isOrientableReturn());

  let threw = false;
  try { new O.DAlembertField({ nx: 16, dx: 1, dt: 2, c: 1 }); } catch (e) { threw = true; }
  ok("dalembert: CFL条件違反を弾く", threw);

  const f = new O.DAlembertField({ nx: 48, dt: 0.4 });
  f.seedGaussian(null, 1);
  for (let i = 0; i < 50; i++) f.step((i2, t) => (i2 === 24 ? Math.sin(t) : 0));
  ok("dalembert: エネルギーが有限", Number.isFinite(f.energy()));
}

// ---- 3. 臨界連鎖ガード ------------------------------------------------------
{
  const core = new O.ChainCore();
  ok("chain: k_eff(0) = ν·p_f", close(core.kEff(0), 2.4 * 0.45, 1e-12));
  const aStar = core.criticalAbsorption();
  ok("chain: k_eff(a*)=1", close(core.kEff(aStar), 1, 1e-9));
  ok("chain: a*+0.05 で未臨界", core.kEff(aStar + 0.05) < 1);

  const g = new O.CriticalGuard({}, 21);
  g.run(60);
  const s = g.summary();
  ok("guard: 常に未臨界を維持", s.alwaysSubcritical && s.maxKEff < 1, s.maxKEff);

  const g2 = new O.CriticalGuard({}, 21);
  g2.run(60, 10, 100000);
  const s2 = g2.summary();
  ok("guard: 大量注入で SCRAM 作動", s2.scramEvents >= 1, s2.scramEvents);
  ok("guard: 外乱後も連鎖を抑え込む", s2.finalPopulation < 100, s2.finalPopulation);
}

// ---- 3b. 臨界期の強度（未臨界増倍と 1/M 法） --------------------------------
{
  // M = 1/(1-k) は k→1 で発散する
  ok("subcrit: M(0)=1", close(O.multiplication(0), 1));
  ok("subcrit: M(0.99)=100", close(O.multiplication(0.99), 100, 1e-9));
  ok("subcrit: M(0.999)=1000", close(O.multiplication(0.999), 1000, 1e-9));
  ok("subcrit: 臨界で発散", !Number.isFinite(O.multiplication(1.0)));
  ok("subcrit: 1/M = 1-k", close(O.inverseMultiplication(0.75), 0.25));

  // 臨界減速
  ok("subcrit: tau(0.9)=10*tau(0)",
     close(O.relaxationTime(0.9, 1e-4), 1e-3, 1e-12));
  ok("subcrit: tau は k とともに増える",
     O.relaxationTime(0.999, 1e-4) > O.relaxationTime(0.99, 1e-4));

  // 1/M 外挿が真の臨界位置 0.8 を当てる（Python 版と同じ seed / 同じ結果）
  const a = new O.ApproachToCritical(null, {}, 0x51de);
  a.run();
  const s = a.summary();
  ok("subcrit: 1/M 外挿が臨界位置 0.8 を予測",
     close(s.finalPrediction, 0.8, 0.01), s.finalPrediction);
  ok("subcrit: 安全接近は臨界を越えない", s.stayedSubcritical && s.maxK < 1, s.maxK);
  ok("subcrit: それでも k>0.99 まで近づく", s.finalK > 0.99, s.finalK);

  const u = O.runUnsafeApproach(null, 0.2);
  ok("subcrit: 固定刻みだと踏み越える", u.crossedCritical && u.maxK >= 1, u.maxK);

  // 点炉動特性
  const pk = new O.PointKinetics();
  ok("kinetics: 即発臨界の境界は beta",
     !pk.isPromptCritical(0.0064) && pk.isPromptCritical(0.0065));
  // 小さい rho では T = (beta-rho)/(lam*rho)
  [0.0005, 0.001, 0.002].forEach((rho) => {
    const analytic = (0.0065 - rho) / (0.0785 * rho);
    ok(`kinetics: T(${rho}) が解析解と一致`,
       Math.abs(pk.period(rho) - analytic) / analytic < 0.05, pk.period(rho));
  });
  const periods = [0.0005, 0.001, 0.002, 0.004, 0.006].map((r) => pk.period(r));
  ok("kinetics: rho が beta に近いほど期は短い",
     periods.every((v, i) => i === 0 || v < periods[i - 1]));
  const steady = new O.PointKinetics({}, 1.0);
  steady.run(0, 5.0, 1e-3);
  ok("kinetics: rho=0 は定常", close(steady.n, 1.0, 1e-3), steady.n);
  ok("kinetics: rho=(k-1)/k", close(O.reactivityFromK(1.0), 0));
}

// ---- 4. 反応速度論 / 熱暴走 --------------------------------------------------
{
  const net = new O.ReactionNetwork({}, { P: 1, C: 0.25 });
  const m0 = net.mass();
  for (let i = 0; i < 500; i++) net.step();
  ok("reaction: 質量保存", Math.abs(net.mass() - m0) < 1e-9, Math.abs(net.mass() - m0));

  const zero = new O.ReactionNetwork({}, { P: 1, C: 0 });
  ok("reaction: 触媒0なら χ=0", zero.chainFactor() === 0);
  for (let i = 0; i < 300; i++) zero.step();
  ok("reaction: 触媒0なら前駆体不変", close(zero.s.P, 1, 1e-12));

  const r1 = new O.ReactionNetwork({}, { P: 1, C: 0.05 });
  const r2 = new O.ReactionNetwork({}, { P: 1, C: 0.10 });
  ok("reaction: χ は触媒量に比例",
     close(r2.chainFactor(), 2 * r1.chainFactor(), 1e-12));

  // Python 版: 制御あり 収率0.5174 純度0.6542 / 制御なし 0.3186 / 0.3207
  const syn = new O.QuantumSynthesizer({ steps: 3000 }, 0xbada);
  syn.run();
  const ss = syn.summary();
  ok("synth: 臨界未満を維持", ss.stayedSubcritical && ss.maxChi < 1, ss.maxChi);
  ok("synth: 収率が Python 版と一致 (0.5174)", close(ss.yield, 0.5174, 5e-4), ss.yield);
  ok("synth: 純度が Python 版と一致 (0.6542)", close(ss.purity, 0.6542, 5e-4), ss.purity);

  const un = O.runUncontrolled(0.30, 3000);
  ok("synth: 制御なしは収率が劣る (0.3186)", close(un.yield, 0.3186, 5e-4), un.yield);
  ok("synth: 制御ありが制御なしを上回る",
     ss.yield > un.yield && ss.purity > un.purity);

  const rc = new O.ThermalReactor();
  ok("thermal: Arrhenius(T_ref)=1", close(rc.arrhenius(300), 1, 1e-12));
  ok("thermal: 高温ほど速い", rc.arrhenius(320) > 1 && rc.arrhenius(280) < 1);
  ok("thermal: 除熱は温度に線形",
     close(rc.heatRemoval(320) - rc.heatRemoval(310), rc.th.UA * 10, 1e-9));
  ok("thermal: 反応なしなら発熱なし", close(rc.heatGeneration(), 0, 1e-12));
}

// ---- 5. 服薬リスク重複チェッカー ---------------------------------------------
{
  ok("medsafe: 一般名と商品名が同クラス",
     O.lookupDrug("セレネース").payload.name === O.lookupDrug("ハロペリドール").payload.name);
  ok("medsafe: ブランド接尾辞は薬剤名ではない",
     O.lookupDrug("アメル").kind === "brand");
  ok("medsafe: 未知の薬は unknown",
     O.checkMeds(["存在しない薬XYZ"]).unknown.length === 1);
  ok("medsafe: 1剤なら重複なし", O.checkMeds(["アムロジピン"]).findings.length === 0);

  const r = O.checkMeds(["フルニトラゼパム", "エチゾラム", "ブロチゾラム"]);
  const resp = r.findings.find((f) => f.tag === "RESPIRATORY_DEPRESSION");
  ok("medsafe: 中枢抑制3剤で呼吸抑制を重大判定",
     resp && resp.severity === "重大" && resp.drugs.length === 3);

  const full = O.checkMeds(["フルニトラゼパム", "エチゾラム", "ブロチゾラム", "アムロジピン",
                            "カンデサルタン", "セレネース", "リスパダール"]);
  const tags = new Set(full.findings.map((f) => f.tag));
  ok("medsafe: 全リストで4種の重大リスクを検出",
     full.hasCritical && ["CNS_DEPRESSION", "RESPIRATORY_DEPRESSION",
                          "HYPOTENSION", "QT_PROLONGATION"].every((t) => tags.has(t)));
}

// ---- 6. 呼吸と心拍変動 ------------------------------------------------------
{
  const p478 = O.BREATH_PATTERNS["478"];
  ok("breath: 4-7-8 の1周期=19秒", close(p478.cycle, 19));
  ok("breath: コヒーレント呼吸=毎分6回",
     close(O.BREATH_PATTERNS.coherent.breathsPerMinute, 6));

  const box = O.BREATH_PATTERNS.box;
  ok("breath: 相の遷移",
     box.phaseAt(0)[0] === "吸う" && box.phaseAt(5)[0] === "止める" &&
     box.phaseAt(9)[0] === "吐く" && box.phaseAt(13)[0] === "止める(空)" &&
     box.phaseAt(16.5)[0] === "吸う");

  const sim = new O.RSASimulator();
  const mc = sim.metrics(O.BREATH_PATTERNS.coherent);
  // Python 版: RSA振幅 11.04bpm / SDNN 54.16ms
  ok("hrv: RSA振幅が Python 版と一致 (11.04)", close(mc.rsaAmplitude, 11.04, 0.05), mc.rsaAmplitude);
  ok("hrv: SDNN が Python 版と一致 (54.16)", close(mc.sdnnMs, 54.16, 0.1), mc.sdnnMs);
  ok("hrv: 生理学的に妥当な範囲",
     mc.rsaAmplitude > 3 && mc.rsaAmplitude < 25 && mc.meanHr > 50 && mc.meanHr < 90);

  const fast = sim.metrics(new O.BreathPattern("速い", 1.5, 0, 1.5, 0));
  ok("hrv: コヒーレント呼吸が速い呼吸に勝る", mc.rsaAmplitude > fast.rsaAmplitude);

  const sweep = O.resonanceSweep();
  const peak = sweep.reduce((a, b) => (b[1] > a[1] ? b : a));
  ok("hrv: 共鳴の山が毎分6回付近 (5.71)", peak[0] >= 5 && peak[0] <= 7, peak[0]);
}

// ---- 7. 形態形成場と腫瘍動態 -------------------------------------------------
{
  const f0 = new O.MorphogenField({ n: 16 });
  f0.run(200);
  ok("morpho: 種がなければ一様のまま",
     f0.totalActivator() === 0 && f0.countSpots() === 0);

  const f = new O.MorphogenField({ n: 24 });
  f.seedSpot(3);
  f.run(400);
  ok("morpho: 濃度が [0,1] に収まる",
     Array.from(f.u).every((x) => x >= 0 && x <= 1) &&
     Array.from(f.v).every((x) => x >= 0 && x <= 1));

  const fd = new O.MorphogenField({ n: 48 });
  fd.seedSpot(3);
  ok("morpho: 初期は1つの種", fd.countSpots() === 1);
  fd.run(1500);
  ok("morpho: 種が複数の細胞に分岐", fd.countSpots() > 1, fd.countSpots());

  // 外部場は場の向きにだけドリフトさせる
  const still = new O.MorphogenField({ n: 40, Ex: 0 });
  still.seedSpot(3); still.run(300);
  const [sx, sy] = still.centroid();
  const driven = new O.MorphogenField({ n: 40, Ex: 0.04 });
  driven.seedSpot(3); driven.run(300);
  const [dx, dy] = driven.centroid();
  ok("morpho: 場の向き(x)にドリフト", Math.abs(dx - sx) > 1.0, Math.abs(dx - sx));
  ok("morpho: 直交方向(y)は動かない", Math.abs(dy - sy) < 0.5, Math.abs(dy - sy));
  ok("morpho: 場ゼロなら中央のまま",
     Math.abs(sx - 20) < 1 && Math.abs(sy - 20) < 1);

  const none = new O.TumorModel({ duration: 400 });
  none.run(O.policyNone);
  ok("tumor: 無治療は収容力に達する", none.total > 0.95 * none.cfg.K);

  const cont = new O.TumorModel(); cont.run(O.policyContinuous);
  const cs = cont.summary();
  ok("tumor: 常時最大強度は耐性を選択する", cs.resistantFraction > 0.95, cs.resistantFraction);

  const adapt = new O.TumorModel(); adapt.run(O.makeAdaptivePolicy());
  const as = adapt.summary();
  ok("tumor: 適応方針が進行を遅らせる",
     as.timeToProgression > cs.timeToProgression,
     `${as.timeToProgression} vs ${cs.timeToProgression}`);
  ok("tumor: 停滞し、治療時間は短い",
     as.stalled && as.treatmentFraction < 0.5, as.treatmentFraction);
  // Python 版: 常時最大 TTP=331.2 / 適応 は進行せず、治療割合 0.20
  ok("tumor: 常時最大の TTP が Python 版と一致 (331.2)",
     close(cs.timeToProgression, 331.2, 0.5), cs.timeToProgression);
  ok("tumor: 適応の治療割合が Python 版と一致 (0.20)",
     close(as.treatmentFraction, 0.20, 0.02), as.treatmentFraction);

  const eps = new O.TumorModel({ duration: 10 });
  eps.run(() => 5.0);
  ok("tumor: 治療強度は 0〜1 に制限される", eps.log.every((f2) => f2.epsilon <= 1));
}

console.log(`\n${pass}/${pass + fail} passed`);
process.exit(fail === 0 ? 0 : 1);
