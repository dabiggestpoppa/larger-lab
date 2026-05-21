"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import { X, CheckCircle, AlertTriangle, Info, XCircle } from "lucide-react";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { ...toast, id }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

function ToastContainer({ toasts, onRemove }: { toasts: Toast[]; onRemove: (id: string) => void }) {
  return (
    <div className="fixed bottom-4 right-4 z-[100] space-y-2 max-w-sm">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  useEffect(() => {
    const duration = toast.duration ?? 5000;
    const timer = setTimeout(() => onRemove(toast.id), duration);
    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onRemove]);

  const config = {
    success: { icon: CheckCircle, bg: "bg-green-900/20 border-green-800/40", iconColor: "text-green-400" },
    error: { icon: XCircle, bg: "bg-red-900/20 border-red-800/40", iconColor: "text-red-400" },
    warning: { icon: AlertTriangle, bg: "bg-yellow-900/20 border-yellow-800/40", iconColor: "text-yellow-400" },
    info: { icon: Info, bg: "bg-blue-900/20 border-blue-800/40", iconColor: "text-blue-400" },
  }[toast.type];

  const Icon = config.icon;

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border backdrop-blur-sm ${config.bg} animate-in slide-in-from-right`}>
      <Icon className={`w-4 h-4 ${config.iconColor} shrink-0 mt-0.5`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-200">{toast.title}</p>
        {toast.message && <p className="text-xs text-gray-400 mt-0.5">{toast.message}</p>}
      </div>
      <button onClick={() => onRemove(toast.id)} className="p-0.5 rounded hover:bg-white/5 text-gray-500 hover:text-gray-300 shrink-0">
        <X className="w-3 h-3" />
      </button>
    </div>
  );
}
