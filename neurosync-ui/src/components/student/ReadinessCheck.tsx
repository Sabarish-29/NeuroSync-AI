import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, Wind, CheckCircle, AlertTriangle, Smile } from 'lucide-react';
import { ProgressBar } from '../shared/ProgressBar';

interface ReadinessCheckProps {
  studentId: string;
  lessonTopic: string;
  onComplete: () => void;
}

type CheckPhase = 'intro' | 'self_report' | 'breathing' | 'result';

const SELF_REPORT_QUESTIONS = [
  { id: 'energy', label: 'How is your energy level right now?', emoji: '⚡' },
  { id: 'stress', label: 'How stressed do you feel?', emoji: '😰' },
  { id: 'focus', label: 'How focused do you feel?', emoji: '🎯' },
  { id: 'sleep', label: 'How well did you sleep last night?', emoji: '😴' },
];

export const ReadinessCheck: React.FC<ReadinessCheckProps> = ({
  studentId,
  lessonTopic,
  onComplete,
}) => {
  const [phase, setPhase] = useState<CheckPhase>('intro');
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [breathingStep, setBreathingStep] = useState(0);
  const [readinessScore, setReadinessScore] = useState(0);
  const [needsBreathing, setNeedsBreathing] = useState(false);

  const handleSelfReportAnswer = (questionId: string, value: number) => {
    setResponses((prev) => ({ ...prev, [questionId]: value }));
  };

  const submitSelfReport = async () => {
    // Calculate readiness from responses
    const avgScore = Object.values(responses).reduce((a, b) => a + b, 0) / Object.values(responses).length;
    const score = avgScore / 5; // Normalize to 0-1
    setReadinessScore(score);

    if (score < 0.5) {
      setNeedsBreathing(true);
      setPhase('breathing');
    } else {
      setPhase('result');
    }
  };

  const runBreathingExercise = async () => {
    for (let i = 0; i < 4; i++) {
      setBreathingStep(i + 1);
      await new Promise((r) => setTimeout(r, 4000));
    }
    setReadinessScore(Math.min(1, readinessScore + 0.25));
    setPhase('result');
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-8">
      <AnimatePresence mode="wait">
        {/* Intro phase */}
        {phase === 'intro' && (
          <motion.div
            key="intro"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="card max-w-lg text-center"
          >
            <Smile className="w-16 h-16 mx-auto mb-4 text-neurosync-400" />
            <h2 className="text-2xl font-bold mb-2">Pre-Lesson Readiness Check</h2>
            <p className="text-gray-400 mb-2">Topic: <span className="text-white font-medium">{lessonTopic}</span></p>
            <p className="text-gray-400 mb-6">
              Let&apos;s make sure you&apos;re in the best state to learn. This takes about 30 seconds.
            </p>
            <button onClick={() => setPhase('self_report')} className="btn-primary">
              Let&apos;s Go
            </button>
          </motion.div>
        )}

        {/* Self-report phase */}
        {phase === 'self_report' && (
          <motion.div
            key="self_report"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="card max-w-lg"
          >
            <h3 className="text-xl font-bold mb-6">Quick Check-in</h3>
            <div className="space-y-6">
              {SELF_REPORT_QUESTIONS.map((q) => (
                <div key={q.id}>
                  <p className="text-sm mb-2">
                    <span className="mr-2">{q.emoji}</span>
                    {q.label}
                  </p>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((value) => (
                      <button
                        key={value}
                        onClick={() => handleSelfReportAnswer(q.id, value)}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                          responses[q.id] === value
                            ? 'bg-neurosync-600 text-white'
                            : 'bg-surface-dark hover:bg-surface-hover text-gray-400'
                        }`}
                      >
                        {value}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={submitSelfReport}
              disabled={Object.keys(responses).length < SELF_REPORT_QUESTIONS.length}
              className="btn-primary w-full mt-6 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue
            </button>
          </motion.div>
        )}

        {/* Breathing exercise phase */}
        {phase === 'breathing' && (
          <motion.div
            key="breathing"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="card max-w-lg text-center"
          >
            <Wind className="w-16 h-16 mx-auto mb-4 text-blue-400" />
            <h3 className="text-xl font-bold mb-2">Breathing Exercise</h3>
            <p className="text-gray-400 mb-6">
              We detected elevated stress. Let&apos;s do a quick breathing exercise.
            </p>

            {breathingStep === 0 ? (
              <button onClick={runBreathingExercise} className="btn-primary">
                Start Breathing
              </button>
            ) : (
              <div>
                <motion.div
                  className="w-32 h-32 mx-auto rounded-full bg-blue-600/30 border-2 border-blue-400 flex items-center justify-center mb-4"
                  animate={{ scale: breathingStep % 2 === 1 ? 1.3 : 0.8 }}
                  transition={{ duration: 4, ease: 'easeInOut' }}
                >
                  <span className="text-lg font-medium">
                    {breathingStep % 2 === 1 ? 'Breathe in' : 'Breathe out'}
                  </span>
                </motion.div>
                <p className="text-sm text-gray-400">Step {breathingStep} of 4</p>
              </div>
            )}
          </motion.div>
        )}

        {/* Result phase */}
        {phase === 'result' && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="card max-w-lg text-center"
          >
            {readinessScore >= 0.5 ? (
              <>
                <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500" />
                <h3 className="text-2xl font-bold mb-2 text-green-400">You&apos;re Ready!</h3>
              </>
            ) : (
              <>
                <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-yellow-500" />
                <h3 className="text-2xl font-bold mb-2 text-yellow-400">Almost There</h3>
              </>
            )}
            <p className="text-gray-400 mb-4">
              Readiness Score: <span className="font-bold text-white">{Math.round(readinessScore * 100)}%</span>
            </p>
            <ProgressBar value={readinessScore * 100} color={readinessScore >= 0.5 ? 'green' : 'yellow'} />
            {needsBreathing && (
              <p className="text-sm text-blue-400 mt-3">
                <Heart className="w-4 h-4 inline mr-1" />
                Breathing exercise improved your readiness
              </p>
            )}
            <button onClick={onComplete} className="btn-primary mt-6">
              Start Lesson
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
