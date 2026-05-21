"use client";

import { useEffect, useRef, useState, useCallback } from "react";

const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000";

export interface WebSocketState<T> {
  data: T | null;
  status: "connecting" | "connected" | "disconnected";
  reconnectCount: number;
  lastError: string | null;
  lastMessageAt: Date | null;
}

export function useWebSocket<T>(path: string, enabled = true): WebSocketState<T> {
  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const [reconnectCount, setReconnectCount] = useState(0);
  const [lastError, setLastError] = useState<string | null>(null);
  const [lastMessageAt, setLastMessageAt] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (!enabled) return;
    setStatus("connecting");
    setLastError(null);
    const ws = new WebSocket(`${WS_BASE}${path}`);

    ws.onopen = () => {
      setStatus("connected");
      setLastError(null);
    };

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as T;
        setData(parsed);
        setLastMessageAt(new Date());
        setLastError(null);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      setReconnectCount((c) => c + 1);
      // Auto-reconnect with exponential backoff (max 30s)
      const delay = Math.min(3000 * Math.pow(1.5, reconnectCount), 30000);
      timerRef.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      setLastError("WebSocket connection failed");
      ws.close();
    };

    wsRef.current = ws;
  }, [path, enabled, reconnectCount]);

  useEffect(() => {
    connect();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { data, status, reconnectCount, lastError, lastMessageAt };
}
