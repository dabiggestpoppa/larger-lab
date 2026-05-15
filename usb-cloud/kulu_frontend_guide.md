# Kulu Node Orchestration System: Frontend Implementation Guide

This step-by-step guide provides detailed instructions for implementing the frontend components of the Kulu Node Orchestration System, focusing on the Local Node Electron application that serves as the user interface and control plane.

## Technology Stack

- **Electron**: Cross-platform desktop application framework
- **React**: UI library for component-based interface development
- **TypeScript**: Type-safe JavaScript for robust application development
- **WebSockets**: Real-time communication with backend services
- **TailwindCSS**: Utility-first CSS framework for styling
- **Vite**: Build tool for fast development and optimized production builds

## Project Structure

```
frontend/
├── electron/
│   ├── main.ts                 # Electron main process
│   ├── preload.ts              # Preload script for IPC
│   └── electron-builder.json   # Electron builder configuration
├── src/
│   ├── assets/                 # Static assets
│   ├── components/             # Reusable UI components
│   │   ├── common/             # Common UI elements
│   │   ├── charts/             # Data visualization components
│   │   ├── cognitive-mirror/   # Cognitive Mirror interface
│   │   └── field-status/       # Field status components
│   ├── contexts/               # React contexts
│   ├── hooks/                  # Custom React hooks
│   ├── pages/                  # Application pages
│   │   ├── Dashboard/          # Main dashboard
│   │   ├── FieldStatus/        # Field status page
│   │   ├── NodeManager/        # Node management page
│   │   ├── AgentManager/       # Agent management page
│   │   └── Settings/           # Settings page
│   ├── services/               # Service integrations
│   │   ├── api.ts              # API client
│   │   ├── websocket.ts        # WebSocket client
│   │   └── ipc.ts              # IPC communication
│   ├── store/                  # State management
│   ├── types/                  # TypeScript type definitions
│   ├── utils/                  # Utility functions
│   ├── App.tsx                 # Main application component
│   ├── main.tsx                # Application entry point
│   └── vite-env.d.ts           # Vite environment types
├── .eslintrc.json              # ESLint configuration
├── .prettierrc                 # Prettier configuration
├── index.html                  # HTML entry point
├── package.json                # Project dependencies
├── tsconfig.json               # TypeScript configuration
└── vite.config.ts              # Vite configuration
```

## Step 1: Set Up Project Structure

```bash
# Create project directory
mkdir -p kulu-orchestration/frontend
cd kulu-orchestration/frontend

# Initialize package.json
npm init -y

# Install dependencies
npm install react react-dom react-router-dom @types/react @types/react-dom @types/node
npm install electron electron-builder vite @vitejs/plugin-react typescript
npm install tailwindcss postcss autoprefixer
npm install chart.js react-chartjs-2 d3 @visx/visx
npm install axios socket.io-client electron-store
npm install @headlessui/react @heroicons/react

# Install dev dependencies
npm install -D eslint prettier eslint-plugin-react eslint-plugin-react-hooks
npm install -D @typescript-eslint/eslint-plugin @typescript-eslint/parser

# Initialize TypeScript
npx tsc --init

# Initialize Tailwind CSS
npx tailwindcss init -p
```

## Step 2: Configure Build Tools

### Vite Configuration (vite.config.ts)

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
  },
});
```

### Electron Builder Configuration (electron-builder.json)

```json
{
  "appId": "com.kulu.orchestration",
  "productName": "Kulu Orchestration",
  "directories": {
    "output": "release/${version}"
  },
  "files": [
    "dist/**/*",
    "electron/**/*"
  ],
  "mac": {
    "category": "public.app-category.developer-tools",
    "target": ["dmg", "zip"]
  },
  "win": {
    "target": ["nsis", "portable"]
  },
  "linux": {
    "target": ["AppImage", "deb"],
    "category": "Development"
  }
}
```

### TypeScript Configuration (tsconfig.json)

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ESNext"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": false,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## Step 3: Set Up Electron Main Process

### Main Process (electron/main.ts)

```typescript
import { app, BrowserWindow, ipcMain, shell } from 'electron';
import * as path from 'path';
import * as url from 'url';
import * as fs from 'fs';

// Handle creating/removing shortcuts on Windows when installing/uninstalling
if (require('electron-squirrel-startup')) {
  app.quit();
}

let mainWindow: BrowserWindow | null = null;

const createWindow = () => {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Load the app
  if (app.isPackaged) {
    // Production mode
    mainWindow.loadURL(
      url.format({
        pathname: path.join(__dirname, '../dist/index.html'),
        protocol: 'file:',
        slashes: true,
      })
    );
  } else {
    // Development mode
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  }

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
};

// Create window when Electron is ready
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for communication with renderer process
ipcMain.handle('get-app-path', () => app.getPath('userData'));

// Handler for starting the local node
ipcMain.handle('start-local-node', async () => {
  try {
    const { spawn } = require('child_process');
    const nodeProcess = spawn('python', ['../nodes/local_node.py', '--node-id', 'local-node'], {
      detached: true,
      stdio: 'ignore',
    });
    nodeProcess.unref();
    return { success: true };
  } catch (error) {
    console.error('Failed to start local node:', error);
    return { success: false, error: error.message };
  }
});

// Handler for checking node status
ipcMain.handle('check-node-status', async () => {
  try {
    const { execFile } = require('child_process');
    return new Promise((resolve, reject) => {
      execFile('python', ['../scripts/check_node_status.py'], (error, stdout, stderr) => {
        if (error) {
          reject({ success: false, error: error.message });
          return;
        }
        resolve({ success: true, data: JSON.parse(stdout) });
      });
    });
  } catch (error) {
    console.error('Failed to check node status:', error);
    return { success: false, error: error.message };
  }
});
```

### Preload Script (electron/preload.ts)

```typescript
import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  getAppPath: () => ipcRenderer.invoke('get-app-path'),
  startLocalNode: () => ipcRenderer.invoke('start-local-node'),
  checkNodeStatus: () => ipcRenderer.invoke('check-node-status'),
});
```

## Step 4: Implement Core React Components

### Application Entry Point (src/main.tsx)

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

### Main Application Component (src/App.tsx)

```tsx
import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { NodeStatusProvider } from './contexts/NodeStatusContext';
import { AgentProvider } from './contexts/AgentContext';
import Sidebar from './components/common/Sidebar';
import Header from './components/common/Header';
import Dashboard from './pages/Dashboard';
import FieldStatus from './pages/FieldStatus';
import NodeManager from './pages/NodeManager';
import AgentManager from './pages/AgentManager';
import Settings from './pages/Settings';
import './App.css';

const App: React.FC = () => {
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Check if local node is running
    window.electronAPI.checkNodeStatus()
      .then((result) => {
        if (result.success) {
          setIsInitialized(true);
        }
      })
      .catch((error) => {
        console.error('Error checking node status:', error);
      });
  }, []);

  const handleInitialize = async () => {
    try {
      const result = await window.electronAPI.startLocalNode();
      if (result.success) {
        setIsInitialized(true);
      } else {
        console.error('Failed to start local node:', result.error);
      }
    } catch (error) {
      console.error('Error starting local node:', error);
    }
  };

  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-4">Kulu Node Orchestration System</h1>
          <p className="text-gray-300 mb-6">The Local Node is not running. Initialize to start.</p>
          <button
            onClick={handleInitialize}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Initialize Local Node
          </button>
        </div>
      </div>
    );
  }

  return (
    <WebSocketProvider>
      <NodeStatusProvider>
        <AgentProvider>
          <div className="flex h-screen bg-gray-900 text-white">
            <Sidebar />
            <div className="flex flex-col flex-1 overflow-hidden">
              <Header />
              <main className="flex-1 overflow-y-auto p-4">
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/field-status" element={<FieldStatus />} />
                  <Route path="/node-manager" element={<NodeManager />} />
                  <Route path="/agent-manager" element={<AgentManager />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </main>
            </div>
          </div>
        </AgentProvider>
      </NodeStatusProvider>
    </WebSocketProvider>
  );
};

export default App;
```

## Step 5: Implement WebSocket Communication

### WebSocket Context (src/contexts/WebSocketContext.tsx)

```tsx
import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react';

interface WebSocketContextType {
  connected: boolean;
  sendMessage: (type: string, payload: any) => void;
  lastMessage: any;
}

const WebSocketContext = createContext<WebSocketContextType>({
  connected: false,
  sendMessage: () => {},
  lastMessage: null,
});

export const useWebSocket = () => useContext(WebSocketContext);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const connectWebSocket = useCallback(() => {
    const socket = new WebSocket('ws://localhost:8000/ws');

    socket.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    socket.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      // Attempt to reconnect after a delay
      setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      socket.close();
    };

    socketRef.current = socket;
  }, []);

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connectWebSocket]);

  const sendMessage = useCallback((type: string, payload: any) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type, payload }));
    } else {
      console.error('WebSocket not connected');
    }
  }, []);

  return (
    <WebSocketContext.Provider value={{ connected, sendMessage, lastMessage }}>
      {children}
    </WebSocketContext.Provider>
  );
};
```

## Step 6: Implement Cognitive Mirror Interface

### Cognitive Mirror Component (src/components/cognitive-mirror/CognitiveMirror.tsx)

```tsx
import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../../contexts/WebSocketContext';
import CognitiveStream from './CognitiveStream';
import AgentGraph from './AgentGraph';
import VMMonitor from './VMMonitor';

type Tab = 'stream' | 'graph' | 'vm';

const CognitiveMirror: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('stream');
  const { connected, lastMessage } = useWebSocket();
  const [streamData, setStreamData] = useState<any[]>([]);
  const [graphData, setGraphData] = useState<any>({ nodes: [], links: [] });
  const [vmData, setVmData] = useState<any[]>([]);

  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === 'cognitive_stream') {
        setStreamData((prev) => [...prev, lastMessage.data].slice(-100));
      } else if (lastMessage.type === 'agent_graph') {
        setGraphData(lastMessage.data);
      } else if (lastMessage.type === 'vm_monitor') {
        setVmData(lastMessage.data);
      }
    }
  }, [lastMessage]);

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden h-full flex flex-col">
      <div className="border-b border-gray-700">
        <nav className="flex">
          <button
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'stream'
                ? 'text-blue-500 border-b-2 border-blue-500'
                : 'text-gray-400 hover:text-gray-300'
            }`}
            onClick={() => setActiveTab('stream')}
          >
            Cognitive Stream
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'graph'
                ? 'text-blue-500 border-b-2 border-blue-500'
                : 'text-gray-400 hover:text-gray-300'
            }`}
            onClick={() => setActiveTab('graph')}
          >
            Agent Graph
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'vm'
                ? 'text-blue-500 border-b-2 border-blue-500'
                : 'text-gray-400 hover:text-gray-300'
            }`}
            onClick={() => setActiveTab('vm')}
          >
            VM Monitor
          </button>
        </nav>
      </div>

      <div className="flex-1 overflow-hidden">
        {!connected && (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-400">Connecting to Kulu field...</p>
          </div>
        )}

        {connected && activeTab === 'stream' && <CognitiveStream data={streamData} />}
        {connected && activeTab === 'graph' && <AgentGraph data={graphData} />}
        {connected && activeTab === 'vm' && <VMMonitor data={vmData} />}
      </div>
    </div>
  );
};

export default CognitiveMirror;
```

### Cognitive Stream Component (src/components/cognitive-mirror/CognitiveStream.tsx)

```tsx
import React, { useRef, useEffect } from 'react';

interface Message {
  id: string;
  timestamp: string;
  agent_id: string;
  agent_type: string;
  content: string;
  level: 'info' | 'warning' | 'error' | 'debug';
}

interface CognitiveStreamProps {
  data: Message[];
}

const CognitiveStream: React.FC<CognitiveStreamProps> = ({ data }) => {
  const streamEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [data]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'text-red-500';
      case 'warning':
        return 'text-yellow-500';
      case 'info':
        return 'text-blue-500';
      case 'debug':
        return 'text-gray-500';
      default:
        return 'text-white';
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4 font-mono text-sm">
      {data.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-400">No cognitive stream data available</p>
        </div>
      ) : (
        data.map((message) => (
          <div key={message.id} className="mb-2">
            <span className="text-gray-500">[{new Date(message.timestamp).toLocaleTimeString()}]</span>{' '}
            <span className="text-purple-500">{message.agent_id}</span>{' '}
            <span className="text-gray-400">({message.agent_type})</span>:{' '}
            <span className={getLevelColor(message.level)}>{message.content}</span>
          </div>
        ))
      )}
      <div ref={streamEndRef} />
    </div>
  );
};

export default CognitiveStream;
```

## Step 7: Implement Field Status Dashboard

### Field Status Page (src/pages/FieldStatus/index.tsx)

```tsx
import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../../contexts/WebSocketContext';
import FieldCoherenceChart from './FieldCoherenceChart';
import NodeStatusTable from './NodeStatusTable';
import AgentAllocationChart from './AgentAllocationChart';
import BreathCycleStats from './BreathCycleStats';

const FieldStatus: React.FC = () => {
  const { connected, sendMessage, lastMessage } = useWebSocket();
  const [fieldStatus, setFieldStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (connected) {
      sendMessage('get_field_status', {});
      const interval = setInterval(() => {
        sendMessage('get_field_status', {});
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [connected, sendMessage]);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'field_status') {
      setFieldStatus(lastMessage.data);
      setLoading(false);
    }
  }, [lastMessage]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading field status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Field Status</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4">Field Coherence</h2>
          <FieldCoherenceChart data={fieldStatus?.coherence_history || []} />
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4">Breath Cycle Statistics</h2>
          <BreathCycleStats stats={fieldStatus?.breath_stats || {}} />
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4">Node Status</h2>
        <NodeStatusTable nodes={fieldStatus?.nodes || []} />
      </div>

      <div className="bg-gray-800 rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4">Agent Allocation</h2>
        <AgentAllocationChart data={fieldStatus?.agent_allocation || {}} />
      </div>
    </div>
  );
};

export default FieldStatus;
```

## Step 8: Implement Node Manager

### Node Manager Page (src/pages/NodeManager/index.tsx)

```tsx
import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../../contexts/WebSocketContext';
import NodeCard from './NodeCard';
import AddNodeModal from './AddNodeModal';

interface Node {
  id: string;
  tier: string;
  status: string;
  uptime: number;
  memory_percent: number;
  cpu_percent: number;
  active_agents: number;
  max_agents: number;
}

const NodeManager: React.FC = () => {
  const { connected, sendMessage, lastMessage } = useWebSocket();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  useEffect(() => {
    if (connected) {
      sendMessage('get_nodes', {});
      const interval = setInterval(() => {
        sendMessage('get_nodes', {});
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [connected, sendMessage]);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'nodes') {
      setNodes(lastMessage.data);
      setLoading(false);
    }
  }, [lastMessage]);

  const handleAddNode = (nodeData: any) => {
    sendMessage('add_node', nodeData);
    setIsAddModalOpen(false);
  };

  const handleRemoveNode = (nodeId: string) => {
    if (window.confirm(`Are you sure you want to remove node ${nodeId}?`)) {
      sendMessage('remove_node', { node_id: nodeId });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading nodes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Node Manager</h1>
        <button
          onClick={() => setIsAddModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Add Node
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {nodes.map((node) => (
          <NodeCard
            key={node.id}
            node={node}
            onRemove={() => handleRemoveNode(node.id)}
          />
        ))}

        {nodes.length === 0 && (
          <div className="col-span-full text-center py-12 bg-gray-800 rounded-lg">
            <p className="text-gray-400">No nodes available</p>
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Add Node
            </button>
          </div>
        )}
      </div>

      <AddNodeModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={handleAddNode}
      />
    </div>
  );
};

export default NodeManager;
```

## Step 9: Implement Agent Manager

### Agent Manager Page (src/pages/AgentManager/index.tsx)

```tsx
import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../../contexts/WebSocketContext';
import AgentCard from './AgentCard';
import SpawnAgentModal from './SpawnAgentModal';
import AgentTypeFilter from './AgentTypeFilter';

interface Agent {
  id: string;
  agent_type: string;
  role_name: string;
  node_id: string;
  status: string;
  allocation_time: string;
}

const AgentManager: React.FC = () => {
  const { connected, sendMessage, lastMessage } = useWebSocket();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSpawnModalOpen, setIsSpawnModalOpen] = useState(false);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    if (connected) {
      sendMessage('get_agents', {});
      const interval = setInterval(() => {
        sendMessage('get_agents', {});
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [connected, sendMessage]);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'agents') {
      setAgents(lastMessage.data);
      setLoading(false);
    }
  }, [lastMessage]);

  const handleSpawnAgent = (agentData: any) => {
    sendMessage('spawn_agent', agentData);
    setIsSpawnModalOpen(false);
  };

  const handleCollapseAgent = (agentId: string) => {
    if (window.confirm(`Are you sure you want to collapse agent ${agentId}?`)) {
      sendMessage('collapse_agent', { agent_id: agentId });
    }
  };

  const filteredAgents = filter === 'all'
    ? agents
    : agents.filter(agent => agent.agent_type === filter);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading agents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Agent Manager</h1>
        <button
          onClick={() => setIsSpawnModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Spawn Agent
        </button>
      </div>

      <AgentTypeFilter value={filter} onChange={setFilter} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            onCollapse={() => handleCollapseAgent(agent.id)}
          />
        ))}

        {filteredAgents.length === 0 && (
          <div className="col-span-full text-center py-12 bg-gray-800 rounded-lg">
            <p className="text-gray-400">No agents available</p>
            <button
              onClick={() => setIsSpawnModalOpen(true)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Spawn Agent
            </button>
          </div>
        )}
      </div>

      <SpawnAgentModal
        isOpen={isSpawnModalOpen}
        onClose={() => setIsSpawnModalOpen(false)}
        onSpawn={handleSpawnAgent}
      />
    </div>
  );
};

export default AgentManager;
```

## Step 10: Package and Build the Application

### Update package.json Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "electron:dev": "concurrently \"npm run dev\" \"electron electron/main.ts\"",
    "electron:build": "npm run build && electron-builder",
    "electron:preview": "npm run build && electron electron/main.ts"
  }
}
```

### Build Commands

```bash
# Development mode
npm run electron:dev

# Production build
npm run electron:build
```

## Conclusion

This step-by-step guide provides detailed instructions for implementing the frontend components of the Kulu Node Orchestration System. The frontend is built as an Electron application with React, TypeScript, and WebSockets, providing a rich user interface for managing the Kulu field.

Key features implemented include:
- Cognitive Mirror interface with Stream, Graph, and VM Monitor views
- Field Status dashboard with coherence charts and node statistics
- Node Manager for adding, monitoring, and removing nodes
- Agent Manager for spawning, monitoring, and collapsing agents
- Real-time communication with backend services via WebSockets

Follow the build commands to package the application for distribution on Windows, macOS, and Linux platforms.
