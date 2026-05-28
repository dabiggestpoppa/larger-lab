/**
 * Chat Store
 * Zustand store for chat state — messages, sessions, active conversation.
 */
import { create } from "zustand";

export interface ChatMessage {
  message_id: string;
  role: "user" | "observer" | "system";
  content: string;
  timestamp: string;
  session_id: string;
  task_domain?: string;
  complexity?: string;
  observer_metadata?: Record<string, unknown>;
}

export interface ChatSession {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  entry_count: number;
  last_role: string;
  last_preview: string;
}

interface ChatStore {
  // Messages for the active session
  messages: ChatMessage[];
  // All sessions
  sessions: ChatSession[];
  // Active session ID
  activeSessionId: string | null;
  // Loading state
  isLoading: boolean;
  isSending: boolean;
  // Error
  error: string | null;

  // Actions
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  setSessions: (sessions: ChatSession[]) => void;
  setActiveSession: (sessionId: string | null) => void;
  setLoading: (loading: boolean) => void;
  setSending: (sending: boolean) => void;
  setError: (error: string | null) => void;

  // API calls
  loadSessions: () => Promise<void>;
  loadHistory: (sessionId: string) => Promise<void>;
  sendMessage: (message: string, sessionId?: string) => Promise<void>;
  createSession: (title?: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  searchMessages: (query: string) => Promise<ChatMessage[]>;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  sessions: [],
  activeSessionId: null,
  isLoading: false,
  isSending: false,
  error: null,

  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((s) => ({ messages: [...s.messages, message] })),
  setSessions: (sessions) => set({ sessions }),
  setActiveSession: (sessionId) => set({ activeSessionId: sessionId }),
  setLoading: (loading) => set({ isLoading: loading }),
  setSending: (sending) => set({ isSending: sending }),
  setError: (error) => set({ error }),

  loadSessions: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch("/api/chat/sessions");
      const data = await res.json();
      const raw = data.sessions || [];
      const sessions: ChatSession[] = raw.map((s: Record<string, unknown>) => ({
        session_id: (s.session_id as string) || "",
        title: (s.title as string) || `Session ${(s.session_id as string || "").slice(-6)}`,
        created_at: (s.created_at as string) || (s.start_time as string) || "",
        updated_at: (s.updated_at as string) || (s.last_active as string) || "",
        entry_count: (s.entry_count as number) || (s.message_count as number) || 0,
        last_role: (s.last_role as string) || "",
        last_preview: (s.last_preview as string) || "",
      }));
      set({ sessions });
      const activeId = data.active_session as string | null;
      if (activeId && !get().activeSessionId) {
        set({ activeSessionId: activeId });
      }
    } catch (err) {
      set({ error: "Failed to load sessions" });
      console.error("Failed to load sessions:", err);
    } finally {
      set({ isLoading: false });
    }
  },

  loadHistory: async (sessionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`/api/chat/history/${sessionId}`);
      const data = await res.json();
      // API returns { session, messages }
      const raw = data.messages || data.entries || [];
      const msgs: ChatMessage[] = raw.map((m: Record<string, unknown>) => ({
        message_id: (m.message_id as string) || `msg_${Date.now()}`,
        role: (m.role as "user" | "observer" | "system") || (m.role as string) === "assistant" ? "observer" : (m.role as "user" | "observer" | "system"),
        content: (m.content as string) || "",
        timestamp: (m.timestamp as string) || new Date().toISOString(),
        session_id: (m.session_id as string) || sessionId,
        task_domain: m.task_domain as string | undefined,
        complexity: m.complexity as string | undefined,
        observer_metadata: (m.observer_metadata as Record<string, unknown>) || {},
      }));
      set({ messages: msgs, activeSessionId: sessionId });
    } catch (err) {
      set({ error: "Failed to load chat history" });
      console.error("Failed to load chat history:", err);
    } finally {
      set({ isLoading: false });
    }
  },

  sendMessage: async (message: string, sessionId?: string) => {
    set({ isSending: true, error: null });
    const userMsg: ChatMessage = {
      message_id: `local_${Date.now()}`,
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
      session_id: sessionId || get().activeSessionId || "",
    };
    set((s) => ({ messages: [...s.messages, userMsg] }));

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          session_id: sessionId || get().activeSessionId,
        }),
      });
      const data = await res.json();

      const observerMsg: ChatMessage = {
        message_id: `observer_${Date.now()}`,
        role: "observer",
        content: data.response || "No response",
        timestamp: new Date().toISOString(),
        session_id: data.session_id || sessionId || "",
        task_domain: data.observer?.task_domain,
        complexity: data.observer?.complexity,
        observer_metadata: {
          routing_path: data.observer?.routing_path,
          model: data.observer?.model,
          confidence: data.confidence,
          agreement: data.observer?.agreement,
          spawn_status: data.observer?.spawn_status,
          system: data.system,
        },
      };
      set((s) => ({ messages: [...s.messages, observerMsg] }));

      // Reload sessions to update the list
      await get().loadSessions();
    } catch (err) {
      set({ error: "Failed to send message" });
      console.error("Failed to send message:", err);
    } finally {
      set({ isSending: false });
    }
  },

  createSession: async (title?: string) => {
    try {
      const res = await fetch("/api/chat/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      const data = await res.json();
      if (data.session) {
        set({ activeSessionId: data.session.session_id, messages: [] });
        await get().loadSessions();
      }
    } catch (err) {
      set({ error: "Failed to create session" });
      console.error("Failed to create session:", err);
    }
  },

  deleteSession: async (sessionId: string) => {
    try {
      await fetch(`/api/chat/sessions/${sessionId}`, { method: "DELETE" });
      const { activeSessionId } = get();
      if (activeSessionId === sessionId) {
        set({ activeSessionId: null, messages: [] });
      }
      await get().loadSessions();
    } catch (err) {
      set({ error: "Failed to delete session" });
      console.error("Failed to delete session:", err);
    }
  },

  searchMessages: async (query: string): Promise<ChatMessage[]> => {
    try {
      const res = await fetch(
        `/api/chat/search?q=${encodeURIComponent(query)}`
      );
      const data = await res.json();
      return data.results || [];
    } catch (err) {
      console.error("Failed to search messages:", err);
      return [];
    }
  },
}));
