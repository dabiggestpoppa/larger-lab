import { create } from "zustand";

export type ProcessStatus = "running" | "idle" | "hung" | "terminated";
export type SandboxStatus = "active" | "inactive" | "error" | "restricted";
export type RecoveryState = "stable" | "recovering" | "failed" | "restarting";

export interface Process {
  id: string;
  name: string;
  pid: number;
  status: ProcessStatus;
  cpu: number;
  memory: number;
  runtime: string;
  command: string;
}

export interface Sandbox {
  id: string;
  name: string;
  status: SandboxStatus;
  type: "dev" | "orchestration" | "testing" | "replay";
  activeTasks: number;
  maxTasks: number;
  resourceUsage: {
    cpu: number;
    memory: number;
  };
}

export interface FilesystemNode {
  id: string;
  name: string;
  path: string;
  type: "file" | "directory";
  size?: number;
  modified?: string;
  children?: FilesystemNode[];
}

export interface RecoveryEvent {
  id: string;
  timestamp: string;
  type: string;
  target: string;
  status: RecoveryState;
  duration: number;
}

interface SubstrateState {
  // Processes
  processes: Process[];
  setProcesses: (processes: Process[]) => void;
  addProcess: (process: Process) => void;
  updateProcess: (id: string, updates: Partial<Process>) => void;
  
  // Sandboxes
  sandboxes: Sandbox[];
  setSandboxes: (sandboxes: Sandbox[]) => void;
  updateSandbox: (id: string, updates: Partial<Sandbox>) => void;
  
  // Filesystem
  filesystem: FilesystemNode | null;
  setFilesystem: (fs: FilesystemNode | null) => void;
  
  // Recovery
  recoveryEvents: RecoveryEvent[];
  addRecoveryEvent: (event: RecoveryEvent) => void;
  
  // Runtime metrics
  systemLoad: {
    cpu: number;
    memory: number;
    disk: number;
  };
  setSystemLoad: (load: { cpu: number; memory: number; disk: number }) => void;
  
  // Loading states
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

export const useSubstrateStore = create<SubstrateState>((set, get) => ({
  processes: [],
  setProcesses: (processes) => set({ processes }),
  addProcess: (process) =>
    set((state) => ({
      processes: [...state.processes, process],
    })),
  updateProcess: (id, updates) =>
    set((state) => ({
      processes: state.processes.map((p) => (p.id === id ? { ...p, ...updates } : p)),
    })),

  sandboxes: [],
  setSandboxes: (sandboxes) => set({ sandboxes }),
  updateSandbox: (id, updates) =>
    set((state) => ({
      sandboxes: state.sandboxes.map((s) => (s.id === id ? { ...s, ...updates } : s)),
    })),

  filesystem: null,
  setFilesystem: (filesystem) => set({ filesystem }),

  recoveryEvents: [],
  addRecoveryEvent: (event) =>
    set((state) => ({
      recoveryEvents: [event, ...state.recoveryEvents].slice(0, 100),
    })),

  systemLoad: { cpu: 0, memory: 0, disk: 0 },
  setSystemLoad: (systemLoad) => set({ systemLoad }),

  loading: false,
  setLoading: (loading) => set({ loading }),
}));