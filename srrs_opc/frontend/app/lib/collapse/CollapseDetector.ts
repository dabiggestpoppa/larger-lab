/**
 * Phase 4 — Collapse Detector
 * Predictive collapse detection and criticality scoring.
 */

export interface CollapseRisk {
  zone: string;
  score: number;       // 0-1, higher = more likely to collapse
  factors: string[];
  timeToCollapse: number | null; // ms, null if not predicted
}

export class CollapseDetector {
  private history: { timestamp: number; zoneStates: Record<string, { entropy: number; failed: number; total: number }> }[] = [];

  /**
   * Record a snapshot for trend analysis.
   */
  recordSnapshot(observers: { zone: string; entropy: number; status: string }[]): void {
    const zones: Record<string, { entropy: number; failed: number; total: number }> = {};
    for (const obs of observers) {
      if (!zones[obs.zone]) zones[obs.zone] = { entropy: 0, failed: 0, total: 0 };
      zones[obs.zone].entropy += obs.entropy;
      zones[obs.zone].total++;
      if (obs.status === "failed" || obs.status === "dormant") {
        zones[obs.zone].failed++;
      }
    }
    // Average entropy per zone
    for (const zone of Object.keys(zones)) {
      zones[zone].entropy /= zones[zone].total;
    }

    this.history.push({ timestamp: Date.now(), zoneStates: zones });
    // Keep last 100 snapshots
    if (this.history.length > 100) this.history.shift();
  }

  /**
   * Analyze collapse risk per zone.
   */
  analyzeRisk(): CollapseRisk[] {
    if (this.history.length < 3) return [];

    const latest = this.history[this.history.length - 1];
    const risks: CollapseRisk[] = [];

    for (const [zone, state] of Object.entries(latest.zoneStates)) {
      const factors: string[] = [];
      let score = 0;

      // Factor 1: High entropy
      if (state.entropy > 0.6) {
        score += 0.3;
        factors.push(`High entropy: ${(state.entropy * 100).toFixed(0)}%`);
      }

      // Factor 2: Failed observer ratio
      const failRatio = state.failed / state.total;
      if (failRatio > 0.2) {
        score += 0.3;
        factors.push(`Failed observers: ${(failRatio * 100).toFixed(0)}%`);
      }

      // Factor 3: Entropy trend (increasing)
      const trend = this.getEntropyTrend(zone);
      if (trend > 0.01) {
        score += 0.2;
        factors.push(`Entropy increasing: +${(trend * 100).toFixed(1)}%/snapshot`);
      }

      // Factor 4: Recent collapse in nearby zone
      const nearbyCollapse = this.history.slice(-5).some(
        (h) => Object.entries(h.zoneStates).some(
          ([z, s]) => z !== zone && s.failed / s.total > 0.5
        )
      );
      if (nearbyCollapse) {
        score += 0.2;
        factors.push("Nearby zone collapse detected");
      }

      // Predict time to collapse
      let timeToCollapse: number | null = null;
      if (score > 0.5 && trend > 0) {
        const snapshotsToCollapse = Math.ceil((1 - state.entropy) / trend);
        timeToCollapse = snapshotsToCollapse * 2000; // Assume 2s per snapshot
      }

      risks.push({
        zone,
        score: Math.min(1, score),
        factors,
        timeToCollapse,
      });
    }

    return risks.sort((a, b) => b.score - a.score);
  }

  private getEntropyTrend(zone: string): number {
    if (this.history.length < 3) return 0;
    const recent = this.history.slice(-5);
    const entropies = recent.map((h) => h.zoneStates[zone]?.entropy || 0);
    if (entropies.length < 2) return 0;
    // Simple linear regression slope
    const n = entropies.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = entropies.reduce((a, b) => a + b, 0);
    const sumXY = entropies.reduce((sum, y, x) => sum + x * y, 0);
    const sumXX = (n * (n - 1) * (2 * n - 1)) / 6;
    const denom = n * sumXX - sumX * sumX;
    if (denom === 0) return 0;
    return (n * sumXY - sumX * sumY) / denom;
  }
}
