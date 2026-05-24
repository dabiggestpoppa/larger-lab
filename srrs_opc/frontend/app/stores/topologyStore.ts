import { create } from "zustand";

export interface ObserverNode {
  id: string;
  label: string;
  type: string;
  status: "active" | "synced" | "isolated" | "entropic" | "repairing" | "dormant" | "failed";
  entropy: number;
  syncScore: number;
  repairState: string;
  x: number;
  y: number;
  clusterId?: string;
}

export interface ObserverEdge {
  source: string;
  target: string;
  strength: number;
  type: "routing" | "sync" | "repair" | "entropy" | "memory" | "field";
  entropyFlow?: number;
  repairFlow?: number;
  syncFlow?: number;
}

export interface ClusterState {
  id: string;
  nodes: string[];
  stabilityScore: number;
  entropyScore: number;
  syncDensity: number;
}

interface TopologyState {
  nodes: ObserverNode[];
  edges: ObserverEdge[];
  clusters: ClusterState[];
  selectedObserverId: string | null;
  viewMode: "topology" | "entropy" | "repair" | "sync" | "routing";
  filters: {
    observerType: string | null;
    entropyLevel: "all" | "low" | "medium" | "high";
    syncState: string | null;
  };
  setNodes: (nodes: ObserverNode[]) => void;
  setEdges: (edges: ObserverEdge[]) => void;
  setClusters: (clusters: ClusterState[]) => void;
  selectObserver: (id: string | null) => void;
  setViewMode: (mode: TopologyState["viewMode"]) => void;
  setFilter: (key: keyof TopologyState["filters"], value: string | null) => void;
}

export const useTopologyStore = create<TopologyState>((set) => ({
  nodes: [],
  edges: [],
  clusters: [],
  selectedObserverId: null,
  viewMode: "topology",
  filters: {
    observerType: null,
    entropyLevel: "all",
    syncState: null,
  },
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setClusters: (clusters) => set({ clusters }),
  selectObserver: (id) => set({ selectedObserverId: id }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value },
    })),
}));
