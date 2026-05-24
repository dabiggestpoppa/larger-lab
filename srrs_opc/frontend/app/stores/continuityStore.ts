/**
 * Phase 5 — Continuity Store
 */
import { create } from "zustand";

interface Checkpoint {
  id: string;
  timestamp: string;
  status: "PASS" | "FAIL";
  drift_score: number;
  observer_health: { alive: number; degraded: number; dead: number };
  elapsed_hours: number;
}

interface ContinuityStore {
  checkpoints: Checkpoint[];
  currentDrift: number;
  observerHealth: { alive: number; degraded: number; dead: number } | null;
  isRunning: boolean;
  elapsedHours: number;
  totalHours: number;

  addCheckpoint: (cp: Checkpoint) => void;
  setCurrentDrift: (drift: number) => void;
  setObserverHealth: (health: { alive: number; degraded: number; dead: number }) => void;
  loadFromAPI: () => Promise<void>;
}

export const useContinuityStore = create<ContinuityStore>((set) => ({
  checkpoints: [],
  currentDrift: 0,
  observerHealth: null,
  isRunning: false,
  elapsedHours: 0,
  totalHours: 72,

  addCheckpoint: (cp) => set((s) => ({ checkpoints: [...s.checkpoints, cp] })),
  setCurrentDrift: (drift) => set({ currentDrift: drift }),
  setObserverHealth: (health) => set({ observerHealth: health }),

  loadFromAPI: async () => {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      set({
        observerHealth: { alive: data.observers || 0, degraded: 0, dead: 0 },
        isRunning: true,
      });
    } catch (err) {
      console.error("Failed to load continuity:", err);
    }
  },
}));
