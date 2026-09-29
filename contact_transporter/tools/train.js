#!/usr/bin/env node
/*
 * train.js — ContactGPT をゼロから学習し data/contactgpt_weights.json に保存する
 *
 *   node tools/train.js [steps] [--resume]
 *
 * コーパス: data/equations.json (設計図書の全方程式 2111 本) + 設計パラメータ Q&A
 */
const fs = require("fs"), path = require("path");
const P = require("../src/physics.js");
const { GPT, buildCorpus, buildVocab } = require("../src/gpt.js");

const DATA = path.join(__dirname, "..", "data");
const OUT = process.env.CT_WEIGHTS_OUT || path.join(DATA, "contactgpt_weights.json");  // 出力先 (既定: data/)
const args = process.argv.slice(2);
const steps = parseInt(args.find((a) => /^\d+$/.test(a)) || "3000", 10);
const resume = args.includes("--resume");

const eqs = JSON.parse(fs.readFileSync(path.join(DATA, "equations.json"), "utf8"));
const corpus = buildCorpus(eqs, P.blueprint());
let model;
const IN = fs.existsSync(OUT) ? OUT : path.join(DATA, "contactgpt_weights.json");
if (resume && fs.existsSync(IN)) model = GPT.fromJSON(JSON.parse(fs.readFileSync(IN, "utf8")));
else model = new GPT({ nLayer: 2, nHead: 4, nEmbd: 96, block: 64, seed: 2111 }, buildVocab(corpus));
const data = Int32Array.from(model.encode(corpus));
// 末尾 5% を検証用に
const split = Math.floor(data.length * 0.95);
const train = data.subarray(0, split), val = data.subarray(split);
console.log(`corpus ${corpus.length} chars, vocab ${model.vocab.length}, params ${model.nParams}, steps ${steps}`);

const t0 = Date.now();
const lr0 = 3e-3, warm = 100, start = model.step;
let ema = null;
for (let s = 0; s < steps; s++) {
  const it = s + 1, prog = s / steps;
  const lr = it < warm && !resume ? lr0 * it / warm : 3e-4 + (lr0 - 3e-4) * 0.5 * (1 + Math.cos(Math.PI * prog));
  const loss = model.trainStep(train, { batch: 12, lr, wd: 0.01 });
  ema = ema == null ? loss : 0.98 * ema + 0.02 * loss;
  if (it % 100 === 0 || it === steps) {
    const vl = model.evalLoss(val, 8);
    console.log(`step ${start + it}  loss ${ema.toFixed(3)}  val ${vl.toFixed(3)}  lr ${lr.toExponential(2)}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    fs.writeFileSync(OUT, JSON.stringify(model.toJSON()));
  }
}
for (const q of ["Q: UFO.19 は？\nA:", "Q: ローレンツ因子 Γ は？\nA:", "Q: Jones 3_1 は？\nA:"])
  console.log("---\n" + q + model.generate(q, { seed: 1, temperature: 0.5 }));
