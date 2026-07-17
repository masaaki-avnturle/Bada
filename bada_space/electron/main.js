// BADA SPACE — 空間コンピューティング — Electron main (Windows 10/11)
const { app, BrowserWindow, Menu, shell } = require('electron');
const path = require('path');
app.commandLine.appendSwitch('high-dpi-support', '1');
let mainWindow = null;
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1500, height: 940, minWidth: 960, minHeight: 620,
    backgroundColor: '#05070e', title: 'BADA SPACE — 空間コンピューティング',
    icon: path.join(__dirname, '..', 'resources', 'icon.png'),
    autoHideMenuBar: true, fullscreenable: true,
    webPreferences: { contextIsolation: true, nodeIntegration: false, spellcheck: false },
  });
  mainWindow.loadFile(path.join(__dirname, '..', 'www', 'index.html'));
  mainWindow.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: 'deny' }; });
  mainWindow.on('closed', () => { mainWindow = null; });
}
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) { app.quit(); } else {
  app.on('second-instance', () => { if (mainWindow) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.focus(); } });
  app.whenReady().then(() => { Menu.setApplicationMenu(null); createWindow();
    app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); }); });
}
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
