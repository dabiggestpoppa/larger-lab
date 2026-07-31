import { create } from "zustand";

export type ConnectionStatus = "connected" | "disconnected" | "connecting" | "error";
export type Layer = "layer1" | "layer2" | "layer3";

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
  activeLayer: Layer;
  layerVisibility: Record<Layer, boolean>;
  toggleRightPanel: () => void;
  setRightPanelContent: (content: "task" | "agent" | "session" | null) => void;
  setSelectedTask: (id: string | null) => void;
  setSelectedAgent: (id: string | null) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  addNotification: (notification: Omit<Notification, "id" | "timestamp">) => void;
  removeNotification: (id: string) => void;
  setActiveLayer: (layer: Layer) => void;
  toggleLayerVisibility: (layer: Layer) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  rightPanelOpen: false,
  rightPanelContent: null,
  selectedTaskId: null,
  selectedAgentId: null,
  connectionStatus: "disconnected",
  notifications: [],
  activeLayer: "layer1",
  layerVisibility: {
    layer1: true,
    layer2: false,
    layer3: false,
  },
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
  setActiveLayer: (layer) => set({ activeLayer: layer }),
  toggleLayerVisibility: (layer) =>
    set((state) => ({
      layerVisibility: { ...state.layerVisibility, [layer]: !state.layerVisibility[layer] },
    })),
}));