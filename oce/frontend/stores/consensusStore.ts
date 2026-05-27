import { create } from "zustand";

export interface ConsensusResult {
  task_type: string;
  complexity: string;
  confidence: number;
  routing_path: string[];
  required_capabilities: string[];
  recommended_model: string;
  spawn_required: boolean;
  timestamp: string;
  voter_count: number;
  agreement_score: number;
}

export interface RoutingDecision {
  task_domain: string;
  selected_route: string;
  alternatives: string[];
  confidence: number;
  timestamp: string;
}

export interface ObserverSpecialization {
  observer_id: string;
  observer_type: string;
  specializations: string[];
  accuracy: number;
  tasks_completed: number;
}

export interface CapabilityInfo {
  capability_id: string;
  name: string;
  description: string;
  observers: string[];
  available: boolean;
}

export interface ConsensusReplayItem {
  replay_id: string;
  timestamp: string;
  consensus_result: ConsensusResult;
  outcome: "success" | "failure" | "partial";
  duration_ms: number;
}

interface ConsensusStore {
  // Consensus state
  currentConsensus: ConsensusResult | null;
  consensusHistory: ConsensusResult[];
  isConsensusActive: boolean;

  // Routing
  routingDecisions: RoutingDecision[];
  currentRoute: string | null;

  // Specializations
  specializations: ObserverSpecialization[];

  // Capabilities
  capabilities: CapabilityInfo[];

  // Replay
  replayHistory: ConsensusReplayItem[];
  selectedReplay: ConsensusReplayItem | null;

  // Actions
  setCurrentConsensus: (result: ConsensusResult | null) => void;
  addConsensusToHistory: (result: ConsensusResult) => void;
  setConsensusActive: (active: boolean) => void;
  addRoutingDecision: (decision: RoutingDecision) => void;
  setCurrentRoute: (route: string | null) => void;
  setSpecializations: (specs: ObserverSpecialization[]) => void;
  setCapabilities: (caps: CapabilityInfo[]) => void;
  setReplayHistory: (history: ConsensusReplayItem[]) => void;
  setSelectedReplay: (item: ConsensusReplayItem | null) => void;
}

export const useConsensusStore = create<ConsensusStore>((set) => ({
  currentConsensus: null,
  consensusHistory: [],
  isConsensusActive: false,
  routingDecisions: [],
  currentRoute: null,
  specializations: [],
  capabilities: [],
  replayHistory: [],
  selectedReplay: null,

  setCurrentConsensus: (result) => set({ currentConsensus: result }),
  addConsensusToHistory: (result) =>
    set((state) => ({
      consensusHistory: [...state.consensusHistory, result].slice(-100),
    })),
  setConsensusActive: (active) => set({ isConsensusActive: active }),
  addRoutingDecision: (decision) =>
    set((state) => ({
      routingDecisions: [...state.routingDecisions, decision].slice(-50),
    })),
  setCurrentRoute: (route) => set({ currentRoute: route }),
  setSpecializations: (specs) => set({ specializations: specs }),
  setCapabilities: (caps) => set({ capabilities: caps }),
  setReplayHistory: (history) => set({ replayHistory: history }),
  setSelectedReplay: (item) => set({ selectedReplay: item }),
}));
