/* preload.js — Contact Transporter Studio
 * アプリ本体 (自己完結 HTML) に、OS 標準のファイル ダイアログだけを公開します。
 *   ctNative.openFile({ title, name, extensions }) → { name, path, data } | null
 *   ctNative.showDownloads(file?)                  → ダウンロード フォルダを開く
 */
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("ctNative", {
  kind: "electron",
  openFile: (opts) => ipcRenderer.invoke("ct-open-file", opts || {}),
  showDownloads: (file) => ipcRenderer.invoke("ct-show-downloads", file || null),
});
