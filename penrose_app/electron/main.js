// Electron main process for the Penrose 絵記号 studio (Windows 10/11 .exe).
// Loads the self-contained studio (www/index.html) into a native window.
// No network is used — the app works fully offline.
const { app, BrowserWindow, Menu, shell, session, dialog } = require('electron');
const path = require('path');

// Make in-app downloads (the generated app from the equation network) prompt a
// Save As dialog and actually write the file. Without this, an anchor/blob
// download inside the window would not save anywhere in the packaged .exe.
function enableDownloads() {
  session.defaultSession.on('will-download', (event, item) => {
    const savePath = dialog.showSaveDialogSync({
      title: '生成アプリを保存',
      defaultPath: item.getFilename() || 'bada_generated_app.html',
      filters: [{ name: 'HTML', extensions: ['html'] }]
    });
    if (savePath) {
      item.setSavePath(savePath);
      item.once('done', (_e, state) => {
        if (state === 'completed') shell.showItemInFolder(savePath);
      });
    } else {
      item.cancel();
    }
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#0b0e14',
    title: 'ペンローズ絵記号スタジオ — Bada',
    icon: path.join(__dirname, '..', 'build', 'icon.png'),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  win.loadFile(path.join(__dirname, '..', 'www', 'index.html'));

  // Open external links (if any) in the system browser, not the app window.
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// A minimal menu (with a Japanese-friendly reload / devtools / quit).
function buildMenu() {
  const template = [
    {
      label: '表示 (View)',
      submenu: [
        { role: 'reload', label: '再読み込み' },
        { role: 'toggleDevTools', label: '開発者ツール' },
        { type: 'separator' },
        { role: 'resetZoom', label: 'ズームをリセット' },
        { role: 'zoomIn', label: '拡大' },
        { role: 'zoomOut', label: '縮小' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: '全画面' }
      ]
    },
    {
      label: 'アプリ (App)',
      submenu: [
        { role: 'quit', label: '終了' }
      ]
    }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.whenReady().then(() => {
  buildMenu();
  enableDownloads();
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
