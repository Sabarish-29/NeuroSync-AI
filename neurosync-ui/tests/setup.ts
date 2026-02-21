import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock window.electronAPI for tests
const mockElectronAPI = {
  startSession: vi.fn().mockResolvedValue({ session_id: 'test-session', status: 'started' }),
  endSession: vi.fn().mockResolvedValue({ session_id: 'test-session', status: 'ended' }),
  sendEvent: vi.fn().mockResolvedValue({ status: 'recorded' }),
  onSignalUpdate: vi.fn().mockReturnValue(() => {}),
  onIntervention: vi.fn().mockReturnValue(() => {}),
  acknowledgeIntervention: vi.fn().mockResolvedValue({ status: 'acknowledged' }),
  uploadPDF: vi.fn().mockResolvedValue({ task_id: 'test-task', status: 'processing' }),
  onGenerationProgress: vi.fn().mockReturnValue(() => {}),
  getDueReviews: vi.fn().mockResolvedValue({ student_id: 'test', reviews: [], total: 0 }),
  submitReview: vi.fn().mockResolvedValue({ status: 'recorded' }),
  startReadinessCheck: vi.fn().mockResolvedValue({ readiness_score: 0.8, status: 'ready' }),
  submitReadinessResponse: vi.fn().mockResolvedValue({ readiness_score: 0.8 }),
  getKnowledgeMap: vi.fn().mockResolvedValue({ student_id: 'test', nodes: [], edges: [] }),
  requestWebcamPermission: vi.fn().mockResolvedValue({ granted: true }),
  minimizeWindow: vi.fn().mockResolvedValue(undefined),
  maximizeWindow: vi.fn().mockResolvedValue(undefined),
  closeWindow: vi.fn().mockResolvedValue(undefined),
};

Object.defineProperty(window, 'electronAPI', {
  value: mockElectronAPI,
  writable: true,
});

// Mock ResizeObserver (needed for Recharts)
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.ResizeObserver = ResizeObserverMock as any;

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
