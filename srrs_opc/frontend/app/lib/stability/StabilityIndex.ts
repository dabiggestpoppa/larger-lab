/**
 * Phase 4 — Stability Index
 * Stability scoring and coherence mapping.
 */

export interface CoherenceRegion {
  zone: string;
  coherence: number;    // 0-1
  observers: string[];
  centerX: number;
  centerY: number;
  radius: number;
}

export interface ResilienceZone {
  zone: string;
  type: "fragile" | "stable" | "critical";
  score: number;
  recommendations: string[];
}

export class StabilityIndex {
  /**
   * Map coherence regions from observer states.
   */
  mapCoherenceRegions(
    observers: { id: string; zone: string; x: number; y: number; status: string; entropy: number }[]
  ): CoherenceRegion[] {
    const zones: Record<string, typeof observers> = {};
    for (const obs of observers) {
      if (!zones[obs.zone]) zones[obs.zone] = [];
      zones[obs.zone].push(obs);
    }

    return Object.entries(zones).map(([zone, obs]) => {
      const activeCount = obs.filter((o) => o.status === "active" || o.status === "synced").length;
      const coherence = activeCount / obs.length;
      const avgEntropy = obs.reduce((s, o) => s + o.entropy, 0) / obs.length;

      const centerX = obs.reduce((s, o) => s + o.x, 0) / obs.length;
      const centerY = obs.reduce((s, o) => s + o.y, 0) / obs.length;

      // Radius based on spread
      const maxDist = Math.max(...obs.map((o) => Math.sqrt((o.x - centerX) ** 2 + (o.y - centerY) ** 2)));

      return {
        zone,
        coherence: coherence * (1 - avgEntropy),
        observers: obs.map((o) => o.id),
        centerX,
        centerY,
        radius: Math.max(20, maxDist + 10),
      };
    });
  }

  /**
   * Detect fragile and stable zones.
   */
  detectResilienceZones(
    observers: { zone: string; entropy: number; status: string }[]
  ): ResilienceZone[] {
    const zones: Record<string, { entropies: number[]; statuses: string[] }> = {};
    for (const obs of observers) {
      if (!zones[obs.zone]) zones[obs.zone] = { entropies: [], statuses: [] };
      zones[obs.zone].entropies.push(obs.entropy);
      zones[obs.zone].statuses.push(obs.status);
    }

    return Object.entries(zones).map(([zone, data]) => {
      const avgEntropy = data.entropies.reduce((a, b) => a + b, 0) / data.entropies.length;
      const failedRatio = data.statuses.filter((s) => s === "failed" || s === "dormant").length / data.statuses.length;
      const score = 1 - (avgEntropy * 0.5 + failedRatio * 0.5);

      let type: "fragile" | "stable" | "critical";
      const recommendations: string[] = [];

      if (score < 0.3) {
        type = "critical";
        recommendations.push("Immediate repair intervention needed");
        recommendations.push("Consider observer redistribution");
      } else if (score < 0.6) {
        type = "fragile";
        recommendations.push("Monitor closely");
        recommendations.push("Prepare repair patches");
      } else {
        type = "stable";
        recommendations.push("Zone is healthy");
      }

      return { zone, type, score, recommendations };
    });
  }
}
