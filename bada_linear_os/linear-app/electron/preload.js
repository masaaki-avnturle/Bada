/* preload.js — 反重力リニア BadaLinear。本体は完全自己完結の WebGL ページで追加ブリッジ不要。 */
const { contextBridge } = require("electron");
contextBridge.exposeInMainWorld("lnNative", { platform: process.platform, app: "YMG-LN01" });
