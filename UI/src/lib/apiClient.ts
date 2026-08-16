/**
 * Typed fetch wrapper for the FastAPI backend. Hand-written rather than
 * codegen'd (openapi-typescript) -- the API surface is small enough that a
 * build-time codegen step against a running server isn't worth the
 * tooling weight.
 */

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const USER_ID_KEY = "finagents.user_id";

/** Anonymous per-browser UUID, generated once and reused -- no login
 * screen for v1 (plan.md decisions). */
export function getUserId(): string {
  let id = localStorage.getItem(USER_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(USER_ID_KEY, id);
  }
  return id;
}

export type RiskProfile = string | [string, string];

export interface CreateSessionRequest {
  instruments: string[];
  risk: RiskProfile;
  target_return: string;
  horizon: string;
  goal: string;
  capital?: number;
}

export interface SessionSummary {
  id: string;
  thread_id: string;
  status: string;
}

export interface SessionListItem {
  id: string;
  thread_id: string;
  goal: string;
  status: string;
  created_at: string;
}

export interface AssetMetrics {
  ticker: string;
  name: string;
  last_price_inr: number;
  return_1y_pct: number;
  volatility_pct: number;
  sharpe_ratio: number;
  trend: string;
  market_cap_cr: string;
  pe_ratio: string;
  pb_ratio: string;
  debt_to_equity: string;
  roe: string;
  eps_ttm: string;
  dividend_yield: string;
  expense_ratio: string;
  // Optional: sessions checkpointed before this field existed may lack it.
  instrument_type?: string;
}

export interface SessionDetail extends SessionListItem {
  error_message: string | null;
  analyzed_metrics?: AssetMetrics[];
  final_thesis?: string;
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getUserId(),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText);
    throw new ApiError(response.status, detail || response.statusText);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function createSession(body: CreateSessionRequest): Promise<SessionSummary> {
  return request<SessionSummary>("/api/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function startRun(sessionId: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/api/sessions/${sessionId}/run`, { method: "POST" });
}

export function getSession(sessionId: string): Promise<SessionDetail> {
  return request<SessionDetail>(`/api/sessions/${sessionId}`);
}

export function listSessions(): Promise<SessionListItem[]> {
  return request<SessionListItem[]>("/api/sessions");
}

export interface PricePoint {
  date: string;
  value: number;
}

export function getPriceHistory(sessionId: string): Promise<Record<string, PricePoint[]>> {
  return request<Record<string, PricePoint[]>>(`/api/sessions/${sessionId}/price-history`);
}

export function sessionStreamUrl(sessionId: string): string {
  return `${API_BASE_URL}/api/sessions/${sessionId}/stream`;
}

export { API_BASE_URL, ApiError };
