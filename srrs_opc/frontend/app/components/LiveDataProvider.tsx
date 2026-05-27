"use client";

import { useEffect, useRef, useCallback } from "react";
import { useTopologyStore } from "@/stores/topologyStore";
import { srraApi } from "@/lib/api";

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
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const setNodes = useTopologyStore((s) => s.setNodes);
  const setEdges = useTopologyStore((s) => s.setEdges);

  const fetchTopology = useCallback(async () => {
    if (!isMounted.current) return;
    try {
      const data = await srraApi.topology();
      if (data.nodes && data.edges) {
        setNodes(data.nodes as any);
        setEdges(data.edges as any);
      }
    } catch (err) {
      // API not available, will retry
    }
  }, [setNodes, setEdges]);

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      if (!isMounted.current) return;
      switch (msg.type) {
        case "topology":
          setNodes((msg.data as any).nodes);
          setEdges((msg.data as any).edges);
          break;
        case "nodes":
          setNodes(msg.data as any);
          break;
        case "edges":
          setEdges(msg.data as any);
          break;
      }
    },
    [setNodes, setEdges]
  );

  useEffect(() => {
    isMounted.current = true;

    // Initial fetch
    fetchTopology();

    // Try WebSocket first
    const connect = () => {
      if (!isMounted.current) return;
      try {
        const ws = new WebSocket("ws://localhost:8001/ws");

        ws.onopen = () => {
          reconnectCount.current = 0;
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
          if (isMounted.current && reconnectCount.current < 10) {
            reconnectTimer.current = setTimeout(() => {
              reconnectCount.current++;
              connect();
            }, 3000 * Math.min(reconnectCount.current + 1, 5));
          }
        };

        ws.onerror = () => {
          // Fall back to polling
          if (pollTimer.current === null) {
            pollTimer.current = setInterval(fetchTopology, 5000);
          }
        };

        wsRef.current = ws;
      } catch {
        // Fall back to polling
        if (pollTimer.current === null) {
          pollTimer.current = setInterval(fetchTopology, 5000);
        }
      }
    };

    connect();

    return () => {
      isMounted.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (pollTimer.current) clearInterval(pollTimer.current);
      wsRef.current?.close();
    };
  }, [fetchTopology, handleMessage]);

  return null;
}