import { useEffect, useCallback } from 'react';
import { useInterventionStore } from '../stores/interventionStore';
import type { Intervention } from '../types/electron';

/**
 * Hook that subscribes to intervention events from the backend.
 * Falls back to demo interventions when not connected.
 */
export function useInterventions(sessionId: string | null) {
  const { activeIntervention, acknowledgeIntervention, triggerIntervention } =
    useInterventionStore();

  useEffect(() => {
    if (!sessionId) return;

    // Subscribe to Electron IPC intervention events
    const unsubscribe = window.electronAPI?.onIntervention((intervention: Intervention) => {
      triggerIntervention(intervention);
    });

    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [sessionId, triggerIntervention]);

  return {
    activeIntervention,
    acknowledgeIntervention,
    triggerIntervention,
  };
}
