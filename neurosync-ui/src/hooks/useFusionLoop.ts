import { useState, useEffect, useCallback, useRef } from 'react';
import { useSignalStore } from '../stores/signalStore';
import type { SignalSnapshot } from '../types/electron';

/**
 * Hook that subscribes to the 250ms fusion loop via WebSocket.
 * Falls back to simulated signals when not connected to backend.
 */
export function useFusionLoop(sessionId: string | null) {
  const { current: signals, history, updateSignals } = useSignalStore();
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    // Attempt WebSocket connection
    try {
      const ws = new WebSocket(`ws://127.0.0.1:8000/ws/${sessionId}`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data: SignalSnapshot = JSON.parse(event.data);
          updateSignals(data);
        } catch {
          // Ignore parse errors
        }
      };

      ws.onerror = () => {
        // Fall back to simulation
        startSimulation();
      };

      ws.onclose = () => {
        wsRef.current = null;
      };
    } catch {
      startSimulation();
    }

    function startSimulation() {
      if (intervalRef.current) return;
      intervalRef.current = setInterval(() => {
        updateSignals({
          session_id: sessionId!,
          attention: 0.6 + Math.random() * 0.4,
          frustration: Math.random() * 0.3,
          fatigue: Math.random() * 0.2,
          boredom: Math.random() * 0.2,
          engagement: 0.5 + Math.random() * 0.5,
          cognitive_load: 0.2 + Math.random() * 0.4,
          emotion: 'neutral',
          face_detected: true,
          timestamp: Date.now(),
        });
      }, 250);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [sessionId, updateSignals]);

  return { signals, history };
}
