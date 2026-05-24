import { create } from "zustand";

export type AgentStatus = "alive" | "degraded" | "dead" | "standby";

export interface Agent {
  id: string;
  name: string;
  tag: string;
  role: string;
  status: AgentStatus;
  currentTask: string;
  tasksCompleted: number;
  errors: number;
  uptimeHours: number;
  lastHeartbeat: string;
}

interface AgentStore {
  agents: Agent[];
  setAgents: (agents: Agent[]) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  getAliveAgents: () => Agent[];
  getAgentsByStatus: (status: AgentStatus) => Agent[];
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  agents: [],
  setAgents: (agents) => set({ agents }),
  updateAgent: (id, updates) =>
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, ...updates } : a)),
    })),
  getAliveAgents: () => get().agents.filter((a) => a.status === "alive"),
  getAgentsByStatus: (status) => get().agents.filter((a) => a.status === status),
}));
