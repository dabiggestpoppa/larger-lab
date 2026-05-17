"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import {
  MessageSquare, Plus, Send, Users, Hash, Radio,
  ChevronRight, X, Bot, User, Settings, Trash2,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────
interface Agent {
  session_key: string;
  label: string;
  role: string;
  status: string;
  last_seen: string;
  capabilities: string[];
}

interface Message {
  id: string;
  sender: string;
  content: string;
  message_type: string;
  timestamp: string;
}

interface Room {
  id: string;
  name: string;
  description: string;
  agent_ids: string[];
  messages: Message[];
  status: string;
  created_at: string;
  updated_at: string;
  persistent: boolean;
}

// ── API Helpers ──────────────────────────────────────────────────────────────
const CC = {
  agents: () => fetch("/command-center/agents").then(r => r.json()),
  registerAgent: (a: Partial<Agent>) =>
    fetch("/command-center/agents/register", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(a),
    }).then(r => r.json()),
  rooms: () => fetch("/command-center/rooms").then(r => r.json()),
  createRoom: (name: string, description: string, agent_ids: string[]) =>
    fetch("/command-center/rooms", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description, agent_ids, persistent: true }),
    }).then(r => r.json()),
  getRoom: (id: string) => fetch(`/command-center/rooms/${id}`).then(r => r.json()),
  sendMessage: (roomId: string, sender: string, content: string) =>
    fetch(`/command-center/rooms/${roomId}/message`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ room_id: roomId, sender, content, message_type: "text" }),
    }).then(r => r.json()),
  deleteRoom: (id: string) =>
    fetch(`/command-center/rooms/${id}`, { method: "DELETE" }).then(r => r.json()),
  addAgentToRoom: (roomId: string, sessionKey: string) =>
    fetch(`/command-center/rooms/${roomId}/agents?session_key=${sessionKey}`, {
      method: "POST",
    }).then(r => r.json()),
};

// ── Main Component ───────────────────────────────────────────────────────────
export default function CommandCenter() {
  const [agents, setAgents] = useState<Record<string, Agent>>({});
  const [rooms, setRooms] = useState<Record<string, Room>>({});
  const [activeRoom, setActiveRoom] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState("");
  const [showCreateRoom, setShowCreateRoom] = useState(false);
  const [showAgentPanel, setShowAgentPanel] = useState(false);
  const [newRoomName, setNewRoomName] = useState("");
  const [newRoomDesc, setNewRoomDesc] = useState("");
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadData = useCallback(async () => {
    try {
      const [agentsRes, roomsRes] = await Promise.all([CC.agents(), CC.rooms()]);
      setAgents(agentsRes.agents || {});
      setRooms(roomsRes.rooms || {});
    } catch (e) { console.error("Failed to load Command Center data:", e); }
  }, []);

  useEffect(() => { loadData(); }, [loadData, refreshKey]);
  useEffect(() => {
    const interval = setInterval(() => setRefreshKey(k => k + 1), 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateRoom = async () => {
    if (!newRoomName.trim()) return;
    await CC.createRoom(newRoomName, newRoomDesc, selectedAgents);
    setNewRoomName("");
    setNewRoomDesc("");
    setSelectedAgents([]);
    setShowCreateRoom(false);
    setRefreshKey(k => k + 1);
  };

  const handleSend = async () => {
    if (!activeRoom || !newMessage.trim()) return;
    await CC.sendMessage(activeRoom, "mad", newMessage);
    setNewMessage("");
    setRefreshKey(k => k + 1);
  };

  const handleDeleteRoom = async (id: string) => {
    await CC.deleteRoom(id);
    if (activeRoom === id) setActiveRoom(null);
    setRefreshKey(k => k + 1);
  };

  const currentRoom = activeRoom ? rooms[activeRoom] : null;
  const agentList = Object.values(agents);

  return (
    <div className="flex h-screen bg-[#0a0a0f] text-gray-100">
      {/* ── Sidebar: Rooms ─────────────────────────────────────────────── */}
      <div className="w-72 border-r border-[#27272a] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-[#27272a]">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg font-bold flex items-center gap-2">
              <Radio className="w-5 h-5 text-cyan-400" />
              Command Center
            </h1>
            <button
              onClick={() => setShowAgentPanel(!showAgentPanel)}
              className="p-1.5 rounded hover:bg-[#1a1a24] text-gray-400 hover:text-white"
              title="Manage Agents"
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
          <button
            onClick={() => setShowCreateRoom(true)}
            className="w-full flex items-center gap-2 px-3 py-2 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-cyan-400 hover:bg-cyan-500/20 transition-colors text-sm"
          >
            <Plus className="w-4 h-4" />
            New Room
          </button>
        </div>

        {/* Agent Panel (collapsible) */}
        {showAgentPanel && (
          <div className="p-3 border-b border-[#27272a] bg-[#111118]">
            <div className="text-xs text-gray-500 mb-2 font-medium">REGISTERED AGENTS ({agentList.length})</div>
            {agentList.length === 0 && (
              <div className="text-xs text-gray-600 italic">No agents registered</div>
            )}
            {agentList.map(a => (
              <div key={a.session_key} className="flex items-center gap-2 py-1.5 text-xs">
                <div className={`w-2 h-2 rounded-full ${a.status === "online" ? "bg-green-400" : "bg-gray-600"}`} />
                <Bot className="w-3 h-3 text-gray-500" />
                <span className="text-gray-300 truncate">{a.label}</span>
              </div>
            ))}
          </div>
        )}

        {/* Room List */}
        <div className="flex-1 overflow-y-auto">
          {Object.keys(rooms).length === 0 && (
            <div className="p-4 text-center text-gray-600 text-sm">
              No rooms yet. Create one to start.
            </div>
          )}
          {Object.values(rooms).map(room => (
            <button
              key={room.id}
              onClick={() => setActiveRoom(room.id)}
              className={`w-full text-left p-3 border-b border-[#1a1a24] hover:bg-[#111118] transition-colors ${
                activeRoom === room.id ? "bg-[#111118] border-l-2 border-l-cyan-400" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Hash className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium truncate">{room.name}</span>
                </div>
                <div className="flex items-center gap-1">
                  {room.persistent && (
                    <div className="w-2 h-2 rounded-full bg-green-400/60" title="Persistent" />
                  )}
                  <span className="text-xs text-gray-600">{room.messages.length}</span>
                </div>
              </div>
              {room.agent_ids.length > 0 && (
                <div className="flex items-center gap-1 mt-1">
                  <Users className="w-3 h-3 text-gray-600" />
                  <span className="text-xs text-gray-600">{room.agent_ids.length} agent(s)</span>
                </div>
              )}
              {room.messages.length > 0 && (
                <div className="text-xs text-gray-600 mt-1 truncate">
                  {room.messages[room.messages.length - 1].content.substring(0, 60)}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* ── Main: Chat Area ────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col">
        {currentRoom ? (
          <>
            {/* Room Header */}
            <div className="p-4 border-b border-[#27272a] flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <Hash className="w-5 h-5 text-cyan-400" />
                  {currentRoom.name}
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">{currentRoom.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">
                  {currentRoom.messages.length} messages
                </span>
                <button
                  onClick={() => handleDeleteRoom(currentRoom.id)}
                  className="p-1.5 rounded hover:bg-red-500/10 text-gray-500 hover:text-red-400"
                  title="Delete Room"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {currentRoom.messages.map(msg => (
                <div key={msg.id} className={`flex gap-3 ${msg.sender === "mad" ? "flex-row-reverse" : ""}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    msg.sender === "mad"
                      ? "bg-cyan-500/20 text-cyan-400"
                      : msg.sender === "system"
                      ? "bg-gray-700/50 text-gray-500"
                      : "bg-purple-500/20 text-purple-400"
                  }`}>
                    {msg.sender === "mad" ? <User className="w-4 h-4" /> :
                     msg.sender === "system" ? <Settings className="w-4 h-4" /> :
                     <Bot className="w-4 h-4" />}
                  </div>
                  <div className={`max-w-[70%] ${
                    msg.sender === "mad" ? "text-right" : ""
                  }`}>
                    <div className={`text-xs text-gray-500 mb-1 ${
                      msg.sender === "mad" ? "text-right" : ""
                    }`}>
                      {msg.sender === "mad" ? "MAD" : msg.sender}
                      <span className="ml-2 text-gray-700">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className={`rounded-lg px-3 py-2 text-sm ${
                      msg.sender === "mad"
                        ? "bg-cyan-500/10 border border-cyan-500/20"
                        : msg.sender === "system"
                        ? "bg-gray-800/50 border border-gray-700/50 text-gray-500 italic"
                        : "bg-[#111118] border border-[#27272a]"
                    }`}>
                      <pre className="whitespace-pre-wrap font-sans text-sm">{msg.content}</pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Input */}
            <div className="p-4 border-t border-[#27272a]">
              <div className="flex gap-2">
                <input
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleSend()}
                  placeholder="Type a message to send to this room..."
                  className="flex-1 bg-[#111118] border border-[#27272a] rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-cyan-500/50 placeholder-gray-600"
                />
                <button
                  onClick={handleSend}
                  className="px-4 py-2 bg-cyan-500/20 border border-cyan-500/30 rounded-lg text-cyan-400 hover:bg-cyan-500/30 transition-colors"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-600">
            <div className="text-center">
              <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-700" />
              <p className="text-lg">Select a room or create a new one</p>
              <p className="text-sm mt-1">Talk to any agent, create teams, run rooms in background</p>
            </div>
          </div>
        )}
      </div>

      {/* ── Create Room Modal ───────────────────────────────────────────── */}
      {showCreateRoom && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-[#111118] border border-[#27272a] rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">Create Room</h3>
              <button onClick={() => setShowCreateRoom(false)} className="text-gray-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <input
              value={newRoomName}
              onChange={e => setNewRoomName(e.target.value)}
              placeholder="Room name (e.g. Quant Lab Team)"
              className="w-full bg-[#0a0a0f] border border-[#27272a] rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:border-cyan-500/50"
            />
            <input
              value={newRoomDesc}
              onChange={e => setNewRoomDesc(e.target.value)}
              placeholder="Description (optional)"
              className="w-full bg-[#0a0a0f] border border-[#27272a] rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:border-cyan-500/50"
            />
            {agentList.length > 0 && (
              <div className="mb-4">
                <div className="text-xs text-gray-500 mb-2">Add agents to room:</div>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {agentList.map(a => (
                    <label key={a.session_key} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedAgents.includes(a.session_key)}
                        onChange={e => {
                          if (e.target.checked) setSelectedAgents([...selectedAgents, a.session_key]);
                          else setSelectedAgents(selectedAgents.filter(s => s !== a.session_key));
                        }}
                        className="rounded border-gray-600"
                      />
                      <Bot className="w-3 h-3 text-gray-500" />
                      <span className="text-gray-300">{a.label}</span>
                      <span className="text-xs text-gray-600">({a.role})</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowCreateRoom(false)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateRoom}
                className="px-4 py-2 bg-cyan-500/20 border border-cyan-500/30 rounded-lg text-cyan-400 hover:bg-cyan-500/30 text-sm"
              >
                Create Room
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
