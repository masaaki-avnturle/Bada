#!/usr/bin/env node
/**
 * selftest.mjs — index.html の計算核（KONNYAKU CORE）だけを抜き出して Node 上で検証する。
 *
 *   node tools/selftest.mjs          … 自己テスト
 *   node tools/selftest.mjs --demo   … 4 つの箱に既定値を入れた照合結果を表示
 *
 * 計算核は index.html の中にしか存在しない（単一ファイル配布のため）。
 * このスクリプトはコピーを持たず、常に本体から抜き出して試す。
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, '..', 'index.html'), 'utf8');

const BEGIN = 'KONNYAKU CORE BEGIN';
const END = '/* ===== KONNYAKU CORE END ===== */';
const from = html.indexOf(BEGIN);
const to = html.indexOf(END);
if (from < 0 || to < 0) { console.error('計算核の区間が index.html に見つかりません'); process.exit(2); }
const coreSrc = html.slice(html.indexOf('*/', from) + 2, to);

const EXPORTS = ['TAU','BINS','DELTA','GATE','FORM_AXES','BOXES','shannon','formEntropy',
  'softHistogram','numericEntropy','matchRate','equivClass','classLabel','elasticity','kindness','cainGate',
  'getBox','collate','groupByClass','canonical','sha256hex','sealRecord','verifyChain','parseSeq'];
const src = coreSrc + '\nexport { ' + EXPORTS.join(', ') + ' };\n';
const core = await import('data:text/javascript;charset=utf-8,' + encodeURIComponent(src));

/* ------------------------------------------------------------------ */
let pass = 0, fail = 0;
const near = (a, b, eps = 1e-6) => Math.abs(a - b) <= eps;
function ok(name, cond, extra = '') {
  if (cond) { pass++; console.log('  ok   ' + name); }
  else { fail++; console.log('  FAIL ' + name + (extra ? ' — ' + extra : '')); }
}

if (process.argv.includes('--demo')) {
  console.log('既定値による照合（H形 / H数値 / 照合率 / 弾力性 / 優しさ / 同値類 / 方程式値）\n');
  for (const b of core.BOXES) {
    const values = Object.fromEntries(b.vars.map(v => [v.key, v.def]));
    const r = core.collate(b.id, values, core.parseSeq(b.seqDef));
    console.log(`${b.id}  ${b.title}`);
    console.log(`     ${b.equation}`);
    console.log(`     入力 ${JSON.stringify(values)}  数列 [${b.seqDef}]`);
    console.log(`     H形=${r.hForm.toFixed(4)}  H数値=${r.hNum.toFixed(4)}  照合率=${(r.match*100).toFixed(2)}%` +
                `  弾力性=${r.elasticity.toFixed(4)}  優しさ=${r.kindness.toFixed(4)}  ≡ ${r.label}` +
                `  値=${r.value.toFixed(6)}  ${r.gate.marked ? 'カインの刻印(' + r.gate.reasons.length + ')' : '刻印なし'}\n`);
  }
  process.exit(0);
}

console.log('KONNYAKU CORE self-test');

console.log('[エントロピー]');
ok('shannon([.5,.5]) = 1 bit', near(core.shannon([0.5, 0.5]), 1));
ok('shannon([1]) = 0 bit', near(core.shannon([1]), 0));
ok('一様な形シグネチャは 2 bit', near(core.formEntropy([1, 1, 1, 1]), 2));
ok('一軸に尖った形は 0 bit', near(core.formEntropy([1, 0, 0, 0]), 0));
ok('4 ビンに均等な数列は 2 bit', near(core.numericEntropy([1, 2, 3, 4]), 2));
ok('定数列は 0 bit', near(core.numericEntropy([5, 5, 5]), 0));
ok('要素 1 個は 0 bit', near(core.numericEntropy([7]), 0));
ok('H は 0〜2 bit に収まる', [[1,2,3,4,5,6,7],[0,0,0,1],[-3,9,9,9,2]].every(s => {
  const h = core.numericEntropy(s); return h >= 0 && h <= 2 + 1e-12;
}));

console.log('[照合と同値類]');
ok('一致で照合率 1', near(core.matchRate(1.23, 1.23), 1));
ok('照合率は乖離に対し単調減少', core.matchRate(1.0, 1.2) > core.matchRate(1.0, 1.6));
ok('r=0 は E₀', core.equivClass(0) === 0 && core.classLabel(0) === 'E₀');
ok('r=0.30 は k=1（τ=0.25 で丸め）', core.equivClass(0.30) === 1);
ok('r=-0.30 は k=-1 かつ E₋₁', core.equivClass(-0.30) === -1 && core.classLabel(-1) === 'E₋₁');
ok('k は ±2 にクリップ', core.equivClass(99) === 2 && core.equivClass(-99) === -2);
{
  const rs = [0.02, 0.26, -0.26, 0.05, 2.4, -3].map(r => core.equivClass(r));
  const eq = (a, b) => a === b;
  const reflexive = rs.every(a => eq(a, a));
  const symmetric = rs.every(a => rs.every(b => eq(a, b) === eq(b, a)));
  const transitive = rs.every(a => rs.every(b => rs.every(c => !(eq(a, b) && eq(b, c)) || eq(a, c))));
  ok('≡ は反射律・対称律・推移律を満たす（同値関係）', reflexive && symmetric && transitive);
}

console.log('[弾力性・優しさ・カインの門]');
ok('柔らかいヒストグラムは確率分布（総和 1）',
   Math.abs(core.softHistogram([1, 2.4, 3.1, 9]).reduce((a, b) => a + b, 0) - 1) < 1e-12);
ok('弾力性は 0〜1', [[1,2,3,4],[0,10,0,10,0],[1,1,1,2]].every(s => {
  const e = core.elasticity(s); return e >= 0 && e <= 1;
}));
ok('弾力性は摂動に反応する（常に 1 ではない）', core.elasticity([1, 2, 3, 4]) < 1);
ok('一点に固まった列は弾力性が低い', core.elasticity([1, 2, 3, 4]) > core.elasticity([1, 1, 1, 5]),
   `spread=${core.elasticity([1,2,3,4]).toFixed(4)} clumped=${core.elasticity([1,1,1,5]).toFixed(4)}`);
ok('滑らかな列のほうが優しい', core.kindness([1,2,3,4,5]) > core.kindness([1,9,2,8,3]));
ok('優しさは 0〜1', [[1,2,3],[5,5,5],[0,100,0]].every(s => {
  const g = core.kindness(s); return g >= 0 && g <= 1;
}));
ok('三条件がそろえば刻印なし', core.cainGate(0.9, 0.8, 0.7).marked === false);
ok('欠けた条件の数だけ理由が残る', core.cainGate(0.1, 0.1, 0.1).reasons.length === 3);

console.log('[方程式の値]');
ok('B1: |t|∫₀ᵗ√(ζx+a)dx (ζ=1,a=2,t=3) = 16.7037…',
   near(core.collate('B1', { zeta: 1, a: 2, t: 3 }).value, 3 * (2 / 3) * (Math.pow(5, 1.5) - Math.pow(2, 1.5)), 1e-9));
ok('B1: ζ→0 の極限が √a·t·|t| に連続接続',
   near(core.collate('B1', { zeta: 1e-15, a: 4, t: 2 }).value, Math.sqrt(4) * 2 * 2, 1e-6));
ok('B2: ζ/√|n·t_a| (4,2,8) = 1', near(core.collate('B2', { zeta: 4, n: 2, ta: 8 }).value, 1));
ok('B2: 分母 0 でも NaN を返さない', Number.isFinite(core.collate('B2', { zeta: 4, n: 0, ta: 8 }).value));
ok('B3: θ=2π で 12π + πr² に戻る', near(core.collate('B3', { r: 2, th: 2 * Math.PI }).value, 12 * Math.PI + Math.PI * 4, 1e-9));
ok('B3: θ=0 で 0', near(core.collate('B3', { r: 2, th: 0 }).value, 0, 1e-12));
ok('B4: −2tσ√π e^(−t²)·k (1,2,2) = −5.2162…',
   near(core.collate('B4', { t: 1, sigma: 2, k: 2 }).value, -2 * 1 * 2 * Math.sqrt(Math.PI) * Math.exp(-1) * 2, 1e-9));
ok('全箱: 既定値で値・指標がすべて有限', core.BOXES.every(b => {
  const r = core.collate(b.id, Object.fromEntries(b.vars.map(v => [v.key, v.def])), []);
  return [r.value, r.hForm, r.hNum, r.match, r.elasticity, r.kindness].every(Number.isFinite);
}));
ok('形シグネチャの重みは 4 成分・非負', core.BOXES.every(b =>
  b.weights.length === core.FORM_AXES.length && b.weights.every(w => w >= 0)));
ok('全箱: 既定値＋既定の数列はカインの門を通る（しきい値の較正）', core.BOXES.every(b => {
  const r = core.collate(b.id, Object.fromEntries(b.vars.map(v => [v.key, v.def])), core.parseSeq(b.seqDef));
  return !r.gate.marked;
}), core.BOXES.map(b => {
  const r = core.collate(b.id, Object.fromEntries(b.vars.map(v => [v.key, v.def])), core.parseSeq(b.seqDef));
  return `${b.id} m=${r.match.toFixed(2)} E=${r.elasticity.toFixed(2)} G=${r.kindness.toFixed(2)}`;
}).join(' / '));

console.log('[同値類マップ]');
{
  const rs = core.BOXES.map(b => core.collate(b.id, Object.fromEntries(b.vars.map(v => [v.key, v.def])), [1, 2, 3]));
  const groups = core.groupByClass(rs);
  const total = groups.reduce((n, g) => n + g.members.length, 0);
  ok('全結果がいずれかの類に属し、重複しない', total === rs.length);
  ok('類は k の昇順', groups.every((g, i) => i === 0 || groups[i - 1].k < g.k));
}

console.log('[アカシックレコード（ハッシュ連鎖）]');
{
  const mk = (i) => ({ seq: i, box: 'B1', v: i * 1.5 });
  let chain = [], prev = null;
  for (let i = 1; i <= 3; i++) { const rec = await core.sealRecord(prev, mk(i)); chain.push(rec); prev = rec.hash; }
  ok('健全な連鎖は検証を通る', (await core.verifyChain(chain)).ok);
  ok('先頭の prev は 0×64', chain[0].prev === '0'.repeat(64));
  ok('ハッシュは 64 桁の 16 進', chain.every(r => /^[0-9a-f]{64}$/.test(r.hash)));
  const tampered = chain.map(r => ({ ...r }));
  tampered[1].v = 999;
  const v = await core.verifyChain(tampered);
  ok('途中の書き換えを検出する', !v.ok && v.brokenAt === 1, 'brokenAt=' + v.brokenAt);
  ok('キー順を変えても正準形は同一', core.canonical({ a: 1, b: [2, 3] }) === core.canonical({ b: [2, 3], a: 1 }));
}

console.log('[数列の読み取り]');
ok('カンマ・読点・空白・改行を区切りとして読む',
   JSON.stringify(core.parseSeq('1, 2、3  4\n5')) === JSON.stringify([1, 2, 3, 4, 5]));
ok('数値でない語は捨てる', JSON.stringify(core.parseSeq('1, abc, 2')) === JSON.stringify([1, 2]));
ok('空入力は空配列', core.parseSeq('').length === 0 && core.parseSeq(null).length === 0);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
