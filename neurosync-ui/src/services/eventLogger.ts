/**
 * Event logger — records and buffers learning events.
 */

import type { LearningEvent } from '../types/electron';

export class EventLogger {
  private buffer: LearningEvent[] = [];
  private flushInterval: ReturnType<typeof setInterval> | null = null;
  private maxBufferSize = 50;

  constructor(private sessionId: string) {}

  /**
   * Log a learning event. Buffers and flushes periodically.
   */
  log(event: Omit<LearningEvent, 'session_id'>): void {
    const fullEvent = {
      session_id: this.sessionId,
      ...event,
      timestamp: (event.timestamp as number | undefined) ?? Date.now(),
    } as LearningEvent;

    this.buffer.push(fullEvent);

    if (this.buffer.length >= this.maxBufferSize) {
      this.flush();
    }
  }

  /**
   * Flush buffered events to the backend.
   */
  async flush(): Promise<void> {
    if (this.buffer.length === 0) return;

    const events = [...this.buffer];
    this.buffer = [];

    for (const event of events) {
      try {
        await window.electronAPI?.sendEvent(event);
      } catch {
        // Re-buffer on failure
        this.buffer.push(event);
      }
    }
  }

  /**
   * Start periodic flushing.
   */
  startAutoFlush(intervalMs = 5000): void {
    if (this.flushInterval) return;
    this.flushInterval = setInterval(() => this.flush(), intervalMs);
  }

  /**
   * Stop periodic flushing and flush remaining events.
   */
  async stop(): Promise<void> {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
    await this.flush();
  }

  get pendingCount(): number {
    return this.buffer.length;
  }
}
