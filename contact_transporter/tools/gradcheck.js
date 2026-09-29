// 数値微分との比較で ContactGPT の逆伝播を検証する
const { GPT, Tape, setFloat } = require("../src/gpt.js");
setFloat(Float64Array);
const g = new GPT({ nLayer: 2, nHead: 2, nEmbd: 8, block: 6, seed: 3 }, ["\u0000", "a", "b", "c", "d", "e"]);
// 微小な値ばかりだと検出力が落ちるので重みを大きめに
for (const t of Object.values(g.params)) for (let i = 0; i < t.data.length; i++) t.data[i] += (Math.sin(i * 12.9898 + t.data.length) * 0.3);
const B = 2, T = 6, idx = Int32Array.from([1,2,3,4,5,1, 2,2,3,1,4,5]), tgt = Int32Array.from([2,3,4,5,1,2, 2,3,1,4,5,3]);
const loss = () => g.forward(new Tape(false), idx, B, T, tgt).loss;
for (const t of Object.values(g.params)) t.grad = null;
const tape = new Tape(true); g.forward(tape, idx, B, T, tgt); tape.backward();
let worst = 0;
for (const [n, t] of Object.entries(g.params)) {
  for (let k = 0; k < Math.min(6, t.data.length); k++) {
    const i = Math.floor((k * 7919) % t.data.length), h = 1e-5, o = t.data[i];
    t.data[i] = o + h; const lp = loss(); t.data[i] = o - h; const lm = loss(); t.data[i] = o;
    const num = (lp - lm) / (2 * h), ana = t.grad[i];
    const rel = Math.abs(num - ana) / Math.max(1e-6, Math.abs(num) + Math.abs(ana));
    worst = Math.max(worst, rel);
    if (rel > 1e-3) console.log("MISMATCH", n, i, num, ana, rel);
  }
}
console.log("gradcheck worst rel err", worst.toExponential(2));
if (worst > 1e-3) process.exit(1);
