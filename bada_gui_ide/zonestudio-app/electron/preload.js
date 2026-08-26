/* preload.js — Zone Studio
 * 本体は完全自己完結の Web ページで、追加のネイティブ ブリッジは不要です。 */
const { contextBridge } = require("electron");
contextBridge.exposeInMainWorld("zoneStudioNative", { platform: process.platform });
