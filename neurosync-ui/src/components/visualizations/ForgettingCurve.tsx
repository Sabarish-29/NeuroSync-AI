import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface ForgettingCurveProps {
  conceptId: string;
  conceptLabel: string;
  dataPoints?: { day: number; retention: number }[];
  reviewDays?: number[];
}

/**
 * Exponential forgetting curve: R = R0 * e^(-t/τ)
 * Default: R0 = 1.0, τ = 3 days
 */
function generateForgettingCurve(
  tauDays: number = 3,
  maxDays: number = 30,
  reviews: number[] = []
): { day: number; retention: number; reviewed: boolean }[] {
  const points: { day: number; retention: number; reviewed: boolean }[] = [];
  let r0 = 1.0;
  let lastReviewDay = 0;

  for (let day = 0; day <= maxDays; day++) {
    const isReview = reviews.includes(day);
    const elapsed = day - lastReviewDay;
    const retention = r0 * Math.exp(-elapsed / tauDays);

    points.push({
      day,
      retention: Math.max(0, Math.min(1, retention)),
      reviewed: isReview,
    });

    if (isReview) {
      r0 = Math.min(1.0, retention + 0.3);
      lastReviewDay = day;
    }
  }

  return points;
}

export const ForgettingCurve: React.FC<ForgettingCurveProps> = ({
  conceptId,
  conceptLabel,
  dataPoints,
  reviewDays = [3, 7, 14],
}) => {
  const data = dataPoints
    ? dataPoints.map((p) => ({ ...p, reviewed: reviewDays.includes(p.day) }))
    : generateForgettingCurve(3, 30, reviewDays);

  return (
    <div className="w-full">
      <h4 className="text-sm font-medium text-gray-400 mb-2">
        Retention Curve — {conceptLabel}
      </h4>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id={`gradient-${conceptId}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="day"
              stroke="#6b7280"
              tick={{ fontSize: 11 }}
              label={{ value: 'Days', position: 'insideBottom', offset: -5, fill: '#9ca3af' }}
            />
            <YAxis
              domain={[0, 1]}
              stroke="#6b7280"
              tick={{ fontSize: 11 }}
              tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1b2e',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#fff',
              }}
              formatter={(value: number) => [`${Math.round(value * 100)}%`, 'Retention']}
            />
            {/* Threshold line at 80% */}
            <ReferenceLine y={0.8} stroke="#22c55e" strokeDasharray="4 4" label="" />
            {/* Review day markers */}
            {reviewDays.map((day) => (
              <ReferenceLine
                key={day}
                x={day}
                stroke="#f59e0b"
                strokeDasharray="2 2"
              />
            ))}
            <Area
              type="monotone"
              dataKey="retention"
              stroke="#6366f1"
              strokeWidth={2}
              fill={`url(#gradient-${conceptId})`}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
