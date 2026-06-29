const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

export function getToken(): string | null {
  return localStorage.getItem('accessToken');
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem('accessToken', token);
  else localStorage.removeItem('accessToken');
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.detail ?? `API error ${response.status}`);
  }
  return data as T;
}

export async function login(email: string, password: string): Promise<void> {
  const body = new URLSearchParams();
  body.set('username', email);
  body.set('password', password);
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail ?? 'Login failed');
  setToken(data.access_token);
}

export function wsUrl(boardId: string): string {
  const token = getToken();
  const base = API_URL.replace(/^http/, 'ws');
  return `${base}/ws/boards/${boardId}?token=${encodeURIComponent(token ?? '')}`;
}
