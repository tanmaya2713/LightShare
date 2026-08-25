/**
 * LightShare V1.0 - Electron Main Desktop App Process
 * Manages background microservice, native window, and desktop lifecycle.
 */

const { app, BrowserWindow, Menu, Tray, nativeImage, shell } = require('electron');
const path = require('node:path');
const { spawn } = require('node:child_process');
const http = require('node:http');

let mainWindow = null;
let pyProcess = null;
const SERVER_PORT = 53317;
const SERVER_URL = `http://localhost:${SERVER_PORT}`;

// Check if Python backend is alive
function checkServerReady(callback) {
  const req = http.get(`${SERVER_URL}/api/status`, (res) => {
    if (res.statusCode === 200) {
      callback(true);
    } else {
      callback(false);
    }
  });
  req.on('error', () => callback(false));
  req.setTimeout(1000, () => {
    req.destroy();
    callback(false);
  });
}

// Start Python FastAPI server if not already active
function startPythonBackend() {
  checkServerReady((isAlive) => {
    if (isAlive) {
      console.log('FastAPI backend already running.');
      createMainWindow();
      return;
    }

    console.log('Spawning Python FastAPI backend...');
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    pyProcess = spawn(pythonCmd, ['-m', 'app.main'], {
      cwd: __dirname,
      detached: false,
      stdio: 'ignore'
    });

    pyProcess.on('error', (err) => {
      console.warn('Python spawn warning:', err.message);
    });

    // Poll until server is ready
    let attempts = 0;
    const interval = setInterval(() => {
      attempts++;
      checkServerReady((ready) => {
        if (ready || attempts > 15) {
          clearInterval(interval);
          createMainWindow();
        }
      });
    }, 400);
  });
}

// Create native desktop GUI window
function createMainWindow() {
  if (mainWindow) return;

  mainWindow = new BrowserWindow({
    width: 1080,
    height: 780,
    minWidth: 420,
    minHeight: 600,
    title: 'LightShare V1.0',
    backgroundColor: '#060813',
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.loadURL(SERVER_URL).catch(() => {
    // Fallback load local static file if offline
    mainWindow.loadFile(path.join(__dirname, 'app', 'static', 'index.html'));
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http:') || url.startsWith('https:')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.whenReady().then(() => {
  startPythonBackend();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (pyProcess) {
    try {
      pyProcess.kill();
    } catch (e) {}
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (pyProcess) {
    try {
      pyProcess.kill();
    } catch (e) {}
  }
});
