import { create } from "zustand";

export type TaskStatus = "pending" | "active" | "completed" | "failed";
export type TaskPriority = "low" | "medium" | "high" | "critical";

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  agent: string;
  progress: number;
  createdAt: string;
  updatedAt: string;
  error?: string;
}

interface TaskStore {
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Omit<Task, "id" | "createdAt" | "updatedAt">) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  removeTask: (id: string) => void;
  getActiveTasks: () => Task[];
  getTasksByStatus: (status: TaskStatus) => Task[];
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
    {
      id: "task-001",
      title: "Phase 11.2 Chaos v2 Test",
      description: "5X chaos amplification test running",
      status: "active",
      priority: "critical",
      agent: "Copilot",
      progress: 35,
      createdAt: "2026-05-23T08:13:00Z",
      updatedAt: "2026-05-24T12:00:00Z",
    },
    {
      id: "task-002",
      title: "Phase 11.4.1 Contradiction Injection",
      description: "Memory contradiction injection test suite",
      status: "completed",
      priority: "high",
      agent: "AS",
      progress: 100,
      createdAt: "2026-05-23T10:00:00Z",
      updatedAt: "2026-05-23T14:00:00Z",
    },
    {
      id: "task-003",
      title: "Phase 11.1-B 72h Continuity",
      description: "72-hour continuity stability test",
      status: "active",
      priority: "high",
      agent: "Copilot",
      progress: 12,
      createdAt: "2026-05-22T23:46:00Z",
      updatedAt: "2026-05-24T12:00:00Z",
    },
    {
      id: "task-004",
      title: "Frontend Build Planning",
      description: "Plan SRRA-OPH + OCE frontend builds",
      status: "completed",
      priority: "medium",
      agent: "AS",
      progress: 100,
      createdAt: "2026-05-24T08:00:00Z",
      updatedAt: "2026-05-24T12:00:00Z",
    },
  ],
  addTask: (task) =>
    set((state) => ({
      tasks: [
        ...state.tasks,
        {
          ...task,
          id: `task-${Date.now()}`,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ],
    })),
  updateTask: (id, updates) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === id ? { ...t, ...updates, updatedAt: new Date().toISOString() } : t
      ),
    })),
  removeTask: (id) =>
    set((state) => ({ tasks: state.tasks.filter((t) => t.id !== id) })),
  getActiveTasks: () => get().tasks.filter((t) => t.status === "active"),
  getTasksByStatus: (status) => get().tasks.filter((t) => t.status === status),
}));
