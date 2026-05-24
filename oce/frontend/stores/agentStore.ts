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
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  getAliveAgents: () => Agent[];
  getAgentsByStatus: (status: AgentStatus) => Agent[];
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  agents: [
    { id: "cc", name: "Claude Code", tag: "CC", role: "Overseer / Architecture", status: "alive", currentTask: "Phase 11.3 Adversarial Drift", tasksCompleted: 1460, errors: 0, uptimeHours: 168, lastHeartbeat: "2026-05-24T12:00:00Z" },
    { id: "as", name: "Assistant Manager", tag: "AS", role: "Quality / Docs / Frontend", status: "alive", currentTask: "OCE Frontend Build", tasksCompleted: 47, errors: 0, uptimeHours: 72, lastHeartbeat: "2026-05-24T12:00:00Z" },
    { id: "pm1", name: "Polymorph", tag: "PM1", role: "Debugger / Tools", status: "alive", currentTask: "Phase 11 Test Infrastructure", tasksCompleted: 89, errors: 2, uptimeHours: 120, lastHeartbeat: "2026-05-24T12:00:00Z" },
    { id: "pm2", name: "Polymorph 2", tag: "PM2", role: "Experimental Track", status: "alive", currentTask: "Topology Snapshot Analysis", tasksCompleted: 34, errors: 1, uptimeHours: 48, lastHeartbeat: "2026-05-24T12:00:00Z" },
    { id: "rl", name: "Research Lead", tag: "RL", role: "Research / DSPy", status: "standby", currentTask: "None", tasksCompleted: 23, errors: 0, uptimeHours: 0, lastHeartbeat: "2026-05-23T18:00:00Z" },
    { id: "oc2", name: "OWL Copilot", tag: "OC2", role: "Execution / Testing", status: "alive", currentTask: "Phase 11.2 Chaos v2", tasksCompleted: 112, errors: 3, uptimeHours: 96, lastHeartbeat: "2026-05-24T12:00:00Z" },
    { id: "copilot", name: "Copilot", tag: "CP", role: "Test Monitoring", status: "alive", currentTask: "72h Continuity Test", tasksCompleted: 28, errors: 0, uptimeHours: 144, lastHeartbeat: "2026-05-24T12:00:00Z" },
  ],
  updateAgent: (id, updates) =>
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, ...updates } : a)),
    })),
  getAliveAgents: () => get().agents.filter((a) => a.status === "alive"),
  getAgentsByStatus: (status) => get().agents.filter((a) => a.status === status),
}));
