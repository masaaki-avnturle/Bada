/* preload.js — LÆVATEIN
 *
 * 本体は完全自己完結の Web ページなので追加のネイティブ ブリッジは不要です。
 * ページ側はこのフックの有無でデスクトップ アプリとして動作していることを
 * 判定し、ヘッダの表示とダウンロードの経路を切り替えます。 */
const { contextBridge } = require("electron");
contextBridge.exposeInMainWorld("ldNative", { platform: process.platform });
