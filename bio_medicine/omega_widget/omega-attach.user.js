// ==UserScript==
// @name         Ω-Apriori Attach (任意アプリ付加ウィジェット)
// @namespace    omega-apriori-bada
// @version      1.0
// @description  未知事前エンジン+単語補完ほかを任意のWebアプリへ付加 (概念実証/非医療)
// @match        *://*/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==
/*
  使い方: Tampermonkey / Violentmonkey に新規スクリプトとして登録。
  omega-attach.js をホスティングした URL を OMEGA_SRC に設定してください
  (同一オリジンに置けるなら相対URLでも可)。ローカル一体運用なら、
  omega-attach.js の中身をこの下にそのまま貼り付けてもOK。
  ⚠ 付加は自分が管理する/許諾されたアプリに対してのみ。
*/
(function () {
  "use strict";
  var OMEGA_SRC = "https://example.com/omega/omega-attach.js"; // ← 配置先URLに変更
  if (window.__omegaAttached) return;
  var s = document.createElement("script");
  s.src = OMEGA_SRC;
  s.onload = function () { console.log("Ω-Apriori attached via userscript"); };
  s.onerror = function () { console.error("omega-attach.js の読込に失敗。OMEGA_SRC を確認してください"); };
  (document.body || document.documentElement).appendChild(s);
})();
