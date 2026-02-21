import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle, XCircle, Clock } from 'lucide-react';
import { ProgressBar } from '../shared/ProgressBar';
import { ForgettingCurve } from '../visualizations/ForgettingCurve';
import type { DueReview } from '../../types/electron';

interface SpacedReviewProps {
  studentId: string;
}

interface ReviewItem extends DueReview {
  question: string;
  options: string[];
  correctIndex: number;
}

const DEMO_REVIEWS: ReviewItem[] = [
  {
    concept_id: 'c1',
    scheduled_at: Date.now() - 3600000,
    review_number: 2,
    predicted_retention: 0.72,
    quiz: {},
    question: 'What is the primary product of photosynthesis?',
    options: ['Carbon dioxide', 'Glucose', 'Water', 'Oxygen'],
    correctIndex: 1,
  },
  {
    concept_id: 'c2',
    scheduled_at: Date.now() - 7200000,
    review_number: 3,
    predicted_retention: 0.55,
    quiz: {},
    question: 'Where does the Calvin cycle occur?',
    options: ['Thylakoid membrane', 'Stroma', 'Cytoplasm', 'Nucleus'],
    correctIndex: 1,
  },
  {
    concept_id: 'c3',
    scheduled_at: Date.now(),
    review_number: 1,
    predicted_retention: 0.88,
    quiz: {},
    question: 'What molecule carries energy from light reactions to the Calvin cycle?',
    options: ['ADP', 'NADPH', 'FAD', 'CoA'],
    correctIndex: 1,
  },
];

export const SpacedReview: React.FC<SpacedReviewProps> = ({ studentId }) => {
  const [reviews] = useState<ReviewItem[]>(DEMO_REVIEWS);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [answered, setAnswered] = useState(false);
  const [results, setResults] = useState<boolean[]>([]);
  const [completed, setCompleted] = useState(false);

  const currentReview = reviews[currentIndex];

  const handleAnswer = (optionIndex: number) => {
    if (answered) return;
    setSelectedAnswer(optionIndex);
    setAnswered(true);

    const isCorrect = optionIndex === currentReview.correctIndex;
    setResults((prev) => [...prev, isCorrect]);
  };

  const nextQuestion = () => {
    if (currentIndex < reviews.length - 1) {
      setCurrentIndex((prev) => prev + 1);
      setSelectedAnswer(null);
      setAnswered(false);
    } else {
      setCompleted(true);
    }
  };

  if (completed) {
    const correctCount = results.filter(Boolean).length;
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="card text-center">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500" />
          <h2 className="text-2xl font-bold mb-2">Review Complete!</h2>
          <p className="text-gray-400 mb-4">
            You got <span className="text-white font-bold">{correctCount}</span> out of{' '}
            <span className="text-white font-bold">{reviews.length}</span> correct
          </p>
          <ProgressBar
            value={(correctCount / reviews.length) * 100}
            color={correctCount === reviews.length ? 'green' : 'yellow'}
          />
          <div className="mt-6">
            <ForgettingCurve
              conceptId="review-session"
              conceptLabel="Session Average"
              reviewDays={[1, 3, 7, 14]}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <RefreshCw className="w-6 h-6 text-neurosync-400" />
          Spaced Review
        </h2>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Clock className="w-4 h-4" />
          {currentIndex + 1} / {reviews.length}
        </div>
      </div>

      {/* Retention indicator */}
      <div className="card mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">Predicted Retention</span>
          <span className="text-sm font-medium">
            {Math.round(currentReview.predicted_retention * 100)}%
          </span>
        </div>
        <ProgressBar
          value={currentReview.predicted_retention * 100}
          color={currentReview.predicted_retention >= 0.7 ? 'green' : 'yellow'}
          showPercentage={false}
        />
      </div>

      {/* Question */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-6">{currentReview.question}</h3>

        <div className="space-y-3">
          {currentReview.options.map((option, index) => {
            let className = 'w-full text-left p-4 rounded-lg transition-all border ';
            if (!answered) {
              className += selectedAnswer === index
                ? 'bg-neurosync-900 border-neurosync-500'
                : 'bg-surface-dark border-gray-800 hover:border-gray-700 hover:bg-surface-hover';
            } else if (index === currentReview.correctIndex) {
              className += 'bg-green-900/30 border-green-600 text-green-300';
            } else if (index === selectedAnswer) {
              className += 'bg-red-900/30 border-red-600 text-red-300';
            } else {
              className += 'bg-surface-dark border-gray-800 opacity-50';
            }

            return (
              <button key={index} onClick={() => handleAnswer(index)} className={className} disabled={answered}>
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-full bg-surface-card flex items-center justify-center text-sm font-medium">
                    {String.fromCharCode(65 + index)}
                  </span>
                  <span>{option}</span>
                  {answered && index === currentReview.correctIndex && (
                    <CheckCircle className="w-5 h-5 text-green-500 ml-auto" />
                  )}
                  {answered && index === selectedAnswer && index !== currentReview.correctIndex && (
                    <XCircle className="w-5 h-5 text-red-500 ml-auto" />
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {answered && (
          <button onClick={nextQuestion} className="btn-primary w-full mt-6">
            {currentIndex < reviews.length - 1 ? 'Next Question' : 'See Results'}
          </button>
        )}
      </div>
    </div>
  );
};
