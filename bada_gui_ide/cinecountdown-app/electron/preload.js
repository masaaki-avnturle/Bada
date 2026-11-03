/* preload.js — Bada 映画カウントダウンエディタ
 *
 * アプリは完全自己完結の Web ページです。単体HTMLプレーヤー書き出し時に
 * エンジン (countdown.js) を同梱するためのソース取得のみを公開します。 */
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("cineNative", {
  platform: process.platform,
  engineSource: function () { return ipcRenderer.invoke("engine-source"); }
});
