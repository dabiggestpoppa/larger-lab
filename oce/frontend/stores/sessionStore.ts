import { create } from "zustand";

export interface ExperimentSession {
  id: string;
  name: string;
  type: string;
  status: "running" | "completed" | "failed";
  startTime: string;
  endTime?: string;
  cycles: number;
  amplification: number;
  passRate: number;
}

interface SessionStore {
  sessions: ExperimentSession[];
  currentSession: string | null;
  setCurrentSession: (id: string | null) => void;
  addSession: (session: Omit<ExperimentSession, "id">) => void;
  updateSession: (id: string, updates: Partial<ExperimentSession>) => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessions: [
    { id: "sess-001", name: "Chaos v2 5X", type: "chaos", status: "running", startTime: "2026-05-23T08:13:00Z", cycles: 6, amplification: 1.86, passRate: 100 },
    { id: "sess-002", name: "Chaos v1 20X", type: "chaos", status: "completed", startTime: "2026-05-22T10:00:00Z", endTime: "2026-05-22T15:00:00Z", cycles: 28, amplification: 1.14, passRate: 100 },
    { id: "sess-003", name: "Contradiction Injection", type: "semantic", status: "completed", startTime: "2026-05-23T10:00:00Z", endTime: "2026-05-23T14:00:00Z", cycles: 9, amplification: 0, passRate: 100 },
    { id: "sess-004", name: "72h Continuity", type: "stability", status: "running", startTime: "2026-05-22T23:46:00Z", cycles: 1, amplification: 0, passRate: 100 },
  ],
  currentSession: null,
  setCurrentSession: (id) => set({ currentSession: id }),
  addSession: (session) =>
    set((state) => ({
      sessions: [...state.sessions, { ...session, id: `sess-${Date.now()}` }],
    })),
  updateSession: (id, updates) =>
    set((state) => ({
      sessions: state.sessions.map((s) => (s.id === id ? { ...s, ...updates } : s)),
    })),
}));
