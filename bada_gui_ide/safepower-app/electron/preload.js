/* preload.js — SafePower のデスクトップ専用ブリッジ
 * 実際の電源操作は main プロセスの IPC で「確認後のみ」実行します。 */
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("safePower", {
  platform: process.platform,
  preview: (action) => ipcRenderer.invoke("safepower:preview", action),
  run: (action) => ipcRenderer.invoke("safepower:run", action)
});
