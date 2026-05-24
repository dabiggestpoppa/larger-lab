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
  setSessions: (sessions: ExperimentSession[]) => void;
  currentSession: string | null;
  setCurrentSession: (id: string | null) => void;
  addSession: (session: Omit<ExperimentSession, "id">) => void;
  updateSession: (id: string, updates: Partial<ExperimentSession>) => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessions: [],
  setSessions: (sessions) => set({ sessions }),
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
