/**
 * useEEGStatus - Monitor EEG hardware status
 *
 * Provides real-time EEG connection and signal quality updates.
 * Gracefully handles absence of EEG hardware (disabled by default).
 */

import { useState, useEffect } from 'react';

export interface EEGStatus {
  enabled: boolean;
  connected: boolean;
  quality: number; // 0.0-1.0
  lastUpdate: number; // timestamp
  usingSignals: boolean;
}

const EEG_QUALITY_THRESHOLD = 0.6;
const POLL_INTERVAL_MS = 2000;

export function useEEGStatus(): EEGStatus {
  const [status, setStatus] = useState<EEGStatus>({
    enabled: false,
    connected: false,
    quality: 0,
    lastUpdate: 0,
    usingSignals: false,
  });

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch('/api/eeg/status');
        if (!response.ok) throw new Error('EEG endpoint unavailable');

        const data = await response.json();
        setStatus({
          enabled: data.enabled ?? false,
          connected: data.connected ?? false,
          quality: data.quality ?? 0,
          lastUpdate: Date.now(),
          usingSignals: (data.quality ?? 0) > EEG_QUALITY_THRESHOLD,
        });
      } catch {
        // EEG not available — this is normal and expected
        setStatus((prev) => ({
          ...prev,
          enabled: false,
          connected: false,
          quality: 0,
          lastUpdate: Date.now(),
          usingSignals: false,
        }));
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  return status;
}

export default useEEGStatus;
