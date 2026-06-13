import { create } from "zustand";

export interface ObserverNode {
  id: string;
  label: string;
  type: string;
  status: "active" | "synced" | "isolated" | "entropic" | "repairing" | "dormant" | "failed" | "degraded";
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
  filters: { observerType: string | null; entropyLevel: "all" | "low" | "medium" | "high"; syncState: string | null; };
  isLoading: boolean;
  lastFetch: string | null;
  setNodes: (nodes: ObserverNode[]) => void;
  setEdges: (edges: ObserverEdge[]) => void;
  setClusters: (clusters: ClusterState[]) => void;
  selectObserver: (id: string | null) => void;
  setViewMode: (mode: TopologyState["viewMode"]) => void;
  setFilter: (key: keyof TopologyState["filters"], value: string | null) => void;
  setLoading: (v: boolean) => void;
  fetchTopology: () => Promise<void>;
  fetchObservers: () => Promise<void>;
}

const API_BASE = "/api/v1";

function buildNodes(observers: any[]): ObserverNode[] {
  return observers.map((obs: any, i: number) => ({
    id: obs.id || obs.observer_id || `obs_${i}`,
    label: obs.label || obs.name || obs.id || `Observer ${i}`,
    type: obs.type || "observer",
    status: obs.status || "active",
    entropy: obs.entropy ?? Math.random() * 0.5,
    syncScore: obs.sync_score ?? obs.syncScore ?? Math.random(),
    repairState: obs.repair_state || "idle",
    x: 400 + (Math.random() - 0.5) * 300,
    y: 300 + (Math.random() - 0.5) * 300,
  }));
}

function buildEdges(nodes: ObserverNode[]): ObserverEdge[] {
  const edges: ObserverEdge[] = [];
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      if (nodes[i].type === nodes[j].type || Math.random() > 0.7) {
        edges.push({
          source: nodes[i].id, target: nodes[j].id,
          strength: 0.3 + Math.random() * 0.7,
          type: ["routing","sync","repair","entropy","memory","field"][Math.floor(Math.random()*6)] as any,
        });
      }
    }
  }
  return edges;
}

export const useTopologyStore = create<TopologyState>((set) => ({
  nodes: [], edges: [], clusters: [],
  selectedObserverId: null, viewMode: "topology",
  filters: { observerType: null, entropyLevel: "all", syncState: null },
  isLoading: false, lastFetch: null,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setClusters: (clusters) => set({ clusters }),
  selectObserver: (id) => set({ selectedObserverId: id }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setFilter: (key, value) => set((s) => ({ filters: { ...s.filters, [key]: value } })),
  setLoading: (v) => set({ isLoading: v }),

  fetchObservers: async () => {
    try {
      const res = await fetch(`${API_BASE}/observers`);
      if (!res.ok) return;
      const data = await res.json();
      const obs = Array.isArray(data) ? data : data.observers || data.data || [];
      if (obs.length > 0) set({ nodes: buildNodes(obs) });
    } catch (e) { console.warn("fetchObservers:", e); }
  },

  fetchTopology: async () => {
    set({ isLoading: true });
    try {
      let nodes: ObserverNode[] = [], edges: ObserverEdge[] = [];
      const r = await fetch(`${API_BASE}/observers`);
      if (r.ok) {
        const data = await r.json();
        const obs = Array.isArray(data) ? data : data.observers || data.data || [];
        nodes = buildNodes(obs);
      }
      if (edges.length === 0 && nodes.length > 1) edges = buildEdges(nodes);
      const clusters: ClusterState[] = [];
      const groups: Record<string, string[]> = {};
      nodes.forEach(n => { if (!groups[n.type]) groups[n.type] = []; groups[n.type].push(n.id); });
      Object.entries(groups).forEach(([type, ids], i) => {
        if (ids.length > 1) clusters.push({ id: `c_${i}`, nodes: ids, stabilityScore: 0.7, entropyScore: 0.2, syncDensity: 0.6 });
      });
      set({ nodes, edges, clusters, lastFetch: new Date().toISOString() });
    } catch (e) { console.error("fetchTopology:", e); }
    finally { set({ isLoading: false }); }
  },
}));