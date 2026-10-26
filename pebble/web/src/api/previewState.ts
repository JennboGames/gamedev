export type PreviewDataState = 'data' | 'loading' | 'empty' | 'error';

export const PREVIEW_STATES: PreviewDataState[] = ['data', 'loading', 'empty', 'error'];

const STORAGE_KEY = 'previewState';
const listeners = new Set<() => void>();

function isPreviewState(value: unknown): value is PreviewDataState {
  return typeof value === 'string' && (PREVIEW_STATES as string[]).includes(value);
}

function readInitialState(): PreviewDataState {
  if (!import.meta.env.DEV || typeof window === 'undefined') {
    return 'data';
  }
  const fromQuery = new URLSearchParams(window.location.search).get('previewState');
  if (isPreviewState(fromQuery)) return fromQuery;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return isPreviewState(stored) ? stored : 'data';
}

let current: PreviewDataState = readInitialState();

export function getPreviewState(): PreviewDataState {
  return current;
}

export function setPreviewState(state: PreviewDataState): void {
  if (!import.meta.env.DEV) return;
  current = state;
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, state);
  }
  listeners.forEach((listener) => listener());
}

export function subscribePreviewState(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
