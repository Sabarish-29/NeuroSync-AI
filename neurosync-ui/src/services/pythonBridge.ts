/**
 * Python backend bridge — TypeScript API for communicating with the FastAPI server.
 * Used when running in a browser (without Electron IPC).
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

async function apiRequest<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    headers?: Record<string, string>;
  } = {},
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export const pythonBridge = {
  // Health
  health: () => apiRequest<{ status: string; version: string }>('/health'),

  // Session
  startSession: (config: {
    session_id: string;
    student_id: string;
    lesson_id: string;
    webcam_enabled: boolean;
  }) => apiRequest('/session/start', { method: 'POST', body: config }),

  endSession: (sessionId: string) =>
    apiRequest(`/session/${sessionId}/end`, { method: 'POST' }),

  // Events
  sendEvent: (event: Record<string, unknown>) =>
    apiRequest('/events', { method: 'POST', body: event }),

  // Reviews
  getDueReviews: (studentId: string) =>
    apiRequest(`/reviews/${studentId}/due`),

  submitReview: (data: { student_id: string; concept_id: string; score: number }) =>
    apiRequest('/reviews/submit', { method: 'POST', body: data }),

  // Readiness
  startReadinessCheck: (config: {
    student_id: string;
    lesson_topic: string;
    session_id?: string;
  }) => apiRequest('/readiness/start', { method: 'POST', body: config }),

  // Knowledge map
  getKnowledgeMap: (studentId: string) =>
    apiRequest(`/knowledge/map/${studentId}`),

  // Content
  uploadPDF: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/content/upload`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  },
};
