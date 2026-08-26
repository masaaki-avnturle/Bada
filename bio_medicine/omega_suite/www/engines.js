/* ===========================================================================
 * engines.js — Ω-Suite 計算コア
 *
 * リポジトリ内の 7 つの Python パッケージの数値モデルを JavaScript へ移植した
 * もの。すべて依存ゼロ・決定論的で、Python 版と同じ数値を返す（test/ に照合
 * テストあり）。
 *
 *   1. GammaManifold      ← omega_gamma_agent_pkg
 *   2. PseudoQuantumVM /
 *      MobiusDisk /
 *      DAlembertField     ← omega_mobius_drive_pkg
 *   3. ChainCore /
 *      CriticalGuard      ← omega_critical_guard_pkg
 *   4. ReactionNetwork /
 *      ThermalReactor     ← omega_pharma_forge_pkg
 *   5. MedSafe            ← omega_medsafe_pkg
 *   6. BreathPattern /
 *      RSASimulator       ← omega_breath_pkg
 *   7. MorphogenField /
 *      TumorModel         ← omega_morphofield_pkg
 *
 * ⚠️ いずれも概念シミュレーション・非医療。実在の医療機器・薬剤・治療方針とは
 *    無関係で、そこから実際の物質や医療判断を導くことはできません。
 * =========================================================================== */
"use strict";

const Omega = (() => {

// ===========================================================================
// 1. ガンマ関数 大域的部分積分多様体
// ===========================================================================

/** Lanczos 近似による log Γ(s)（Python の math.lgamma 相当）。 */
function logGamma(s) {
  const g = 7;
  const C = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
  ];
  if (s < 0.5) {
    // 反射公式 Γ(s)Γ(1−s) = π / sin(πs)
    return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * s))) - logGamma(1 - s);
  }
  s -= 1;
  let x = C[0];
  for (let i = 1; i < g + 2; i++) x += C[i] / (s + i);
  const t = s + g + 0.5;
  return 0.5 * Math.log(2 * Math.PI) + (s + 0.5) * Math.log(t) - t + Math.log(x);
}

function gammaFn(s) {
  if (s < 0.5) return Math.PI / (Math.sin(Math.PI * s) * gammaFn(1 - s));
  return Math.exp(logGamma(s));
}

/** 部分積分が与える大域的漸化 Γ(s+1) = s·Γ(s) の係数。 */
const ibpRecurrence = (s) => s;

class ManifoldState {
  constructor(s, logWeight = 0, label = "") {
    this.s = s; this.logWeight = logWeight; this.label = label;
  }
  get weight() { return Math.exp(this.logWeight); }
  advance() {
    const s = this.s > 1e-9 ? this.s : 1e-9;
    return new ManifoldState(
      s + 1, this.logWeight + Math.log(Math.abs(ibpRecurrence(s))), this.label);
  }
}

class GammaManifold {
  constructor() { this.states = []; this.epoch = 0; }
  register(s, label = "") {
    const st = new ManifoldState(s, 0, label);
    this.states.push(st);
    return st;
  }
  step() {
    this.states = this.states.map((st) => st.advance());
    this.epoch++;
  }
  softmax(temperature = 1.0) {
    if (!this.states.length) return [];
    const logits = this.states.map((st) => st.logWeight / Math.max(temperature, 1e-9));
    const m = Math.max(...logits);
    const exps = logits.map((l) => Math.exp(l - m));
    const z = exps.reduce((a, b) => a + b, 0);
    return exps.map((e) => e / z);
  }
  dominant() {
    return this.states.reduce((a, b) => (b.logWeight > a.logWeight ? b : a));
  }
}

/** Γ(s+1) = s·Γ(s) の数値検証。 */
function gammaSelfCheck() {
  for (const s of [0.5, 1.0, 2.3, 4.7, 9.0]) {
    if (Math.abs(gammaFn(s + 1) - s * gammaFn(s)) > 1e-6 * Math.abs(gammaFn(s + 1))) {
      return false;
    }
  }
  return true;
}

// ===========================================================================
// 2. 擬似量子VM / メビウス回路HDD / 反ダランベルシアン場
// ===========================================================================

/** 決定論的擬似乱数（Python 版 _LCG と同一系列）。 */
class LCG {
  constructor(seed = 0x9e3779b1) { this.state = seed >>> 0; }
  random() {
    // (1103515245 * state + 12345) & 0x7FFFFFFF を 32bit 安全に計算
    this.state = Number((BigInt(1103515245) * BigInt(this.state) + BigInt(12345))
                        & BigInt(0x7fffffff));
    return this.state / 0x7fffffff;
  }
}

class QReg {
  constructor(a0 = 1, a1 = 0) { this.a0 = a0; this.a1 = a1; }
  normalize() {
    const n = Math.hypot(this.a0, this.a1);
    if (n > 1e-12) { this.a0 /= n; this.a1 /= n; }
  }
  probOne() {
    const n = this.a0 * this.a0 + this.a1 * this.a1;
    return n > 1e-12 ? (this.a1 * this.a1) / n : 0;
  }
}

/** ノイマン型 擬似量子VM（本物の量子計算機ではありません）。 */
class PseudoQuantumVM {
  constructor(nRegs = 4, seed = 0x9e3779b1) {
    this.regs = Array.from({ length: nRegs }, () => new QReg());
    this.rng = new LCG(seed);
    this.output = [];
    this.halted = false;
  }
  run(program) {
    for (const instr of program) {
      if (this.halted) break;
      this.exec(instr);
    }
    return this.output;
  }
  exec(instr) {
    const op = String(instr[0]).toUpperCase();
    if (op === "LOAD") {
      const [, r, imm] = instr;
      this.regs[r] = new QReg(1 - imm, imm);
      this.regs[r].normalize();
    } else if (op === "H") {
      const reg = this.regs[instr[1]];
      const { a0, a1 } = reg;
      reg.a0 = (a0 + a1) / Math.SQRT2;
      reg.a1 = (a0 - a1) / Math.SQRT2;
    } else if (op === "X") {
      const reg = this.regs[instr[1]];
      [reg.a0, reg.a1] = [reg.a1, reg.a0];
    } else if (op === "PHASE") {
      const [, r, theta] = instr;
      this.regs[r].a1 *= Math.cos(theta);
      this.regs[r].normalize();
    } else if (op === "ENT") {
      const [, r, s] = instr;
      const avg0 = (this.regs[r].a0 + this.regs[s].a0) / 2;
      const avg1 = (this.regs[r].a1 + this.regs[s].a1) / 2;
      for (const q of [this.regs[r], this.regs[s]]) {
        q.a0 = avg0; q.a1 = avg1; q.normalize();
      }
    } else if (op === "MEASURE") {
      const r = instr[1];
      const bit = this.rng.random() < this.regs[r].probOne() ? 1 : 0;
      this.regs[r] = new QReg(1 - bit, bit);
      this.output.push(bit);
    } else if (op === "HALT") {
      this.halted = true;
    } else {
      throw new Error("unknown opcode: " + op);
    }
  }
}

/** メビウス位相の仮想HDD。1周で表裏反転、2周で復帰（二重被覆）。 */
class MobiusDisk {
  constructor(sectors = 64) {
    if (sectors < 2) throw new Error("sectors must be >= 2");
    this.n = sectors;
    this.disk = Array.from({ length: sectors }, () => ({ value: 0, polarity: 1 }));
    this.head = 0; this.face = 1; this.laps = 0;
  }
  seek(delta) {
    let pos = this.head, face = this.face;
    const step = delta >= 0 ? 1 : -1;
    for (let i = 0; i < Math.abs(delta); i++) {
      pos += step;
      if (pos >= this.n) { pos = 0; face = -face; this.laps++; }
      else if (pos < 0) { pos = this.n - 1; face = -face; this.laps++; }
    }
    this.head = pos; this.face = face;
  }
  write(value) {
    const s = this.disk[this.head];
    s.value = value & 0xff;
    s.polarity = this.face;
  }
  read() {
    const s = this.disk[this.head];
    return this.face * s.polarity < 0 ? (~s.value) & 0xff : s.value;
  }
  isOrientableReturn() { return this.laps % 2 === 0; }
}

/** 1D ダランベルシアン場（反ダランベルシアンはソース符号反転）。 */
class DAlembertField {
  constructor(cfg = {}) {
    this.cfg = Object.assign({ nx: 128, dx: 1, dt: 0.5, c: 1, kappa: 0.05 }, cfg);
    if (this.courant > 1 + 1e-12) {
      throw new Error(`CFL条件違反: courant=${this.courant.toFixed(3)} > 1`);
    }
    this.phiPrev = new Float64Array(this.cfg.nx);
    this.phi = new Float64Array(this.cfg.nx);
    this.t = 0;
    this.anti = true;
  }
  get courant() { return this.cfg.c * this.cfg.dt / this.cfg.dx; }
  seedGaussian(center = null, amp = 1, width = 6) {
    const n = this.cfg.nx;
    const c = center === null ? Math.floor(n / 2) : center;
    for (let i = 0; i < n; i++) {
      this.phi[i] = amp * Math.exp(-((i - c) ** 2) / (2 * width * width));
    }
    this.phiPrev = Float64Array.from(this.phi);
  }
  step(sourceFn = null) {
    const { nx, c, dt, dx, kappa } = this.cfg;
    const r2 = (c * dt / dx) ** 2;
    const next = new Float64Array(nx);
    for (let i = 0; i < nx; i++) {
      const left = i > 0 ? this.phi[i - 1] : this.phi[i];
      const right = i < nx - 1 ? this.phi[i + 1] : this.phi[i];
      const lap = left - 2 * this.phi[i] + right;
      let val = 2 * this.phi[i] - this.phiPrev[i] + r2 * lap;
      if (sourceFn) {
        val += (this.anti ? -1 : 1) * kappa * dt * dt * sourceFn(i, this.t);
      }
      next[i] = val;
    }
    this.phiPrev = this.phi;
    this.phi = next;
    this.t += dt;
  }
  energy() {
    const { nx, dx } = this.cfg;
    let e = 0;
    for (let i = 0; i < nx; i++) {
      const right = i < nx - 1 ? this.phi[i + 1] : this.phi[i];
      const grad = (right - this.phi[i]) / dx;
      e += 0.5 * (this.phi[i] ** 2 + grad ** 2);
    }
    return e;
  }
  liftIndex() {
    const { nx } = this.cfg;
    let s = 0;
    for (let i = 0; i < nx; i++) {
      const right = i < nx - 1 ? this.phi[i + 1] : this.phi[i];
      s += right - this.phi[i];
    }
    return s;
  }
}

// ===========================================================================
// 3. 臨界連鎖の分岐過程と防止ガード
// ===========================================================================

class ChainCore {
  constructor(cfg = {}, seed = 0x2545f491, initialNeutrons = 100) {
    this.cfg = Object.assign({ nu: 2.4, pFission: 0.45, maxPopulation: 200000 }, cfg);
    this.rng = new LCG(seed);
    this.population = initialNeutrons;
    this.generation = 0;
  }
  kEff(absorption) {
    const a = Math.min(Math.max(absorption, 0), 1);
    return this.cfg.nu * this.cfg.pFission * (1 - a);
  }
  /** k_eff = 1 となる吸収量（これ以上入れれば未臨界）。 */
  criticalAbsorption() { return 1 - 1 / (this.cfg.nu * this.cfg.pFission); }
  step(absorption) {
    const a = Math.min(Math.max(absorption, 0), 1);
    const pNext = this.cfg.pFission * (1 - a);
    let next;
    if (this.population > 5000) {
      const mean = this.population * pNext * this.cfg.nu;
      const base = Math.floor(mean);
      next = base + (this.rng.random() < mean - base ? 1 : 0);
    } else {
      next = 0;
      for (let i = 0; i < this.population; i++) {
        if (this.rng.random() < pNext) next += this.rng.random() < 0.6 ? 2 : 3;
      }
    }
    this.population = Math.min(next, this.cfg.maxPopulation);
    this.generation++;
    return this.population;
  }
}

/** 擬似量子VMで吸収量を制御し、常に未臨界に保つガード。 */
class CriticalGuard {
  constructor(cfg = {}, seed = 0xc0ffee, core = null) {
    this.cfg = Object.assign({
      margin: 0.08, dither: 0.02, targetPopulation: 100,
      scramThreshold: 5000, scramReleaseBelow: 50,
    }, cfg);
    this.core = core || new ChainCore({}, seed);
    this.vm = new PseudoQuantumVM(2, seed);
    this.scramActive = false;
    this.log = [];
  }
  quantumDither(error) {
    this.vm.output = []; this.vm.halted = false;
    return this.vm.run([
      ["LOAD", 0, 0], ["H", 0], ["PHASE", 0, 0.5 * Math.tanh(error)],
      ["MEASURE", 0], ["HALT"],
    ])[0];
  }
  decideAbsorption() {
    const { cfg, core } = this;
    const pop = core.population;
    if (pop >= cfg.scramThreshold) this.scramActive = true;
    else if (this.scramActive && pop <= cfg.scramReleaseBelow) this.scramActive = false;
    if (this.scramActive) return { absorption: 1, bit: 0, scram: true };

    const base = core.criticalAbsorption() + cfg.margin;
    const error = (pop - cfg.targetPopulation) / Math.max(cfg.targetPopulation, 1);
    const bit = this.quantumDither(error);
    return {
      absorption: Math.min(base + (bit ? cfg.dither : -cfg.dither), 1),
      bit, scram: false,
    };
  }
  run(generations = 60, perturbationAt = -1, perturbationNeutrons = 0) {
    for (let g = 0; g < generations; g++) {
      if (g === perturbationAt) this.core.population += perturbationNeutrons;
      const { absorption, bit, scram } = this.decideAbsorption();
      const k = this.core.kEff(absorption);
      this.core.step(absorption);
      this.log.push({
        generation: this.core.generation, population: this.core.population,
        absorption, kEff: k, qbit: bit, scram,
      });
    }
    return this.log;
  }
  summary() {
    if (!this.log.length) return {};
    const ks = this.log.map((t) => t.kEff);
    const pops = this.log.map((t) => t.population);
    return {
      generations: this.log.length,
      maxKEff: Math.max(...ks),
      alwaysSubcritical: ks.every((k) => k < 1),
      maxPopulation: Math.max(...pops),
      finalPopulation: pops[pops.length - 1],
      scramEvents: this.log.filter((t) => t.scram).length,
      extinguished: pops[pops.length - 1] === 0,
    };
  }
}

// ===========================================================================
// 4. 自己触媒連鎖の反応速度論 + 温度結合反応器
// ===========================================================================

const DEFAULT_RATES = { k1: 0.25, k2: 6.0, k3: 0.35, k4: 0.9, k5: 0.01, k6: 0.02 };

class ReactionNetwork {
  constructor(rates = {}, state = {}, dt = 0.02) {
    this.k = Object.assign({}, DEFAULT_RATES, rates);
    this.s = Object.assign({ P: 1, C: 0, I: 0, A: 0, B: 0, Cdead: 0 }, state);
    this.dt = dt;
    this.t = 0;
  }
  mass() { return this.s.P + this.s.I + this.s.A + this.s.B; }
  derivs(y) {
    const [P, C, I, A, B] = y;
    const k = this.k;
    const r1 = k.k1 * P * C;
    const r2 = k.k2 * P * I * C;       // 触媒媒介の連鎖成長
    const r3 = k.k3 * I;
    const r4 = k.k4 * I * I;
    const r5 = k.k5 * A;
    const r6 = k.k6 * C;
    return [-r1 - r2, -r6, r1 + r2 - r3 - 2 * r4, r3 - r5, 2 * r4 + r5, r6];
  }
  step(dose = 0) {
    this.s.C += Math.max(dose, 0);
    let y = [this.s.P, this.s.C, this.s.I, this.s.A, this.s.B, this.s.Cdead];
    const h = this.dt;
    const k1 = this.derivs(y);
    const k2 = this.derivs(y.map((v, i) => v + 0.5 * h * k1[i]));
    const k3 = this.derivs(y.map((v, i) => v + 0.5 * h * k2[i]));
    const k4 = this.derivs(y.map((v, i) => v + h * k3[i]));
    y = y.map((v, i) => Math.max(v + (h / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]), 0));
    [this.s.P, this.s.C, this.s.I, this.s.A, this.s.B, this.s.Cdead] = y;
    this.t += h;
  }
  /** 連鎖係数 χ = k2·P·C/(k3+2·k4·I)。χ>1 で暴走。 */
  chainFactor() {
    const denom = this.k.k3 + 2 * this.k.k4 * this.s.I;
    if (denom <= 1e-12) return Infinity;
    return (this.k.k2 * this.s.P * this.s.C) / denom;
  }
  yieldFraction(m0) { return m0 > 1e-12 ? this.s.A / m0 : 0; }
  purity() {
    const d = this.s.A + this.s.B;
    return d > 1e-12 ? this.s.A / d : 0;
  }
}

const DEFAULT_THERMAL = {
  Tref: 300, Tinit: 300, Tjacket: 295, EaOverR: 6000,
  dH: 1.2e5, rhoCpV: 2.0e3, UA: 600, Talarm: 330, Tscram: 345,
};

class ThermalReactor {
  constructor(rates = {}, thermal = {}, state = {}, dt = 0.02) {
    this.kRef = Object.assign({}, DEFAULT_RATES, rates);
    this.th = Object.assign({}, DEFAULT_THERMAL, thermal);
    this.T = this.th.Tinit;
    this.net = new ReactionNetwork(this.ratesAt(this.T), state, dt);
    this.dt = dt; this.t = 0; this.Tmax = this.T;
  }
  arrhenius(T) {
    return Math.exp(-this.th.EaOverR * (1 / T - 1 / this.th.Tref));
  }
  ratesAt(T) {
    const f = this.arrhenius(T), k = this.kRef;
    return { k1: k.k1 * f, k2: k.k2 * f, k3: k.k3 * f, k4: k.k4 * f, k5: k.k5, k6: k.k6 };
  }
  heatGeneration(T) {
    T = T === undefined ? this.T : T;
    const k = this.ratesAt(T), s = this.net.s;
    return this.th.dH * (k.k1 * s.P * s.C + k.k2 * s.P * s.I * s.C + k.k4 * s.I * s.I);
  }
  heatRemoval(T) {
    T = T === undefined ? this.T : T;
    return this.th.UA * (T - this.th.Tjacket);
  }
  /** Semenov 余裕 = d(除熱)/dT − d(発熱)/dT。負なら熱暴走。 */
  semenovMargin(dT = 0.5) {
    const dgen = (this.heatGeneration(this.T + dT) - this.heatGeneration(this.T - dT)) / (2 * dT);
    const drem = (this.heatRemoval(this.T + dT) - this.heatRemoval(this.T - dT)) / (2 * dT);
    return drem - dgen;
  }
  get isRunaway() { return this.semenovMargin() < 0; }
  step(dose = 0, Tjacket = null) {
    if (Tjacket !== null) this.th.Tjacket = Tjacket;
    this.net.k = this.ratesAt(this.T);
    this.net.step(dose);
    this.T += ((this.heatGeneration() - this.heatRemoval()) / this.th.rhoCpV) * this.dt;
    this.Tmax = Math.max(this.Tmax, this.T);
    this.t += this.dt;
  }
}

/** 擬似量子VMで触媒投与を制御する合成シミュレータ。 */
class QuantumSynthesizer {
  constructor(cfg = {}, seed = 0xbada, rates = {}, dt = 0.02) {
    this.cfg = Object.assign({
      chiTarget: 0.30, chiMax: 0.45, chiScram: 1.0,
      doseHigh: 0.0020, doseLow: 0.0005, catalystBudget: 0.30, steps: 3000,
    }, cfg);
    this.net = new ReactionNetwork(rates, {}, dt);
    this.vm = new PseudoQuantumVM(2, seed);
    this.initialMass = this.net.mass();
    this.dosedTotal = 0;
    this.scramLatched = false;
    this.log = [];
  }
  quantumBit(error) {
    this.vm.output = []; this.vm.halted = false;
    return this.vm.run([
      ["LOAD", 0, 0], ["H", 0], ["PHASE", 0, 0.8 * Math.tanh(error)],
      ["MEASURE", 0], ["HALT"],
    ])[0];
  }
  decideDose() {
    const { cfg } = this;
    const chi = this.net.chainFactor();
    if (chi >= cfg.chiScram) this.scramLatched = true;
    if (this.scramLatched || chi >= cfg.chiMax) {
      return { dose: 0, bit: 0, scram: this.scramLatched };
    }
    if (this.dosedTotal >= cfg.catalystBudget) return { dose: 0, bit: 0, scram: false };
    const bit = this.quantumBit(cfg.chiTarget - chi);
    const dose = Math.min(bit ? cfg.doseHigh : cfg.doseLow,
                          cfg.catalystBudget - this.dosedTotal);
    return { dose, bit, scram: false };
  }
  run(steps = null) {
    const n = steps === null ? this.cfg.steps : steps;
    for (let i = 0; i < n; i++) {
      const { dose, bit, scram } = this.decideDose();
      this.net.step(dose);
      this.dosedTotal += dose;
      const s = this.net.s;
      this.log.push({
        t: this.net.t, P: s.P, I: s.I, A: s.A, B: s.B, C: s.C,
        chi: this.net.chainFactor(), dose, bit, scram,
      });
    }
    return this.log;
  }
  summary() {
    if (!this.log.length) return {};
    const chis = this.log.map((f) => f.chi).filter(Number.isFinite);
    return {
      steps: this.log.length,
      yield: this.net.yieldFraction(this.initialMass),
      purity: this.net.purity(),
      maxI: Math.max(...this.log.map((f) => f.I)),
      maxChi: chis.length ? Math.max(...chis) : 0,
      stayedSubcritical: chis.every((c) => c < 1),
      catalystUsed: this.dosedTotal,
      massError: Math.abs(this.net.mass() - this.initialMass),
      scram: this.scramLatched,
    };
  }
}

/** 比較用: 触媒一括投与・制御なし。 */
function runUncontrolled(catalyst = 0.30, steps = 3000, dt = 0.02) {
  const net = new ReactionNetwork({}, {}, dt);
  const m0 = net.mass();
  net.s.C = catalyst;
  let maxChi = net.chainFactor(), maxI = net.s.I;
  for (let i = 0; i < steps; i++) {
    net.step();
    const c = net.chainFactor();
    if (Number.isFinite(c)) maxChi = Math.max(maxChi, c);
    maxI = Math.max(maxI, net.s.I);
  }
  return {
    yield: net.yieldFraction(m0), purity: net.purity(),
    maxChi, maxI, massError: Math.abs(net.mass() - m0),
  };
}

// ===========================================================================
// 5. 服薬リスク重複チェッカー
// ===========================================================================

const RISK_LABELS = {
  CNS_DEPRESSION: "中枢神経抑制（眠気・意識レベル低下）",
  RESPIRATORY_DEPRESSION: "呼吸抑制（呼吸が浅く・遅くなる）",
  HYPOTENSION: "血圧低下（ふらつき・失神）",
  QT_PROLONGATION: "QT延長（重篤な不整脈）",
  EPS_NMS: "錐体外路症状・悪性症候群",
  ANTICHOLINERGIC: "抗コリン作用（口渇・便秘・尿閉・せん妄）",
  FALL_RISK: "転倒リスク（特に高齢者）",
  DEPENDENCE: "依存・耐性形成、急な中断による離脱症状",
  SEROTONERGIC: "セロトニン症候群",
  BLEEDING: "出血傾向",
  HYPERKALEMIA: "高カリウム血症",
  RENAL: "腎機能への負担",
};

const CRITICAL_TAGS = new Set(["RESPIRATORY_DEPRESSION", "QT_PROLONGATION", "SEROTONERGIC"]);

const CLASSES = {
  benzodiazepine: { name: "ベンゾジアゼピン系（抗不安・催眠）",
    risks: ["CNS_DEPRESSION", "RESPIRATORY_DEPRESSION", "FALL_RISK", "DEPENDENCE"] },
  thienodiazepine: { name: "チエノジアゼピン系（抗不安・催眠）",
    risks: ["CNS_DEPRESSION", "RESPIRATORY_DEPRESSION", "FALL_RISK", "DEPENDENCE"] },
  z_drug: { name: "非ベンゾジアゼピン系睡眠薬（Z薬）",
    risks: ["CNS_DEPRESSION", "RESPIRATORY_DEPRESSION", "FALL_RISK", "DEPENDENCE"] },
  antipsychotic_typical: { name: "定型抗精神病薬",
    risks: ["CNS_DEPRESSION", "QT_PROLONGATION", "EPS_NMS", "HYPOTENSION",
            "ANTICHOLINERGIC", "FALL_RISK"] },
  antipsychotic_atypical: { name: "非定型抗精神病薬",
    risks: ["CNS_DEPRESSION", "QT_PROLONGATION", "EPS_NMS", "HYPOTENSION", "FALL_RISK"] },
  ccb_dihydropyridine: { name: "カルシウム拮抗薬（降圧）", risks: ["HYPOTENSION", "FALL_RISK"] },
  arb: { name: "ARB（降圧）", risks: ["HYPOTENSION", "HYPERKALEMIA", "RENAL"] },
  acei: { name: "ACE阻害薬（降圧）", risks: ["HYPOTENSION", "HYPERKALEMIA", "RENAL"] },
  diuretic: { name: "利尿薬", risks: ["HYPOTENSION", "RENAL", "FALL_RISK"] },
  beta_blocker: { name: "β遮断薬", risks: ["HYPOTENSION", "FALL_RISK"] },
  ssri: { name: "SSRI（抗うつ）", risks: ["SEROTONERGIC", "BLEEDING"] },
  snri: { name: "SNRI（抗うつ）", risks: ["SEROTONERGIC", "BLEEDING"] },
  tricyclic: { name: "三環系抗うつ薬",
    risks: ["CNS_DEPRESSION", "ANTICHOLINERGIC", "QT_PROLONGATION", "SEROTONERGIC", "FALL_RISK"] },
  opioid: { name: "オピオイド系鎮痛薬",
    risks: ["CNS_DEPRESSION", "RESPIRATORY_DEPRESSION", "DEPENDENCE", "FALL_RISK"] },
  antihistamine_1st: { name: "第一世代抗ヒスタミン薬",
    risks: ["CNS_DEPRESSION", "ANTICHOLINERGIC", "FALL_RISK"] },
  mood_stabilizer: { name: "気分安定薬", risks: ["CNS_DEPRESSION", "RENAL"] },
  anticoagulant: { name: "抗凝固薬", risks: ["BLEEDING"] },
  alcohol: { name: "アルコール",
    risks: ["CNS_DEPRESSION", "RESPIRATORY_DEPRESSION", "FALL_RISK", "DEPENDENCE"] },
};

const DRUG_TO_CLASS = {
  "フルニトラゼパム": "benzodiazepine", "サイレース": "benzodiazepine",
  "ジアゼパム": "benzodiazepine", "セルシン": "benzodiazepine",
  "ロラゼパム": "benzodiazepine", "ワイパックス": "benzodiazepine",
  "アルプラゾラム": "benzodiazepine", "ソラナックス": "benzodiazepine",
  "トリアゾラム": "benzodiazepine", "ハルシオン": "benzodiazepine",
  "ニトラゼパム": "benzodiazepine", "クロナゼパム": "benzodiazepine",
  "エチゾラム": "thienodiazepine", "デパス": "thienodiazepine",
  "ブロチゾラム": "thienodiazepine", "レンドルミン": "thienodiazepine",
  "ゾルピデム": "z_drug", "マイスリー": "z_drug",
  "エスゾピクロン": "z_drug", "ルネスタ": "z_drug", "ゾピクロン": "z_drug",
  "ハロペリドール": "antipsychotic_typical", "セレネース": "antipsychotic_typical",
  "クロルプロマジン": "antipsychotic_typical",
  "リスペリドン": "antipsychotic_atypical", "リスパダール": "antipsychotic_atypical",
  "オランザピン": "antipsychotic_atypical", "ジプレキサ": "antipsychotic_atypical",
  "クエチアピン": "antipsychotic_atypical", "アリピプラゾール": "antipsychotic_atypical",
  "エビリファイ": "antipsychotic_atypical",
  "アムロジピン": "ccb_dihydropyridine", "アムロジン": "ccb_dihydropyridine",
  "ノルバスク": "ccb_dihydropyridine", "ニフェジピン": "ccb_dihydropyridine",
  "カンデサルタン": "arb", "ブロプレス": "arb", "ロサルタン": "arb",
  "バルサルタン": "arb", "テルミサルタン": "arb",
  "エナラプリル": "acei", "フロセミド": "diuretic", "ラシックス": "diuretic",
  "カルベジロール": "beta_blocker", "ビソプロロール": "beta_blocker",
  "セルトラリン": "ssri", "ジェイゾロフト": "ssri",
  "エスシタロプラム": "ssri", "レクサプロ": "ssri",
  "パロキセチン": "ssri", "パキシル": "ssri",
  "デュロキセチン": "snri", "サインバルタ": "snri",
  "アミトリプチリン": "tricyclic",
  "トラマドール": "opioid", "コデイン": "opioid", "モルヒネ": "opioid",
  "ジフェンヒドラミン": "antihistamine_1st", "炭酸リチウム": "mood_stabilizer",
  "ワルファリン": "anticoagulant", "アルコール": "alcohol", "飲酒": "alcohol",
};

const BRAND_SUFFIXES = {
  "アメル": "共和薬品工業のジェネリック医薬品ブランド名です。薬剤そのものの名前ではないため、"
          + "「リスペリドン錠〈アメル〉」のように前についている一般名で調べてください。",
  "サワイ": "沢井製薬のジェネリック医薬品ブランド名です（薬剤名ではありません）。",
  "トーワ": "東和薬品のジェネリック医薬品ブランド名です（薬剤名ではありません）。",
  "日医工": "日医工のジェネリック医薬品ブランド名です（薬剤名ではありません）。",
};

function normalizeDrug(name) {
  return String(name).trim().replace(/^[「〈（(錠\s　]+|[」〉）)錠\s　]+$/g, "").replace(/\s/g, "");
}

function lookupDrug(name) {
  const key = normalizeDrug(name);
  if (DRUG_TO_CLASS[key]) return { kind: "class", payload: CLASSES[DRUG_TO_CLASS[key]] };
  if (BRAND_SUFFIXES[key]) return { kind: "brand", payload: BRAND_SUFFIXES[key] };
  return { kind: "unknown", payload: null };
}

/**
 * 薬剤名リストのリスク重複を調べる。
 * 用量・配合比・「安全な組み合わせ」は **決して出力しない**。
 */
function checkMeds(drugNames) {
  const resolved = {}, brandNotes = {}, unknown = [], tagMap = {};
  for (const raw of drugNames) {
    const { kind, payload } = lookupDrug(raw);
    if (kind === "class") {
      resolved[raw] = payload.name;
      for (const tag of payload.risks) (tagMap[tag] = tagMap[tag] || []).push(raw);
    } else if (kind === "brand") {
      brandNotes[raw] = payload;
    } else {
      unknown.push(raw);
    }
  }
  const findings = [];
  for (const [tag, drugs] of Object.entries(tagMap)) {
    if (drugs.length < 2) continue;   // 重複していなければ指摘しない
    findings.push({
      tag, label: RISK_LABELS[tag] || tag, drugs,
      severity: (CRITICAL_TAGS.has(tag) || drugs.length >= 3) ? "重大" : "注意",
    });
  }
  findings.sort((a, b) =>
    (a.severity !== "重大") - (b.severity !== "重大") || b.drugs.length - a.drugs.length);
  return {
    resolved, brandNotes, unknown, findings,
    hasCritical: findings.some((f) => f.severity === "重大"),
  };
}

// ===========================================================================
// 6. 呼吸パターンと心拍変動 (RSA / 圧受容器反射共鳴)
// ===========================================================================

class BreathPattern {
  constructor(name, inhale, holdIn, exhale, holdOut, note = "") {
    Object.assign(this, { name, inhale, holdIn, exhale, holdOut, note });
  }
  get cycle() { return this.inhale + this.holdIn + this.exhale + this.holdOut; }
  get breathsPerMinute() { return 60 / this.cycle; }
  phaseAt(t) {
    let u = ((t % this.cycle) + this.cycle) % this.cycle;
    const phases = [["吸う", this.inhale], ["止める", this.holdIn],
                    ["吐く", this.exhale], ["止める(空)", this.holdOut]];
    for (const [name, dur] of phases) {
      if (dur <= 0) continue;
      if (u < dur) return [name, u / dur];
      u -= dur;
    }
    return ["吐く", 1];
  }
  lungVolume(t) {
    const [phase, p] = this.phaseAt(t);
    if (phase === "吸う") return p;
    if (phase === "止める") return 1;
    if (phase === "吐く") return 1 - p;
    return 0;
  }
}

const BREATH_PATTERNS = {
  slow: new BreathPattern("ゆっくり呼吸", 4, 0, 6, 0,
    "吐く方を長くするだけの最小構成。どこでもできる。"),
  coherent: new BreathPattern("コヒーレント呼吸", 5, 0, 5, 0,
    "毎分6回。心拍変動が最も大きくなる共鳴周波数(約0.1Hz)付近。"),
  box: new BreathPattern("ボックス呼吸", 4, 4, 4, 4,
    "4拍ずつ均等。落ち着いて集中したいときに。"),
  "478": new BreathPattern("4-7-8呼吸", 4, 7, 8, 0,
    "吐く時間を長くとる。息苦しければ半分の長さから始める。"),
};

/** 圧受容器反射を 2次減衰共振系としてモデル化。共鳴は毎分6回付近。 */
class RSASimulator {
  constructor(cfg = {}) {
    this.cfg = Object.assign({
      hrBase: 66, resonanceHz: 0.10, damping: 0.22, gain: 3.0,
      dt: 0.05, warmup: 60, duration: 180,
    }, cfg);
  }
  derivs(x, v, u) {
    const w0 = 2 * Math.PI * this.cfg.resonanceHz;
    return [v, w0 * w0 * (u - x) - 2 * this.cfg.damping * w0 * v];
  }
  simulate(pattern) {
    const c = this.cfg;
    let t = 0, x = 0, v = 0;
    const ts = [], hrs = [], vols = [];
    const drive = (tt) => 2 * pattern.lungVolume(tt) - 1;
    const n = Math.floor(c.duration / c.dt);
    for (let i = 0; i < n; i++) {
      const h = c.dt;
      const [k1x, k1v] = this.derivs(x, v, drive(t));
      const [k2x, k2v] = this.derivs(x + 0.5 * h * k1x, v + 0.5 * h * k1v, drive(t + 0.5 * h));
      const [k3x, k3v] = this.derivs(x + 0.5 * h * k2x, v + 0.5 * h * k2v, drive(t + 0.5 * h));
      const [k4x, k4v] = this.derivs(x + h * k3x, v + h * k3v, drive(t + h));
      x += (h / 6) * (k1x + 2 * k2x + 2 * k3x + k4x);
      v += (h / 6) * (k1v + 2 * k2v + 2 * k3v + k4v);
      t += h;
      if (t >= c.warmup) {
        ts.push(t); hrs.push(c.hrBase + c.gain * x); vols.push(pattern.lungVolume(t));
      }
    }
    return { t: ts, hr: hrs, volume: vols };
  }
  metrics(pattern) {
    const { hr } = this.simulate(pattern);
    if (!hr.length) return { rsaAmplitude: 0, sdnnMs: 0, meanHr: 0 };
    const rsa = Math.max(...hr) - Math.min(...hr);
    const rr = hr.filter((h) => h > 1e-6).map((h) => 60000 / h);
    const meanRr = rr.reduce((a, b) => a + b, 0) / rr.length;
    const varRr = rr.reduce((a, r) => a + (r - meanRr) ** 2, 0) / rr.length;
    return {
      rsaAmplitude: rsa, sdnnMs: Math.sqrt(varRr),
      meanHr: hr.reduce((a, b) => a + b, 0) / hr.length,
      breathsPerMinute: pattern.breathsPerMinute,
    };
  }
}

/** 呼吸周期を振って共鳴の山を探す。 */
function resonanceSweep(cfg = {}) {
  const sim = new RSASimulator(cfg);
  const out = [];
  for (let i = 0; i < 33; i++) {
    const cycle = 4 + 0.5 * i;
    const p = new BreathPattern(`${cycle.toFixed(1)}s`, cycle / 2, 0, cycle / 2, 0);
    out.push([p.breathsPerMinute, sim.metrics(p).rsaAmplitude]);
  }
  return out;
}

// ===========================================================================
// 7. 形態形成場 (Gray-Scott) と腫瘍動態 (Gompertz + 耐性競合)
// ===========================================================================

class MorphogenField {
  constructor(cfg = {}) {
    this.cfg = Object.assign({
      n: 64, Du: 0.16, Dv: 0.08, F: 0.030, k: 0.0565, dt: 1, Ex: 0, Ey: 0,
    }, cfg);
    const n = this.cfg.n;
    this.u = new Float64Array(n * n).fill(1);
    this.v = new Float64Array(n * n);
    this.t = 0;
  }
  idx(i, j) { return j * this.cfg.n + i; }
  seedSpot(radius = 4, cx = null, cy = null, amp = 0.5) {
    const n = this.cfg.n;
    cx = cx === null ? Math.floor(n / 2) : cx;
    cy = cy === null ? Math.floor(n / 2) : cy;
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        if ((i - cx) ** 2 + (j - cy) ** 2 <= radius * radius) {
          const p = this.idx(i, j);
          this.u[p] = 1 - amp; this.v[p] = amp;
        }
      }
    }
  }
  step() {
    const c = this.cfg, n = c.n;
    const nu = new Float64Array(n * n), nv = new Float64Array(n * n);
    for (let j = 0; j < n; j++) {
      const jm = (j - 1 + n) % n, jp = (j + 1) % n;
      for (let i = 0; i < n; i++) {
        const p = this.idx(i, j);
        const im = (i - 1 + n) % n, ip = (i + 1) % n;
        const L = this.idx(im, j), R = this.idx(ip, j);
        const U = this.idx(i, jm), D = this.idx(i, jp);
        const ui = this.u[p], vi = this.v[p];
        const lapU = this.u[L] + this.u[R] + this.u[U] + this.u[D] - 4 * ui;
        const lapV = this.v[L] + this.v[R] + this.v[U] + this.v[D] - 4 * vi;
        // 風上差分による移流（外部場ドリフト）
        let advU = 0, advV = 0;
        if (c.Ex > 0) { advU += c.Ex * (ui - this.u[L]); advV += c.Ex * (vi - this.v[L]); }
        else if (c.Ex < 0) { advU += c.Ex * (this.u[R] - ui); advV += c.Ex * (this.v[R] - vi); }
        if (c.Ey > 0) { advU += c.Ey * (ui - this.u[U]); advV += c.Ey * (vi - this.v[U]); }
        else if (c.Ey < 0) { advU += c.Ey * (this.u[D] - ui); advV += c.Ey * (this.v[D] - vi); }
        const uvv = ui * vi * vi;
        nu[p] = Math.min(Math.max(ui + c.dt * (c.Du * lapU - uvv + c.F * (1 - ui) - advU), 0), 1);
        nv[p] = Math.min(Math.max(vi + c.dt * (c.Dv * lapV + uvv - (c.F + c.k) * vi - advV), 0), 1);
      }
    }
    this.u = nu; this.v = nv; this.t += c.dt;
  }
  run(steps) { for (let i = 0; i < steps; i++) this.step(); }
  totalActivator() { return this.v.reduce((a, b) => a + b, 0); }
  countSpots(threshold = 0.25) {
    const n = this.cfg.n, SZ = n * n;
    const seen = new Uint8Array(SZ), stack = new Int32Array(SZ);
    let count = 0;
    for (let start = 0; start < SZ; start++) {
      if (seen[start] || this.v[start] <= threshold) continue;
      count++;
      let sp = 0; stack[sp++] = start; seen[start] = 1;
      while (sp > 0) {
        const p = stack[--sp];
        const i = p % n, j = (p - i) / n;
        for (const q of [this.idx((i - 1 + n) % n, j), this.idx((i + 1) % n, j),
                         this.idx(i, (j - 1 + n) % n), this.idx(i, (j + 1) % n)]) {
          if (!seen[q] && this.v[q] > threshold) { seen[q] = 1; stack[sp++] = q; }
        }
      }
    }
    return count;
  }
  /** 周期境界のため円周平均で重心を求める。 */
  centroid(threshold = 0.1) {
    const n = this.cfg.n;
    let sx = 0, sy = 0, cx = 0, cy = 0, w = 0;
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const val = this.v[this.idx(i, j)];
        if (val <= threshold) continue;
        const ax = 2 * Math.PI * i / n, ay = 2 * Math.PI * j / n;
        sx += val * Math.sin(ax); cx += val * Math.cos(ax);
        sy += val * Math.sin(ay); cy += val * Math.cos(ay);
        w += val;
      }
    }
    if (w <= 1e-12) return [0, 0];
    const mod = (a) => ((a % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
    return [mod(Math.atan2(sx, cx)) * n / (2 * Math.PI),
            mod(Math.atan2(sy, cy)) * n / (2 * Math.PI)];
  }
}

class TumorModel {
  constructor(cfg = {}) {
    this.cfg = Object.assign({
      rS: 0.030, rR: 0.021, K: 1.0e4, kappa: 0.055,
      S0: 8.0e3, R0: 4.0e1, dt: 0.25, duration: 900,
    }, cfg);
    this.S = this.cfg.S0; this.R = this.cfg.R0; this.t = 0; this.log = [];
  }
  get total() { return this.S + this.R; }
  derivs(S, R, eps) {
    const c = this.cfg;
    const N = Math.max(S + R, 1e-9);
    const growth = N < c.K ? Math.log(c.K / N) : 0;
    return [c.rS * S * growth - eps * c.kappa * S, c.rR * R * growth];
  }
  step(eps) {
    const h = this.cfg.dt, S = this.S, R = this.R;
    const [k1S, k1R] = this.derivs(S, R, eps);
    const [k2S, k2R] = this.derivs(S + 0.5 * h * k1S, R + 0.5 * h * k1R, eps);
    const [k3S, k3R] = this.derivs(S + 0.5 * h * k2S, R + 0.5 * h * k2R, eps);
    const [k4S, k4R] = this.derivs(S + h * k3S, R + h * k3R, eps);
    this.S = Math.max(S + (h / 6) * (k1S + 2 * k2S + 2 * k3S + k4S), 0);
    this.R = Math.max(R + (h / 6) * (k1R + 2 * k2R + 2 * k3R + k4R), 0);
    this.t += h;
    this.log.push({ t: this.t, S: this.S, R: this.R, epsilon: eps });
  }
  run(policy, duration = null) {
    const d = duration === null ? this.cfg.duration : duration;
    const n = Math.floor(d / this.cfg.dt);
    for (let i = 0; i < n; i++) {
      this.step(Math.min(Math.max(policy(this), 0), 1));
    }
    return this.log;
  }
  summary() {
    if (!this.log.length) return {};
    const n0 = this.cfg.S0 + this.cfg.R0;
    const totals = this.log.map((f) => f.S + f.R);
    let progression = Infinity;
    for (const f of this.log) {
      if (f.S + f.R > 1.2 * n0) { progression = f.t; break; }
    }
    const tail = totals.slice(Math.floor(totals.length / 2));
    return {
      finalTotal: totals[totals.length - 1],
      finalS: this.S, finalR: this.R,
      resistantFraction: this.R / Math.max(this.total, 1e-9),
      maxTotal: Math.max(...totals),
      timeToProgression: progression,
      stalled: Math.max(...tail) <= 1.2 * n0,
      treatmentFraction: this.log.filter((f) => f.epsilon > 0).length / this.log.length,
    };
  }
}

const policyNone = () => 0;
const policyContinuous = () => 1;

/** 適応方針: S をあえて残し、競合で R を抑えさせる。 */
function makeAdaptivePolicy(onRatio = 1.0, offRatio = 0.9, epsilon = 1.0) {
  let on = true;
  return (m) => {
    const n0 = m.cfg.S0 + m.cfg.R0, n = m.total;
    if (on && n <= offRatio * n0) on = false;
    else if (!on && n >= onRatio * n0) on = true;
    return on ? epsilon : 0;
  };
}

function comparePolicies(cfg = {}) {
  const out = {};
  const entries = [["無治療", policyNone], ["常時最大強度", policyContinuous],
                   ["適応的（断続）", makeAdaptivePolicy()]];
  for (const [name, pol] of entries) {
    const m = new TumorModel(cfg);
    m.run(pol);
    out[name] = m.summary();
  }
  return out;
}

// ===========================================================================

return {
  // 1
  logGamma, gammaFn, ibpRecurrence, ManifoldState, GammaManifold, gammaSelfCheck,
  // 2
  LCG, QReg, PseudoQuantumVM, MobiusDisk, DAlembertField,
  // 3
  ChainCore, CriticalGuard,
  // 4
  ReactionNetwork, ThermalReactor, QuantumSynthesizer, runUncontrolled,
  DEFAULT_RATES, DEFAULT_THERMAL,
  // 5
  RISK_LABELS, CLASSES, DRUG_TO_CLASS, BRAND_SUFFIXES,
  normalizeDrug, lookupDrug, checkMeds,
  // 6
  BreathPattern, BREATH_PATTERNS, RSASimulator, resonanceSweep,
  // 7
  MorphogenField, TumorModel, policyNone, policyContinuous,
  makeAdaptivePolicy, comparePolicies,
};

})();

if (typeof module !== "undefined" && module.exports) module.exports = Omega;
