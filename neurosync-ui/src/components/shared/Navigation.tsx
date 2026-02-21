import React from 'react';
import { Brain, BookOpen, GraduationCap, BarChart3, RefreshCw, Network } from 'lucide-react';
import type { AppView } from '../../App';

interface NavigationProps {
  currentView: AppView;
  onNavigate: (view: AppView) => void;
}

const NAV_ITEMS: { view: AppView; label: string; icon: React.ElementType }[] = [
  { view: 'teacher', label: 'Teacher Dashboard', icon: BarChart3 },
  { view: 'student', label: 'Learn', icon: BookOpen },
  { view: 'readiness', label: 'Readiness Check', icon: GraduationCap },
  { view: 'review', label: 'Spaced Review', icon: RefreshCw },
  { view: 'knowledge', label: 'Knowledge Map', icon: Network },
];

export const Navigation: React.FC<NavigationProps> = ({ currentView, onNavigate }) => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-surface-card/95 backdrop-blur-sm border-b border-neurosync-900/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <Brain className="w-8 h-8 text-neurosync-500" />
            <span className="text-xl font-bold bg-gradient-to-r from-neurosync-400 to-purple-400 bg-clip-text text-transparent">
              NeuroSync AI
            </span>
          </div>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            {NAV_ITEMS.map(({ view, label, icon: Icon }) => (
              <button
                key={view}
                onClick={() => onNavigate(view)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  currentView === view
                    ? 'bg-neurosync-600 text-white shadow-lg shadow-neurosync-600/25'
                    : 'text-gray-400 hover:text-white hover:bg-surface-hover'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden md:inline">{label}</span>
              </button>
            ))}
          </div>

          {/* Version badge */}
          <div className="text-xs text-gray-500 font-mono">v5.1.0</div>
        </div>
      </div>
    </nav>
  );
};
