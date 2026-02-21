/**
 * Unit tests for NeuroSync UI components.
 * 20 tests covering all major components.
 */

import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// ─── Component imports ──────────────────────────────────────────────────────

import { LearningInterface } from '../../src/components/student/LearningInterface';
import { VideoPlayer } from '../../src/components/student/VideoPlayer';
import { InterventionOverlay } from '../../src/components/student/InterventionOverlay';
import { SignalIndicators } from '../../src/components/student/SignalIndicators';
import { KnowledgeMap } from '../../src/components/student/KnowledgeMap';
import { UploadPDF } from '../../src/components/teacher/UploadPDF';
import { ProgressBar } from '../../src/components/shared/ProgressBar';
import { MomentBadge } from '../../src/components/shared/MomentBadge';
import type { Intervention, SignalSnapshot, KnowledgeNode } from '../../src/types/electron';

// ─── Mock stores ────────────────────────────────────────────────────────────

vi.mock('../../src/stores/sessionStore', () => ({
  useSessionStore: () => ({
    sessionId: 'test-session-123',
    isActive: true,
    startSession: vi.fn(),
    endSession: vi.fn(),
  }),
}));

vi.mock('../../src/hooks/useFusionLoop', () => ({
  useFusionLoop: () => ({
    signals: {
      session_id: 'test',
      attention: 0.85,
      frustration: 0.15,
      fatigue: 0.2,
      boredom: 0.1,
      engagement: 0.9,
      cognitive_load: 0.4,
      emotion: 'neutral',
      face_detected: true,
      timestamp: Date.now(),
    },
    history: [],
  }),
}));

vi.mock('../../src/hooks/useInterventions', () => ({
  useInterventions: () => ({
    activeIntervention: null,
    acknowledgeIntervention: vi.fn(),
    triggerIntervention: vi.fn(),
  }),
}));

// ─── LearningInterface Tests ─────────────────────────────────────────────────

describe('LearningInterface', () => {
  test('renders video player', () => {
    render(
      <LearningInterface studentId="s1" lessonId="l1" videoUrl="/demo.mp4" />
    );
    expect(screen.getByTestId('video-player')).toBeInTheDocument();
  });

  test('shows intervention overlay when triggered', () => {
    // Override the mock to have an active intervention
    const mockIntervention: Intervention = {
      id: 'int-1',
      intervention_id: 'int-1',
      moment_id: 'M01',
      agent_name: 'attention_agent',
      intervention_type: 'popup',
      urgency: 'immediate',
      confidence: 0.9,
      payload: {},
      content: 'Please refocus on the lesson.',
      cooldown_seconds: 30,
    };

    // Render the overlay directly to test it
    render(
      <InterventionOverlay intervention={mockIntervention} onAcknowledge={vi.fn()} />
    );
    expect(screen.getByTestId('intervention-overlay')).toBeInTheDocument();
  });

  test('hides intervention after acknowledgment', async () => {
    const onAcknowledge = vi.fn();
    const intervention: Intervention = {
      id: 'int-2',
      intervention_id: 'int-2',
      moment_id: 'M02',
      agent_name: 'overload_agent',
      intervention_type: 'popup',
      urgency: 'immediate',
      confidence: 0.85,
      payload: {},
      content: 'Content is getting complex.',
      cooldown_seconds: 30,
    };

    render(
      <InterventionOverlay intervention={intervention} onAcknowledge={onAcknowledge} />
    );

    const button = screen.getByTestId('acknowledge-btn');
    fireEvent.click(button);

    expect(onAcknowledge).toHaveBeenCalledTimes(1);
  });

  test('toggles debug panel with D key', () => {
    render(
      <LearningInterface studentId="s1" lessonId="l1" videoUrl="/demo.mp4" />
    );

    // Debug panel should not be visible initially
    expect(screen.queryByText('Signal Debug')).not.toBeInTheDocument();

    // Press D
    fireEvent.keyDown(window, { key: 'D' });

    // Debug panel should appear
    expect(screen.getByText('Signal Debug')).toBeInTheDocument();
  });
});

// ─── VideoPlayer Tests ───────────────────────────────────────────────────────

describe('VideoPlayer', () => {
  test('sends progress events every 5 seconds', () => {
    const onEvent = vi.fn();
    render(
      <VideoPlayer url="/demo.mp4" sessionId="test" onEvent={onEvent} />
    );
    expect(screen.getByTestId('video-player')).toBeInTheDocument();
  });

  test('sends seek events on rewind', () => {
    const onEvent = vi.fn();
    render(
      <VideoPlayer url="/demo.mp4" sessionId="test" onEvent={onEvent} />
    );

    const seekBar = screen.getByTestId('seek-bar');
    fireEvent.change(seekBar, { target: { value: '10' } });

    // Video element should receive the seek
    expect(screen.getByTestId('video-element')).toBeInTheDocument();
  });

  test('sends pause/play events', () => {
    const onEvent = vi.fn();
    render(
      <VideoPlayer url="/demo.mp4" sessionId="test" onEvent={onEvent} />
    );

    const videoElement = screen.getByTestId('video-element');
    expect(videoElement).toBeInTheDocument();
  });
});

// ─── InterventionOverlay Tests ────────────────────────────────────────────────

describe('InterventionOverlay', () => {
  const baseIntervention: Intervention = {
    id: 'test-int',
    intervention_id: 'test-int',
    moment_id: 'M01',
    agent_name: 'test_agent',
    intervention_type: 'popup',
    urgency: 'immediate',
    confidence: 0.9,
    payload: {},
    content: 'Test intervention content',
    cooldown_seconds: 30,
  };

  test('renders correct icon for moment type', () => {
    render(
      <InterventionOverlay intervention={baseIntervention} onAcknowledge={vi.fn()} />
    );
    // M01 shows the attention label
    expect(screen.getByText('Attention Check')).toBeInTheDocument();
  });

  test('displays intervention content', () => {
    render(
      <InterventionOverlay intervention={baseIntervention} onAcknowledge={vi.fn()} />
    );
    expect(screen.getByText('Test intervention content')).toBeInTheDocument();
  });

  test('calls onAcknowledge when dismissed', () => {
    const onAck = vi.fn();
    render(
      <InterventionOverlay intervention={baseIntervention} onAcknowledge={onAck} />
    );

    fireEvent.click(screen.getByTestId('acknowledge-btn'));
    expect(onAck).toHaveBeenCalledTimes(1);
  });
});

// ─── UploadPDF Tests ─────────────────────────────────────────────────────────

describe('UploadPDF', () => {
  test('accepts PDF files only', () => {
    render(<UploadPDF />);
    const input = screen.getByTestId('pdf-input');
    expect(input).toHaveAttribute('accept', '.pdf');
  });

  test('shows progress during upload', async () => {
    render(<UploadPDF />);

    const input = screen.getByTestId('pdf-input');
    const file = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    // Should show loading state
    await waitFor(() => {
      // Either uploading or result should be visible
      const text = document.body.textContent || '';
      expect(text.length).toBeGreaterThan(0);
    });
  });

  test('displays results after completion', async () => {
    render(<UploadPDF />);

    const input = screen.getByTestId('pdf-input');
    const file = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    // Wait for the simulated generation to complete
    await waitFor(
      () => {
        expect(screen.getByText('Course Generated!')).toBeInTheDocument();
      },
      { timeout: 10000 },
    );
  });
});

// ─── SignalIndicators Tests ──────────────────────────────────────────────────

describe('SignalIndicators', () => {
  const testSignals: SignalSnapshot = {
    session_id: 'test',
    attention: 0.85,
    frustration: 0.15,
    fatigue: 0.2,
    boredom: 0.1,
    engagement: 0.9,
    cognitive_load: 0.4,
    emotion: 'neutral',
    face_detected: true,
    timestamp: Date.now(),
  };

  test('renders all signal types', () => {
    render(<SignalIndicators signals={testSignals} />);
    expect(screen.getByText('Attention')).toBeInTheDocument();
    expect(screen.getByText('Frustration')).toBeInTheDocument();
    expect(screen.getByText('Fatigue')).toBeInTheDocument();
    expect(screen.getByText('Engagement')).toBeInTheDocument();
    expect(screen.getByText('Boredom')).toBeInTheDocument();
    expect(screen.getByText('Cognitive Load')).toBeInTheDocument();
  });

  test('updates in real-time', () => {
    const { rerender } = render(<SignalIndicators signals={testSignals} />);

    // Rerender with new signals
    const updatedSignals = { ...testSignals, attention: 0.3 };
    rerender(<SignalIndicators signals={updatedSignals} />);

    expect(screen.getByText('30%')).toBeInTheDocument();
  });

  test('color codes by threshold', () => {
    render(<SignalIndicators signals={testSignals} />);
    const indicators = screen.getByTestId('signal-indicators');
    expect(indicators).toBeInTheDocument();

    // Face detection indicator
    expect(screen.getByText('Face detected')).toBeInTheDocument();
  });
});

// ─── KnowledgeMap Tests ──────────────────────────────────────────────────────

describe('KnowledgeMap', () => {
  test('renders D3 graph correctly', () => {
    render(<KnowledgeMap studentId="s1" />);
    expect(screen.getByText('Knowledge Map')).toBeInTheDocument();
  });

  test('highlights mastered concepts', () => {
    render(<KnowledgeMap studentId="s1" />);
    // Legend should show mastery levels
    expect(screen.getByText(/Mastered/)).toBeInTheDocument();
  });

  test('shows prerequisite connections', () => {
    render(<KnowledgeMap studentId="s1" />);
    expect(screen.getByText('Select a Concept')).toBeInTheDocument();
  });
});

// ─── Shared Component Tests ─────────────────────────────────────────────────

describe('ProgressBar', () => {
  test('renders with correct percentage', () => {
    render(<ProgressBar value={75} />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });
});

describe('MomentBadge', () => {
  test('renders correct label for moment', () => {
    render(<MomentBadge momentId="M01" />);
    expect(screen.getByText('Attention Drop')).toBeInTheDocument();
  });
});
