# OCE System Architecture — Mermaid Graphs

## 1. System Architecture

```mermaid
graph TB
    MAD["🧑‍🔬 MAD (Human Operator)<br/>Strategic Initiator / Attractor Definer"]
    
    subgraph OCE["🐙 OCE Continuity Core (FastAPI :8000)"]
        EF["📡 Event Fabric (Phase 2)<br/>Ingest → Route → Persist → Stream<br/>32 tests ✅"]
        TR["🔀 Topological Router<br/>Dijkstra-based event routing"]
        OR["👁️ Observer Runtime (Phase 3)<br/>Lifecycle → Health → Events → Snapshots<br/>20 tests ✅"]
        SM["🧠 Structural Memory (Phase 4)<br/>WORK → LEARNED → KNOWLEDGE<br/>FTS5 + SQLite + TTL + Compression<br/>30 tests ✅"]
        SA["🔌 SRRA-OPH Adapter<br/>Substrate integration"]
    end
    
    subgraph SRRA["⚙️ SRRA-OPH Substrate (srrs_opc/)"]
        P1["Phase 1: Observer Mesh"]
        P2["Phase 2: Reconstruction"]
        P3["Phase 3: Emergent Topology"]
        P4["Phase 4: Workspace Integration"]
        P5["Phase 5: Long-Horizon Continuity"]
        P6["Phase 6: Recursive Introspection"]
        P7["Phase 7: Overlap Cognition"]
        P8["Phase 8: Sovereign Coevolution"]
        P9["Phase 9: Entropy Economics"]
    end
    
    subgraph Operator["🎮 Operator Control Layer (:8001)"]
        DC["🖥️ Desktop Control<br/>Screen capture, Input sim, Window mgmt"]
        VS["💻 VS Code Bridge<br/>Files, Editor, Terminal, Extensions, Git"]
        SO["⚙️ System Operator<br/>Process, Package, Env, Service, Scheduler"]
        OI["🔗 Observer Integration<br/>exec/kill/install → emit events"]
        OD["🔍 Observer Debug CLI<br/>list/status/health/events/logs"]
    end
    
    subgraph Memory["💾 Memory & Knowledge Layer"]
        AM["📚 AgentMemory (MCP :3111)<br/>BM25 + Vector + Graph (RRF)<br/>Auto-capture via 12 hooks"]
        LW["📖 LLM Wiki<br/>Self-building knowledge base<br/>Karpathy pattern + Obsidian"]
        TC["💬 Team Chat<br/>shared-conversations/team-chat.md"]
        PF["📊 Progress Files<br/>Per-agent tracking"]
        ED["🗃️ Error DB<br/>Pattern analysis + Self-healing"]
    end
    
    subgraph External["🌐 External Tools"]
        CB["🛡️ CloakBrowser<br/>Stealth Chromium, Bot bypass<br/>30/30 detection tests passed"]
        TV["📈 TradingView MCP<br/>Real-time market data + 30+ indicators"]
        TT["🤖 TensorTrade<br/>RL trading framework"]
        ST["🔊 Supertonic TTS<br/>31 languages, ONNX, on-device"]
        AH["🪝 Agent Hooks<br/>Pre/post tool use hooks"]
    end
    
    subgraph Frontend["🖥️ OCE Frontend (Next.js :3000)"]
        DASH["📊 Dashboard<br/>Observer panels, Attractor metrics, Memory view"]
        CHAT["💬 Continuity Chat<br/>WebSocket real-time events"]
    end
    
    MAD --> OCE
    OCE --> EF
    EF --> TR
    TR --> OR
    OR --> SM
    SM --> SA
    SA --> SRRA
    
    P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7 --> P8 --> P9
    
    OCE --> Operator
    Operator --> DC
    Operator --> VS
    Operator --> SO
    Operator --> OI
    Operator --> OD
    
    OCE --> Memory
    Memory --> AM
    Memory --> LW
    Memory --> TC
    Memory --> PF
    Memory --> ED
    
    OCE --> External
    External --> CB
    External --> TV
    External --> TT
    External --> ST
    External --> AH
    
    OCE --> Frontend
    Frontend --> DASH
    Frontend --> CHAT
    
    EF -->|WebSocket| CHAT
    OR -->|events| EF
    SM -->|store/search| AM
    OI -->|emit| EF
    OD -->|query| OR
```

## 2. Data Flow / Touring Graph

```mermaid
flowchart TD
    EXT["🌐 External Event<br/>Market data / User action / System signal"]
    
    subgraph Ingest["📥 Ingestion Layer"]
        VALIDATE["✅ Validate & Classify<br/>Auto-detect priority from event_type"]
        TIMESTAMP["⏱️ Timestamp<br/>UTC ISO-8601"]
    end
    
    subgraph Route["🔀 Routing Layer"]
        TOPO["🔀 Topological Router<br/>Dijkstra on coupling graph"]
        BROADCAST["📢 Broadcast<br/>All observers within max_hops"]
        TARGETED["🎯 Targeted<br/>Specific observer by ID"]
    end
    
    subgraph Persist["💾 Persistence Layer"]
        SQLITE["🗃️ SQLite Storage<br/>events.db with indexes"]
        COMPRESS["🗜️ Compression<br/>Keep last N per type"]
        TTL["⏰ TTL Expiration<br/>Auto-delete expired entries"]
    end
    
    subgraph Memory["🧠 Memory Layer"]
        WORK["⚡ WORK<br/>Active task context"]
        LEARNED["📚 LEARNED<br/>Completed work, lessons"]
        KNOWLEDGE["🎓 KNOWLEDGE<br/>Reference material"]
        FTS5["🔍 FTS5 Search<br/>Full-text + Graph traversal"]
    end
    
    subgraph Observers["👁️ Observer Layer"]
        TRADING["📈 Trading Observer<br/>Market data → Strategy execution"]
        REPAIR["🔧 Repair Observer<br/>Fault detection → Auto-remediation"]
        ENTROPY["🌡️ Entropy Observer<br/>Budget monitoring → Compression"]
        CONTENT["📝 Content Observer<br/>Content farm → Publishing"]
        SYSTEM["⚙️ System Observer<br/>Health monitoring → Alerts"]
        PLANNER["🗺️ Planner Observer<br/>Strategic planning → Task decomposition"]
        EXECUTION["⚡ Execution Observer<br/>Task dispatch → Tool operation"]
        MEM_OBS["🧠 Memory Observer<br/>Persistence → Reconstruction"]
    end
    
    subgraph Output["📤 Output Layer"]
        WS["🔌 WebSocket Stream<br/>Real-time to frontend"]
        API["🌐 REST API<br/>Query + CRUD endpoints"]
        CLI["💻 CLI Tools<br/>Debug + Operator integration"]
    end
    
    EXT --> VALIDATE
    VALIDATE --> TIMESTAMP
    TIMESTAMP --> TOPO
    TOPO --> BROADCAST
    TOPO --> TARGETED
    BROADCAST --> Observers
    TARGETED --> Observers
    
    TIMESTAMP --> SQLITE
    SQLITE --> COMPRESS
    SQLITE --> TTL
    
    Observers --> WORK
    WORK --> LEARNED
    LEARNED --> KNOWLEDGE
    KNOWLEDGE --> FTS5
    
    SQLITE --> WS
    Observers --> API
    Observers --> CLI
    
    WS --> Frontend["🖥️ OCE Frontend"]
    API --> Frontend
    CLI --> Operator["🎮 Operator Tools"]
```

## 3. Logic Chain (Execution Flow)

```mermaid
flowchart TD
    START(["🚀 Start Session"])
    
    LOAD["📖 Load Context<br/>OPERATOR_RULES.md → AGENTS.md → team-chat.md"]
    
    HEALTH["🏥 Health Check<br/>Gateway / Workspace / Disk"]
    
    PRIORITIZE["📋 Prioritize Tasks<br/>Continuity > Entropy > Orchestration"]
    
    DECIDE{"🤔 Can I do it<br/>directly?"}
    
    BUILD["🔨 Build Directly<br/>Write code → Run tests → Verify"]
    
    SPAWN["🤖 Spawn Sub-agent<br/>Task spec → Timeout → Monitor"]
    
    VERIFY["✅ Verify Output<br/>Tests pass? Docs complete?"]
    
    UPDATE["📝 Update<br/>team-chat + progress files"]
    
    MORE{"📋 More<br/>tasks?"}
    
    YIELD(["⏸️ Yield / Wait<br/>for events"])
    
    ERROR["❌ Error Detected"]
    LOG["📖 Read the LOG<br/>Not the dashboard"]
    ROOT["🔍 Root cause<br/>Not symptom"]
    FIX["🔧 Fix ONE thing<br/>Never batch"]
    RETEST["🧪 Test again"]
    
    START --> LOAD
    LOAD --> HEALTH
    HEALTH --> PRIORITIZE
    PRIORITIZE --> DECIDE
    DECIDE -->|YES| BUILD
    DECIDE -->|NO| SPAWN
    BUILD --> VERIFY
    SPAWN --> VERIFY
    VERIFY --> UPDATE
    UPDATE --> MORE
    MORE -->|YES| PRIORITIZE
    MORE -->|NO| YIELD
    
    BUILD --> ERROR
    SPAWN --> ERROR
    ERROR --> LOG
    LOG --> ROOT
    ROOT --> FIX
    FIX --> RETEST
    RETEST -->|FAIL| LOG
    RETEST -->|PASS| UPDATE
```

## 4. Sub-Agent Governance Chain

```mermaid
flowchart TD
    SPAWN_DECISION{"🤖 Spawn<br/>sub-agent?"}
    
    CHECK_LIMIT{"📊 Concurrent < 5?"}
    
    CREATE_TASK["📝 Create Task Spec<br/>Deliverable + Success criteria + Timeout"]
    
    SPAWN_AGENT["🚀 Spawn Agent<br/>Label + Model + Context"]
    
    MONITOR["👁️ Monitor<br/>Check every 5 min"]
    
    CHECK_PROGRESS{"📈 Making<br/>progress?"}
    
    KILL["⏹️ Kill & Retry<br/>Break task smaller"]
    
    COMPLETE["✅ Complete<br/>Verify output"]
    
    INTEGRATE["🔗 Integrate<br/>Code review → Merge → Test"]
    
    WAIT_OTHER["⏳ Wait for<br/>other sub-agents"]
    
    SPAWN_DECISION -->|YES| CHECK_LIMIT
    CHECK_LIMIT -->|YES| CREATE_TASK
    CHECK_LIMIT -->|NO| WAIT_OTHER
    CREATE_TASK --> SPAWN_AGENT
    SPAWN_AGENT --> MONITOR
    MONITOR --> CHECK_PROGRESS
    CHECK_PROGRESS -->|YES| MONITOR
    CHECK_PROGRESS -->|NO| KILL
    KILL --> CREATE_TASK
    CHECK_PROGRESS -->|DONE| COMPLETE
    COMPLETE --> INTEGRATE
    INTEGRATE --> SPAWN_DECISION
```

## 5. Entropy Governance Chain

```mermaid
flowchart TD
    ACTION["🎯 Proposed Action"]
    
    NECESSARY{"❓ Is this<br/>necessary?"}
    
    SKIP["⏭️ Skip<br/>Don't waste entropy"]
    
    EXISTING{"🔧 Can existing<br/>tool do this?"}
    
    USE_EXISTING["✅ Use existing<br/>No new code"]
    
    BUILD_MINIMAL["🔨 Build minimal<br/>Smallest possible solution"]
    
    TEST_DOC["🧪 Test + Document<br/>Verify + Update docs"]
    
    COMPRESS["🗜️ Compress / Clean<br/>Remove dead code"]
    
    CONTINUE["➡️ Continue<br/>Next task"]
    
    ACTION --> NECESSARY
    NECESSARY -->|NO| SKIP
    NECESSARY -->|YES| EXISTING
    EXISTING -->|YES| USE_EXISTING
    EXISTING -->|NO| BUILD_MINIMAL
    BUILD_MINIMAL --> TEST_DOC
    TEST_DOC --> COMPRESS
    COMPRESS --> CONTINUE
    USE_EXISTING --> CONTINUE
```

---

## Copy-Paste Ready for Planner Agent

### System Summary
```
OCE (Operator Continuity Engine) — 101 tests passing
├── Event Fabric (Phase 2) — 32 tests — Ingest/Route/Persist/Stream
├── Observer Runtime (Phase 3) — 20 tests — Lifecycle/Health/Events
├── Structural Memory (Phase 4) — 30 tests — WORK/LEARNED/KNOWLEDGE + FTS5
├── Topology + Persistence — 19 tests — Dijkstra routing + SQLite
└── SRRA-OPH Substrate — 77 tests — Phases 1-9 complete

Operator Control Layer — Port 8001
├── Desktop Control (screen, input, windows)
├── VS Code Bridge (files, editor, terminal, git)
├── System Operator (process, package, env, service)
├── Observer Integration (exec/kill/install → emit)
└── Observer Debug CLI (list/status/health/events/logs)

Memory Layer
├── Structural Memory (SQLite + FTS5 + TTL + Compression)
├── AgentMemory (MCP server — BM25 + Vector + Graph)
├── LLM Wiki (self-building knowledge base)
├── Team Chat (coordination hub)
└── Error DB (pattern analysis + self-healing)

External Tools
├── CloakBrowser (stealth Chromium, bot bypass)
├── TradingView MCP (real-time market data)
├── TensorTrade (RL trading framework)
├── Supertonic TTS (31 languages, on-device)
└── Agent Hooks (pre/post tool use)

Governance
├── OPERATOR_RULES.md — Bounded sovereign operational continuity
├── SUB_AGENT_RULES.md — Max 5 concurrent, no recursive spawning
├── Max sub-agent runtime: 15 min soft limit
├── All execution logged and observable
└── Human (MAD) is strategic anchor — OWL coordinates, doesn't replace
```
