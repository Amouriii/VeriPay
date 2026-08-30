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
