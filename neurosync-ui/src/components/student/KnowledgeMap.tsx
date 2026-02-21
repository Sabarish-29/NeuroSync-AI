import React, { useState, useEffect } from 'react';
import { Network } from 'lucide-react';
import { KnowledgeGraph } from '../visualizations/KnowledgeGraph';
import { ProgressBar } from '../shared/ProgressBar';
import type { KnowledgeNode, KnowledgeEdge, KnowledgeMapData } from '../../types/electron';

interface KnowledgeMapProps {
  studentId: string;
}

const DEMO_MAP: KnowledgeMapData = {
  student_id: 'student-001',
  nodes: [
    { id: 'c1', label: 'Photosynthesis', category: 'biology', mastery: 0.85, status: 'mastered' },
    { id: 'c2', label: 'Cellular Respiration', category: 'biology', mastery: 0.62, status: 'learning' },
    { id: 'c3', label: 'ATP Cycle', category: 'biology', mastery: 0.45, status: 'learning' },
    { id: 'c4', label: 'Chloroplast Structure', category: 'biology', mastery: 0.92, status: 'mastered' },
    { id: 'c5', label: 'Mitochondria', category: 'biology', mastery: 0.38, status: 'learning' },
    { id: 'c6', label: 'Light Reactions', category: 'biology', mastery: 0.78, status: 'learning' },
    { id: 'c7', label: 'Calvin Cycle', category: 'biology', mastery: 0.55, status: 'learning' },
    { id: 'c8', label: 'Electron Transport', category: 'biology', mastery: 0.30, status: 'not_started' },
  ],
  edges: [
    { source: 'c4', target: 'c1', relationship: 'part_of' },
    { source: 'c6', target: 'c1', relationship: 'part_of' },
    { source: 'c7', target: 'c1', relationship: 'part_of' },
    { source: 'c1', target: 'c2', relationship: 'prerequisite' },
    { source: 'c5', target: 'c2', relationship: 'part_of' },
    { source: 'c2', target: 'c3', relationship: 'prerequisite' },
    { source: 'c8', target: 'c2', relationship: 'part_of' },
  ],
};

export const KnowledgeMap: React.FC<KnowledgeMapProps> = ({ studentId }) => {
  const [mapData, setMapData] = useState<KnowledgeMapData>(DEMO_MAP);
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null);

  useEffect(() => {
    // In production, fetch from API
    const fetchMap = async () => {
      try {
        const data = await window.electronAPI?.getKnowledgeMap(studentId);
        if (data && data.nodes.length > 0) {
          setMapData(data);
        }
      } catch {
        // Use demo data as fallback
      }
    };
    fetchMap();
  }, [studentId]);

  const overallMastery =
    mapData.nodes.length > 0
      ? mapData.nodes.reduce((sum, n) => sum + n.mastery, 0) / mapData.nodes.length
      : 0;

  const masteredCount = mapData.nodes.filter((n) => n.mastery >= 0.8).length;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Network className="w-6 h-6 text-neurosync-400" />
          Knowledge Map
        </h2>
        <div className="text-sm text-gray-400">
          {masteredCount} / {mapData.nodes.length} concepts mastered
        </div>
      </div>

      {/* Overall progress */}
      <div className="card mb-6">
        <ProgressBar
          value={overallMastery * 100}
          label="Overall Mastery"
          color={overallMastery >= 0.7 ? 'green' : overallMastery >= 0.4 ? 'yellow' : 'red'}
        />
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Graph visualization */}
        <div className="col-span-2 card">
          <KnowledgeGraph
            nodes={mapData.nodes}
            edges={mapData.edges}
            width={700}
            height={450}
            onNodeClick={(node) => setSelectedNode(node)}
          />
        </div>

        {/* Node detail panel */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">
            {selectedNode ? selectedNode.label : 'Select a Concept'}
          </h3>
          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <span className="text-sm text-gray-400">Category</span>
                <p className="capitalize">{selectedNode.category}</p>
              </div>
              <div>
                <span className="text-sm text-gray-400">Mastery</span>
                <ProgressBar
                  value={selectedNode.mastery * 100}
                  color={selectedNode.mastery >= 0.7 ? 'green' : selectedNode.mastery >= 0.4 ? 'yellow' : 'red'}
                />
              </div>
              <div>
                <span className="text-sm text-gray-400">Status</span>
                <p className={`capitalize ${
                  selectedNode.status === 'mastered'
                    ? 'text-green-400'
                    : selectedNode.status === 'learning'
                    ? 'text-yellow-400'
                    : 'text-gray-400'
                }`}>
                  {selectedNode.status.replace('_', ' ')}
                </p>
              </div>
              {/* Connected concepts */}
              <div>
                <span className="text-sm text-gray-400">Connected To</span>
                <div className="mt-2 space-y-1">
                  {mapData.edges
                    .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((e, i) => {
                      const otherId = e.source === selectedNode.id ? e.target : e.source;
                      const other = mapData.nodes.find((n) => n.id === otherId);
                      return (
                        <div key={i} className="text-sm flex items-center gap-2">
                          <span className="text-xs text-gray-500">{e.relationship}</span>
                          <span className="text-gray-300">{other?.label || otherId}</span>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">
              Click on a node in the graph to see details about that concept.
            </p>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mt-4 text-sm text-gray-400">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          Mastered (≥70%)
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          Learning (40-70%)
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          Needs Work (&lt;40%)
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gray-500" />
          Not Started
        </div>
      </div>
    </div>
  );
};
