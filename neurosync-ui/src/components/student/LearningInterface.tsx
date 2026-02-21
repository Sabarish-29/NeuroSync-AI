import React, { useState, useEffect, useCallback } from 'react';
import { VideoPlayer } from './VideoPlayer';
import { InterventionOverlay } from './InterventionOverlay';
import { SignalIndicators } from './SignalIndicators';
import { useFusionLoop } from '../../hooks/useFusionLoop';
import { useInterventions } from '../../hooks/useInterventions';
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

  // Keyboard shortcut: D => toggle debug panel
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'd' || e.key === 'D') {
        if (document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
          setShowDebugPanel((prev) => !prev);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleVideoEvent = useCallback(
    (event: Omit<LearningEvent, 'session_id'>) => {
      if (!sessionId) return;
      window.electronAPI?.sendEvent({
        session_id: sessionId,
        ...event,
      });
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

        {/* Intervention overlay (M01–M22) */}
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
              <span className="text-xs text-gray-500">250ms</span>
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
            Press <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-300">D</kbd> for debug panel
          </div>
        </div>
      </div>
    </div>
  );
};
