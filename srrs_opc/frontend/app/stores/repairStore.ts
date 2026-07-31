/**
 * Phase 5 — Repair Store
 * Zustand store for repair state.
 */
import { create } from "zustand";

interface RepairEvent {
  id: string;
  source: string;
  target: string;
  type: "trigger" | "propagation" | "complete" | "fail";
  timestamp: number;
  strength: number;
}

interface RepairStore {
  activeRepairs: RepairEvent[];
  completedRepairs: RepairEvent[];
  failedRepairs: RepairEvent[];
  saturationLevel: number;

  addRepair: (repair: RepairEvent) => void;
  completeRepair: (id: string) => void;
  failRepair: (id: string) => void;
  setSaturation: (level: number) => void;
  loadFromAPI: () => Promise<void>;
}

export const useRepairStore = create<RepairStore>((set, get) => ({
  activeRepairs: [],
  completedRepairs: [],
  failedRepairs: [],
  saturationLevel: 0,

  addRepair: (repair) =>
    set((s) => ({ activeRepairs: [...s.activeRepairs, repair] })),

  completeRepair: (id) =>
    set((s) => {
      const repair = s.activeRepairs.find((r) => r.id === id);
      return {
        activeRepairs: s.activeRepairs.filter((r) => r.id !== id),
        completedRepairs: repair
          ? [...s.completedRepairs, { ...repair, type: "complete" as const }]
          : s.completedRepairs,
      };
    }),

  failRepair: (id) =>
    set((s) => {
      const repair = s.activeRepairs.find((r) => r.id === id);
      return {
        activeRepairs: s.activeRepairs.filter((r) => r.id !== id),
        failedRepairs: repair
          ? [...s.failedRepairs, { ...repair, type: "fail" as const }]
          : s.failedRepairs,
      };
    }),

  setSaturation: (level) => set({ saturationLevel: Math.max(0, Math.min(1, level)) }),

  loadFromAPI: async () => {
    try {
      const res = await fetch("/api/repair/chains");
      const data = await res.json();
      const active: RepairEvent[] = [];
      const completed: RepairEvent[] = [];
      const failed: RepairEvent[] = [];
      for (const chain of data.chains || []) {
        for (const evt of chain.events || []) {
          const repair: RepairEvent = {
            id: evt.id || `repair_${Math.random().toString(36).slice(8)}`,
            source: evt.source || "",
            target: evt.target || "",
            type: evt.repair_triggered ? "trigger" : "propagation",
            timestamp: new Date(evt.timestamp).getTime(),
            strength: Math.abs(evt.entropy_delta || 0),
          };
          if (evt.event_type === "repair_complete") completed.push(repair);
          else if (evt.event_type === "repair_fail") failed.push(repair);
          else active.push(repair);
        }
      }
      set({ activeRepairs: active, completedRepairs: completed, failedRepairs: failed });
    } catch (err) {
      console.error("Failed to load repair data:", err);
    }
  },
}));
