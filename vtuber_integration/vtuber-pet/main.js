const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain, shell } = require('electron');
const path = require('path');

let mainWindow;
let tray;

const VTUBER_URL = 'http://localhost:12393';
const CONFIG_PATH = path.join(__dirname, 'pet-config.json');

const DEFAULT_CONFIG = {
  width: 320,
  height: 480,
  x: null,
  y: null,
  zoom: 1.0,
  alwaysOnTop: true,
  transparent: true,
  clickThrough: false,
};

function loadConfig() {
  try {
    const fs = require('fs');
    if (fs.existsSync(CONFIG_PATH)) {
      return { ...DEFAULT_CONFIG, ...JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8')) };
    }
  } catch (e) {}
  return { ...DEFAULT_CONFIG };
}

function saveConfig(cfg) {
  try {
    const fs = require('fs');
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(cfg, null, 2));
  } catch (e) {}
}

function createTray(win, config) {
  // Create a simple icon
  const iconSize = 128;
  const canvas = { 
    getBitmap: () => Buffer.alloc(iconSize * iconSize * 4) 
  };
  
  tray = new Tray(path.join(__dirname, 'icon.png'));
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Toggle Always on Top',
      type: 'checkbox',
      checked: config.alwaysOnTop,
      click: (item) => {
        config.alwaysOnTop = item.checked;
        win.setAlwaysOnTop(item.checked, 'floating');
        saveConfig(config);
      }
    },
    {
      label: 'Toggle Click-Through',
      type: 'checkbox',
      checked: config.clickThrough,
      click: (item) => {
        config.clickThrough = item.checked;
        win.setIgnoreMouseEvents(item.checked);
        saveConfig(config);
      }
    },
    { type: 'separator' },
    {
      label: 'Zoom In',
      click: () => {
        config.zoom = Math.min(config.zoom + 0.1, 2.0);
        win.webContents.setZoomFactor(config.zoom);
        saveConfig(config);
      }
    },
    {
      label: 'Zoom Out',
      click: () => {
        config.zoom = Math.max(config.zoom - 0.1, 0.5);
        win.webContents.setZoomFactor(config.zoom);
        saveConfig(config);
      }
    },
    { type: 'separator' },
    {
      label: 'Reload',
      click: () => win.reload()
    },
    {
      label: 'Open in Browser',
      click: () => shell.openExternal(VTUBER_URL)
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        saveConfig(config);
        app.quit();
      }
    }
  ]);
  
  tray.setToolTip('VTuber Pet - Right-click for options');
  tray.setContextMenu(contextMenu);
  
  tray.on('click', () => {
    if (win.isVisible()) {
      win.hide();
    } else {
      win.show();
    }
  });
}

function createWindow() {
  const config = loadConfig();
  
  // Remove frame for transparent look
  mainWindow = new BrowserWindow({
    width: config.width,
    height: config.height,
    x: config.x,
    y: config.y,
    frame: false,
    transparent: config.transparent,
    hasShadow: true,
    resizable: true,
    alwaysOnTop: config.alwaysOnTop,
    skipTaskbar: true,
    title: 'VTuber Pet',
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  });

  // Load VTuber frontend
  mainWindow.loadURL(VTUBER_URL);
  
  // Apply zoom
  mainWindow.webContents.setZoomFactor(config.zoom);
  
  // Click-through support
  if (config.clickThrough) {
    mainWindow.setIgnoreMouseEvents(true);
  }
  
  // Dragging support (drag the window by any visible area)
  mainWindow.on('will-move', (event, newBounds) => {
    config.x = newBounds.x;
    config.y = newBounds.y;
    saveConfig(config);
  });
  
  mainWindow.on('resize', (event, newBounds) => {
    config.width = newBounds.width;
    config.height = newBounds.height;
    saveConfig(config);
  });
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
  
  // Wait for page to load, then inject transparency helpers
  mainWindow.webContents.on('did-finish-load', () => {
    // Inject CSS to make background transparent
    mainWindow.webContents.insertCSS(`
      body, html {
        background: transparent !important;
      }
      /* Hide header/navbar if present */
      header, nav, .navbar, #header, .vtb-header {
        display: none !important;
      }
    `);
  });
  
  // Create tray
  createTray(mainWindow, config);
  
  // Global shortcuts
  const { globalShortcut } = require('electron');
  globalShortcut.register('Alt+V', () => {
    if (mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow.show();
    }
  });
  globalShortcut.register('Alt+Q', () => {
    saveConfig(config);
    app.quit();
  });
}

app.whenReady().then(() => {
  createWindow();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  globalShortcut.unregisterAll();
});