/* preload.js — MadoKey デスクトップ専用ブリッジ
 * 設定エディタ (renderer) のキーバインドを main プロセスへ渡し、本物の
 * グローバル ホットキーとして登録します。ブラウザ版では存在しません。 */
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("madokey", {
  platform: process.platform,
  setBinds: (binds) => ipcRenderer.invoke("madokey:setBinds", binds)
});
