import React, { useState } from 'react';
import { UploadPDF } from './UploadPDF';
import { ContentLibrary } from './ContentLibrary';
import { StudentAnalytics } from './StudentAnalytics';
import { ProgressMonitor } from './ProgressMonitor';
import { BookOpen, Upload, BarChart3, Activity } from 'lucide-react';

type TabId = 'upload' | 'library' | 'analytics' | 'monitor';

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: 'upload', label: 'Upload Content', icon: Upload },
  { id: 'library', label: 'Content Library', icon: BookOpen },
  { id: 'analytics', label: 'Student Analytics', icon: BarChart3 },
  { id: 'monitor', label: 'Live Monitor', icon: Activity },
];

export const TeacherDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('upload');

  const renderTab = () => {
    switch (activeTab) {
      case 'upload':
        return <UploadPDF />;
      case 'library':
        return <ContentLibrary />;
      case 'analytics':
        return <StudentAnalytics />;
      case 'monitor':
        return <ProgressMonitor />;
      default:
        return <UploadPDF />;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-neurosync-400 to-purple-400 bg-clip-text text-transparent">
          Teacher Dashboard
        </h1>
        <p className="text-gray-400 mt-2">
          Upload content, monitor students, and manage your adaptive courses.
        </p>
      </div>

      {/* Tab navigation */}
      <div className="flex gap-2 mb-8 border-b border-gray-800 pb-4">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === id
                ? 'bg-neurosync-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-white hover:bg-surface-hover'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="animate-fade-in">{renderTab()}</div>
    </div>
  );
};
