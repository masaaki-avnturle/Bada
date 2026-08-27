/* preload.js — InstantOn のデスクトップ専用ブリッジ
 * 実際の設定・休止は main プロセスの IPC で「確認後のみ」実行します。 */
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("instantOn", {
  platform: process.platform,
  preview: (action) => ipcRenderer.invoke("instanton:preview", action),
  run: (action) => ipcRenderer.invoke("instanton:run", action)
});
