/* preload.js — www/ の IDE へ安全に公開するデスクトップ専用ブリッジ */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("badaNative", {
  buildAndRun: (cSource) => ipcRenderer.invoke("bada:buildAndRun", cSource),
  saveFile: (name, text) => ipcRenderer.invoke("bada:saveFile", name, text),
  exportBinary: (srcPath) => ipcRenderer.invoke("bada:exportBinary", srcPath)
});
