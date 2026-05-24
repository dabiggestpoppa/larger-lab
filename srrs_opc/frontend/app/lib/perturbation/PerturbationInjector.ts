/**
 * Phase 4 — Perturbation Injector
 * Controlled chaos injection for testing system resilience.
 */

export type PerturbationType =
  | "NODE_FAILURE"
  | "SYNC_BREAK"
  | "ROUTING_CORRUPTION"
  | "MEMORY_LOSS"
  | "SIGNAL_DELAY"
  | "REPAIR_BLOCK"
  | "FIELD_DISTORTION"
  | "CASCADE_STRESS";

export type ChaosProfile = {
  name: string;
  perturbations: { type: PerturbationType; target: string; magnitude: number }[];
  duration: number; // ms
  cooldown: number; // ms
};

export class PerturbationInjector {
  private activePerturbations: Map<string, { type: PerturbationType; expiresAt: number }> = new Map();

  /**
   * Inject a perturbation into the system.
   */
  inject(type: PerturbationType, target: string, magnitude: number, duration: number): void {
    const key = `${type}_${target}`;
    this.activePerturbations.set(key, {
      type,
      expiresAt: Date.now() + duration,
    });
  }

  /**
   * Apply a chaos profile (multiple perturbations).
   */
  applyProfile(profile: ChaosProfile): void {
    for (const p of profile.perturbations) {
      this.inject(p.type, p.target, p.magnitude, profile.duration);
    }
  }

  /**
   * Get current perturbation state for an observer.
   */
  getObserverState(observerId: string): { type: PerturbationType; remaining: number } | null {
    for (const [key, state] of this.activePerturbations) {
      if (key.includes(observerId) || key.includes("FIELD_DISTORTION") || key.includes("CASCADE_STRESS")) {
        const remaining = Math.max(0, state.expiresAt - Date.now());
        if (remaining > 0) {
          return { type: state.type, remaining };
        }
      }
    }
    return null;
  }

  /**
   * Clear expired perturbations.
   */
  cleanup(): void {
    const now = Date.now();
    for (const [key, state] of this.activePerturbations) {
      if (state.expiresAt <= now) {
        this.activePerturbations.delete(key);
      }
    }
  }

  /**
   * Get all active perturbations.
   */
  getActive(): { key: string; type: PerturbationType; remainingMs: number }[] {
    const now = Date.now();
    return Array.from(this.activePerturbations.entries())
      .filter(([, s]) => s.expiresAt > now)
      .map(([key, s]) => ({
        key,
        type: s.type,
        remainingMs: s.expiresAt - now,
      }));
  }

  /**
   * Predefined chaos profiles.
   */
  static profiles: Record<string, ChaosProfile> = {
    gentle: {
      name: "Gentle Stress",
      perturbations: [
        { type: "SIGNAL_DELAY", target: "zone_0", magnitude: 0.3, duration: 5000 },
      { type: "SYNC_BREAK", target: "zone_1", magnitude: 0.2, duration: 3000 },
      ],
      duration: 5000,
      cooldown: 10000,
    },
    moderate: {
      name: "Moderate Chaos",
      perturbations: [
        { type: "NODE_FAILURE", target: "zone_0", magnitude: 0.5, duration: 8000 },
        { type: "ROUTING_CORRUPTION", target: "zone_2", magnitude: 0.4, duration: 6000 },
        { type: "MEMORY_LOSS", target: "zone_1", magnitude: 0.3, duration: 5000 },
      ],
      duration: 8000,
      cooldown: 15000,
    },
    severe: {
      name: "Severe Cascade",
      perturbations: [
        { type: "CASCADE_STRESS", target: "all", magnitude: 0.8, duration: 15000 },
        { type: "FIELD_DISTORTION", target: "all", magnitude: 0.7, duration: 12000 },
        { type: "REPAIR_BLOCK", target: "repair_0", magnitude: 0.6, duration: 10000 },
      ],
      duration: 15000,
      cooldown: 30000,
    },
  };
}
