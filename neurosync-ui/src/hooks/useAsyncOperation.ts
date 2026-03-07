/**
 * useAsyncOperation - Hook for managing async state
 *
 * Provides loading, error, and success states for async operations.
 * Ensures consistent UX across all async actions.
 */

import { useState, useCallback } from 'react';

interface AsyncState<T> {
  loading: boolean;
  error: Error | null;
  data: T | null;
}

interface UseAsyncOperationReturn<T> {
  loading: boolean;
  error: Error | null;
  data: T | null;
  execute: (...args: unknown[]) => Promise<T>;
  reset: () => void;
}

export function useAsyncOperation<T>(
  asyncFunction: (...args: unknown[]) => Promise<T>
): UseAsyncOperationReturn<T> {
  const [state, setState] = useState<AsyncState<T>>({
    loading: false,
    error: null,
    data: null,
  });

  const execute = useCallback(
    async (...args: unknown[]): Promise<T> => {
      setState({ loading: true, error: null, data: null });

      try {
        const result = await asyncFunction(...args);
        setState({ loading: false, error: null, data: result });
        return result;
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        setState({ loading: false, error: err, data: null });
        throw err;
      }
    },
    [asyncFunction]
  );

  const reset = useCallback(() => {
    setState({ loading: false, error: null, data: null });
  }, []);

  return {
    loading: state.loading,
    error: state.error,
    data: state.data,
    execute,
    reset,
  };
}

export default useAsyncOperation;
