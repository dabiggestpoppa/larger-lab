/**
 * Chat Store - Zustand store for PO chat with real-time SSE streaming.
 * Persists sessions and messages to localStorage for cross-session continuity.
 * Syncs with backend OCE API for field-aware context.
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
  source?: "web" | "telegram";  // Track which channel the message came from
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
  persistToStorage: () => void;
  loadFromStorage: () => void;
}

let msgCounter = 0;
const nextId = (p: string) => `${p}_${Date.now()}_${++msgCounter}`;

// localStorage keys
const STORAGE_KEY_SESSIONS = "oce_chat_sessions";
const STORAGE_KEY_MESSAGES_PREFIX = "oce_chat_msgs_";
const STORAGE_KEY_ACTIVE = "oce_chat_active_session";

function saveSessionsToStorage(sessions: ChatSession[]) {
  try { localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(sessions)); } catch { /* quota */ }
}

function saveMessagesToStorage(sessionId: string, messages: ChatMessage[]) {
  try { localStorage.setItem(`${STORAGE_KEY_MESSAGES_PREFIX}${sessionId}`, JSON.stringify(messages)); } catch { /* quota */ }
}

function loadSessionsFromStorage(): ChatSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_SESSIONS);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

export function loadMessagesFromStorage(sessionId: string): ChatMessage[] {
  try {
    const raw = localStorage.getItem(`${STORAGE_KEY_MESSAGES_PREFIX}${sessionId}`);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

const isBrowser = typeof window !== "undefined";

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  sessions: isBrowser ? loadSessionsFromStorage() : [],
  activeSessionId: isBrowser ? (localStorage.getItem(STORAGE_KEY_ACTIVE) || null) : null,
  isLoading: false,
  isSending: false,
  error: null,
  streamStatus: { active: false, stage: "", detail: "" },

  setMessages: (m) => { set({ messages: m }); saveMessagesToStorage(get().activeSessionId || "default", m); },
  addMessage: (m) => {
    const msgs = [...get().messages, m];
    set({ messages: msgs });
    saveMessagesToStorage(m.session_id || get().activeSessionId || "default", msgs);
  },
  setSessions: (s) => { set({ sessions: s }); saveSessionsToStorage(s); },
  setActiveSession: (id) => {
    set({ activeSessionId: id });
    if (id) localStorage.setItem(STORAGE_KEY_ACTIVE, id);
    else localStorage.removeItem(STORAGE_KEY_ACTIVE);
    // Load messages for this session from storage
    if (id) {
      const msgs = loadMessagesFromStorage(id);
      if (msgs.length > 0) set({ messages: msgs });
    }
  },
  setLoading: (v) => set({ isLoading: v }),
  setSending: (v) => set({ isSending: v }),
  setError: (e) => set({ error: e }),
  setStreamStatus: (s) => set({ streamStatus: s }),

  persistToStorage: () => {
    saveSessionsToStorage(get().sessions);
    const sid = get().activeSessionId;
    if (sid) saveMessagesToStorage(sid, get().messages);
  },

  loadFromStorage: () => {
    const sessions = loadSessionsFromStorage();
    const activeId = localStorage.getItem(STORAGE_KEY_ACTIVE);
    set({ sessions, activeSessionId: activeId });
    if (activeId) {
      const msgs = loadMessagesFromStorage(activeId);
      if (msgs.length > 0) set({ messages: msgs });
    }
  },

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
    const sid = sessionId || get().activeSessionId || `session_${Date.now()}`;
    set({ isSending: true, error: null, streamStatus: { active: true, stage: "thinking", detail: "Thinking..." } });

    const userMsg: ChatMessage = {
      message_id: nextId("usr"), role: "user", content: message,
      timestamp: new Date().toISOString(), session_id: sid, source: "web",
    };
    set((s) => ({ messages: [...s.messages, userMsg] }));
    saveMessagesToStorage(sid, [...get().messages, userMsg]);

    // Create session if it doesn't exist
    const existingSession = get().sessions.find(s => s.session_id === sid);
    if (!existingSession) {
      const newSession: ChatSession = {
        session_id: sid, title: message.substring(0, 40),
        created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
        entry_count: 1, last_role: "user", last_preview: message.substring(0, 60),
      };
      const updatedSessions = [...get().sessions, newSession];
      set({ sessions: updatedSessions, activeSessionId: sid });
      saveSessionsToStorage(updatedSessions);
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 min timeout

      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sid }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let accumulatedResponse = "";
      let streamError = null;
      let chunkCount = 0;

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
                set({ streamStatus: { active: true, stage: "tool_call", detail: `🔧 ${edata.tool}`, tool: edata.tool } });
              } else if (etype === "tool_result") {
                const prev = (edata.result || "").substring(0, 80);
                set({ streamStatus: { active: true, stage: "tool_result", detail: `✅ ${edata.tool}: ${prev}...` } });
              } else if (etype === "complete" || etype === "max_rounds") {
                set({ streamStatus: { active: true, stage: "responding", detail: "Generating response..." } });
              } else if (etype === "final") {
                accumulatedResponse = edata.response || "";
              } else if (etype === "chunk") {
                const delta = evt.choices?.[0]?.delta?.content || edata.content || "";
                if (delta) { accumulatedResponse += delta; chunkCount++; }
              } else if (etype === "done") {
                set({ streamStatus: { active: true, stage: "responding", detail: "Finalizing..." } });
              } else if (etype === "error") {
                streamError = edata.message || "Unknown error";
                set({ streamStatus: { active: true, stage: "error", detail: streamError } });
              }
            } catch (_) { /* skip malformed */ }
          }
        }
      }

      // Add the observer message with whatever response we got
      if (accumulatedResponse) {
        const obsMsg: ChatMessage = {
          message_id: nextId("obs"),
          role: "observer",
          content: accumulatedResponse,
          timestamp: new Date().toISOString(),
          session_id: sid,
        };
        set((s) => ({
          messages: [...s.messages, obsMsg],
          streamStatus: { active: false, stage: "done", detail: "" },
        }));
      } else if (streamError) {
        const errMsg: ChatMessage = {
          message_id: nextId("err"),
          role: "observer",
          content: `❌ Error: ${streamError}`,
          timestamp: new Date().toISOString(),
          session_id: sid,
        };
        set((s) => ({
          messages: [...s.messages, errMsg],
          streamStatus: { active: false, stage: "error", detail: streamError },
        }));
      } else {
        const noRespMsg: ChatMessage = {
          message_id: nextId("empty"),
          role: "observer",
          content: "⚠️ No response received. The agent may have timed out.",
          timestamp: new Date().toISOString(),
          session_id: sid,
        };
        set((s) => ({
          messages: [...s.messages, noRespMsg],
          streamStatus: { active: false, stage: "done", detail: "" },
        }));
      }
    } catch (err: any) {
      set({ error: err.message || "Failed to send", streamStatus: { active: false, stage: "error", detail: "Connection failed" } });
    } finally {
      set({ isSending: false });
    }
  },

  createSession: async (title?: string) => {
    const sid = `session_${Date.now()}`;
    const sessionTitle = title || `Chat ${new Date().toLocaleDateString()}`;
    const newSession: ChatSession = {
      session_id: sid, title: sessionTitle,
      created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
      entry_count: 0, last_role: "", last_preview: "",
    };
    const updatedSessions = [...get().sessions, newSession];
    set({ sessions: updatedSessions, activeSessionId: sid, messages: [] });
    saveSessionsToStorage(updatedSessions);
    // Also try to create on backend (non-critical)
    try {
      await fetch("/api/chat/sessions", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: sessionTitle }),
      });
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
