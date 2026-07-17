// ═══════════════════════════════════════════════════
// BADA KEYHOLE — P2P インターネットTV — Electron main (Windows 10/11)
// ═══════════════════════════════════════════════════
const { app, BrowserWindow, Menu, shell, session } = require('electron');
const path = require('path');

app.commandLine.appendSwitch('high-dpi-support', '1');

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1120,
    height: 900,
    minWidth: 560,
    minHeight: 620,
    backgroundColor: '#0a0d14',
    title: 'BADA KEYHOLE — P2P インターネットTV',
    icon: path.join(__dirname, '..', 'resources', 'icon.png'),
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      spellcheck: false,
    },
  });

  // カメラ/マイクの許可（P2P 放送用）
  session.defaultSession.setPermissionRequestHandler((wc, permission, cb) => {
    cb(permission === 'media' || permission === 'fullscreen' ? true : false);
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'www', 'index.html'));

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => { mainWindow = null; });
}

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
