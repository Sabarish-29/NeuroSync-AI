import { create } from 'zustand';
import type { SignalSnapshot } from '../types/electron';

const DEFAULT_SIGNALS: SignalSnapshot = {
  session_id: '',
  attention: 1.0,
  frustration: 0.0,
  fatigue: 0.0,
  boredom: 0.0,
  engagement: 1.0,
  cognitive_load: 0.3,
  emotion: 'neutral',
  face_detected: true,
  timestamp: 0,
};

interface SignalState {
  current: SignalSnapshot;
  history: SignalSnapshot[];
  maxHistory: number;

  updateSignals: (snapshot: SignalSnapshot) => void;
  reset: () => void;
}

export const useSignalStore = create<SignalState>((set) => ({
  current: DEFAULT_SIGNALS,
  history: [],
  maxHistory: 120, // ~30 seconds at 250ms interval

  updateSignals: (snapshot) =>
    set((state) => ({
      current: snapshot,
      history: [...state.history.slice(-(state.maxHistory - 1)), snapshot],
    })),

  reset: () =>
    set({
      current: DEFAULT_SIGNALS,
      history: [],
    }),
}));
