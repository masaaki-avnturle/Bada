const { app, BrowserWindow } = require('electron');
const path = require('path');

function indexPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, 'www', 'index.html')
    : path.join(__dirname, '..', 'www', 'index.html');
}

function iconPath() {
  return app.isPackaged
    ? path.join(process.resourcesPath, 'www', 'icon.png')
    : path.join(__dirname, '..', 'www', 'icon.png');
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 900,
    backgroundColor: '#0a1628',
    title: 'Ω-DrugForge — 形態形成場 薬剤製造シミュレーション',
    icon: iconPath(),
    webPreferences: { nodeIntegration: false, contextIsolation: true }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(indexPath());
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
