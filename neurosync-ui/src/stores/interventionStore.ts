import { create } from 'zustand';
import type { Intervention } from '../types/electron';

interface InterventionState {
  activeIntervention: Intervention | null;
  history: Intervention[];

  triggerIntervention: (intervention: Intervention) => void;
  acknowledgeIntervention: (id: string) => void;
  reset: () => void;
}

export const useInterventionStore = create<InterventionState>((set) => ({
  activeIntervention: null,
  history: [],

  triggerIntervention: (intervention) =>
    set((state) => ({
      activeIntervention: intervention,
      history: [...state.history, intervention],
    })),

  acknowledgeIntervention: (id) => {
    window.electronAPI?.acknowledgeIntervention(id);
    set({ activeIntervention: null });
  },

  reset: () =>
    set({
      activeIntervention: null,
      history: [],
    }),
}));
