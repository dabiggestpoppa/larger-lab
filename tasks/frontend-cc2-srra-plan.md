# 🔵 CC2 — SRRA-OPH Frontend Plan
## Topology Observatory Engine (Phases 1-2)

**Agent:** CC2
**Frontend:** SRRA-OPH (:3001)
**Base:** `srrs_opc/frontend/` (Next.js 15, React 19, TypeScript)

---

## PHASE 1 — OBSERVATORY FOUNDATION

### 1.1 Project Dependencies
```bash
cd srrs_opc/frontend
npm install zustand cytoscape react-cytoscapejs d3 framer-motion clsx lucide-react
npm install -D @types/cytoscape @types/d3
```

### 1.2 Theme + Visual Foundation
**Files:**
- `app/globals.css` — Replace with dark scientific theme
- `tailwind.config.ts` — Add custom color tokens
- `app/styles/tokens.css` — CSS variables for field states

**Color tokens:**
```css
--bg-primary: #0a0a0f
--bg-secondary: #12121a
--field-neutral: #1a1a2e
--entropy-low: #1a3a1a
--entropy-high: #3a1a1a
--repair-active: #00d4ff
--observer-sync: #00ff88
--observer-isolated: #4a4a5a
--attractor-active: #8b5cf6
```

**Typography:** IBM Plex Mono (primary), Inter (labels only)

### 1.3 Layout System
**Files:**
- `app/layout.tsx` — Four-region observatory layout
- `components/layout/LeftRail.tsx` — 240px control rail
- `components/layout/MainCanvas.tsx` — Full graph rendering area
- `components/layout/BottomTimeline.tsx` — 160px timeline bar
- `components/layout/RightContext.tsx` — 280px inspection panel

### 1.4 State Management (Zustand)
**Files:**
- `stores/topologyStore.ts` — nodes, edges, clusters, selectedObserver
- `stores/playbackStore.ts` — currentFrame, isPlaying, speed, timelinePosition
- `stores/entropyStore.ts` — entropy levels, perturbations, propagation state
- `stores/observerStore.ts` — observer states, health, synchronization
- `stores/uiStore.ts` — view mode, filters, panel visibility

### 1.5 Routing
**Files:**
- `app/topology/page.tsx` — Topology Observatory (main view)
- `app/entropy/page.tsx` — Entropy Field View
- `app/repair/page.tsx` — Repair Cascade Viewer
- `app/attractors/page.tsx` — Attractor Basin View
- `app/experiments/page.tsx` — Experiment Session Viewer
- `app/playback/page.tsx` — Temporal Playback

### 1.6 Mock Data
**Files:**
- `lib/mock/topology.ts` — 500 nodes, 2000 edges generator
- `lib/mock/entropy.ts` — Entropy spike/propagation data
- `lib/mock/repair.ts` — Repair chain/cascade data
- `lib/mock/events.ts` — Event stream data

### 1.7 Cytoscape Integration
**Files:**
- `components/visualization/TopologyCanvas.tsx` — Main Cytoscape wrapper
- `components/visualization/NodeRenderer.tsx` — Custom node rendering
- `components/visualization/EdgeRenderer.tsx` — Custom edge rendering
- `lib/cytoscape/observer-styles.ts` — Cytoscape stylesheet for observer states

### 1.8 Timeline Foundation
**Files:**
- `components/timeline/TimelineController.tsx` — Play/pause/stop/speed
- `components/timeline/Scrubber.tsx` — Draggable timeline scrubber
- `components/timeline/EventMarkers.tsx` — Event density markers

### 1.9 WebSocket Infrastructure
**Files:**
- `lib/websocket/observer-socket.ts` — WebSocket client for live data
- `hooks/useObserverStream.ts` — React hook for live observer data

---

## PHASE 2 — LIVING TOPOLOGY

### 2.1 Observer State Engine
**Files:**
- `components/visualization/ObserverStates.tsx` — State visual mapping
- `lib/observer/state-machine.ts` — Observer state transitions

**States:** ACTIVE, SYNCED, ISOLATED, ENTROPIC, REPAIRING, DORMANT, FAILED

### 2.2 Edge Dynamics
**Files:**
- `components/visualization/EdgeFlow.tsx` — Directional flow animation
- `lib/edge/edge-types.ts` — ROUTING, SYNC, REPAIR, ENTROPY, MEMORY, FIELD

### 2.3 Spatial Layout
**Files:**
- `lib/layout/force-directed.ts` — Force-directed layout with custom forces
- `lib/layout/entropy-reactive.ts` — Entropy deformation pressure
- `lib/layout/cluster-aware.ts` — Cluster-aware positioning

### 2.4 Clustering Engine
**Files:**
- `components/visualization/ClusterOverlay.tsx` — Cluster boundaries
- `lib/clustering/sync-clusters.ts` — Synchronization-based clustering

### 2.5 Entropy Overlay
**Files:**
- `components/visualization/EntropyHeatmap.tsx` — Heat layer
- `components/visualization/PerturbationOrigin.tsx` — Perturbation source marker

### 2.6 Repair Propagation
**Files:**
- `components/visualization/RepairWave.tsx` — Repair wave animation
- `lib/repair/propagation-engine.ts` — Repair chain logic

### 2.7 Filtering + Inspection
**Files:**
- `components/controls/FilterPanel.tsx` — Filter by type/entropy/sync
- `components/inspection/NodeInspector.tsx` — Selected node details

### 2.8 Performance
- Virtualization for 10k+ nodes
- Edge batching
- Progressive rendering
- Target: 30fps under load

---

## SUCCESS CONDITIONS

### Phase 1:
✅ Observatory launches with dark scientific theme
✅ Four-region layout stable
✅ Cytoscape renders 500 nodes + 2000 edges
✅ Timeline controls functional
✅ Zustand stores operational
✅ 60fps idle

### Phase 2:
✅ Observer states visually distinct
✅ Edge flow animated
✅ Clusters emerge naturally
✅ Entropy heatmap renders
✅ Repair waves visible
✅ 30fps with 10k nodes
