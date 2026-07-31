// O7-F9: persistenceStore
// Zustand store for persistent field state.

import { create } from "zustand";

interface PersistentFieldState {
  // Runtime state
  runtimeStatus: {
    state: string;
    uptime_seconds: number;
    active_observers: number;
    entropy_level: number;
    continuity_score: number;
    total_restarts: number;
  } | null;

  // Heartbeat
  heartbeat: {
    field_state: string;
    entropy_level: number;
    observer_health: number;
    runtime_load: number;
    active_agents: number;
    continuity_score: number;
    timestamp: string;
  } | null;

  // Dormant state
  dormantState: {
    current_state: string;
    time_in_state_seconds: number;
    total_transitions: number;
  } | null;

  // Environment
  environment: {
    overall_status: string;
    metrics: Record<string, number>;
    alerts: Array<{ metric: string; value: number; status: string }>;
  } | null;

  // Repair
  repairStatus: {
    total_repairs: number;
    active_repairs: number;
    recent_success_rate: number;
  } | null;

  // Drift
  driftReport: {
    overall_status: string;
    metrics: Record<string, unknown>;
    alerts: Array<{ metric: string; status: string; deviation: number }>;
  } | null;

  // Scheduler
  schedulerStatus: {
    total_tasks: number;
    pending: number;
    running: number;
    due_now: number;
  } | null;

  // Continuity
  continuitySummary: {
    total_records: number;
    continuity_score: number;
    by_type: Record<string, number>;
  } | null;

  // Loading
  loading: boolean;
  error: string | null;

  // Actions
  fetchStatus: () => Promise<void>;
  fetchHeartbeat: () => Promise<void>;
  pulseHeartbeat: () => Promise<void>;
  fetchDormantState: () => Promise<void>;
  transitionState: (state: string, reason?: string) => Promise<void>;
  fetchEnvironment: () => Promise<void>;
  fetchRepairStatus: () => Promise<void>;
  triggerRepair: (action: string, target: string) => Promise<void>;
  fetchDriftReport: () => Promise<void>;
  fetchSchedulerStatus: () => Promise<void>;
  fetchContinuity: () => Promise<void>;
  fetchRecoveryStatus: () => Promise<void>;
  createSnapshot: (components: string[]) => Promise<void>;
}

const API_BASE = "";

export const usePersistenceStore = create<PersistentFieldState>((set, get) => ({
  runtimeStatus: null,
  heartbeat: null,
  dormantState: null,
  environment: null,
  repairStatus: null,
  driftReport: null,
  schedulerStatus: null,
  continuitySummary: null,
  loading: false,
  error: null,

  fetchStatus: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/persistent-field/status`);
      const data = await res.json();
      set({ runtimeStatus: data });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  fetchHeartbeat: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/persistent-field/heartbeat`);
      const data = await res.json();
      set({ heartbeat: data });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  pulseHeartbeat: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/persistent-field/heartbeat`, { method: "POST" });
      const data = await res.json();
      set({ heartbeat: data });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  fetchDormantState: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/persistent-field/dormant-state`);
      const data = await res.json();
      set({ dormantState: data });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  transitionState: async (state: string, reason?: string) => {
    try {
      await fetch(
        `${API_BASE}/api/persistent-field/dormant-state/transition?state=${state}&reason=${reason || ""}`,
        { method: "POST" }
      );
      await get().fetchDormantState();
    } catch (e) {
      set({ error: String(e) });
    }
  },

  fetchEnvironment: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/persistent-field/environment`);
      const data = await res.json();
      set({ environment: data });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  fetchRepairStatus: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/persistent-field/repair`);
      const data = await res.json();
      set({ repairStatus: data });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  triggerRepair: async (action: string, target: string) => {
    try {
      await fetch(
        `${API_BASE}/api/persistent-field/repair?action=${action}&target=${target}`,
        { method: "POST" }
      );
      await get().fetchRepairStatus();
    } catch (e) {
      set({ error: String(e) });
    }
  },

  fetchDriftReport: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/persistent-field/drift`);
      const data = await res.json();
      set({ driftReport: data });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  fetchSchedulerStatus: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/persistent-field/scheduler`);
      const data = await res.json();
      set({ schedulerStatus: data });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  fetchContinuity: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/persistent-field/continuity`);
      const data = await res.json();
      set({ continuitySummary: data });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  fetchRecoveryStatus: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/persistent-field/recovery`);
      const data = await res.json();
      // Could add recovery status to state if needed
    } catch (e) {
      set({ error: String(e) });
    }
  },

  createSnapshot: async (components: string[]) => {
    try {
      await fetch(`${API_BASE}/api/persistent-field/snapshot?components=${components.join(",")}`, {
        method: "POST",
      });
    } catch (e) {
      set({ error: String(e) });
    }
  },
}));
