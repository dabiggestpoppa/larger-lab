/**
 * Session Store
 * Zustand store for session state.
 */
import { create } from "zustand";

interface Session {
  sessionId: string;
  status: "active" | "paused" | "ended";
  taskCount: number;
  lastActive: string;
}

interface SessionStore {
  sessions: Session[];
  currentSession: Session | null;
  setSessions: (sessions: Session[]) => void;
  setCurrentSession: (session: Session | null) => void;
  addSession: (session: Session) => void;
  loadFromAPI: () => Promise<void>;
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessions: [],
  currentSession: null,
  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (session) => set({ currentSession: session }),
  addSession: (session) => set((s) => ({ sessions: [...s.sessions, session] })),
  loadFromAPI: async () => {
    try {
      const res = await fetch("/api/sessions");
      const data = await res.json();
      set({ sessions: data.sessions || [] });
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  },
}));