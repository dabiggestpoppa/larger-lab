/* Edge type definitions for SRRA-OPH topology */

export type EdgeType = "routing" | "sync" | "repair" | "entropy" | "memory" | "field";

export interface EdgeStyle {
  color: string;
  width: number;
  dashArray?: string;
  opacity: number;
  animated: boolean;
}

export const EDGE_STYLES: Record<EdgeType, EdgeStyle> = {
  routing:  { color: "#6366f1", width: 1.5, opacity: 0.5, animated: true },
  sync:     { color: "#10b981", width: 2,   opacity: 0.6, animated: true },
  repair:   { color: "#06b6d4", width: 2.5, opacity: 0.7, animated: true },
  entropy:  { color: "#dc2626", width: 1,   opacity: 0.4, animated: false, dashArray: "4 2" },
  memory:   { color: "#8b5cf6", width: 1,   opacity: 0.3, animated: false },
  field:    { color: "#059669", width: 0.5, opacity: 0.2, animated: false },
};

export function getEdgeStyle(type: EdgeType, strength: number): EdgeStyle {
  const base = EDGE_STYLES[type];
  return {
    ...base,
    width: base.width * strength,
    opacity: Math.min(base.opacity * strength, 1),
  };
}
