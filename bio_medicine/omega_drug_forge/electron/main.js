const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 900,
    title: 'Ω-DrugForge — 形態形成場 薬剤製造シミュレーション',
    icon: path.join(__dirname, '..', 'www', 'icon.png'),
    webPreferences: { nodeIntegration: false, contextIsolation: true }
  });
  win.loadFile(path.join(__dirname, '..', 'www', 'index.html'));
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
