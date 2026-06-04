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
      // Use streaming endpoint for real-time progress updates
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          session_id: sessionId || get().activeSessionId,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      // Read SSE stream
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalData: any = null;
      const progressMessages: ChatMessage[] = [];

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const evt = JSON.parse(jsonStr);
              const eventType = evt.type || evt.event;
              const data = evt.data || {};

              if (eventType === "round") {
                const msg: ChatMessage = {
                  message_id: `progress_${Date.now()}_round`,
                  role: "system",
                  content: `🔄 Round ${data.round}/${data.max} — Thinking...`,
                  timestamp: new Date().toISOString(),
                  session_id: sessionId || get().activeSessionId || "",
                };
                progressMessages.push(msg);
                set((s) => ({ messages: [...s.messages, msg] }));
              } else if (eventType === "tool_call") {
                const msg: ChatMessage = {
                  message_id: `progress_${Date.now()}_tool`,
                  role: "system",
                  content: `🔧 Tool: ${data.tool} — Executing...`,
                  timestamp: new Date().toISOString(),
                  session_id: sessionId || get().activeSessionId || "",
                };
                progressMessages.push(msg);
                set((s) => ({ messages: [...s.messages, msg] }));
              } else if (eventType === "tool_result") {
                const preview = (data.result || "").substring(0, 120);
                const msg: ChatMessage = {
                  message_id: `progress_${Date.now()}_result`,
                  role: "system",
                  content: `📋 ${data.tool}: ${preview}${data.result?.length > 120 ? "..." : ""}`,
                  timestamp: new Date().toISOString(),
                  session_id: sessionId || get().activeSessionId || "",
                };
                progressMessages.push(msg);
                set((s) => ({ messages: [...s.messages, msg] }));
              } else if (eventType === "final") {
                finalData = data;
              } else if (eventType === "error") {
                const msg: ChatMessage = {
                  message_id: `error_${Date.now()}`,
                  role: "system",
                  content: `❌ Error: ${data.message || "Unknown error"}`,
                  timestamp: new Date().toISOString(),
                  session_id: sessionId || get().activeSessionId || "",
                };
                set((s) => ({ messages: [...s.messages, msg] }));
              }
            } catch (parseErr) {
              // Skip malformed SSE events
            }
          }
        }
      }

      // Send final response
      if (finalData) {
        const observerMsg: ChatMessage = {
          message_id: `observer_${Date.now()}`,
          role: "observer",
          content: finalData.response || "No response",
          timestamp: new Date().toISOString(),
          session_id: finalData.session_id || sessionId || "",
          task_domain: finalData.observer?.task_domain,
          complexity: finalData.observer?.complexity,
          observer_metadata: {
            routing_path: finalData.observer?.routing_path,
            model: finalData.observer?.model,
            confidence: finalData.confidence,
            agreement: finalData.observer?.agreement,
            spawn_status: finalData.observer?.spawn_status,
            system: finalData.system,
          },
        };
        set((s) => ({ messages: [...s.messages, observerMsg] }));
      }

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
