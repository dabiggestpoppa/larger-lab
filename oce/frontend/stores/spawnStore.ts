import { create } from "zustand";

export type AgentLifecycleState = "pending" | "running" | "complete" | "failed" | "timeout" | "cancelled";

export interface SpawnAgent {
  agentId: string;
  planId: string;
  taskType: string;
  model: string;
  state: AgentLifecycleState;
  createdAt: string;
  startedAt?: string;
  endedAt?: string;
  turnsUsed: number;
  tokensUsed: number;
  groupId?: string;
  error?: string;
}

export interface SpawnTrace {
  traceId: string;
  agentId: string;
  taskType: string;
  model: string;
  status: string;
  tokensUsed: number;
  turnsUsed: number;
  durationSeconds: number;
  keyFindings: string[];
  timestamp: string;
}

export interface RuntimeLoad {
  activeAgents: number;
  maxAgents: number;
  totalTokens: number;
  avgDuration: number;
  successRate: number;
}

interface SpawnStore {
  agents: SpawnAgent[];
  traces: SpawnTrace[];
  runtimeLoad: RuntimeLoad;
  selectedAgentId: string | null;
  filterState: AgentLifecycleState | "all";
  registerAgent: (agent: SpawnAgent) => void;
  updateAgentState: (agentId: string, state: AgentLifecycleState, extra?: Partial<SpawnAgent>) => void;
  addTrace: (trace: SpawnTrace) => void;
  setSelectedAgent: (agentId: string | null) => void;
  setFilter: (filter: AgentLifecycleState | "all") => void;
  getActiveAgents: () => SpawnAgent[];
  getAgentsByState: (state: AgentLifecycleState) => SpawnAgent[];
  getAgentById: (agentId: string) => SpawnAgent | undefined;
  getTracesByAgent: (agentId: string) => SpawnTrace[];
  clearCompleted: () => void;
}

export const useSpawnStore = create<SpawnStore>((set, get) => ({
  agents: [],
  traces: [],
  runtimeLoad: { activeAgents: 0, maxAgents: 50, totalTokens: 0, avgDuration: 0, successRate: 100 },
  selectedAgentId: null,
  filterState: "all",

  registerAgent: (agent) =>
    set((s) => ({
      agents: [...s.agents, agent],
      runtimeLoad: {
        ...s.runtimeLoad,
        activeAgents: s.agents.filter((a) => a.state === "running" || a.state === "pending").length + 1,
      },
    })),

  updateAgentState: (agentId, state, extra) =>
    set((s) => {
      const agents = s.agents.map((a) =>
        a.agentId === agentId
          ? { ...a, state, endedAt: state !== "running" && state !== "pending" ? new Date().toISOString() : a.endedAt, ...extra }
          : a
      );
      return { agents, runtimeLoad: { ...s.runtimeLoad, activeAgents: agents.filter((a) => a.state === "running" || a.state === "pending").length } };
    }),

  addTrace: (trace) =>
    set((s) => {
      const traces = [...s.traces, trace];
      const totalTokens = traces.reduce((sum, t) => sum + t.tokensUsed, 0);
      const durations = traces.filter((t) => t.durationSeconds > 0).map((t) => t.durationSeconds);
      const avgDuration = durations.length > 0 ? durations.reduce((a, b) => a + b, 0) / durations.length : 0;
      const successCount = traces.filter((t) => t.status === "complete").length;
      return {
        traces,
        runtimeLoad: {
          ...s.runtimeLoad,
          totalTokens,
          avgDuration: Math.round(avgDuration * 10) / 10,
          successRate: traces.length > 0 ? Math.round((successCount / traces.length) * 100) : 100,
        },
      };
    }),

  setSelectedAgent: (agentId) => set({ selectedAgentId: agentId }),
  setFilter: (filter) => set({ filterState: filter }),
  getActiveAgents: () => get().agents.filter((a) => a.state === "running" || a.state === "pending"),
  getAgentsByState: (state) => get().agents.filter((a) => a.state === state),
  getAgentById: (agentId) => get().agents.find((a) => a.agentId === agentId),
  getTracesByAgent: (agentId) => get().traces.filter((t) => t.agentId === agentId),
  clearCompleted: () => set((s) => ({ agents: s.agents.filter((a) => a.state === "running" || a.state === "pending") })),
}));
