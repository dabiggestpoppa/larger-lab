/**
 * Phase 4 — Entropy Store
 * Zustand store for entropy field data.
 */
import { create } from "zustand";
import { EntropyEngine, EntropyMetrics, FieldStress } from "../lib/entropy/EntropyEngine";

interface EntropyStore {
  metrics: EntropyMetrics;
  fieldStress: (FieldStress & { x: number; y: number })[];
  globalEntropy: number;
  history: { timestamp: number; metrics: EntropyMetrics }[];
  engine: EntropyEngine;

  updateFromFrame: (observerStates: Record<string, any>) => void;
  loadFromAPI: () => Promise<void>;
}

export const useEntropyStore = create<EntropyStore>((set, get) => ({
  metrics: { local: 0, cluster: 0, global: 0 },
  fieldStress: [],
  globalEntropy: 0,
  history: [],
  engine: new EntropyEngine(),

  updateFromFrame: (observerStates) => {
    const observers = Object.values(observerStates).map((o: any) => ({
      entropy: o.entropy || 0,
      zone: o.zone || "default",
      status: o.status || "active",
    }));

    const metrics = get().engine.computeMetrics(observers);
    const stress = get().engine.computeFieldStress(observers);

    // Position zones on canvas (simplified grid)
    const zones = [...new Set(observers.map((o) => o.zone))];
    const fieldStress = stress.map((s, i) => ({
      ...s,
      x: 15 + (i % 3) * 35,
      y: 20 + Math.floor(i / 3) * 30,
    }));

    set({
      metrics,
      fieldStress,
      globalEntropy: metrics.global,
      history: [
        ...get().history.slice(-99),
        { timestamp: Date.now(), metrics },
      ],
    });
  },

  loadFromAPI: async () => {
    try {
      const res = await fetch("/api/entropy/timeseries");
      const data = await res.json();
      const timeseries = data.timeseries || [];
      if (timeseries.length > 0) {
        const latest = timeseries[timeseries.length - 1];
        set({ globalEntropy: latest.entropy_after || 0 });
      }
    } catch (err) {
      console.error("Failed to load entropy:", err);
    }
  },
}));
