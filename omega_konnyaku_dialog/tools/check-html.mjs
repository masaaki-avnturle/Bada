#!/usr/bin/env node
/**
 * check-html.mjs — index.html の健全性検査（ビルド前のゲート）。
 *
 *   node tools/check-html.mjs
 *
 * - すべてのインライン <script> が構文として正しいか（node --check）
 * - 計算核の区間マーカーが残っているか（selftest.mjs が依存する）
 * - ダイアログと箱の要素 id がそろっているか（UI の配線が消えていないか）
 * - 単一ファイルであること（外部 src / link に依存していない）
 */
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';

const here = dirname(fileURLToPath(import.meta.url));
const file = join(here, '..', 'index.html');
const html = readFileSync(file, 'utf8');
const problems = [];

/* インライン script の構文検査 */
const scripts = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
if (scripts.length < 2) problems.push(`インライン script が ${scripts.length} 個しかない（計算核 + UI の 2 個以上を期待）`);
const dir = mkdtempSync(join(tmpdir(), 'konnyaku-'));
scripts.forEach((src, i) => {
  const p = join(dir, `inline-${i}.js`);
  writeFileSync(p, src);
  try { execFileSync(process.execPath, ['--check', p], { stdio: 'pipe' }); }
  catch (e) { problems.push(`インライン script #${i} の構文エラー:\n${e.stderr?.toString() || e.message}`); }
});

/* selftest.mjs が抜き出す区間のマーカー */
for (const marker of ['KONNYAKU CORE BEGIN', '/* ===== KONNYAKU CORE END ===== */']) {
  if (!html.includes(marker)) problems.push(`計算核のマーカーがない: ${marker}`);
}

/* 計算核の関数と、UI の配線 */
for (const marker of ['function shannon', 'function formEntropy', 'function numericEntropy',
                      'function elasticity', 'function kindness', 'function cainGate',
                      'function collate', 'function groupByClass', 'function sealRecord',
                      'function verifyChain', 'const BOXES']) {
  if (!html.includes(marker)) problems.push(`計算核に見当たらない: ${marker}`);
}
for (const id of ['dlgInput', 'dlgResult', 'dlgClasses', 'dlgLedger', 'dlgHelp', 'dlgMsg',
                  'boxes', 'btnAll', 'btnLedger', 'btnVerify', 'btnExport', 'btnClear']) {
  if (!html.includes(`id="${id}"`)) problems.push(`要素 id がない: ${id}`);
}
if (!html.includes('showModal()')) problems.push('モーダルダイアログの呼び出し (showModal) がない');

/* 単一ファイルであること */
if (/<script[^>]*\bsrc=/.test(html)) problems.push('外部 script を参照している（単一ファイル配布が壊れる）');
if (/<link[^>]*\brel=["']?stylesheet/i.test(html)) problems.push('外部スタイルシートを参照している（単一ファイル配布が壊れる）');

if (problems.length) {
  console.error('index.html の検査に失敗しました:');
  for (const p of problems) console.error(' - ' + p);
  process.exit(1);
}
console.log(`index.html OK — インライン script ${scripts.length} 個、計算核・ダイアログ配線・単一ファイル性を確認`);
