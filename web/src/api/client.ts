// Base API client for backend services. Wire to the decision/investigation APIs.
const BASE_URL = import.meta.env.VITE_API_BASE ?? '/api';

export async function apiGet<T>(path: string): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`);
  if (!resp.ok) throw new Error(`API ${resp.status}`);
  return resp.json() as Promise<T>;
}
