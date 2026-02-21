/**
 * Session manager — handles session lifecycle and persistence.
 */

import type { SessionConfig, SessionResponse } from '../types/electron';

export class SessionManager {
  private sessionId: string | null = null;
  private startTime: number | null = null;

  async start(config: SessionConfig): Promise<SessionResponse> {
    const response = await (
      window.electronAPI?.startSession(config) ??
      Promise.resolve({ session_id: config.session_id, status: 'started' })
    );

    this.sessionId = config.session_id;
    this.startTime = Date.now();

    return response;
  }

  async end(): Promise<SessionResponse | null> {
    if (!this.sessionId) return null;

    const response = await (
      window.electronAPI?.endSession(this.sessionId) ??
      Promise.resolve({ session_id: this.sessionId, status: 'ended' })
    );

    this.sessionId = null;
    this.startTime = null;

    return response;
  }

  get isActive(): boolean {
    return this.sessionId !== null;
  }

  get currentSessionId(): string | null {
    return this.sessionId;
  }

  get elapsedMs(): number {
    if (!this.startTime) return 0;
    return Date.now() - this.startTime;
  }
}

export const sessionManager = new SessionManager();
