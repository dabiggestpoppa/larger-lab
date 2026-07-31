import { create } from "zustand";

export interface VaultNote {
  id: string;
  title: string;
  path: string;
  content: string;
  tags: string[];
  links: string[];
  modified: string;
  category: string;
}

export interface GraphNode {
  id: string;
  label: string;
  category: string;
  connections: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}

interface VaultState {
  notes: VaultNote[];
  selectedNote: VaultNote | null;
  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];
  selectedNode: GraphNode | null;
  loading: boolean;
  error: string | null;
  filter: string;
  category: string;

  // Actions
  setNotes: (notes: VaultNote[]) => void;
  setSelectedNote: (note: VaultNote | null) => void;
  setGraphData: (nodes: GraphNode[], edges: GraphEdge[]) => void;
  setSelectedNode: (node: GraphNode | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilter: (filter: string) => void;
  setCategory: (category: string) => void;

  // Async actions
  fetchNotes: () => Promise<void>;
  fetchGraph: () => Promise<void>;
}

export const useVaultStore = create<VaultState>((set, get) => ({
  notes: [],
  selectedNote: null,
  graphNodes: [],
  graphEdges: [],
  selectedNode: null,
  loading: false,
  error: null,
  filter: "",
  category: "all",

  setNotes: (notes) => set({ notes }),
  setSelectedNote: (note) => set({ selectedNote: note }),
  setGraphData: (nodes, edges) => set({ graphNodes: nodes, graphEdges: edges }),
  setSelectedNode: (node) => set({ selectedNode: node }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setFilter: (filter) => set({ filter }),
  setCategory: (category) => set({ category }),

  fetchNotes: async () => {
    set({ loading: true, error: null });
    try {
      const res = await fetch("/api/vault/notes");
      if (!res.ok) {
        set({ notes: [], loading: false, error: "Vault API not yet available" });
        return;
      }
      const data = await res.json();
      set({ notes: data.notes || [], loading: false });
    } catch {
      set({ notes: [], loading: false, error: "Vault API not yet available" });
    }
  },

  fetchGraph: async () => {
    set({ loading: true, error: null });
    try {
      const res = await fetch("/api/vault/graph");
      if (!res.ok) {
        set({
          graphNodes: [],
          graphEdges: [],
          loading: false,
          error: "Graph API not yet available",
        });
        return;
      }
      const data = await res.json();
      set({
        graphNodes: data.nodes || [],
        graphEdges: data.edges || [],
        loading: false,
      });
    } catch {
      set({
        graphNodes: [],
        graphEdges: [],
        loading: false,
        error: "Graph API not yet available",
      });
    }
  },
}));
