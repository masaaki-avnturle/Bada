/* preload.js — 反重力発生器 航空機 YMG-AG01
 *
 * 本体は完全自己完結の WebGL ページ (BadaUFO-OS 反重力方程式コアと Three.js を
 * 同梱) で、追加ネイティブ ブリッジは不要。将来のデスクトップ専用機能のための
 * 最小フックだけ残す。 */
const { contextBridge } = require("electron");
contextBridge.exposeInMainWorld("agNative", { platform: process.platform, app: "YMG-AG01" });
