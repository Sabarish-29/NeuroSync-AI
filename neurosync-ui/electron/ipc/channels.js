/**
 * IPC channel name definitions.
 * Single source of truth for all main ↔ renderer communication channels.
 */

const CHANNELS = {
  // Session
  SESSION_START: 'session:start',
  SESSION_END: 'session:end',

  // Events
  EVENT_SEND: 'event:send',

  // Signals
  SIGNAL_UPDATE: 'signal:update',

  // Interventions
  INTERVENTION_TRIGGERED: 'intervention:triggered',
  INTERVENTION_ACK: 'intervention:ack',

  // Content
  CONTENT_UPLOAD: 'content:upload',
  CONTENT_PROGRESS: 'content:progress',

  // Reviews
  REVIEWS_DUE: 'reviews:due',
  REVIEWS_SUBMIT: 'reviews:submit',

  // Readiness
  READINESS_START: 'readiness:start',
  READINESS_SUBMIT: 'readiness:submit',

  // Knowledge
  KNOWLEDGE_MAP: 'knowledge:map',

  // Webcam
  WEBCAM_PERMISSION: 'webcam:permission',

  // Window
  WINDOW_MINIMIZE: 'window:minimize',
  WINDOW_MAXIMIZE: 'window:maximize',
  WINDOW_CLOSE: 'window:close',
};

module.exports = CHANNELS;
