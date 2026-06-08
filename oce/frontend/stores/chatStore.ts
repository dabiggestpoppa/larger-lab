/**
 * Chat Store - Zustand store for PO chat with real-time SSE streaming.
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
}

interface ChatStore {
  messages: ChatMessage[];
  sessions: ChatSession[];
  activeSessionId: string | null;
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  streamStatus: StreamStatus;
  setMessages: (m: ChatMessage[]) => void;
  addMessage: (m: ChatMessage) => void;
  setSessions: (s: ChatSession[]) => void;
  setActiveSession: (id: string | null) => void;
  setLoading: (v: boolean) => void;
  setSending: (v: boolean) => void;
  setError: (e: string | null) => void;
  setStreamStatus: (s: StreamStatus) => void;
  loadSessions: () => Promise<void>;
  loadHistory: (sessionId: string) => Promise<void>;
  sendMessage: (message: string, sessionId?: string) => Promise<void>;
  createSession: (title?: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
}

let msgCounter = 0;
const nextId = (p: string) => `${p}_${Date.now()}_${++msgCounter}`;

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  sessions: [],
  activeSessionId: null,
  isLoading: false,
  isSending: false,
  error: null,
  streamStatus: { active: false, stage: "", detail: "" },

  setMessages: (m) => set({ messages: m }),
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  setSessions: (s) => set({ sessions: s }),
  setActiveSession: (id) => set({ activeSessionId: id }),
  setLoading: (v) => set({ isLoading: v }),
  setSending: (v) => set({ isSending: v }),
  setError: (e) => set({ error: e }),
  setStreamStatus: (s) => set({ streamStatus: s }),

  loadSessions: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch("/api/chat/sessions");
      const data = await res.json();
      set({ sessions: data.sessions || [] });
    } catch {
      set({ error: "Failed to load sessions" });
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
      const msgs: ChatMessage[] = raw.map((m: any) => ({
        message_id: m.message_id || nextId("msg"),
        role: m.role === "assistant" ? "observer" : (m.role || "user"),
        content: m.content || "",
        timestamp: m.timestamp || new Date().toISOString(),
        session_id: m.session_id || sessionId,
      }));
      set({ messages: msgs, activeSessionId: sessionId });
    } catch {
      set({ error: "Failed to load history" });
    } finally {
      set({ isLoading: false });
    }
  },

  sendMessage: async (message: string, sessionId?: string) => {
    const sid = sessionId || get().activeSessionId || "";
    set({
      isSending: true,
      error: null,
      streamStatus: { active: true, stage: "thinking", detail: "Thinking..." }
    });

    const userMsg: ChatMessage = {
      message_id: nextId("usr"),
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
      session_id: sid,
    };
    set((s) => ({ messages: [...s.messages, userMsg] }));

    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sid }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

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
              const etype = evt.type || evt.event;
              const edata = evt.data || {};

              if (etype === "round") {
                set({ streamStatus: { active: true, stage: "thinking", detail: `Round ${edata.round}/${edata.max}`, round: edata.round, maxRounds: edata.max } });
              } else if (etype === "tool_call") {
                set({ streamStatus: { active: true, stage: "tool_call", detail: `Tool: ${edata.tool}`, tool: edata.tool } });
              } else if (etype === "tool_result") {
                const prev = (edata.result || "").substring(0, 60);
                set({ streamStatus: { active: true, stage: "tool_result", detail: `${edata.tool}: ${prev}` } });
              } else if (etype === "complete" || etype === "max_rounds") {
                set({ streamStatus: { active: true, stage: "responding", detail: "Generating response..." } });
              } else if (etype === "final") {
                finalData = edata;
              } else if (etype === "error") {
                set({ streamStatus: { active: true, stage: "error", detail: edata.message || "Error" } });
              }
            } catch (_) { /* skip malformed */ }
          }
        }
      }

      if (finalData) {
        const obsMsg: ChatMessage = {
          message_id: nextId("obs"),
          role: "observer",
          content: finalData.response || "No response",
          timestamp: new Date().toISOString(),
          session_id: finalData.session_id || sid,
        };
        set((s) => ({
          messages: [...s.messages, obsMsg],
          streamStatus: { active: false, stage: "done", detail: "" },
        }));
      } else {
        set({ streamStatus: { active: false, stage: "", detail: "" } });
      }
    } catch (err: any) {
      set({ error: err.message || "Failed to send", streamStatus: { active: false, stage: "error", detail: "Connection failed" } });
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
      }
    } catch { /* ignore */ }
  },

  deleteSession: async (sessionId: string) => {
    try {
      await fetch(`/api/chat/sessions/${sessionId}`, { method: "DELETE" });
      if (get().activeSessionId === sessionId) {
        set({ activeSessionId: null, messages: [] });
      }
    } catch { /* ignore */ }
  },
}));
