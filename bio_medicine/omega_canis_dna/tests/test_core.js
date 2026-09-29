// node bio_medicine/omega_canis_dna/tests/test_core.js
const assert = require("assert");
const C = require("../www/core.js");

// Jones 多項式を既知の値と照合
const fmt = (v) => C.polyToString(v);
const j31 = C.jones(C.KNOTS["3_1 (三葉結び目)"]);
const j41 = C.jones(C.KNOTS["4_1 (8の字結び目)"]);
const j51 = C.jones(C.KNOTS["5_1 (五葉結び目)"]);
console.log("3_1:", fmt(j31));
console.log("4_1:", fmt(j41));
console.log("5_1:", fmt(j51));
assert.deepStrictEqual(j41, { "-2": 1, "-1": -1, 0: 1, 1: -1, 2: 1 });
// 3_1 / 5_1 はキラル: 左右どちらかの既知形に一致すること
const mirror = (v) => Object.fromEntries(Object.entries(v).map(([e, c]) => [String(-e), c]));
const k31 = { "-4": -1, "-3": 1, "-1": 1 };
const k51 = { "-7": -1, "-6": 1, "-5": -1, "-4": 1, "-2": 1 };
const eq = (a, b) => JSON.stringify(Object.entries(a).sort()) === JSON.stringify(Object.entries(b).sort());
assert(eq(j31, k31) || eq(j31, mirror(k31)), "3_1 Jones mismatch");
assert(eq(j51, k51) || eq(j51, mirror(k51)), "5_1 Jones mismatch");
for (const v of [j31, j41, j51]) assert(Math.abs(C.evalPoly(v, 1) - 1) < 1e-12, "V(1)=1");

// Γ核
assert(Math.abs(C.gammaKernel(1) - 2) < 1e-12);
assert(C.gammaKernel(1 / Math.E) > C.gammaKernel(0.9));

// 種判別: 無関係なランダム参照 2 種で合成リードを作り、混合比を再現できること
let s = 7;
const rnd = () => ((s = (Math.imul(s, 1103515245) + 12345) >>> 0) / 4294967296);
const randSeq = (n) => Array.from({ length: n }, () => "ACGT"[Math.floor(rnd() * 4)]).join("");
const refs = { dog: randSeq(16000), human: randSeq(16500) };
const idx = C.buildIndex(refs, 21);
for (const [frac, expect] of [[0, "neg"], [0.3, "mixed"], [1, "dog"]]) {
  const reads = C.simulateReads(refs, "dog", "human", 400, 150, frac, 0.01, 99);
  const res = C.classifyReads(reads, idx, { minHits: 3 });
  const v = C.verdict(res, "dog");
  console.log(`dogFrac=${frac}:`, res.counts, v.level);
  assert.strictEqual(v.level, expect);
}

// 入力形式
assert.deepStrictEqual(C.parseSequences(">a\nACGU\nNN\n>b\nttt\n"), ["ACGTNN", "TTT"]);
assert.deepStrictEqual(C.parseSequences("@r1\nACGT\n+\nIIII\n@r2\nGG\n+\nII\n"), ["ACGT", "GG"]);
assert(C.looksLikeSnpArray("# rsid\tchromosome\tposition\tgenotype\nrs123\t1\t100\tAG\n"));
console.log("all tests passed");
