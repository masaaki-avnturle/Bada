/* preload.js — ACPI
 *
 * ACPI 本体は完全自己完結の Web ページ (物理層 + Ω 作用素層はすべて
 * ページ内 JS で完結) なので、追加のネイティブ ブリッジは不要です。
 * ページ側はこのフックの有無でデスクトップ アプリとして動作していることを
 * 判定し、ヘッダの表示を切り替えます。 */
const { contextBridge } = require("electron");
contextBridge.exposeInMainWorld("acpiNative", { platform: process.platform });
