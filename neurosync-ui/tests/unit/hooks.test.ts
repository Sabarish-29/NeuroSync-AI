/**
 * Unit tests for hooks.
 * Tests for useFusionLoop, useInterventions, useSignals, useWebcam.
 */

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

import { useSignalStore } from '../../src/stores/signalStore';
import { useSessionStore } from '../../src/stores/sessionStore';
import { useInterventionStore } from '../../src/stores/interventionStore';
import { EventLogger } from '../../src/services/eventLogger';
import { SessionManager } from '../../src/services/sessionManager';

// ─── Signal Store Tests ─────────────────────────────────────────────────────

describe('SignalStore', () => {
  beforeEach(() => {
    useSignalStore.getState().reset();
  });

  test('initializes with default signals', () => {
    const state = useSignalStore.getState();
    expect(state.current.attention).toBe(1.0);
    expect(state.current.frustration).toBe(0.0);
    expect(state.history).toHaveLength(0);
  });

  test('updates signals correctly', () => {
    const store = useSignalStore.getState();
    store.updateSignals({
      session_id: 'test',
      attention: 0.5,
      frustration: 0.3,
      fatigue: 0.2,
      boredom: 0.1,
      engagement: 0.8,
      cognitive_load: 0.4,
      emotion: 'focused',
      face_detected: true,
      timestamp: Date.now(),
    });

    const updated = useSignalStore.getState();
    expect(updated.current.attention).toBe(0.5);
    expect(updated.current.frustration).toBe(0.3);
    expect(updated.history).toHaveLength(1);
  });

  test('limits history to maxHistory', () => {
    const store = useSignalStore.getState();
    for (let i = 0; i < 150; i++) {
      store.updateSignals({
        session_id: 'test',
        attention: Math.random(),
        frustration: 0,
        fatigue: 0,
        boredom: 0,
        engagement: 1,
        cognitive_load: 0.3,
        emotion: 'neutral',
        face_detected: true,
        timestamp: Date.now(),
      });
    }
    const state = useSignalStore.getState();
    expect(state.history.length).toBeLessThanOrEqual(state.maxHistory);
  });
});

// ─── Session Store Tests ─────────────────────────────────────────────────────

describe('SessionStore', () => {
  beforeEach(() => {
    useSessionStore.getState().reset();
  });

  test('starts session', () => {
    useSessionStore.getState().startSession({
      session_id: 'test-123',
      student_id: 'student-1',
      lesson_id: 'lesson-1',
      webcam_enabled: true,
    });

    const state = useSessionStore.getState();
    expect(state.sessionId).toBe('test-123');
    expect(state.isActive).toBe(true);
  });

  test('ends session', () => {
    const store = useSessionStore.getState();
    store.startSession({
      session_id: 'test-123',
      student_id: 's1',
      lesson_id: 'l1',
      webcam_enabled: false,
    });
    store.endSession('test-123');

    const state = useSessionStore.getState();
    expect(state.isActive).toBe(false);
  });
});

// ─── Intervention Store Tests ───────────────────────────────────────────────

describe('InterventionStore', () => {
  beforeEach(() => {
    useInterventionStore.getState().reset();
  });

  test('triggers intervention', () => {
    useInterventionStore.getState().triggerIntervention({
      id: 'int-1',
      intervention_id: 'int-1',
      moment_id: 'M01',
      agent_name: 'test',
      intervention_type: 'popup',
      urgency: 'immediate',
      confidence: 0.9,
      payload: {},
      content: 'Test',
      cooldown_seconds: 30,
    });

    const state = useInterventionStore.getState();
    expect(state.activeIntervention).not.toBeNull();
    expect(state.activeIntervention?.moment_id).toBe('M01');
    expect(state.history).toHaveLength(1);
  });

  test('acknowledges intervention', () => {
    const store = useInterventionStore.getState();
    store.triggerIntervention({
      id: 'int-1',
      intervention_id: 'int-1',
      moment_id: 'M01',
      agent_name: 'test',
      intervention_type: 'popup',
      urgency: 'immediate',
      confidence: 0.9,
      payload: {},
      content: 'Test',
      cooldown_seconds: 30,
    });

    store.acknowledgeIntervention('int-1');

    const state = useInterventionStore.getState();
    expect(state.activeIntervention).toBeNull();
    expect(state.history).toHaveLength(1); // History preserved
  });
});

// ─── EventLogger Tests ──────────────────────────────────────────────────────

describe('EventLogger', () => {
  test('buffers events', () => {
    const logger = new EventLogger('test-session');

    logger.log({ event_type: 'video_play', timestamp: Date.now() });
    logger.log({ event_type: 'video_pause', timestamp: Date.now() });

    expect(logger.pendingCount).toBe(2);
  });

  test('flushes events', async () => {
    const logger = new EventLogger('test-session');
    logger.log({ event_type: 'video_play', timestamp: Date.now() });

    await logger.flush();

    expect(logger.pendingCount).toBe(0);
    expect(window.electronAPI?.sendEvent).toHaveBeenCalled();
  });
});

// ─── SessionManager Tests ───────────────────────────────────────────────────

describe('SessionManager', () => {
  test('manages session lifecycle', async () => {
    const manager = new SessionManager();

    expect(manager.isActive).toBe(false);

    await manager.start({
      session_id: 'sm-test',
      student_id: 's1',
      lesson_id: 'l1',
      webcam_enabled: false,
    });

    expect(manager.isActive).toBe(true);
    expect(manager.currentSessionId).toBe('sm-test');

    await manager.end();

    expect(manager.isActive).toBe(false);
    expect(manager.currentSessionId).toBeNull();
  });
});
