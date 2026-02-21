import React, { useState, useCallback } from 'react';
import { Upload, CheckCircle, Loader, FileText, AlertTriangle } from 'lucide-react';
import { ProgressBar } from '../shared/ProgressBar';

interface GenerationResult {
  task_id: string;
  title: string;
  concept_count: number;
  slide_count: number;
  question_count: number;
  video_duration: string;
  formats_generated: string[];
}

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
    const unsubscribe = window.electronAPI?.onGenerationProgress((data) => {
      setProgress(data.progress);
      setStage(data.stage || data.message || '');
    });

    try {
      // Simulate progress for demo (in production, use actual API)
      const stages = [
        'Parsing PDF...',
        'Extracting concepts...',
        'Generating slides...',
        'Writing notes...',
        'Creating story...',
        'Generating quiz...',
        'Finalizing...',
      ];

      for (let i = 0; i < stages.length; i++) {
        setStage(stages[i]);
        setProgress(((i + 1) / stages.length) * 100);
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
      setError(err instanceof Error ? err.message : 'Upload failed');
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

  const reset = () => {
    setResult(null);
    setProgress(0);
    setStage('');
    setError(null);
  };

  return (
    <div className="card max-w-2xl mx-auto">
      {/* Idle state — file picker */}
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
            <span className="text-neurosync-400">Slides</span> {' · '}
            <span className="text-neurosync-400">Written Notes</span> {' · '}
            <span className="text-neurosync-400">Story Explanation</span> {' · '}
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

      {/* Uploading state */}
      {uploading && (
        <div className="text-center py-8">
          <Loader className="w-16 h-16 mx-auto mb-4 animate-spin text-neurosync-500" />
          <h3 className="text-xl font-semibold mb-4">Generating Course Content...</h3>
          <ProgressBar value={progress} color="purple" size="lg" />
          <p className="text-gray-400 mt-3">{stage}</p>
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
