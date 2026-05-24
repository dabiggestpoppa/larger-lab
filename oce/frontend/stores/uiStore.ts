import { create } from "zustand";

interface UIStore {
  rightPanelOpen: boolean;
  rightPanelContent: "task" | "agent" | "session" | null;
  selectedTaskId: string | null;
  selectedAgentId: string | null;
  toggleRightPanel: () => void;
  setRightPanelContent: (content: "task" | "agent" | "session" | null) => void;
  setSelectedTask: (id: string | null) => void;
  setSelectedAgent: (id: string | null) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  rightPanelOpen: false,
  rightPanelContent: null,
  selectedTaskId: null,
  selectedAgentId: null,
  toggleRightPanel: () => set((state) => ({ rightPanelOpen: !state.rightPanelOpen })),
  setRightPanelContent: (content) => set({ rightPanelContent: content, rightPanelOpen: content !== null }),
  setSelectedTask: (id) => set({ selectedTaskId: id, rightPanelContent: id ? "task" : null, rightPanelOpen: id !== null }),
  setSelectedAgent: (id) => set({ selectedAgentId: id, rightPanelContent: id ? "agent" : null, rightPanelOpen: id !== null }),
}));
