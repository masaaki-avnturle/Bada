/* preload.js — Bada QuantumCrypto
 *
 * アプリは完全自己完結の Web ページで、ネイティブ ブリッジは不要です
 * (鍵導出・暗号化・解除はすべてページ内 JS で完結し、通信しません)。
 * 将来のデスクトップ専用機能のためにフックだけ残します。 */
const { contextBridge } = require("electron");
contextBridge.exposeInMainWorld("qcNative", { platform: process.platform });
