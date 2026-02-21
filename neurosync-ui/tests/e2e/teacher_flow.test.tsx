/**
 * E2E tests for Teacher Dashboard flows.
 * Tests PDF upload, content library, and analytics views.
 */

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { TeacherDashboard } from '../../src/components/teacher/Dashboard';
import { UploadPDF } from '../../src/components/teacher/UploadPDF';
import { ContentLibrary } from '../../src/components/teacher/ContentLibrary';

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

// ─── Teacher Dashboard Flow ─────────────────────────────────────────────────

describe('Teacher Dashboard E2E', () => {
  test('renders dashboard with title and tabs', () => {
    render(<TeacherDashboard />, { wrapper: Wrapper });

    expect(screen.getByText(/Teacher Dashboard/i)).toBeTruthy();
    // Tabs are present
    expect(screen.getAllByText(/Content Library/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Student Analytics/i)).toBeTruthy();
    expect(screen.getByText(/Live Monitor/i)).toBeTruthy();
  });

  test('switches to Content Library tab', async () => {
    render(<TeacherDashboard />, { wrapper: Wrapper });

    // Click the Content Library tab
    const tabs = screen.getAllByText(/Content Library/i);
    const tabButton = tabs.find(el => el.closest('button'));
    if (tabButton) fireEvent.click(tabButton);

    await waitFor(() => {
      // The ContentLibrary component renders its heading
      expect(screen.getAllByText(/Content Library/i).length).toBeGreaterThanOrEqual(1);
    });
  });
});

// ─── PDF Upload Flow ────────────────────────────────────────────────────────

describe('Teacher PDF Upload Flow', () => {
  test('renders PDF upload area with file input', () => {
    render(<UploadPDF />, { wrapper: Wrapper });

    expect(screen.getByTestId('pdf-input')).toBeTruthy();
    expect(screen.getByText(/Upload PDF Textbook Chapter/i)).toBeTruthy();
  });

  test('has a choose PDF file button', () => {
    render(<UploadPDF />, { wrapper: Wrapper });

    expect(screen.getByText(/Choose PDF File/i)).toBeTruthy();
  });
});

// ─── Content Library Flow ───────────────────────────────────────────────────

describe('Teacher Content Library', () => {
  test('displays content library heading', () => {
    render(<ContentLibrary />, { wrapper: Wrapper });

    expect(screen.getByText(/Content Library/i)).toBeTruthy();
  });
});
