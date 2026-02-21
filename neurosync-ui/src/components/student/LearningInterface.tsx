import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { VideoPlayer } from './VideoPlayer';
import { InterventionOverlay } from './InterventionOverlay';
import { SignalIndicators } from './SignalIndicators';
import { useFusionLoop } from '../../hooks/useFusionLoop';
import { useInterventions } from '../../hooks/useInterventions';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { KeyboardShortcutsHelp } from '../shared/KeyboardShortcutsHelp';
import { useSessionStore } from '../../stores/sessionStore';
import type { Intervention, LearningEvent } from '../../types/electron';

interface LearningInterfaceProps {
  studentId: string;
  lessonId: string;
  videoUrl: string;
}

export const LearningInterface: React.FC<LearningInterfaceProps> = ({
  studentId,
  lessonId,
  videoUrl,
}) => {
  const [showDebugPanel, setShowDebugPanel] = useState(false);
  const [useMockData, setUseMockData] = useState(false);
  const { sessionId, startSession, endSession, isActive } = useSessionStore();
  const { signals } = useFusionLoop(sessionId);
  const { activeIntervention, acknowledgeIntervention } = useInterventions(sessionId);

  // Start session on mount
  useEffect(() => {
    startSession({
      session_id: `session-${Date.now()}`,
      student_id: studentId,
      lesson_id: lessonId,
      webcam_enabled: true,
    });

    return () => {
      if (sessionId) endSession(sessionId);
    };
  }, [studentId, lessonId]);

  // Keyboard shortcuts
  const shortcuts = useMemo(() => [
    {
      key: 'd',
      description: 'Toggle debug panel',
      action: () => setShowDebugPanel(prev => !prev),
    },
    {
      key: 'm',
      description: 'Toggle mock signals',
      action: () => setUseMockData(prev => !prev),
    },
    {
      key: '?',
      description: 'Show keyboard shortcuts',
      action: () => { /* Handled by KeyboardShortcutsHelp */ },
    },
    {
      key: 'Escape',
      description: 'Close overlays',
      action: () => {
        setShowDebugPanel(false);
      },
    },
  ], []);

  useKeyboardShortcuts(shortcuts);

  const handleVideoEvent = useCallback(
    (event: Omit<LearningEvent, 'session_id'>) => {
      if (!sessionId) return;
      window.electronAPI?.sendEvent({
        ...event,
        session_id: sessionId,
      } as LearningEvent);
    },
    [sessionId],
  );

  const handleAcknowledge = useCallback(() => {
    if (activeIntervention) {
      acknowledgeIntervention(activeIntervention.id || activeIntervention.intervention_id);
    }
  }, [activeIntervention, acknowledgeIntervention]);

  return (
    <div className="learning-interface h-[calc(100vh-4rem)] bg-surface-dark text-white relative">
      {/* Main video area */}
      <div className="relative h-full">
        <VideoPlayer
          url={videoUrl}
          sessionId={sessionId || ''}
          onEvent={handleVideoEvent}
        />

        {/* Intervention overlay (M01-M22) */}
        {activeIntervention && (
          <InterventionOverlay
            intervention={activeIntervention}
            onAcknowledge={handleAcknowledge}
          />
        )}

        {/* Debug panel */}
        {showDebugPanel && (
          <div className="absolute top-4 right-4 w-80 bg-black/85 backdrop-blur-sm p-4 rounded-xl border border-neurosync-800/50 z-40">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-neurosync-400">Signal Debug</h4>
              <div className="flex items-center gap-2">
                {useMockData && (
                  <span className="text-xs text-yellow-400 bg-yellow-900/30 px-2 py-0.5 rounded">MOCK</span>
                )}
                <span className="text-xs text-gray-500">250ms</span>
              </div>
            </div>
            <SignalIndicators signals={signals} />
          </div>
        )}

        {/* Session info bar */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 flex justify-between items-end z-30">
          <div className="text-xs text-gray-400">
            Session: {sessionId || 'Starting...'} · Student: {studentId}
          </div>
          <div className="text-xs text-gray-500">
            Press <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-300">D</kbd> for debug ·{' '}
            <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-300">M</kbd> for mock ·{' '}
            <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-300">?</kbd> for help
          </div>
        </div>
      </div>

      {/* Keyboard shortcuts help */}
      <KeyboardShortcutsHelp shortcuts={shortcuts} />
    </div>
  );
};
