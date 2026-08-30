// Base API client for backend services. Wire to the decision/investigation APIs.
const BASE_URL = import.meta.env.VITE_API_BASE ?? '/api';

export async function apiGet<T>(path: string): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`);
  if (!resp.ok) throw new Error(`API ${resp.status}`);
  return resp.json() as Promise<T>;
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await resp.json().catch(() => null);
  if (!resp.ok) {
    const error = new Error(`API ${resp.status}`) as Error & { status?: number };
    error.status = resp.status;
    throw error;
  }
  return data as T;
}

// ---------------------------------------------------------------- analyst ---
// Fraud-analyst console client. When VITE_ANALYST_API_BASE is configured the
// console talks to the real `analyst_api` service; otherwise it uses the local
// MSW mocks (served under /api in dev). If a live backend is unreachable or
// answers with an error, the call falls back to the mocks so the console stays
// navigable without a running backend.
const ANALYST_API_BASE = import.meta.env.VITE_ANALYST_API_BASE ?? '';
const ANALYST_MOCK_BASE = '/api';
const IS_DEV = import.meta.env.DEV;

const ANALYST_JSON_HEADERS = { 'Content-Type': 'application/json' };

async function analystRequest<T>(
  url: string,
  method: 'GET' | 'POST',
  body?: unknown,
): Promise<T> {
  const resp = await fetch(url, {
    method,
    headers: ANALYST_JSON_HEADERS,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await resp.json().catch(() => null);
  if (!resp.ok) {
    const error = new Error(`API ${resp.status}`) as Error & { status?: number };
    error.status = resp.status;
    throw error;
  }
  return data as T;
}

async function analystFetch<T>(
  path: string,
  method: 'GET' | 'POST',
  body?: unknown,
): Promise<T> {
  if (ANALYST_API_BASE) {
    try {
      return await analystRequest<T>(`${ANALYST_API_BASE}${path}`, method, body);
    } catch (err) {
      if (!IS_DEV) throw err; // production: surface the live error
      // dev: fall through to the MSW mocks when the live backend fails
    }
  }
  return analystRequest<T>(`${ANALYST_MOCK_BASE}${path}`, method, body);
}

export function analystGet<T>(path: string): Promise<T> {
  return analystFetch<T>(path, 'GET');
}

export function analystPost<T>(path: string, body?: unknown): Promise<T> {
  return analystFetch<T>(path, 'POST', body);
}