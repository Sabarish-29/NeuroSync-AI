/**
 * Type declarations for the Electron API bridge exposed via preload.js.
 */

export interface ElectronAPI {
  // Session management
  startSession: (config: SessionConfig) => Promise<SessionResponse>;
  endSession: (sessionId: string) => Promise<SessionResponse>;

  // Events
  sendEvent: (event: LearningEvent) => Promise<{ status: string }>;

  // Signals (real-time)
  onSignalUpdate: (callback: (data: SignalSnapshot) => void) => () => void;

  // Interventions
  onIntervention: (callback: (data: Intervention) => void) => () => void;
  acknowledgeIntervention: (id: string) => Promise<{ status: string }>;

  // Content generation
  uploadPDF: (filePath: string) => Promise<ContentResult>;
  onGenerationProgress: (callback: (data: ProgressData) => void) => () => void;

  // Spaced repetition
  getDueReviews: (studentId: string) => Promise<DueReviewsResponse>;
  submitReview: (data: ReviewSubmission) => Promise<ReviewResult>;

  // Readiness check
  startReadinessCheck: (config: ReadinessConfig) => Promise<ReadinessResult>;
  submitReadinessResponse: (data: ReadinessSubmission) => Promise<ReadinessResult>;

  // Knowledge graph
  getKnowledgeMap: (studentId: string) => Promise<KnowledgeMapData>;

  // Webcam
  requestWebcamPermission: () => Promise<{ granted: boolean }>;

  // Window controls
  minimizeWindow: () => Promise<void>;
  maximizeWindow: () => Promise<void>;
  closeWindow: () => Promise<void>;
}

export interface SessionConfig {
  session_id: string;
  student_id: string;
  lesson_id: string;
  webcam_enabled: boolean;
}

export interface SessionResponse {
  session_id: string;
  status: string;
}

export interface LearningEvent {
  session_id: string;
  event_type: string;
  timestamp: number;
  playback_position_ms?: number;
  seek_from_ms?: number;
  seek_to_ms?: number;
  [key: string]: unknown;
}

export interface SignalSnapshot {
  session_id: string;
  attention: number;
  frustration: number;
  fatigue: number;
  boredom: number;
  engagement: number;
  cognitive_load: number;
  emotion: string;
  face_detected: boolean;
  timestamp: number;
}

export interface Intervention {
  id: string;
  intervention_id: string;
  moment_id: string;
  agent_name: string;
  intervention_type: string;
  urgency: 'immediate' | 'next_pause' | 'deferred';
  confidence: number;
  payload: Record<string, unknown>;
  content: string;
  cooldown_seconds: number;
}

export interface ContentResult {
  task_id: string;
  status: string;
  progress: number;
  title: string;
  concept_count: number;
  slide_count: number;
  question_count: number;
  video_duration: string;
  formats_generated: string[];
  errors: string[];
}

export interface ProgressData {
  progress: number;
  stage: string;
  message: string;
}

export interface DueReviewsResponse {
  student_id: string;
  reviews: DueReview[];
  total: number;
}

export interface DueReview {
  concept_id: string;
  scheduled_at: number;
  review_number: number;
  predicted_retention: number;
  quiz: Record<string, unknown>;
}

export interface ReviewSubmission {
  student_id: string;
  concept_id: string;
  score: number;
}

export interface ReviewResult {
  student_id: string;
  concept_id: string;
  score: number;
  next_review_at: number;
  status: string;
}

export interface ReadinessConfig {
  session_id: string;
  student_id: string;
  lesson_topic: string;
  self_report_responses?: Record<string, number>;
  blink_rate?: number;
}

export interface ReadinessSubmission {
  session_id: string;
  student_id: string;
  lesson_topic: string;
  self_report_responses?: Record<string, number>;
}

export interface ReadinessResult {
  check_id: string;
  session_id: string;
  student_id: string;
  lesson_topic: string;
  readiness_score: number;
  anxiety_score: number;
  status: 'ready' | 'not_ready' | 'needs_intervention';
  recommendation: string;
  breathing_offered: boolean;
}

export interface KnowledgeMapData {
  student_id: string;
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
}

export interface KnowledgeNode {
  id: string;
  label: string;
  category: string;
  mastery: number;
  status: string;
}

export interface KnowledgeEdge {
  source: string;
  target: string;
  relationship: string;
}

// Extend Window to include electronAPI
declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}
