import React, { useState, useCallback, useEffect } from 'react';
import { Upload, CheckCircle, Loader, FileText, AlertTriangle, Circle } from 'lucide-react';
import { ProgressBar } from '../shared/ProgressBar';
import { ErrorAlert } from '../shared/ErrorAlert';

interface GenerationResult {
  task_id: string;
  title: string;
  concept_count: number;
  slide_count: number;
  question_count: number;
  video_duration: string;
  formats_generated: string[];
}

const GENERATION_STEPS = [
  { id: 1, label: "Parsing PDF", progress: 8 },
  { id: 2, label: "Cleaning text", progress: 15 },
  { id: 3, label: "Analyzing structure", progress: 22 },
  { id: 4, label: "Extracting concepts (AI)", progress: 35 },
  { id: 5, label: "Generating slide outlines", progress: 45 },
  { id: 6, label: "Creating narration scripts (AI)", progress: 58 },
  { id: 7, label: "Generating audio (TTS)", progress: 70 },
  { id: 8, label: "Rendering slides to images", progress: 80 },
  { id: 9, label: "Assembling video", progress: 90 },
  { id: 10, label: "Creating quiz (AI)", progress: 95 },
  { id: 11, label: "Finalizing outputs", progress: 100 },
];

export const UploadPDF: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true);
    setProgress(0);
    setError(null);
    setResult(null);

    // Subscribe to progress updates if in Electron
    const unsubscribe = window.electronAPI?.onGenerationProgress((data: { progress: number; stage?: string; message?: string }) => {
      setProgress(data.progress);
      setStage(data.stage || data.message || '');
    });

    try {
      // Simulate progress for demo (in production, use actual API)
      for (let i = 0; i < GENERATION_STEPS.length; i++) {
        setStage(GENERATION_STEPS[i].label);
        setProgress(GENERATION_STEPS[i].progress);
        await new Promise((r) => setTimeout(r, 600));
      }

      setResult({
        task_id: `task-${Date.now()}`,
        title: file.name.replace('.pdf', ''),
        concept_count: 12,
        slide_count: 24,
        question_count: 36,
        video_duration: '18:42',
        formats_generated: ['slides', 'notes', 'story', 'quiz'],
      });
    } catch (err) {
      let errorMessage = 'Upload failed. Please try again.';

      if (err instanceof Error) {
        if (err.message?.includes('GROQ_API_KEY')) {
          errorMessage = 'Groq API key not configured. Please add GROQ_API_KEY to your .env file.';
        } else if (err.message?.includes('rate limit')) {
          errorMessage = 'API rate limit reached. Please wait a moment and try again.';
        } else if (err.message?.includes('ECONNREFUSED')) {
          errorMessage = 'Cannot connect to backend. Please ensure the server is running.';
        } else {
          errorMessage = err.message;
        }
      }

      setError(errorMessage);
    } finally {
      setUploading(false);
      if (unsubscribe) unsubscribe();
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      handleUpload(file);
    }
  };

  const handleCancelUpload = () => {
    setUploading(false);
    setProgress(0);
    setStage('');
  };

  const reset = () => {
    setResult(null);
    setProgress(0);
    setStage('');
    setError(null);
  };

  // Trigger confetti on success
  useEffect(() => {
    if (result && result.task_id) {
      try {
        import('canvas-confetti').then((confetti) => {
          confetti.default({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#00bfff', '#00ff88', '#ff8c00'],
          });
        });
      } catch {
        // confetti not installed, skip
      }
    }
  }, [result]);

  return (
    <div className="card max-w-2xl mx-auto">
      {/* Error alert overlay */}
      <ErrorAlert
        error={error}
        onDismiss={() => setError(null)}
        onRetry={reset}
      />

      {/* Idle state -- file picker */}
      {!uploading && !result && !error && (
        <div
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
            dragOver
              ? 'border-neurosync-500 bg-neurosync-900/20'
              : 'border-gray-700 hover:border-gray-600'
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <Upload className="w-16 h-16 mx-auto mb-4 text-gray-500" />
          <h3 className="text-xl font-semibold mb-2">Upload PDF Textbook Chapter</h3>
          <p className="text-gray-400 mb-6 leading-relaxed">
            NeuroSync will automatically generate:<br />
            <span className="text-neurosync-400">Slides</span> {' \u00B7 '}
            <span className="text-neurosync-400">Written Notes</span> {' \u00B7 '}
            <span className="text-neurosync-400">Story Explanation</span> {' \u00B7 '}
            <span className="text-neurosync-400">Quiz Bank</span>
          </p>
          <label className="btn-primary cursor-pointer inline-block">
            <span className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Choose PDF File
            </span>
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleFileSelect}
              data-testid="pdf-input"
            />
          </label>
          <p className="text-xs text-gray-600 mt-4">or drag and drop</p>
        </div>
      )}

      {/* Uploading state with step-by-step progress */}
      {uploading && (
        <div className="py-8">
          <div className="text-center mb-8">
            <Loader className="w-16 h-16 mx-auto mb-4 animate-spin text-neurosync-500" />

            <h3 className="text-2xl font-bold mb-2">
              Generating Course Content...
            </h3>

            <p className="text-gray-400 mb-6">
              This will take approximately 10-12 minutes
            </p>
          </div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="w-full bg-gray-800 rounded-full h-6 overflow-hidden">
              <div
                className="bg-gradient-to-r from-neurosync-600 to-neurosync-400 h-6 rounded-full transition-all duration-500 ease-out flex items-center justify-center text-white text-sm font-semibold"
                style={{ width: `${progress}%` }}
              >
                {Math.round(progress)}%
              </div>
            </div>
          </div>

          {/* Current Step List */}
          <div className="space-y-3">
            {GENERATION_STEPS.map((step) => {
              const isComplete = progress >= step.progress;
              const isCurrent = progress < step.progress &&
                               (step.id === 1 || progress >= GENERATION_STEPS[step.id - 2].progress);

              return (
                <div
                  key={step.id}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                    isComplete
                      ? 'bg-green-900/20 text-green-400'
                      : isCurrent
                      ? 'bg-neurosync-900/20 text-neurosync-400 animate-pulse'
                      : 'bg-gray-900/20 text-gray-600'
                  }`}
                >
                  {isComplete ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : isCurrent ? (
                    <Loader className="w-5 h-5 animate-spin text-neurosync-400" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-700" />
                  )}

                  <span className="font-medium">{step.label}</span>

                  {isComplete && (
                    <CheckCircle className="w-4 h-4 ml-auto text-green-600" />
                  )}
                </div>
              );
            })}
          </div>

          {/* Cancel Button */}
          <button
            onClick={handleCancelUpload}
            className="mt-6 w-full py-2 border border-gray-700 rounded-lg hover:bg-gray-800 transition-colors text-gray-400"
          >
            Cancel Upload
          </button>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="text-center py-8">
          <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-red-500" />
          <h3 className="text-xl font-semibold mb-2 text-red-400">Generation Failed</h3>
          <p className="text-gray-400 mb-6">{error}</p>
          <button onClick={reset} className="btn-secondary">
            Try Again
          </button>
        </div>
      )}

      {/* Success state */}
      {result && (
        <div className="text-center py-4">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500" />
          <h3 className="text-2xl font-bold mb-2">Course Generated!</h3>
          <p className="text-gray-400 mb-6">{result.title}</p>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="card text-center">
              <p className="text-2xl font-bold text-neurosync-400">{result.slide_count}</p>
              <p className="text-sm text-gray-400">Slides</p>
            </div>
            <div className="card text-center">
              <p className="text-2xl font-bold text-neurosync-400">{result.question_count}</p>
              <p className="text-sm text-gray-400">Quiz Questions</p>
            </div>
            <div className="card text-center">
              <p className="text-2xl font-bold text-neurosync-400">{result.concept_count}</p>
              <p className="text-sm text-gray-400">Concepts</p>
            </div>
            <div className="card text-center">
              <p className="text-2xl font-bold text-neurosync-400">
                {result.formats_generated.length}
              </p>
              <p className="text-sm text-gray-400">Formats</p>
            </div>
          </div>

          <button onClick={reset} className="btn-secondary">
            Upload Another
          </button>
        </div>
      )}
    </div>
  );
};
