/**
 * SRRA-OPH API Client
 * ===================
 * Typed client for the SRRA-OPH API wrapper.
 */

const API_BASE = process.env.NEXT_PUBLIC_SRRA_API || "";

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${path}: ${body}`);
  }
  return res.json();
}

// ─── Types ───────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  timestamp: string;
  patches: Record<string, { state: string; healthy: boolean; repair_count: number }>;
  total_patches: number;
  stable_count: number;
  entropy_remaining: number;
  coherence_yield: number;
}

export interface ModuleInfo {
  name: string;
  phase: number;
  module_type: string;
  status: string;
  is_stable: boolean;
  repair_count: number;
  local_state_keys: string[];
}

export interface TopologyNode {
  id: string;
  label: string;
  type: string;
  status: string;
  entropy: number;
  syncScore: number;
  repairState: string;
  x: number;
  y: number;
  clusterId?: string;
}

export interface TopologyEdge {
  source: string;
  target: string;
  strength: number;
  type: string;
}

export interface TopologyResponse {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  stats: Record<string, number>;
}

export interface TestResult {
  phase: number;
  test_file: string;
  status: string;
  passed: number | null;
  failed: number | null;
  total: number | null;
  duration_ms: number | null;
  output: string | null;
}

export interface TestSummary {
  total_tests: number;
  passed: number;
  failed: number;
  phases: TestResult[];
  last_run: string | null;
}

export interface EventItem {
  event_id: string;
  event_type: string;
  timestamp: string;
  source: string;
  priority: number;
  payload: Record<string, unknown>;
}

export interface PhaseInfo {
  phase: number;
  name: string;
  description: string;
  modules: string[];
  status: string;
}

// ─── API Functions ───────────────────────────────────────────────────────────

export const srraApi = {
  health: () => fetchJSON<HealthResponse>("/api/health"),
  modules: () => fetchJSON<ModuleInfo[]>("/api/modules"),
  moduleDetail: (name: string) => fetchJSON<Record<string, unknown>>(`/api/modules/${name}`),
  topology: () => fetchJSON<TopologyResponse>("/api/topology"),
  tests: () => fetchJSON<TestSummary>("/api/tests"),
  events: (limit = 50) => fetchJSON<EventItem[]>(`/api/events?limit=${limit}`),
  phases: () => fetchJSON<PhaseInfo[]>("/api/phases"),
  phaseDetail: (id: number) => fetchJSON<Record<string, unknown>>(`/api/phases/${id}`),
  root: () => fetchJSON<Record<string, unknown>>("/api/"),
};
