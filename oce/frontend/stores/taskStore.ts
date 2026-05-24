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
  addTask: (task) => {
    const now = new Date().toISOString();
    set((state) => ({
      tasks: [...state.tasks, { ...task, id: `task-${Date.now()}`, createdAt: now, updatedAt: now }],
    }));
  },
  updateTask: (id, updates) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? { ...t, ...updates, updatedAt: new Date().toISOString() } : t)),
    })),
  removeTask: (id) => set((state) => ({ tasks: state.tasks.filter((t) => t.id !== id) })),
  getActiveTasks: () => get().tasks.filter((t) => t.status === "active"),
  getTasksByStatus: (status) => get().tasks.filter((t) => t.status === status),
}));
