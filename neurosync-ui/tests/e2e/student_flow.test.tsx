/**
 * E2E tests for Student Learning Interface flows.
 * Tests lesson flow, interventions, readiness checks, and spaced review.
 */

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { LearningInterface } from '../../src/components/student/LearningInterface';
import { ReadinessCheck } from '../../src/components/student/ReadinessCheck';
import { SpacedReview } from '../../src/components/student/SpacedReview';
import { InterventionOverlay } from '../../src/components/student/InterventionOverlay';
import { useSessionStore } from '../../src/stores/sessionStore';

function Wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

// ─── Student Lesson Flow ────────────────────────────────────────────────────

describe('Student Learning Flow E2E', () => {
  beforeEach(() => {
    useSessionStore.getState().reset();
  });

  test('renders learning interface with video player', () => {
    render(
      <LearningInterface studentId="s1" lessonId="l1" videoUrl="/test.mp4" />,
      { wrapper: Wrapper }
    );

    // Should render without crashing and show the video player area
    expect(document.querySelector('[data-testid="video-player"]')).toBeTruthy();
  });

  test('starts a session on mount', async () => {
    render(
      <LearningInterface studentId="s1" lessonId="l1" videoUrl="/test.mp4" />,
      { wrapper: Wrapper }
    );

    await waitFor(() => {
      const state = useSessionStore.getState();
      expect(state.isActive).toBe(true);
    });
  });
});

// ─── Intervention Flow ──────────────────────────────────────────────────────

describe('Student Intervention Flow', () => {
  test('displays intervention overlay with acknowledge button', () => {
    const mockIntervention = {
      id: 'int-test',
      intervention_id: 'int-test',
      moment_id: 'M01',
      agent_name: 'attention_agent',
      intervention_type: 'popup' as const,
      urgency: 'immediate' as const,
      confidence: 0.92,
      payload: {},
      content: 'Your attention seems to be dropping. Take a moment to refocus.',
      cooldown_seconds: 30,
    };

    render(
      <InterventionOverlay
        intervention={mockIntervention}
        onAcknowledge={vi.fn()}
      />,
      { wrapper: Wrapper }
    );

    expect(screen.getByTestId('intervention-overlay')).toBeTruthy();
    expect(screen.getByTestId('acknowledge-btn')).toBeTruthy();
    expect(screen.getByText(/attention seems to be dropping/i)).toBeTruthy();
  });
});

// ─── Readiness Check Flow ───────────────────────────────────────────────────

describe('Student Readiness Check Flow', () => {
  test('renders readiness check intro phase', () => {
    render(
      <ReadinessCheck studentId="s1" lessonTopic="Math" onComplete={vi.fn()} />,
      { wrapper: Wrapper }
    );

    expect(screen.getByText(/Pre-Lesson Readiness Check/i)).toBeTruthy();
    expect(screen.getByText(/Let's Go/i)).toBeTruthy();
  });

  test('advances to self-report phase', async () => {
    render(
      <ReadinessCheck studentId="s1" lessonTopic="Math" onComplete={vi.fn()} />,
      { wrapper: Wrapper }
    );

    const goBtn = screen.getByText(/Let's Go/i);
    fireEvent.click(goBtn);

    await waitFor(() => {
      // Should advance to self-report phase which asks about energy
      expect(screen.getByText(/energy/i)).toBeTruthy();
    });
  });
});

// ─── Spaced Review Flow ─────────────────────────────────────────────────────

describe('Student Spaced Review Flow', () => {
  test('renders spaced review interface', () => {
    render(<SpacedReview studentId="s1" />, { wrapper: Wrapper });

    expect(screen.getByText(/Spaced Review/i)).toBeTruthy();
  });
});
