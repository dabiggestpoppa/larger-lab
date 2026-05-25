"use client";

import { useEffect, useRef, useCallback } from "react";
import { useTaskStore } from "@/stores/taskStore";
import { useAgentStore } from "@/stores/agentStore";
import { useSessionStore } from "@/stores/sessionStore";
import { useUIStore } from "@/stores/uiStore";

type WSMessage = {
  type: string;
  data: unknown;
  timestamp?: string;
};

export default function LiveDataProvider() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMounted = useRef(true);

  const setAgents = useAgentStore((s) => s.setAgents);
  const setTasks = useTaskStore((s) => s.setTasks);
  const setSessions = useSessionStore((s) => s.setSessions);
  const setConnectionStatus = useUIStore((s) => s.setConnectionStatus);
  const addNotification = useUIStore((s) => s.addNotification);

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      if (!isMounted.current) return;
      switch (msg.type) {
        case "agents":
          setAgents(msg.data as any);
          break;
        case "tasks":
          setTasks(msg.data as any);
          break;
        case "sessions":
          setSessions(msg.data as any);
          break;
        case "notification":
          addNotification(msg.data as any);
          break;
      }
    },
    [setAgents, setTasks, setSessions, setConnectionStatus, addNotification]
  );

  useEffect(() => {
    isMounted.current = true;

    const connect = () => {
      if (!isMounted.current) return;
      try {
        const ws = new WebSocket("ws://localhost:8000/ws");

        ws.onopen = () => {
          reconnectCount.current = 0;
          setConnectionStatus("connected");
        };

        ws.onmessage = (event) => {
          try {
            const msg: WSMessage = JSON.parse(event.data);
            handleMessage(msg);
          } catch {
            // ignore non-JSON
          }
        };

        ws.onclose = () => {
          setConnectionStatus("disconnected");
          if (isMounted.current && reconnectCount.current < 10) {
            reconnectTimer.current = setTimeout(() => {
              reconnectCount.current++;
              connect();
            }, 3000 * Math.min(reconnectCount.current + 1, 5));
          }
        };

        ws.onerror = () => {
          setConnectionStatus("error");
        };

        wsRef.current = ws;
      } catch {
        setConnectionStatus("error");
      }
    };

    connect();

    return () => {
      isMounted.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [handleMessage, setConnectionStatus]);

  return null;
}
