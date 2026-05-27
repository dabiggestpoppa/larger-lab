import { create } from "zustand";

export type ObserverHealthStatus = "healthy" | "degraded" | "recovering" | "failed";

export interface ObserverStateData {
  observerId: string;
  status: ObserverHealthStatus;
  continuityScore: number;
  activeTask: string | null;
  activeAgents: string[];
  runtimeState: Record<string, unknown>;
  entropyState: {
    level: number;
    trend: "rising" | "falling" | "stable";
  };
  repairState: {
    active: boolean;
    targets: string[];
  };
  lastUpdated: string;
  requestCount: number;
}

interface ObserverStore {
  // State
  observer: ObserverStateData;
  events: Array<{
    eventType: string;
    source: string;
    timestamp: string;
    data: Record<string, unknown>;
  }>;
  sessions: Array<{
    sessionId: string;
    status: string;
    taskCount: number;
    lastActive: string;
  }>;

  // Actions
  setObserverState: (update: Partial<ObserverStateData>) => void;
  setHealth: (status: ObserverHealthStatus) => void;
  setContinuityScore: (score: number) => void;
  setActiveTask: (taskId: string | null) => void;
  addActiveAgent: (agentId: string) => void;
  removeActiveAgent: (agentId: string) => void;
  setRuntimeState: (key: string, value: unknown) => void;
  setEntropy: (level: number, trend: "rising" | "falling" | "stable") => void;
  setRepair: (active: boolean, targets?: string[]) => void;
  addEvent: (event: { eventType: string; source: string; timestamp: string; data: Record<string, unknown> }) => void;
  setSessions: (sessions: ObserverStore["sessions"]) => void;
  reset: () => void;
}

const defaultObserverState: ObserverStateData = {
  observerId: "primary_observer",
  status: "healthy",
  continuityScore: 1.0,
  activeTask: null,
  activeAgents: [],
  runtimeState: {},
  entropyState: {
    level: 0,
    trend: "stable",
  },
  repairState: {
    active: false,
    targets: [],
  },
  lastUpdated: new Date().toISOString(),
  requestCount: 0,
};

export const useObserverStore = create<ObserverStore>((set) => ({
  observer: defaultObserverState,
  events: [],
  sessions: [],

  setObserverState: (update) =>
    set((state) => ({
      observer: {
        ...state.observer,
        ...update,
        lastUpdated: new Date().toISOString(),
      },
    })),

  setHealth: (status) =>
    set((state) => ({
      observer: {
        ...state.observer,
        status,
        lastUpdated: new Date().toISOString(),
      },
    })),

  setContinuityScore: (score) =>
    set((state) => ({
      observer: {
        ...state.observer,
        continuityScore: Math.max(0, Math.min(1, score)),
        lastUpdated: new Date().toISOString(),
      },
    })),

  setActiveTask: (taskId) =>
    set((state) => ({
      observer: {
        ...state.observer,
        activeTask: taskId,
        lastUpdated: new Date().toISOString(),
      },
    })),

  addActiveAgent: (agentId) =>
    set((state) => ({
      observer: {
        ...state.observer,
        activeAgents: [...state.observer.activeAgents, agentId],
        lastUpdated: new Date().toISOString(),
      },
    })),

  removeActiveAgent: (agentId) =>
    set((state) => ({
      observer: {
        ...state.observer,
        activeAgents: state.observer.activeAgents.filter((a) => a !== agentId),
        lastUpdated: new Date().toISOString(),
      },
    })),

  setRuntimeState: (key, value) =>
    set((state) => ({
      observer: {
        ...state.observer,
        runtimeState: { ...state.observer.runtimeState, [key]: value },
        lastUpdated: new Date().toISOString(),
      },
    })),

  setEntropy: (level, trend) =>
    set((state) => ({
      observer: {
        ...state.observer,
        entropyState: { level, trend },
        lastUpdated: new Date().toISOString(),
      },
    })),

  setRepair: (active, targets = []) =>
    set((state) => ({
      observer: {
        ...state.observer,
        repairState: { active, targets },
        lastUpdated: new Date().toISOString(),
      },
    })),

  addEvent: (event) =>
    set((state) => ({
      events: [...state.events, event].slice(-100),
    })),

  setSessions: (sessions) => set({ sessions }),

  reset: () =>
    set({
      observer: defaultObserverState,
      events: [],
      sessions: [],
    }),
}));
