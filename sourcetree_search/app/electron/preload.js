/* preload.js — Bada Search: renderer へ検索 API を安全に公開 */
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("badaSearch", {
  chooseFolder: function(){ return ipcRenderer.invoke("choose-folder"); },
  buildIndex:  function(dir){ return ipcRenderer.invoke("build-index", dir); },
  search:      function(q, opts){ return ipcRenderer.invoke("search", q, opts); },
  openFile:    function(p){ return ipcRenderer.invoke("open-file", p); },
  revealFile:  function(p){ return ipcRenderer.invoke("reveal-file", p); },
  startupRepo: function(){ return ipcRenderer.invoke("startup-repo"); },
  appPath:     function(){ return ipcRenderer.invoke("app-path"); }
});
