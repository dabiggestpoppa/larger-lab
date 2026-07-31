/**
 * Phase 4 — Repair ↔ Entropy Interaction
 * Models the counterforce dynamics between repair and entropy.
 */

export interface RepairEntropyBalance {
  zone: string;
  entropyForce: number;    // 0-1, how much entropy is pushing
  repairForce: number;     // 0-1, how much repair is countering
  netForce: number;        // positive = entropy winning, negative = repair winning
  stability: number;       // 0-1, how stable this zone is
}

export class RepairEntropyDynamics {
  /**
   * Compute the repair-entropy balance per zone.
   */
  computeBalance(
    observers: { zone: string; entropy: number; status: string }[],
    activeRepairs: { zone: string; strength: number }[]
  ): RepairEntropyBalance[] {
    const zones = [...new Set(observers.map((o) => o.zone))];
    const repairMap = new Map(activeRepairs.map((r) => [r.zone, r.strength]));

    return zones.map((zone) => {
      const zoneObs = observers.filter((o) => o.zone === zone);
      const avgEntropy = zoneObs.reduce((s, o) => s + o.entropy, 0) / zoneObs.length;
      const failedRatio = zoneObs.filter((o) => o.status === "failed" || o.status === "dormant").length / zoneObs.length;

      const entropyForce = avgEntropy * 0.6 + failedRatio * 0.4;
      const repairForce = (repairMap.get(zone) || 0) * (1 - failedRatio);
      const netForce = entropyForce - repairForce;
      const stability = Math.max(0, 1 - Math.abs(netForce));

      return { zone, entropyForce, repairForce, netForce, stability };
    });
  }

  /**
   * Determine if a zone needs repair intervention.
   */
  needsRepair(balance: RepairEntropyBalance): boolean {
    return balance.netForce > 0.3 && balance.stability < 0.5;
  }

  /**
   * Compute optimal repair allocation across zones.
   */
  allocateRepair(
    balances: RepairEntropyBalance[],
    totalRepairBudget: number
  ): Record<string, number> {
    const needsRepair = balances.filter((b) => this.needsRepair(b));
    if (needsRepair.length === 0) return {};

    const totalNeed = needsRepair.reduce((s, b) => s + b.netForce, 0);
    const allocation: Record<string, number> = {};

    for (const b of needsRepair) {
      allocation[b.zone] = (b.netForce / totalNeed) * totalRepairBudget;
    }

    return allocation;
  }
}
