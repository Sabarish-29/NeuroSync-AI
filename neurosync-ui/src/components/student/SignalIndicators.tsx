import React from 'react';
import type { SignalSnapshot } from '../../types/electron';

interface SignalIndicatorsProps {
  signals: SignalSnapshot;
}

interface SignalConfig {
  key: keyof SignalSnapshot;
  label: string;
  invert?: boolean; // High = bad (frustration, fatigue, boredom)
}

const SIGNAL_CONFIGS: SignalConfig[] = [
  { key: 'attention', label: 'Attention' },
  { key: 'engagement', label: 'Engagement' },
  { key: 'frustration', label: 'Frustration', invert: true },
  { key: 'fatigue', label: 'Fatigue', invert: true },
  { key: 'boredom', label: 'Boredom', invert: true },
  { key: 'cognitive_load', label: 'Cognitive Load', invert: true },
];

function getSignalColor(value: number, invert?: boolean): string {
  const v = invert ? 1 - value : value;
  if (v >= 0.7) return 'bg-green-500';
  if (v >= 0.4) return 'bg-yellow-500';
  return 'bg-red-500';
}

function getTextColor(value: number, invert?: boolean): string {
  const v = invert ? 1 - value : value;
  if (v >= 0.7) return 'text-green-400';
  if (v >= 0.4) return 'text-yellow-400';
  return 'text-red-400';
}

export const SignalIndicators: React.FC<SignalIndicatorsProps> = ({ signals }) => {
  return (
    <div className="space-y-2.5" data-testid="signal-indicators">
      {SIGNAL_CONFIGS.map(({ key, label, invert }) => {
        const value = typeof signals[key] === 'number' ? (signals[key] as number) : 0;
        return (
          <div key={key} className="flex items-center gap-3">
            <span className="text-xs text-gray-400 w-24 truncate">{label}</span>
            <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${getSignalColor(value, invert)}`}
                style={{ width: `${Math.round(value * 100)}%` }}
              />
            </div>
            <span className={`text-xs font-mono w-10 text-right ${getTextColor(value, invert)}`}>
              {Math.round(value * 100)}%
            </span>
          </div>
        );
      })}

      {/* Face detection indicator */}
      <div className="flex items-center gap-2 pt-1">
        <div
          className={`w-2 h-2 rounded-full ${signals.face_detected ? 'bg-green-500' : 'bg-red-500'}`}
        />
        <span className="text-xs text-gray-500">
          {signals.face_detected ? 'Face detected' : 'No face detected'}
        </span>
      </div>

      {/* Emotion */}
      {signals.emotion && (
        <div className="text-xs text-gray-500 pt-1">
          Emotion: <span className="text-gray-300 capitalize">{signals.emotion}</span>
        </div>
      )}
    </div>
  );
};
