import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Users, TrendingUp, Clock, AlertCircle } from 'lucide-react';
import { MomentBadge } from '../shared/MomentBadge';

const DEMO_STUDENTS = [
  { id: 's1', name: 'Alice Chen', mastery: 82, sessionsCount: 12, avgEngagement: 0.87, recentMoments: ['M08', 'M12'] },
  { id: 's2', name: 'Bob Kumar', mastery: 65, sessionsCount: 8, avgEngagement: 0.72, recentMoments: ['M01', 'M07'] },
  { id: 's3', name: 'Carol Zhang', mastery: 91, sessionsCount: 15, avgEngagement: 0.93, recentMoments: ['M12', 'M13'] },
  { id: 's4', name: 'David Patel', mastery: 45, sessionsCount: 5, avgEngagement: 0.58, recentMoments: ['M02', 'M04', 'M07'] },
];

const MASTERY_DATA = [
  { concept: 'Photosynthesis', mastery: 85 },
  { concept: 'Respiration', mastery: 72 },
  { concept: 'ATP Cycle', mastery: 55 },
  { concept: 'Chloroplast', mastery: 90 },
  { concept: 'Mitochondria', mastery: 63 },
];

function getMasteryColor(value: number): string {
  if (value >= 80) return '#22c55e';
  if (value >= 60) return '#f59e0b';
  return '#ef4444';
}

export const StudentAnalytics: React.FC = () => {
  return (
    <div>
      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="card">
          <div className="flex items-center gap-3">
            <Users className="w-8 h-8 text-neurosync-400" />
            <div>
              <p className="text-2xl font-bold">{DEMO_STUDENTS.length}</p>
              <p className="text-sm text-gray-400">Active Students</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-green-400" />
            <div>
              <p className="text-2xl font-bold">73%</p>
              <p className="text-sm text-gray-400">Avg Mastery</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <Clock className="w-8 h-8 text-blue-400" />
            <div>
              <p className="text-2xl font-bold">2.4h</p>
              <p className="text-sm text-gray-400">Avg Study Time</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-8 h-8 text-yellow-400" />
            <div>
              <p className="text-2xl font-bold">47</p>
              <p className="text-sm text-gray-400">Interventions Today</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Mastery chart */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Concept Mastery</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MASTERY_DATA} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" domain={[0, 100]} stroke="#6b7280" />
                <YAxis type="category" dataKey="concept" stroke="#6b7280" width={100} tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1a1b2e',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
                <Bar dataKey="mastery" radius={[0, 4, 4, 0]}>
                  {MASTERY_DATA.map((entry, index) => (
                    <Cell key={index} fill={getMasteryColor(entry.mastery)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Student list */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Student Overview</h3>
          <div className="space-y-3">
            {DEMO_STUDENTS.map((student) => (
              <div
                key={student.id}
                className="flex items-center justify-between p-3 rounded-lg bg-surface-dark hover:bg-surface-hover transition-colors"
              >
                <div>
                  <p className="font-medium">{student.name}</p>
                  <p className="text-xs text-gray-400">
                    {student.sessionsCount} sessions · {Math.round(student.avgEngagement * 100)}% engagement
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    {student.recentMoments.map((m) => (
                      <MomentBadge key={m} momentId={m} showLabel={false} size="sm" />
                    ))}
                  </div>
                  <span
                    className={`text-sm font-bold ${
                      student.mastery >= 80
                        ? 'text-green-400'
                        : student.mastery >= 60
                        ? 'text-yellow-400'
                        : 'text-red-400'
                    }`}
                  >
                    {student.mastery}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
