import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { SignalSnapshot } from '../../types/electron';

interface SignalChartProps {
  history: SignalSnapshot[];
  visibleSignals?: string[];
}

const SIGNAL_COLORS: Record<string, string> = {
  attention: '#22c55e',
  frustration: '#ef4444',
  fatigue: '#f59e0b',
  boredom: '#a855f7',
  engagement: '#3b82f6',
  cognitive_load: '#ec4899',
};

export const SignalChart: React.FC<SignalChartProps> = ({
  history,
  visibleSignals = ['attention', 'frustration', 'fatigue', 'engagement'],
}) => {
  const data = history.map((snapshot, i) => ({
    time: i,
    ...snapshot,
  }));

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="time"
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
            label={{ value: 'Time', position: 'insideBottom', offset: -5, fill: '#9ca3af' }}
          />
          <YAxis
            domain={[0, 1]}
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
            ticks={[0, 0.25, 0.5, 0.75, 1.0]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1b2e',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#fff',
            }}
          />
          <Legend />
          {visibleSignals.map((signal) => (
            <Line
              key={signal}
              type="monotone"
              dataKey={signal}
              stroke={SIGNAL_COLORS[signal] || '#6366f1'}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
