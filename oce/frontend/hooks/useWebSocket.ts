"use client";

import { useEffect, useRef, useCallback, useState } from "react";

type WSMessage = {
  type: string;
  data: unknown;
  timestamp?: string;
};

type WSOptions = {
  url: string;
  onMessage?: (msg: WSMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (err: Event) => void;
  reconnectInterval?: number;
  maxReconnects?: number;
};

export function useWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  reconnectInterval = 3000,
  maxReconnects = 10,
}: WSOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [status, setStatus] = useState<"connecting" | "open" | "closed" | "error">("closed");

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setStatus("open");
      reconnectCount.current = 0;
      onConnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        onMessage?.(msg);
      } catch {
        // ignore non-JSON messages
      }
    };

    ws.onclose = () => {
      setStatus("closed");
      onDisconnect?.();
      if (reconnectCount.current < maxReconnects) {
        reconnectTimer.current = setTimeout(() => {
          reconnectCount.current++;
          connect();
        }, reconnectInterval * Math.min(reconnectCount.current + 1, 5));
      }
    };

    ws.onerror = (err) => {
      setStatus("error");
      onError?.(err);
    };

    wsRef.current = ws;
  }, [url, onMessage, onConnect, onDisconnect, onError, reconnectInterval, maxReconnects]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    reconnectCount.current = maxReconnects; // prevent reconnect
    wsRef.current?.close();
    wsRef.current = null;
  }, [maxReconnects]);

  const send = useCallback((msg: WSMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { status, send, connect, disconnect };
}
