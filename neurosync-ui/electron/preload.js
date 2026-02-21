const { contextBridge, ipcRenderer } = require('electron');

/**
 * Expose protected methods to the renderer process via contextBridge.
 * All communication with the main process goes through these channels.
 */
contextBridge.exposeInMainWorld('electronAPI', {
  // ─── Session management ───────────────────────────────────────
  startSession: (config) => ipcRenderer.invoke('session:start', config),
  endSession: (sessionId) => ipcRenderer.invoke('session:end', sessionId),

  // ─── Events ───────────────────────────────────────────────────
  sendEvent: (event) => ipcRenderer.invoke('event:send', event),

  // ─── Signals (real-time) ──────────────────────────────────────
  onSignalUpdate: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('signal:update', handler);
    return () => ipcRenderer.removeListener('signal:update', handler);
  },

  // ─── Interventions ────────────────────────────────────────────
  onIntervention: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('intervention:triggered', handler);
    return () => ipcRenderer.removeListener('intervention:triggered', handler);
  },
  acknowledgeIntervention: (id) => ipcRenderer.invoke('intervention:ack', id),

  // ─── Content generation ───────────────────────────────────────
  uploadPDF: (filePath) => ipcRenderer.invoke('content:upload', filePath),
  onGenerationProgress: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('content:progress', handler);
    return () => ipcRenderer.removeListener('content:progress', handler);
  },

  // ─── Spaced repetition ────────────────────────────────────────
  getDueReviews: (studentId) => ipcRenderer.invoke('reviews:due', studentId),
  submitReview: (data) => ipcRenderer.invoke('reviews:submit', data),

  // ─── Readiness check ──────────────────────────────────────────
  startReadinessCheck: (config) => ipcRenderer.invoke('readiness:start', config),
  submitReadinessResponse: (data) => ipcRenderer.invoke('readiness:submit', data),

  // ─── Knowledge graph ──────────────────────────────────────────
  getKnowledgeMap: (studentId) => ipcRenderer.invoke('knowledge:map', studentId),

  // ─── Webcam ───────────────────────────────────────────────────
  requestWebcamPermission: () => ipcRenderer.invoke('webcam:permission'),

  // ─── Window controls ──────────────────────────────────────────
  minimizeWindow: () => ipcRenderer.invoke('window:minimize'),
  maximizeWindow: () => ipcRenderer.invoke('window:maximize'),
  closeWindow: () => ipcRenderer.invoke('window:close'),
});
