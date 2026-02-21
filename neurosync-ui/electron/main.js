const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

/**
 * Start the Python FastAPI backend server.
 * Returns a promise that resolves after the server is ready.
 */
function startPythonBackend() {
  const pythonPath = process.env.PYTHON_PATH || 'python3';
  const scriptPath = path.join(__dirname, '..', '..', 'neurosync', 'api', 'server.py');

  pythonProcess = spawn(pythonPath, ['-m', 'uvicorn', 'neurosync.api.server:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: path.join(__dirname, '..', '..'),
    env: { ...process.env, PYTHONPATH: path.join(__dirname, '..', '..') },
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Python] ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Python] ${data.toString().trim()}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`[Python] Process exited with code ${code}`);
  });

  // Wait for server to start
  return new Promise((resolve) => {
    setTimeout(resolve, 3000);
  });
}

async function createWindow() {
  // Start Python backend first
  await startPythonBackend();

  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    minWidth: 1024,
    minHeight: 768,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    frame: true,
    backgroundColor: '#0f1018',
    show: false,
  });

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Load Vite dev server in development
  if (process.env.NODE_ENV !== 'production') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
    pythonProcess = null;
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Load IPC handlers
require('./ipc/handlers.js');
