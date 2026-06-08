/**
 * Chat Store
 * Zustand store for chat state — messages, sessions, active conversation.
 * Supports real-time SSE streaming with live progress tracking.
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

export interface StreamStatus {
  active: boolean;
  stage: string;
  detail: string;
  round?: number;
  maxRounds?: number;
  tool?: string;
  toolResult?: string;
}

interface ChatStore {
  messages: ChatMessage[];
  sessions: ChatSession[];
  activeSessionId: string | null;
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  streamStatus: StreamStatus;

  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  setSessions: (sessions: ChatSession[]) => void;
  setActiveSession: (sessionId: string | null) => void;
  setLoading: (loading: boolean) => void;
  setSending: (sending: boolean) => void;
  setError: (error: string | null) => void;
  setStreamStatus: (status: StreamStatus) => void;
  clearStreamStatus: () => void;

  loadSessions: () => Promise<void>;
  loadHistory: (sessionId: string) => Promise<void>;
  sendMessage: (message: string, sessionId?: string) => Promise<void>;
  createSession: (title?: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  searchMessages: (query: string) => Promise<ChatMessage[]>;
}

export const useChatStore = create<ChatStore>((set, get) => {
  let messageCounter = 0;

  const getNextId = (prefix: string) => {
    messageCounter += 1;
    return `${prefix}_${Date.now()}_${messageCounter}`;
  };

  return {
    messages: [],
    sessions: [],
    activeSessionId: null,
    isLoading: false,
    isSending: false,
    error: null,
    streamStatus: { active: false, stage: "", detail: "" },

    setMessages: (messages) => set({ messages }),
    addMessage: (message) => set((s) => ({ messages: [...s.messages, message] })),
    setSessions: (sessions) => set({ sessions }),
    setActiveSession: (sessionId) => set({ activeSessionId: sessionId }),
    setLoading: (loading) => set({ isLoading: loading }),
    setSending: (sending) => set({ isSending: sending }),
    setError: (error) => set({ error }),
    setStreamStatus: (status) => set({ streamStatus: status }),
    clearStreamStatus: () => set({ streamStatus: { active: false, stage: "", detail: "" } }),

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
        const raw = data.messages || data.entries || [];
        const msgs: ChatMessage[] = raw.map((m: Record<string, unknown>) => ({
          message_id: (m.message_id as string) || getNextId("msg"),
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
      set({
        isSending: true,
        error: null,
        streamStatus: { active: true, stage: "thinking", detail: "🧠 Thinking..." }
      });

      const userMsg: ChatMessage = {
        message_id: getNextId("local"),
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
        session_id: sessionId || get().activeSessionId || "",
      };
      set((s) => ({ messages: [...s.messages, userMsg] }));

      try {
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

        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let finalData: any = null;

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
              if (!jsonStr || jsonStr === "[DONE]") continue;

              try {
                const evt = JSON.parse(jsonStr);
                const eventType = evt.type || evt.event;
                const data = evt.data || {};

                if (eventType === "round") {
                  set({
                    streamStatus: {
                      active: true,
                      stage: "thinking",
                      detail: `🔄 Round ${data.round}/${data.max} — Thinking...`,
                      round: data.round,
                      maxRounds: data.max,
                    }
                  });
                } else if (eventType === "tool_call") {
                  set({
                    streamStatus: {
                      active: true,
                      stage: "tool_call",
                      detail: `🔧 ${data.tool}`,
                      tool: data.tool,
                      round: data.round,
                    }
                  });
                } else if (eventType === "tool_result") {
                  const preview = (data.result || "").substring(0, 80);
                  set({
                    streamStatus: {
                      active: true,
                      stage: "tool_result",
                      detail: `📋 ${data.tool}: ${preview}${data.result?.length > 80 ? "…" : ""}`,
                      tool: data.tool,
                      toolResult: preview,
                    }
                  });
                } else if (eventType === "complete") {
                  set({
                    streamStatus: {
                      active: true,
                      stage: "responding",
                      detail: "💬 Generating response...",
                    }
                  });
                } else if (eventType === "max_rounds") {
                  set({
                    streamStatus: {
                      active: true,
                      stage: "responding",
                      detail: "⚠️ Max rounds — Generating final response...",
                    }
                  });
                } else if (eventType === "final") {
                  finalData = data;
                } else if (eventType === "error") {
                  set({
                    streamStatus: {
                      active: true,
                      stage: "error",
                      detail: `❌ ${data.message || "Unknown error"}`,
                    }
                  });
                }
              } catch (_parseErr) {
                // Skip malformed SSE events
              }
            }
          }
        }

        // Add final response as a chat message
        if (finalData) {
          const observerMsg: ChatMessage = {
            message_id: getNextId("observer"),
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
          set((s) => ({
            messages: [...s.messages, observerMsg],
            streamStatus: { active: false, stage: "complete", detail: "" },
          }));
        } else {
          set({ streamStatus: { active: false, stage: "", detail: "" } });
        }

        await get().loadSessions();
      } catch (err) {
        set({
          error: "Failed to send message",
          streamStatus: { active: false, stage: "error", detail: "Connection failed" },
        });
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
  };
});
