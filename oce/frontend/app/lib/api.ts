/**
 * OCE API Client
 * ==============
 * Typed client for the OCE Continuity Core API.
 * All endpoints return typed data with error handling.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

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

export interface ObserverStatus {
  observer_id: string;
  state: "active" | "idle" | "monitoring" | "created" | "suspended" | "destroyed";
  entropy: number;
  task: string;
  health_score?: number;
  event_count?: number;
  error_count?: number;
}

export interface AttractorState {
  goal: string;
  confidence: number;
  entropy_pressure: number;
  convergence: number;
}

export interface MemoryView {
  trajectory_memory: unknown[];
  structural_memory: unknown;
  repair_memory: unknown[];
}

export interface EventItem {
  event_id: string;
  event_type: string;
  timestamp: string;
  source: string;
  priority: number;
  payload: Record<string, unknown>;
}

export interface EventStats {
  total_events: number;
  by_type: Record<string, number>;
  by_source: Record<string, number>;
  by_priority: Record<string, number>;
}

// ─── Metrics Types ───────────────────────────────────────────────────────────

export interface MetricLatency {
  avg_ms: number;
  p95_ms: number;
  p99_ms: number;
  count: number;
}

export interface MetricObserver {
  health: number;
  entropy: number;
  error_rate: number;
}

export interface MetricMemoryLayer {
  size_bytes: number;
  entries: number;
  compression_ratio: number;
}

export interface MetricMemory {
  total_size_bytes: number;
  total_entries: number;
  layers: Record<string, MetricMemoryLayer>;
}

export interface MetricEntropy {
  consumed: number;
  remaining: number;
  total: number;
  usage_pct: number;
}

export interface MetricsSummary {
  timestamp: string;
  events: {
    total_count: number;
    rate_per_sec: number;
    latency: MetricLatency;
    by_type: Record<string, number>;
    by_source: Record<string, number>;
  };
  observers: {
    count: number;
    avg_health: number;
    by_id: Record<string, MetricObserver>;
  };
  memory: MetricMemory;
  entropy: MetricEntropy;
}

// ─── Tracing Types ───────────────────────────────────────────────────────────

export interface TraceHop {
  observer_id: string;
  action: string;
  latency_ms: number;
  timestamp: string;
  metadata: Record<string, unknown>;
}

export interface Trace {
  trace_id: string;
  event_id: string;
  event_type: string;
  source: string;
  hops: TraceHop[];
  outcome: "success" | "error" | "dropped" | "timeout" | "in_progress";
  total_latency_ms: number;
  started_at: string;
  ended_at: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
}

export interface TraceStats {
  active_traces: number;
  completed_traces: number;
  avg_latency_ms: number;
  outcome_distribution: Record<string, number>;
  ttl_sec: number;
}

// ─── Alert Types ─────────────────────────────────────────────────────────────

export interface AlertRule {
  rule_id: string;
  name: string;
  metric: string;
  threshold: number;
  comparison: string;
  severity: "info" | "warning" | "critical";
  cooldown_sec: number;
  enabled: boolean;
  description: string;
  auto_repair: boolean;
  created_at: string;
}

export interface Alert {
  alert_id: string;
  rule_id: string;
  rule_name: string;
  severity: "info" | "warning" | "critical";
  state: "firing" | "acknowledged" | "resolved";
  metric: string;
  threshold: number;
  actual_value: number;
  message: string;
  fired_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  metadata: Record<string, unknown>;
}

export interface AlertStats {
  active_firing: number;
  active_acknowledged: number;
  total_active: number;
  total_history: number;
  rules_count: number;
  by_severity: Record<string, number>;
}

// ─── Dashboard Type ──────────────────────────────────────────────────────────

export interface DashboardData {
  metrics: MetricsSummary;
  alerts: {
    active: Alert[];
    stats: AlertStats;
  };
  traces: {
    active_count: number;
    stats: TraceStats;
  };
  timestamp: string;
}

// ─── API Functions ───────────────────────────────────────────────────────────

export const api = {
  // Health
  health: () => fetchJSON<{ status: string; service: string }>("/health"),

  // Observers
  getObservers: () => fetchJSON<ObserverStatus[]>("/observers"),

  // Attractor
  getAttractor: () => fetchJSON<AttractorState>("/attractor"),

  // Memory
  getMemory: () => fetchJSON<MemoryView>("/memory"),
  getMemoryStats: () => fetchJSON<Record<string, unknown>>("/memory/stats"),

  // Events
  getEvents: (params?: { limit?: number; event_type?: string; source?: string }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.event_type) q.set("event_type", params.event_type);
    if (params?.source) q.set("source", params.source);
    return fetchJSON<EventItem[]>(`/events?${q}`);
  },
  getEventStats: () => fetchJSON<EventStats>("/events/stats"),
  ingestEvent: (data: { event_type: string; source: string; payload?: Record<string, unknown>; priority?: number }) =>
    fetchJSON<{ status: string; event_id: string }>("/events/ingest", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Chat
  chat: (message: string) =>
    fetchJSON<{ response: string; session_id: string; continuity_preserved: boolean }>("/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  // ─── Observability: Metrics ────────────────────────────────────────────

  getMetrics: () => fetchJSON<MetricsSummary>("/metrics"),
  getMetricsHistory: (metricName: string, limit = 100) =>
    fetchJSON<Array<{ timestamp: string; value: unknown }>>(
      `/metrics/history?metric_name=${encodeURIComponent(metricName)}&limit=${limit}`
    ),

  // ─── Observability: Traces ─────────────────────────────────────────────

  getTraces: (params?: { active?: boolean; event_type?: string; outcome?: string; source?: string; min_latency_ms?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.active) q.set("active", "true");
    if (params?.event_type) q.set("event_type", params.event_type);
    if (params?.outcome) q.set("outcome", params.outcome);
    if (params?.source) q.set("source", params.source);
    if (params?.min_latency_ms) q.set("min_latency_ms", String(params.min_latency_ms));
    if (params?.limit) q.set("limit", String(params.limit));
    return fetchJSON<Trace[]>(`/traces?${q}`);
  },
  getTrace: (traceId: string) => fetchJSON<Trace>(`/traces/${traceId}`),
  getTracesByObserver: (observerId: string, limit = 50) =>
    fetchJSON<Trace[]>(`/traces/observer/${observerId}?limit=${limit}`),

  // ─── Observability: Alerts ─────────────────────────────────────────────

  getAlerts: () => fetchJSON<Alert[]>("/alerts"),
  getAlertHistory: (limit = 100) => fetchJSON<Alert[]>(`/alerts/history?limit=${limit}`),
  acknowledgeAlert: (alertId: string) =>
    fetchJSON<{ ok: boolean; alert_id: string; state: string }>(`/alerts/${alertId}/acknowledge`, { method: "POST" }),
  addAlertRule: (data: Omit<AlertRule, "rule_id" | "created_at">) =>
    fetchJSON<{ ok: boolean; rule_id: string }>("/alerts/rules", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // ─── Observability: Dashboard ──────────────────────────────────────────

  getDashboard: () => fetchJSON<DashboardData>("/dashboard"),
};
