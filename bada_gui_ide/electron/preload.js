/* preload.js — www/ の IDE へ安全に公開するデスクトップ専用ブリッジ */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("badaNative", {
  buildAndRun: (cSource) => ipcRenderer.invoke("bada:buildAndRun", cSource),
  saveFile: (name, text) => ipcRenderer.invoke("bada:saveFile", name, text),
  exportBinary: (srcPath) => ipcRenderer.invoke("bada:exportBinary", srcPath),
  /* @reviser : extension の FFI — インタープリタは同期実行のため sendSync */
  ffiSync: (lang, name, code, params, argv) =>
    ipcRenderer.sendSync("bada:ffiSync", lang, name, code, params, argv)
});
