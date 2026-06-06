import { create } from "zustand";

export interface ResearchPaper {
  id: string;
  doi: string;
  title: string;
  year: number;
  source: string;
  citation_count: number;
  abstract?: string;
  status?: string;
  operational_relevance?: number;
}

export interface ResearchAgent {
  task_id: string;
  query: string;
  status: string;
  priority: number;
  confidence: number;
  created_at: string;
}

export interface DoctrineNote {
  path: string;
  title: string;
  preview: string;
  domain?: string;
}

export interface KnowledgeGap {
  id: string;
  concept: string;
  domain: string;
  score: number;
  reason: string;
}

export interface ResearchStats {
  papers_ingested: number;
  papers_distilled: number;
  doctrine_notes: number;
  contradictions_found: number;
  agents_spawned: number;
  graph_nodes: number;
  graph_edges: number;
  last_ingestion: string | null;
}

interface ResearchState {
  // Papers
  papers: ResearchPaper[];
  paperLoading: boolean;
  paperError: string | null;
  paperQuery: string;
  paperDomain: string;

  // Agents
  agents: ResearchAgent[];
  agentLoading: boolean;
  agentError: string | null;

  // Doctrine
  doctrine: DoctrineNote[];
  doctrineLoading: boolean;
  doctrineError: string | null;
  doctrineDomain: string;

  // Gaps
  gaps: KnowledgeGap[];
  gapLoading: boolean;

  // Stats
  stats: ResearchStats | null;

  // Graph data (reuse vaultStore types)
  graphNodes: { id: string; label: string; category: string; connections: number }[];
  graphEdges: { source: string; target: string; label?: string }[];

  // Actions
  setPapers: (papers: ResearchPaper[]) => void;
  setPaperLoading: (loading: boolean) => void;
  setPaperError: (error: string | null) => void;
  setPaperQuery: (query: string) => void;
  setPaperDomain: (domain: string) => void;

  setAgents: (agents: ResearchAgent[]) => void;
  setAgentLoading: (loading: boolean) => void;
  setAgentError: (error: string | null) => void;

  setDoctrine: (doctrine: DoctrineNote[]) => void;
  setDoctrineLoading: (loading: boolean) => void;
  setDoctrineError: (error: string | null) => void;
  setDoctrineDomain: (domain: string) => void;

  setGaps: (gaps: KnowledgeGap[]) => void;
  setGapLoading: (loading: boolean) => void;

  setStats: (stats: ResearchStats | null) => void;
  setGraphData: (nodes: ResearchState["graphNodes"], edges: ResearchState["graphEdges"]) => void;

  // Async actions
  fetchPapers: (query?: string, domain?: string) => Promise<void>;
  fetchAgents: () => Promise<void>;
  fetchDoctrine: (domain?: string) => Promise<void>;
  fetchGaps: () => Promise<void>;
  fetchStats: () => Promise<void>;
  fetchGraph: () => Promise<void>;
  triggerIngest: (domains?: string[]) => Promise<void>;
  spawnAgent: (query: string, domains?: string[]) => Promise<void>;
}

const API_BASE = "/api/research";

export const useResearchStore = create<ResearchState>((set, get) => ({
  papers: [],
  paperLoading: false,
  paperError: null,
  paperQuery: "",
  paperDomain: "",

  agents: [],
  agentLoading: false,
  agentError: null,

  doctrine: [],
  doctrineLoading: false,
  doctrineError: null,
  doctrineDomain: "",

  gaps: [],
  gapLoading: false,

  stats: null,
  graphNodes: [],
  graphEdges: [],

  setPapers: (papers) => set({ papers }),
  setPaperLoading: (paperLoading) => set({ paperLoading }),
  setPaperError: (paperError) => set({ paperError }),
  setPaperQuery: (paperQuery) => set({ paperQuery }),
  setPaperDomain: (paperDomain) => set({ paperDomain }),

  setAgents: (agents) => set({ agents }),
  setAgentLoading: (agentLoading) => set({ agentLoading }),
  setAgentError: (agentError) => set({ agentError }),

  setDoctrine: (doctrine) => set({ doctrine }),
  setDoctrineLoading: (doctrineLoading) => set({ doctrineLoading }),
  setDoctrineError: (doctrineError) => set({ doctrineError }),
  setDoctrineDomain: (doctrineDomain) => set({ doctrineDomain }),

  setGaps: (gaps) => set({ gaps }),
  setGapLoading: (gapLoading) => set({ gapLoading }),

  setStats: (stats) => set({ stats }),
  setGraphData: (nodes, edges) => set({ graphNodes: nodes, graphEdges: edges }),

  fetchPapers: async (query, domain) => {
    set({ paperLoading: true, paperError: null });
    try {
      const params = new URLSearchParams();
      if (query) params.set("query", query);
      if (domain) params.set("domain", domain);
      params.set("limit", "50");
      const res = await fetch(`${API_BASE}/papers?${params}`);
      const data = await res.json();
      set({ papers: data.papers || [], paperLoading: false });
    } catch (err) {
      set({ paperError: String(err), paperLoading: false });
    }
  },

  fetchAgents: async () => {
    set({ agentLoading: true, agentError: null });
    try {
      const res = await fetch(`${API_BASE}/agents`);
      const data = await res.json();
      set({ agents: data.agents || [], agentLoading: false });
    } catch (err) {
      set({ agentError: String(err), agentLoading: false });
    }
  },

  fetchDoctrine: async (domain) => {
    set({ doctrineLoading: true, doctrineError: null });
    try {
      const params = new URLSearchParams();
      if (domain) params.set("domain", domain);
      params.set("limit", "50");
      const res = await fetch(`${API_BASE}/doctrine?${params}`);
      const data = await res.json();
      set({ doctrine: data.doctrine || [], doctrineLoading: false });
    } catch (err) {
      set({ doctrineError: String(err), doctrineLoading: false });
    }
  },

  fetchGaps: async () => {
    set({ gapLoading: true });
    try {
      const res = await fetch(`${API_BASE}/gaps`);
      const data = await res.json();
      set({ gaps: data.gaps || [], gapLoading: false });
    } catch {
      set({ gapLoading: false });
    }
  },

  fetchStats: async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      const data = await res.json();
      set({ stats: data });
    } catch {}
  },

  fetchGraph: async () => {
    try {
      const res = await fetch(`${API_BASE}/graph?limit=200`);
      const data = await res.json();
      set({
        graphNodes: data.nodes || [],
        graphEdges: data.edges || [],
      });
    } catch {}
  },

  triggerIngest: async (domains) => {
    try {
      await fetch(`${API_BASE}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domains, max_papers: 500 }),
      });
      // Refresh stats after ingest
      await get().fetchStats();
    } catch {}
  },

  spawnAgent: async (query, domains) => {
    try {
      await fetch(`${API_BASE}/agents/spawn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, domains, priority: 3 }),
      });
      await get().fetchAgents();
    } catch {}
  },
}));
