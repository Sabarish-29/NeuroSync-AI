/**
 * IPC handlers — bridges Electron main process to the Python FastAPI backend.
 */

const { ipcMain, BrowserWindow } = require('electron');

const PYTHON_API = process.env.NEUROSYNC_API_URL || 'http://127.0.0.1:8000';

/**
 * Helper: forward a request to the Python API.
 */
async function apiRequest(path, options = {}) {
  const url = `${PYTHON_API}${path}`;
  const fetchOpts = {
    method: options.method || 'GET',
    headers: { 'Content-Type': 'application/json', ...options.headers },
  };
  if (options.body) {
    fetchOpts.body = JSON.stringify(options.body);
  }
  try {
    const response = await fetch(url, fetchOpts);
    return await response.json();
  } catch (error) {
    console.error(`[IPC] API error ${path}:`, error.message);
    return { status: 'error', message: error.message };
  }
}

// ─── Session ──────────────────────────────────────────────────────────────────

ipcMain.handle('session:start', async (_event, config) => {
  return apiRequest('/session/start', { method: 'POST', body: config });
});

ipcMain.handle('session:end', async (_event, sessionId) => {
  return apiRequest(`/session/${sessionId}/end`, { method: 'POST' });
});

// ─── Events ───────────────────────────────────────────────────────────────────

ipcMain.handle('event:send', async (_event, eventData) => {
  return apiRequest('/events', { method: 'POST', body: eventData });
});

// ─── Content generation ────────────────────────────────────────────────────────

ipcMain.handle('content:upload', async (_event, filePath) => {
  // In production, use FormData + file streaming
  // For Electron, we pass the file path to the backend
  return apiRequest('/content/upload', {
    method: 'POST',
    body: { file_path: filePath },
  });
});

// ─── Reviews ──────────────────────────────────────────────────────────────────

ipcMain.handle('reviews:due', async (_event, studentId) => {
  return apiRequest(`/reviews/${studentId}/due`);
});

ipcMain.handle('reviews:submit', async (_event, data) => {
  return apiRequest('/reviews/submit', { method: 'POST', body: data });
});

// ─── Readiness ────────────────────────────────────────────────────────────────

ipcMain.handle('readiness:start', async (_event, config) => {
  return apiRequest('/readiness/start', { method: 'POST', body: config });
});

ipcMain.handle('readiness:submit', async (_event, data) => {
  return apiRequest('/readiness/start', { method: 'POST', body: data });
});

// ─── Knowledge graph ──────────────────────────────────────────────────────────

ipcMain.handle('knowledge:map', async (_event, studentId) => {
  return apiRequest(`/knowledge/map/${studentId}`);
});

// ─── Webcam permission ────────────────────────────────────────────────────────

ipcMain.handle('webcam:permission', async () => {
  return { granted: true }; // Browser handles actual permission
});

// ─── Window controls ──────────────────────────────────────────────────────────

ipcMain.handle('window:minimize', async (event) => {
  BrowserWindow.fromWebContents(event.sender)?.minimize();
});

ipcMain.handle('window:maximize', async (event) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  if (win?.isMaximized()) {
    win.unmaximize();
  } else {
    win?.maximize();
  }
});

ipcMain.handle('window:close', async (event) => {
  BrowserWindow.fromWebContents(event.sender)?.close();
});
