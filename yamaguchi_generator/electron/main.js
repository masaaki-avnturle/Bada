// ═══════════════════════════════════════════════════
// Yamaguchi Framework — Electron main process
// Windows 10 / 11 デスクトップアプリのエントリポイント
// ═══════════════════════════════════════════════════
const { app, BrowserWindow, Menu, shell } = require('electron');
const path = require('path');

// 高DPIディスプレイでのペン/タッチ座標精度を確保
app.commandLine.appendSwitch('high-dpi-support', '1');
app.commandLine.appendSwitch('force-device-scale-factor', '1');

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#06080f',
    title: '山口フレームワーク — 方程式↔抽象画 生成器',
    icon: path.join(__dirname, '..', 'resources', 'icon.png'),
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      // ペン/タッチ入力を有効化
      enableBlinkFeatures: 'PointerEvent',
      spellcheck: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'www', 'index.html'));

  // 外部リンクは既定ブラウザで開く
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => { mainWindow = null; });
}

// シングルインスタンス化
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(() => {
    Menu.setApplicationMenu(null);
    createWindow();
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
