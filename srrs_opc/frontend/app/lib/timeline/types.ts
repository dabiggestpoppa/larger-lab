/**
 * Phase 3 — Temporal Playback Types
 * Core type definitions for the timeline engine.
 */

export type ObserverState = {
  id: string;
  status: "active" | "synced" | "isolated" | "entropic" | "repairing" | "dormant" | "failed";
  entropy: number;
  zone: string;
  x: number;
  y: number;
};

export type EdgeState = {
  source: string;
  target: string;
  type: string;
  weight: number;
  active: boolean;
};

export type TimelineEvent = {
  id: string;
  type: "PERTURBATION" | "REPAIR_TRIGGER" | "REPAIR_PROPAGATION" | "SYNC_COLLAPSE" | "SYNC_RESTORE" | "ENTROPY_SPIKE" | "ROUTING_SHIFT" | "OBSERVER_FAILURE" | "ATTRACTOR_FORMATION";
  timestamp: number;
  source: string;
  target?: string;
  entropyDelta: number;
  continuityScore: number;
  fieldZone: string;
};

export type RuntimeFrame = {
  frameId: string;
  timestamp: number;
  topologySnapshot: { nodes: ObserverState[]; edges: EdgeState[] };
  entropySnapshot: { local: number; cluster: number; global: number };
  repairSnapshot: { active: TimelineEvent[]; completed: TimelineEvent[] };
  events: TimelineEvent[];
  observerStates: Record<string, ObserverState>;
};

export type PlaybackState = {
  isPlaying: boolean;
  isReversed: boolean;
  speed: number; // 0.25 to 10
  currentFrame: number;
  totalFrames: number;
  loop: boolean;
};
