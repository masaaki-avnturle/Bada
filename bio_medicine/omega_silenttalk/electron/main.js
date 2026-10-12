/* main.js — Electron ラッパー (Windows/Linux) — Ω-SilentTalk → BadaGPT
   概念デモ・非医療・非読心。カメラは口の動きエネルギーの疑似記号化のみ。 */
const { app, BrowserWindow } = require("electron");
const path = require("path");
function indexPath(){return app.isPackaged?path.join(process.resourcesPath,"www","index.html"):path.join(__dirname,"..","www","index.html");}
function createWindow(){const win=new BrowserWindow({width:1080,height:860,backgroundColor:"#0b0e14",title:"Ω-SilentTalk → BadaGPT",webPreferences:{contextIsolation:true,nodeIntegration:false}});win.setMenuBarVisibility(false);win.loadFile(indexPath());}
app.whenReady().then(createWindow);
app.on("window-all-closed",()=>{if(process.platform!=="darwin")app.quit();});
app.on("activate",()=>{if(BrowserWindow.getAllWindows().length===0)createWindow();});
