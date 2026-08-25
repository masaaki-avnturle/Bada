/* preload.js — ZoneBrowser
 *
 * ZoneBrowser は完全自己完結の Web ページで、追加のネイティブ ブリッジは
 * 不要です(zone:// 解決・Jones 量子暗号・描画はすべてページ内 Bada
 * ランタイムで完結)。将来のデスクトップ専用機能のためにフックだけ残します。 */
const { contextBridge } = require("electron");
contextBridge.exposeInMainWorld("zoneNative", { platform: process.platform });
