import React from 'react';
import { BookOpen, FileText, HelpCircle, Video, Trash2 } from 'lucide-react';

interface ContentItem {
  id: string;
  title: string;
  createdAt: string;
  conceptCount: number;
  formats: string[];
}

const DEMO_CONTENT: ContentItem[] = [
  {
    id: '1',
    title: 'Chapter 5 — Photosynthesis',
    createdAt: '2026-02-18',
    conceptCount: 12,
    formats: ['slides', 'notes', 'story', 'quiz'],
  },
  {
    id: '2',
    title: 'Chapter 6 — Cellular Respiration',
    createdAt: '2026-02-17',
    conceptCount: 9,
    formats: ['slides', 'notes', 'quiz'],
  },
  {
    id: '3',
    title: 'Chapter 7 — DNA Replication',
    createdAt: '2026-02-15',
    conceptCount: 15,
    formats: ['slides', 'notes', 'story', 'quiz'],
  },
];

const FORMAT_ICONS: Record<string, React.ElementType> = {
  slides: FileText,
  notes: BookOpen,
  quiz: HelpCircle,
  video: Video,
  story: BookOpen,
};

export const ContentLibrary: React.FC = () => {
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Content Library</h2>
        <span className="text-sm text-gray-400">
          {DEMO_CONTENT.length} courses generated
        </span>
      </div>

      <div className="space-y-4">
        {DEMO_CONTENT.map((item) => (
          <div key={item.id} className="card-hover flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-neurosync-900/50 flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-neurosync-400" />
              </div>
              <div>
                <h3 className="font-semibold">{item.title}</h3>
                <p className="text-sm text-gray-400">
                  {item.conceptCount} concepts · Created {item.createdAt}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Format badges */}
              <div className="flex gap-1.5">
                {item.formats.map((format) => {
                  const Icon = FORMAT_ICONS[format] || FileText;
                  return (
                    <span
                      key={format}
                      className="px-2 py-1 rounded text-xs bg-surface-hover text-gray-300 flex items-center gap-1"
                      title={format}
                    >
                      <Icon className="w-3 h-3" />
                      {format}
                    </span>
                  );
                })}
              </div>
              <button className="p-2 rounded-lg hover:bg-red-900/30 text-gray-500 hover:text-red-400 transition-colors">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {DEMO_CONTENT.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <BookOpen className="w-16 h-16 mx-auto mb-4 opacity-30" />
          <p>No content generated yet. Upload a PDF to get started.</p>
        </div>
      )}
    </div>
  );
};
