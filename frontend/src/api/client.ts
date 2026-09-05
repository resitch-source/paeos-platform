// Tenant-aware API client (frontend foundation, section AD).
// Attaches the auth token and a correlation id; never stores secrets in code.

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export interface ApiError {
  code: string;
  message: string;
  details: Record<string, unknown>;
  correlation_id: string;
}

export class ApiClientError extends Error {
  readonly status: number;
  readonly body: ApiError | null;
  constructor(status: number, body: ApiError | null) {
    super(body?.message ?? `Request failed with status ${status}`);
    this.status = status;
    this.body = body;
  }
}

function correlationId(): string {
  return crypto.randomUUID();
}

let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token;
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  headers.set("X-Correlation-ID", correlationId());
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }

  const resp = await fetch(`${API_BASE}${path}`, { ...init, headers });
  const text = await resp.text();
  const json = text ? JSON.parse(text) : null;

  if (!resp.ok) {
    throw new ApiClientError(resp.status, json?.error ?? null);
  }
  return json as T;
}
