import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertCircle,
  Lightbulb,
  Coffee,
  BookOpen,
  Eye,
  Brain,
  Frown,
  Meh,
  Zap,
  HelpCircle,
} from 'lucide-react';
import type { Intervention } from '../../types/electron';

interface InterventionOverlayProps {
  intervention: Intervention;
  onAcknowledge: () => void;
}

const MOMENT_ICONS: Record<string, React.ElementType> = {
  M01: Eye,
  M02: Brain,
  M03: Meh,
  M04: HelpCircle,
  M07: Frown,
  M08: Lightbulb,
  M09: Coffee,
  M10: BookOpen,
  M20: Zap,
};

const MOMENT_TITLES: Record<string, string> = {
  M01: 'Attention Check',
  M02: 'Let\'s Simplify',
  M03: 'Engagement Boost',
  M04: 'Clarification',
  M07: 'Take a Moment',
  M08: 'Great Insight!',
  M09: 'Rest Your Eyes',
  M10: 'Quick Review',
  M20: 'Plateau Breaker',
};

export const InterventionOverlay: React.FC<InterventionOverlayProps> = ({
  intervention,
  onAcknowledge,
}) => {
  const Icon = MOMENT_ICONS[intervention.moment_id] || AlertCircle;
  const title = MOMENT_TITLES[intervention.moment_id] || intervention.moment_id;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 flex items-center justify-center bg-black/60 z-50"
        data-testid="intervention-overlay"
      >
        <motion.div
          className="bg-gradient-to-br from-neurosync-900 to-purple-900 p-8 rounded-2xl max-w-2xl shadow-2xl border border-neurosync-700/30"
          initial={{ scale: 0.8, y: 50 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.8, y: -50 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        >
          <div className="flex items-start gap-5">
            <div className="p-3 rounded-xl bg-neurosync-800/50">
              <Icon className="w-10 h-10 text-yellow-400" />
            </div>

            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-neurosync-400 bg-neurosync-900/50 px-2 py-0.5 rounded">
                  {intervention.moment_id}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  intervention.urgency === 'immediate'
                    ? 'bg-red-900/50 text-red-400'
                    : intervention.urgency === 'next_pause'
                    ? 'bg-yellow-900/50 text-yellow-400'
                    : 'bg-gray-900/50 text-gray-400'
                }`}>
                  {intervention.urgency}
                </span>
              </div>

              <h3 className="text-2xl font-bold mb-3">{title}</h3>

              <div className="text-base mb-6 leading-relaxed text-gray-200">
                {intervention.content || 'The system has detected a learning signal and is adapting your experience.'}
              </div>

              <button
                onClick={onAcknowledge}
                className="btn-success flex items-center gap-2"
                data-testid="acknowledge-btn"
              >
                Continue Learning
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
