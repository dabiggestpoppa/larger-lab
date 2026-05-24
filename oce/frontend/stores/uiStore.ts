import { create } from "zustand";

export type ConnectionStatus = "connected" | "disconnected" | "connecting" | "error";

export interface Notification {
  id: string;
  type: "success" | "error" | "warning" | "info";
  message: string;
  timestamp: string;
}

interface UIStore {
  rightPanelOpen: boolean;
  rightPanelContent: "task" | "agent" | "session" | null;
  selectedTaskId: string | null;
  selectedAgentId: string | null;
  connectionStatus: ConnectionStatus;
  notifications: Notification[];
  toggleRightPanel: () => void;
  setRightPanelContent: (content: "task" | "agent" | "session" | null) => void;
  setSelectedTask: (id: string | null) => void;
  setSelectedAgent: (id: string | null) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  addNotification: (notification: Omit<Notification, "id" | "timestamp">) => void;
  removeNotification: (id: string) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  rightPanelOpen: false,
  rightPanelContent: null,
  selectedTaskId: null,
  selectedAgentId: null,
  connectionStatus: "disconnected",
  notifications: [],
  toggleRightPanel: () => set((state) => ({ rightPanelOpen: !state.rightPanelOpen })),
  setRightPanelContent: (content) => set({ rightPanelContent: content, rightPanelOpen: content !== null }),
  setSelectedTask: (id) => set({ selectedTaskId: id, rightPanelContent: id ? "task" : null, rightPanelOpen: id !== null }),
  setSelectedAgent: (id) => set({ selectedAgentId: id, rightPanelContent: id ? "agent" : null, rightPanelOpen: id !== null }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
  addNotification: (notification) => set((state) => ({
    notifications: [
      { ...notification, id: `notif-${Date.now()}`, timestamp: new Date().toISOString() },
      ...state.notifications,
    ].slice(0, 5),
  })),
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter((n) => n.id !== id),
  })),
}));
