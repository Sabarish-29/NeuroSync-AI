import { create } from 'zustand';
import type { SessionConfig } from '../types/electron';

interface SessionState {
  sessionId: string | null;
  studentId: string;
  lessonId: string;
  isActive: boolean;
  webcamEnabled: boolean;
  startedAt: number | null;

  startSession: (config: SessionConfig) => void;
  endSession: (sessionId: string) => void;
  reset: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: null,
  studentId: '',
  lessonId: '',
  isActive: false,
  webcamEnabled: false,
  startedAt: null,

  startSession: (config) => {
    // Call Electron API if available
    window.electronAPI?.startSession(config);

    set({
      sessionId: config.session_id,
      studentId: config.student_id,
      lessonId: config.lesson_id,
      webcamEnabled: config.webcam_enabled,
      isActive: true,
      startedAt: Date.now(),
    });
  },

  endSession: (sessionId) => {
    window.electronAPI?.endSession(sessionId);

    set({
      isActive: false,
    });
  },

  reset: () =>
    set({
      sessionId: null,
      studentId: '',
      lessonId: '',
      isActive: false,
      webcamEnabled: false,
      startedAt: null,
    }),
}));
