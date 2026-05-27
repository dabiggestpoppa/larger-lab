import { create } from "zustand";

export interface TraceEntry {
  id: string;
  type: "task" | "routing" | "failure" | "entropy" | "spawn" | "topology" | "repair" | "consensus";
  timestamp: string;
  data: Record<string, unknown>;
}

export interface WorkflowPattern {
  id: string;
  domain: string;
  sequence: string[];
  frequency: number;
  successRate: number;
  lastSeen: string;
}

export interface RoutingImprovement {
  domain: string;
  previousModel: string;
  currentModel: string;
  improvementScore: number;
  timestamp: string;
}

export interface FailureRecord {
  id: string;
  type: "routing" | "entropy" | "topology" | "repair" | "context";
  description: string;
  timestamp: string;
  resolved: boolean;
}

export interface LearningState {
  // State
  traces: TraceEntry[];
  workflowPatterns: WorkflowPattern[];
  routingImprovements: RoutingImprovement[];
  failures: FailureRecord[];
  observerSpecializations: Record<string, number>;
  topologyClusters: Array<{ id: string; stability: number; entropy: number }>;
  adaptationEvents: Array<{ id: string; type: string; impact: number; timestamp: string }>;
  isReplaying: boolean;
  replayIndex: number;

  // Actions
  addTrace: (trace: TraceEntry) => void;
  setWorkflowPatterns: (patterns: WorkflowPattern[]) => void;
  addRoutingImprovement: (improvement: RoutingImprovement) => void;
  addFailure: (failure: FailureRecord) => void;
  resolveFailure: (id: string) => void;
  setObserverSpecialization: (observerId: string, score: number) => void;
  setTopologyClusters: (clusters: LearningState["topologyClusters"]) => void;
  addAdaptationEvent: (event: LearningState["adaptationEvents"][0]) => void;
  setReplaying: (replaying: boolean) => void;
  setReplayIndex: (index: number) => void;
  reset: () => void;
}

export const useLearningStore = create<LearningState>((set) => ({
  traces: [],
  workflowPatterns: [],
  routingImprovements: [],
  failures: [],
  observerSpecializations: {},
  topologyClusters: [],
  adaptationEvents: [],
  isReplaying: false,
  replayIndex: 0,

  addTrace: (trace) =>
    set((state) => ({
      traces: [...state.traces, trace].slice(-200),
    })),

  setWorkflowPatterns: (patterns) => set({ workflowPatterns: patterns }),

  addRoutingImprovement: (improvement) =>
    set((state) => ({
      routingImprovements: [...state.routingImprovements, improvement].slice(-50),
    })),

  addFailure: (failure) =>
    set((state) => ({
      failures: [...state.failures, failure].slice(-50),
    })),

  resolveFailure: (id) =>
    set((state) => ({
      failures: state.failures.map((f) =>
        f.id === id ? { ...f, resolved: true } : f
      ),
    })),

  setObserverSpecialization: (observerId, score) =>
    set((state) => ({
      observerSpecializations: {
        ...state.observerSpecializations,
        [observerId]: score,
      },
    })),

  setTopologyClusters: (clusters) => set({ topologyClusters: clusters }),

  addAdaptationEvent: (event) =>
    set((state) => ({
      adaptationEvents: [...state.adaptationEvents, event].slice(-50),
    })),

  setReplaying: (replaying) => set({ isReplaying: replaying }),
  setReplayIndex: (index) => set({ replayIndex: index }),

  reset: () =>
    set({
      traces: [],
      workflowPatterns: [],
      routingImprovements: [],
      failures: [],
      observerSpecializations: {},
      topologyClusters: [],
      adaptationEvents: [],
      isReplaying: false,
      replayIndex: 0,
    }),
}));
