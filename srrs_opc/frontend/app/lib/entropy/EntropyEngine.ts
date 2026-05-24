/**
 * Phase 4 — Entropy Engine
 * Entropy computation and field stress calculation.
 */

export interface EntropyMetrics {
  local: number;   // Per-observer entropy (0-1)
  cluster: number; // Per-cluster entropy (0-1)
  global: number;  // System-wide entropy (0-1)
}

export interface FieldStress {
  zone: string;
  pressure: number;    // 0-1, how much stress this zone is under
  coherence: number;   // 0-1, how coherent this zone is
  drift: number;       // Rate of entropy change
}

export class EntropyEngine {
  /**
   * Compute entropy metrics from observer states.
   */
  computeMetrics(observers: { entropy: number; zone: string }[]): EntropyMetrics {
    if (observers.length === 0) return { local: 0, cluster: 0, global: 0 };

    const local = observers.reduce((sum, o) => sum + o.entropy, 0) / observers.length;

    // Cluster entropy: group by zone
    const zones: Record<string, number[]> = {};
    for (const obs of observers) {
      if (!zones[obs.zone]) zones[obs.zone] = [];
      zones[obs.zone].push(obs.entropy);
    }
    const zoneEntropies = Object.values(zones).map((ents) =>
      ents.reduce((a, b) => a + b, 0) / ents.length
    );
    const cluster = zoneEntropies.reduce((a, b) => a + b, 0) / zoneEntropies.length;

    // Global: weighted combination
    const global = local * 0.4 + cluster * 0.6;

    return { local, cluster, global };
  }

  /**
   * Compute field stress per zone.
   */
  computeFieldStress(
    observers: { entropy: number; zone: string; status: string }[]
  ): FieldStress[] {
    const zones: Record<string, { entropies: number[]; statuses: string[] }> = {};
    for (const obs of observers) {
      if (!zones[obs.zone]) zones[obs.zone] = { entropies: [], statuses: [] };
      zones[obs.zone].entropies.push(obs.entropy);
      zones[obs.zone].statuses.push(obs.status);
    }

    return Object.entries(zones).map(([zone, data]) => {
      const avgEntropy = data.entropies.reduce((a, b) => a + b, 0) / data.entropies.length;
      const failedCount = data.statuses.filter((s) => s === "failed" || s === "dormant").length;
      const coherence = 1 - failedCount / data.statuses.length;
      return {
        zone,
        pressure: avgEntropy,
        coherence,
        drift: avgEntropy * (1 - coherence), // High entropy + low coherence = high drift
      };
    });
  }

  /**
   * Compute stability index (0-1, higher = more stable).
   */
  stabilityIndex(metrics: EntropyMetrics): number {
    return 1 - (metrics.local * 0.3 + metrics.cluster * 0.3 + metrics.global * 0.4);
  }
}
