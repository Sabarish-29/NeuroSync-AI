import React, { useState, useEffect } from 'react';
import { Activity, Wifi, WifiOff } from 'lucide-react';
import { SignalChart } from '../visualizations/SignalChart';
import type { SignalSnapshot } from '../../types/electron';

/**
 * Live progress monitor — shows real-time signals for active sessions.
 */
export const ProgressMonitor: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [signalHistory, setSignalHistory] = useState<SignalSnapshot[]>([]);

  useEffect(() => {
    // Simulate real-time signal updates for demo
    setConnected(true);
    const interval = setInterval(() => {
      setSignalHistory((prev) => {
        const newSignal: SignalSnapshot = {
          session_id: 'demo',
          attention: 0.6 + Math.random() * 0.4,
          frustration: Math.random() * 0.4,
          fatigue: Math.min(0.8, (prev.length * 0.005) + Math.random() * 0.1),
          boredom: Math.random() * 0.3,
          engagement: 0.5 + Math.random() * 0.5,
          cognitive_load: 0.2 + Math.random() * 0.5,
          emotion: 'neutral',
          face_detected: true,
          timestamp: Date.now(),
        };
        return [...prev.slice(-60), newSignal];
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-3">
          <Activity className="w-6 h-6 text-neurosync-400" />
          Live Session Monitor
        </h2>
        <div className="flex items-center gap-2">
          {connected ? (
            <span className="flex items-center gap-2 text-green-400 text-sm">
              <Wifi className="w-4 h-4" />
              Connected
            </span>
          ) : (
            <span className="flex items-center gap-2 text-red-400 text-sm">
              <WifiOff className="w-4 h-4" />
              Disconnected
            </span>
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Signal Timeline</h3>
        <SignalChart
          history={signalHistory}
          visibleSignals={['attention', 'frustration', 'fatigue', 'engagement']}
        />
      </div>

      {/* Current signal values */}
      {signalHistory.length > 0 && (
        <div className="grid grid-cols-6 gap-3 mt-4">
          {Object.entries(signalHistory[signalHistory.length - 1])
            .filter(([key]) => ['attention', 'frustration', 'fatigue', 'boredom', 'engagement', 'cognitive_load'].includes(key))
            .map(([key, value]) => (
              <div key={key} className="card text-center">
                <p className="text-xs text-gray-400 capitalize">{key.replace('_', ' ')}</p>
                <p className="text-xl font-bold mt-1">
                  {typeof value === 'number' ? `${Math.round(value * 100)}%` : String(value)}
                </p>
              </div>
            ))}
        </div>
      )}
    </div>
  );
};
