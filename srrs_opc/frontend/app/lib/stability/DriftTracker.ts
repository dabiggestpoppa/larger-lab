/**
 * Phase 4 — Drift Tracker
 * Observer drift tracking over time.
 */

export interface DriftRecord {
  observerId: string;
  timestamp: number;
  entropy: number;
  status: string;
  zone: string;
  dx: number; // Position change
  dy: number;
}

export interface DriftAnalysis {
  observerId: string;
  totalDrift: number;       // Total distance moved
  entropyTrend: number;     // Positive = increasing entropy
  statusChanges: number;    // How many times status changed
  currentZone: string;
  zonesVisited: string[];
  riskLevel: "low" | "medium" | "high";
}

export class DriftTracker {
  private records: Map<string, DriftRecord[]> = new Map();

  /**
   * Record an observer state snapshot.
   */
  record(observer: { id: string; entropy: number; status: string; zone: string; x: number; y: number }): void {
    const existing = this.records.get(observer.id) || [];
    const last = existing[existing.length - 1];

    const dx = last ? observer.x - last.entropy : 0;
    const dy = last ? observer.y - (last as any).y || 0 : 0;

    existing.push({
      observerId: observer.id,
      timestamp: Date.now(),
      entropy: observer.entropy,
      status: observer.status,
      zone: observer.zone,
      dx,
      dy,
    });

    // Keep last 100 records per observer
    if (existing.length > 100) existing.shift();
    this.records.set(observer.id, existing);
  }

  /**
   * Analyze drift for a specific observer.
   */
  analyze(observerId: string): DriftAnalysis | null {
    const records = this.records.get(observerId);
    if (!records || records.length < 2) return null;

    const totalDrift = records.reduce((sum, r) => sum + Math.sqrt(r.dx ** 2 + r.dy ** 2), 0);

    // Entropy trend (linear regression on last 10 points)
    const recent = records.slice(-10);
    const entropyTrend = this.computeTrend(recent.map((r) => r.entropy));

    // Status changes
    let statusChanges = 0;
    for (let i = 1; i < records.length; i++) {
      if (records[i].status !== records[i - 1].status) statusChanges++;
    }

    const zonesVisited = [...new Set(records.map((r) => r.zone))];
    const current = records[records.length - 1];

    let riskLevel: "low" | "medium" | "high" = "low";
    if (entropyTrend > 0.05 || totalDrift > 50) riskLevel = "medium";
    if (entropyTrend > 0.1 || totalDrift > 100 || statusChanges > 5) riskLevel = "high";

    return {
      observerId,
      totalDrift,
      entropyTrend,
      statusChanges,
      currentZone: current.zone,
      zonesVisited,
      riskLevel,
    };
  }

  /**
   * Get all drift analyses.
   */
  analyzeAll(): DriftAnalysis[] {
    return Array.from(this.records.keys())
      .map((id) => this.analyze(id))
      .filter((a): a is DriftAnalysis => a !== null)
      .sort((a, b) => {
        const riskOrder = { high: 0, medium: 1, low: 2 };
        return riskOrder[a.riskLevel] - riskOrder[b.riskLevel];
      });
  }

  private computeTrend(values: number[]): number {
    if (values.length < 2) return 0;
    const n = values.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = values.reduce((a, b) => a + b, 0);
    const sumXY = values.reduce((sum, y, x) => sum + x * y, 0);
    const sumXX = (n * (n - 1) * (2 * n - 1)) / 6;
    const denom = n * sumXX - sumX * sumX;
    if (denom === 0) return 0;
    return (n * sumXY - sumX * sumY) / denom;
  }
}
