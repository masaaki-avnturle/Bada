/*
 * core.js — PatchGuard の中核: Bada 処理系の上で guard.bada を動かす
 *
 * ブラウザ (index.html) と Node (cli.js) の両方で使います。
 *   const pg = PatchGuardCore.create({ Engine, PHP, Diff, guardSrc });
 *   const rep = pg.revise({ "index.php": "<?php ..." }, [{ "index.php": "<?php ..." }], waivers);
 *   pg.patchText(rep, false)   // 正味パッチ (base → final)
 *   pg.patchText(rep, true)    // 安全な部分パッチ (保留したファイルを除く)
 *   pg.rollbackText(rep)       // ロールバック用の逆パッチ
 * 判定・タプル・折り畳みはすべて guard.bada (Bada) が行い、ここは
 * ネイティブ組込み (PHP 解析・差分・SHA-256) を渡すだけです。
 */
"use strict";
(function (root) {
  function create(opts) {
    const { Engine, PHP, Diff, guardSrc } = opts;
    const I = new Engine.Interp({ maxSteps: 4e9, seed: 1 });
    const def = (name, fn) => { fn.bname = name; I.global.def(name, fn); };
    def("php_analyze", a => PHP.analyzePhp(String(a[0]), a[1] || []));
    def("diff_lines", a => Diff.diffLines(String(a[0]), String(a[1])));
    def("patch_apply", a => Diff.applyHunks(String(a[0]), a[1]));
    def("patch_reverse", a => Diff.reverseHunks(a[0]));
    def("unified", a => Diff.unified(String(a[0]), a[1], a[2] || {}));
    def("sha256", a => Diff.sha256(String(a[0])));
    I.run(guardSrc);
    const fn = name => I.global.get(name);
    const call = (name, args) => { I.steps = 0; return I.call(fn(name), args); };
    return {
      interp: I,
      version: fn("GUARD_VERSION"),
      revise(base, revisions, waivers) { return call("revise", [base, revisions, waivers || []]); },
      patchText(rep, onlySafe) { return call("patch_text", [rep, !!onlySafe]); },
      rollbackText(rep) { return call("rollback_text", [rep]); },
      tuples() { return fn("TS").items; },
      blob(h) { return call("blob", [h]); },
      rules() {
        return {
          sinks: fn("SINKS"), sanitizers: fn("SANITIZERS"),
          checks: fn("CHECKS").map(c => ({ id: c.id, title: c.title })), grammar: Array.from(I.rules.keys())
        };
      },
      sevRank: s => ({ none: -1, info: 0, low: 1, medium: 2, high: 3, critical: 4 })[s]
    };
  }
  const api = { create };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.PatchGuardCore = api;
})(this);
