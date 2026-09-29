// node bio_medicine/omega_junishi_dna/tests/test_core.js
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

// 種判別: 十二支 (辰を除く 11 種) + ヒトの無関係なランダム参照で合成リードを作り、
// 混合比と判定レベルを再現できること
let s = 7;
const rnd = () => ((s = (Math.imul(s, 1103515245) + 12345) >>> 0) / 4294967296);
const randSeq = (n) => Array.from({ length: n }, () => "ACGT"[Math.floor(rnd() * 4)]).join("");
const species = C.JUNISHI.filter((j) => j.species);
assert.strictEqual(C.JUNISHI.length, 12);
assert.strictEqual(species.length, 11); // 辰は DNA なし
const refs = { human: randSeq(16569) };
for (const sp of species) refs[sp.key] = randSeq(16000 + Math.floor(rnd() * 1500));
const idx = C.buildIndex(refs, 21);
const reads = C.simulateMix(refs, { human: 0.6, inu: 0.3, tora: 0.1, ne: 0.002 }, 3000, 150, 0.01, 99);
const res = C.classifyReads(reads, idx, { minHits: 3 });
const v = Object.fromEntries(C.verdictAll(res, species.concat([C.HUMAN]), "human").map((x) => [x.key, x.level]));
console.log(res.counts, v);
assert.strictEqual(res.counts.unassigned, 0);
assert.strictEqual(v.inu, "mixed");
assert.strictEqual(v.tora, "mixed");
assert.strictEqual(v.ne, "trace");
assert.strictEqual(v.ushi, "neg");
assert.strictEqual(v.human, "major");
const dogOnly = C.classifyReads(C.simulateMix(refs, { inu: 1 }, 300, 150, 0.01, 5), idx, {});
assert.strictEqual(C.speciesVerdict(dogOnly, "inu", "イヌ", "human").level, "major");

// 干支
assert.strictEqual(C.etoOfYear(2026).kanji, "午");
assert.strictEqual(C.etoOfYear(1984).kanji, "子");
assert.strictEqual(C.etoOfYear(2024).kanji, "辰");

// 入力形式
assert.deepStrictEqual(C.parseSequences(">a\nACGU\nNN\n>b\nttt\n"), ["ACGTNN", "TTT"]);
assert.deepStrictEqual(C.parseSequences("@r1\nACGT\n+\nIIII\n@r2\nGG\n+\nII\n"), ["ACGT", "GG"]);
assert(C.looksLikeSnpArray("# rsid\tchromosome\tposition\tgenotype\nrs123\t1\t100\tAG\n"));
console.log("all tests passed");
