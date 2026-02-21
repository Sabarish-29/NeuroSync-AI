import { useState, useEffect, useRef, useCallback } from 'react';
import type { SignalSnapshot } from '../types/electron';

/**
 * Hook for subscribing to signal updates (simpler alternative to useFusionLoop).
 */
export function useSignals(sessionId: string | null) {
  const [signals, setSignals] = useState<SignalSnapshot>({
    session_id: sessionId || '',
    attention: 1.0,
    frustration: 0.0,
    fatigue: 0.0,
    boredom: 0.0,
    engagement: 1.0,
    cognitive_load: 0.3,
    emotion: 'neutral',
    face_detected: true,
    timestamp: 0,
  });

  useEffect(() => {
    if (!sessionId) return;

    const unsubscribe = window.electronAPI?.onSignalUpdate((data) => {
      setSignals(data);
    });

    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [sessionId]);

  return signals;
}
