/**
 * Error handling utilities
 *
 * Centralized error classification and user-friendly messaging.
 */

export class NeuroSyncError extends Error {
  constructor(
    message: string,
    public code: string,
    public userMessage: string,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = 'NeuroSyncError';
  }
}

export const ErrorCodes = {
  GROQ_API_ERROR: 'GROQ_API_ERROR',
  WEBCAM_ACCESS_DENIED: 'WEBCAM_ACCESS_DENIED',
  EEG_NOT_FOUND: 'EEG_NOT_FOUND',
  NETWORK_ERROR: 'NETWORK_ERROR',
  CONTENT_GENERATION_FAILED: 'CONTENT_GENERATION_FAILED',
  INVALID_CONFIGURATION: 'INVALID_CONFIGURATION',
} as const;

export function handleError(error: unknown): NeuroSyncError {
  if (error instanceof NeuroSyncError) {
    return error;
  }

  const msg = error instanceof Error ? error.message : String(error);

  if (msg.includes('GROQ_API_KEY') || msg.includes('groq')) {
    return new NeuroSyncError(
      msg,
      ErrorCodes.GROQ_API_ERROR,
      'API configuration error. Please check your Groq API key in settings.',
      false
    );
  }

  if (msg.includes('webcam') || msg.includes('camera') || msg.includes('MediaPipe')) {
    return new NeuroSyncError(
      msg,
      ErrorCodes.WEBCAM_ACCESS_DENIED,
      'Camera access denied. Please allow camera permissions.',
      true
    );
  }

  if (msg.includes('EEG') || msg.includes('eeg')) {
    return new NeuroSyncError(
      msg,
      ErrorCodes.EEG_NOT_FOUND,
      'EEG hardware not detected. Continuing with webcam-only detection.',
      false
    );
  }

  if (msg.includes('network') || msg.includes('fetch') || msg.includes('ECONNREFUSED')) {
    return new NeuroSyncError(
      msg,
      ErrorCodes.NETWORK_ERROR,
      'Network error. Please check your internet connection.',
      true
    );
  }

  return new NeuroSyncError(
    msg,
    'UNKNOWN_ERROR',
    'An unexpected error occurred. Please try again.',
    true
  );
}

export function logError(error: Error | NeuroSyncError, context?: string): void {
  console.error(`[NeuroSync${context ? ` - ${context}` : ''}]:`, error.message);
}
