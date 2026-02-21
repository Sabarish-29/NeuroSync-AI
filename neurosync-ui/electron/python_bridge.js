/**
 * Python subprocess manager for the Electron app.
 * Manages the lifecycle of the FastAPI backend process.
 */

const { spawn } = require('child_process');
const path = require('path');

class PythonBridge {
  constructor() {
    this.process = null;
    this.isReady = false;
    this.port = 8000;
    this.host = '127.0.0.1';
  }

  /**
   * Start the Python FastAPI backend.
   * @returns {Promise<void>}
   */
  async start() {
    if (this.process) {
      console.warn('[PythonBridge] Backend already running');
      return;
    }

    const pythonPath = process.env.PYTHON_PATH || 'python3';
    const projectRoot = path.join(__dirname, '..', '..');

    this.process = spawn(
      pythonPath,
      ['-m', 'uvicorn', 'neurosync.api.server:app', '--host', this.host, '--port', String(this.port)],
      {
        cwd: projectRoot,
        env: { ...process.env, PYTHONPATH: projectRoot },
        stdio: ['pipe', 'pipe', 'pipe'],
      }
    );

    this.process.stdout.on('data', (data) => {
      const msg = data.toString().trim();
      console.log(`[Python] ${msg}`);
      if (msg.includes('Uvicorn running') || msg.includes('Application startup complete')) {
        this.isReady = true;
      }
    });

    this.process.stderr.on('data', (data) => {
      const msg = data.toString().trim();
      console.error(`[Python] ${msg}`);
      if (msg.includes('Uvicorn running') || msg.includes('Application startup complete')) {
        this.isReady = true;
      }
    });

    this.process.on('close', (code) => {
      console.log(`[PythonBridge] Process exited with code ${code}`);
      this.process = null;
      this.isReady = false;
    });

    // Wait for server to be ready
    await this.waitForReady();
  }

  /**
   * Wait until the backend is accepting connections.
   * @param {number} timeout - Max wait time in ms
   * @returns {Promise<void>}
   */
  async waitForReady(timeout = 15000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      try {
        const response = await fetch(`http://${this.host}:${this.port}/health`);
        if (response.ok) {
          this.isReady = true;
          console.log('[PythonBridge] Backend is ready');
          return;
        }
      } catch {
        // Not ready yet
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    console.warn('[PythonBridge] Backend startup timed out, continuing anyway');
  }

  /**
   * Stop the Python backend process.
   */
  stop() {
    if (this.process) {
      this.process.kill('SIGTERM');
      this.process = null;
      this.isReady = false;
      console.log('[PythonBridge] Backend stopped');
    }
  }

  /**
   * Get the base URL of the running backend.
   * @returns {string}
   */
  get baseUrl() {
    return `http://${this.host}:${this.port}`;
  }
}

module.exports = PythonBridge;
