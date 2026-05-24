/* Observer state machine for SRRA-OPH topology */

export type ObserverStatus =
  | "active"
  | "synced"
  | "isolated"
  | "entropic"
  | "repairing"
  | "dormant"
  | "failed";

export interface ObserverStateConfig {
  color: string;
  glow: string;
  pulse: boolean;
  dim: boolean;
  label: string;
}

export const OBSERVER_STATUSES: Record<ObserverStatus, ObserverStateConfig> = {
  active:   { color: "#22d3ee", glow: "#22d3ee", pulse: true,  dim: false, label: "Active" },
  synced:   { color: "#10b981", glow: "#10b981", pulse: false, dim: false, label: "Synced" },
  isolated: { color: "#4b5563", glow: "none",     pulse: false, dim: true,  label: "Isolated" },
  entropic: { color: "#dc2626", glow: "#dc2626", pulse: true,  dim: false, label: "Entropic" },
  repairing:{ color: "#06b6d4", glow: "#06b6d4", pulse: true,  dim: false, label: "Repairing" },
  dormant:  { color: "#374151", glow: "none",     pulse: false, dim: true,  label: "Dormant" },
  failed:   { color: "#6b7280", glow: "none",     pulse: false, dim: true,  label: "Failed" },
};

export function getObserverStyle(status: ObserverStatus): ObserverStateConfig {
  return OBSERVER_STATUSES[status] || OBSERVER_STATUSES.dormant;
}

/** Determine observer status from runtime metrics */
export function computeObserverStatus(entropy: number, syncScore: number, repairState: string): ObserverStatus {
  if (repairState === "active") return "repairing";
  if (entropy > 0.7) return "entropic";
  if (syncScore < 0.3) return "isolated";
  if (syncScore > 0.8) return "synced";
  if (entropy < 0.3 && syncScore > 0.5) return "active";
  return "dormant";
}
