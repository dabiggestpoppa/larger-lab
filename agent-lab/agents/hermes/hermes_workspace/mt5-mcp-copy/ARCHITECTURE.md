# MT5 Agent Strategy Builder — Architecture & Implementation Plan

> **Status**: Architecture complete — ready for implementation  
> **Harness**: Follows 12-component Agent Harness pattern from `.agents/AGENTS.md`  
> **Contract**: All agents operate under `CLAUDE.md` 12-rule behavioral contract  

---

## 1. Repo Evaluation: What We're Working With

### UI-TARS Desktop (bytedance/UI-TARS-desktop) — ⚠️ Partially Useful

| Aspect | Assessment |
|--------|-----------|
| **What it is** | Multimodal GUI agent stack — controls computers/browsers via vision + MCP |
| **Agent TARS CLI** | ✅ Active, headless MCP-based agent. Good reference for MCP server patterns |
| **UI-TARS Desktop** | ⚠️ Being sunset (archived). Remote operator features dead |
| **MCP integration** | ✅ Kernel is built on MCP, supports mounting MCP servers |
| **Event Stream protocol** | ✅ Protocol-driven context engineering — useful pattern to study |
| **Relevance to MT5** | Low direct utility. It's for GUI/browser automation, not trading. But the MCP server architecture pattern is worth studying |

**Verdict**: Don't use as a dependency. Study its MCP server registration pattern and Event Stream protocol for inspiration. The desktop app is dying; the CLI agent-tars is alive.

### OpenClaw — ✅ Reference Implementation (Not a Dependency)

| Aspect | Assessment |
|--------|-----------|
| **What it is** | Open-source messaging-first agent (Gitlawb/openclaude, 26.6k stars) |
| **Why we reference it** | Good example of MCP client integration patterns and slash command architecture |
| **License** | Open source |
| **Maturity** | Active community, regular updates |

**Verdict**: Reference only. We study its MCP client patterns but do NOT use it as our runtime. Our execution layer is **Hermes** (Telegram) + **Claude Code** (desk-based coding). The MT5 MCP server is protocol-agnostic — any MCP client can connect.

---

## 2. Target Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HUMAN INTERFACE LAYER                            │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │  Hermes  │  │  Claude Code │  │  VS Code / Custom UI         │  │
│  │(Telegram)│  │  (desk IDE)  │  │  (via gRPC or MCP stdio)     │  │
│  └─────┬────┘  └──────┬───────┘  └──────────────┬───────────────┘  │
│        │               │                        │                   │
│        └───────────────┼────────────────────────┘                   │
│                        │  MCP Protocol (JSON-RPC)                   │
└────────────────────────┼────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────────┐
│                    MT5 MCP SERVER (Python)                           │
│                                                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │
│  │  Data Tools   │ │  Code Gen    │ │  Build Tools │ │  Backtest  │  │
│  │              │ │  Tools       │ │              │ │  Tools     │  │
│  │ mt5_connect  │ │ mt5_create_  │ │ mt5_compile  │ │ mt5_       │  │
│  │ mt5_account  │ │ indicator    │ │ mt5_write_   │ │ backtest   │  │
│  │ mt5_market_  │ │ mt5_create_  │ │ mql5         │ │ mt5_       │  │
│  │ data         │ │ ea           │ │ mt5_list_    │ │ backtest_  │  │
│  │ mt5_symbols  │ │ mt5_write_   │ │ files        │ │ python     │  │
│  │              │ │ mql5         │ │              │ │ mt5_       │  │
│  │              │ │              │ │              │ │ optimize   │  │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬──────┘  │
│         └────────────────┼────────────────┼────────────────┘         │
│                          │                │                           │
│  ┌───────────────────────▼────────────────▼──────────────────────┐   │
│  │              MT5 RUNTIME LAYER                                  │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │   │
│  │  │ MT5 Terminal │  │ MetaEditor   │  │ Strategy Tester     │   │   │
│  │  │ (Python API) │  │ (CLI compile)│  │ (EA backtesting)    │   │   │
│  │  └─────────────┘  └──────────────┘  └─────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────────┐
│                    AGENT ORCHESTRATION LAYER                         │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Orchestrator Agent (per AGENTS.md)                           │   │
│  │  - Task decomposition                                         │   │
│  │  - Dependency mapping                                         │   │
│  │  - Parallel subagent execution                                │   │
│  │  - Verification loops (tests, linters, LLM-as-judge)          │   │
│  │  - Progress tracking (todo lists)                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │
│  │  Research    │ │  Architect   │ │  Code        │ │  QA Agent  │  │
│  │  Agent       │ │  Agent       │ │  Reviewer    │ │            │  │
│  │  (market     │ │  (system     │ │  (12-rule    │ │  (verify   │  │
│  │  research)   │ │  design)     │ │  compliance) │ │  intent)   │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. MT5 MCP Server — Tool Specification

### 3.1 Connection & Setup Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `mt5_connect` | Connect to MT5 terminal | `login?`, `password?`, `server_name?`, `terminal_path?` |
| `mt5_get_account_info` | Get account details (balance, equity, margin) | None |
| `mt5_get_symbols` | List all available trading symbols | None |

### 3.2 Market Data Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `mt5_get_market_data` | Fetch OHLCV candle data | `symbol`, `timeframe`, `bars` |
| `mt5_get_tick_data` | Fetch tick data for precise testing | `symbol`, `count` |
| `mt5_get_current_prices` | Get current bid/ask for a symbol | `symbol` |

### 3.3 Code Creation Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `mt5_create_indicator` | Generate + write MQL5 indicator | `name`, `description`, `inputs?`, `logic?` |
| `mt5_create_ea` | Generate + write MQL5 Expert Advisor | `name`, `description`, `strategy_logic?`, `inputs?` |
| `mt5_write_mql5` | Write raw MQL5 code to file | `filename`, `content`, `folder` |

### 3.4 Build Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `mt5_compile_file` | Compile MQL5 via MetaEditor CLI | `filepath` |
| `mt5_list_files` | List MQL5 files in a folder | `folder` |

### 3.5 Backtesting Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `mt5_backtest_python` | Python-based simulated backtest (no MT5 terminal needed) | `ea_code`, `symbol`, `timeframe_str`, `deposit`, `bars` |
| `mt5_backtest_terminal` | Launch MT5 Strategy Tester via CLI | `ea_name`, `symbol`, `timeframe`, `deposit`, `from_date`, `to_date` |
| `mt5_get_last_report` | Fetch last backtest report | None |
| `mt5_optimize` | Parameter optimization | `ea_name`, `param_ranges?`, `symbol`, `timeframe`, `method` |

### 3.6 Trade Management Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `mt5_open_trade` | Open a live/demo trade | `symbol`, `order_type`, `lot_size`, `sl_pips`, `tp_pips`, `comment?` |
| `mt5_get_positions` | List all open positions | None |
| `mt5_close_trade` | Close a position by ticket | `ticket` |

---

## 4. Strategy Building Workflow

### The 6-Step Agent Pipeline

```
Step 1: IDEA → RESEARCH
         User gives idea
         Research Agent: market context, similar strategies, feasibility
         
Step 2: DESIGN → ARCHITECT
         Architect Agent: indicator/EA specification
         Define inputs, logic, success criteria
         
Step 3: CODE → BUILD
         Agent generates MQL5 via mt5_create_indicator/ea
         Compiles via mt5_compile_file
         
Step 4: TEST → VERIFY
         mt5_backtest_python for quick iteration
         mt5_backtest_terminal for production-grade results
         QA Agent: verify intent, check edge cases
         
Step 5: OPTIMIZE → IMPROVE
         mt5_optimize for parameter tuning
         Code Reviewer: check for overfitting, logic issues
         
Step 6: REPORT → DELIVER
         Formatted backtest results
         Go/no-go recommendation with risk assessment
```

### Example User Request → Agent Pipeline

**User**: "Create an RSI divergence strategy on EURUSD H4, backtest it, and tell me if it's viable."

**Agent execution:**

```
1. Research Agent → Fetches EURUSD H4 data, researches RSI divergence patterns
2. Architect Agent → Specifies: RSI(14) divergence with price action confirmation
3. Code Generation → mt5_create_indicator("RSI_Divergence_H4", ...)
4. Compilation → mt5_compile_file(...)
5. Quick Backtest → mt5_backtest_python(EA code, "EURUSD", "H4", 10000, 2000)
6. Full Backtest → mt5_backtest_terminal("RSI_Divergence_H4", "EURUSD", "H4", ...)
7. QA Agent → Verifies test results, checks for curve-fitting
8. Report → Formatted results with Sharpe, drawdown, win rate, recommendation
```

---

## 5. Why This Architecture Won't Break

### Decoupled Layers

| Layer | Change Frequency | Isolation |
|-------|-----------------|-----------|
| **Human Interface** (Hermes, Claude Code, OpenClaw, UI) | Changes often | Swap without touching logic |
| **MCP Protocol** (JSON-RPC) | Stable standard | Version independently |
| **MT5 MCP Server** (Python tools) | Moderate changes | Each tool is independent |
| **MT5 Runtime** (terminal, compiler, tester) | Rarely changes | External dependency |
| **Agent Orchestration** (harness) | Stable | 12-component pattern proven |

### Key Design Decisions That Prevent Rot

1. **Thin harness, thick model** (Decision #7 from agent harness): Let the AI model do the reasoning; the harness just manages context and tools. When models improve, harness complexity can decrease.

2. **Independent tools**: Each MCP tool does one thing. Adding a new tool (e.g., `mt5_get_fundamental_data`) doesn't affect existing ones.

3. **Two-path backtesting**: Python simulation for fast iteration, terminal backtest for validation. If one path breaks, the other still works.

4. **File-based compilation**: MQL5 files are written to disk → compiled by MetaEditor → results read back. This is the most stable integration pattern because it doesn't depend on undocumented APIs.

5. **Verification at every step**: Each agent in the pipeline runs verification loops before passing to the next step. Errors are caught early, not compounded.

6. **Self-evolving skills**: Repeated patterns (e.g., "RSI divergence on H4") become SKILL.md files. The Curator prunes what's unused. The system gets better over time instead of worse.

---

## 6. Implementation Priority

### Phase 1: Core (Week 1)
- [ ] Create `mt5_mcp_server.py` with connection + data tools
- [ ] Implement `mt5_create_indicator` and `mt5_create_ea`
- [ ] Implement `mt5_compile_file` (MetaEditor CLI)
- [ ] Implement `mt5_backtest_python` (simulation)
- [ ] Test with a simple EMA crossover strategy

### Phase 2: Full Pipeline (Week 2)
- [ ] Add `mt5_backtest_terminal` (Strategy Tester integration)
- [ ] Add `mt5_optimize` (parameter search)
- [ ] Add trade management tools (`mt5_open_trade`, `mt5_get_positions`)
- [ ] Configure MCP in your agent (Hermes/Claude Code/OpenClaw — see `mcp-config-stdio.json`)
- [ ] Test full pipeline: idea → code → compile → backtest → report

### Phase 3: Agent Integration (Week 3)
- [ ] Create agent skill for MT5 strategy building
- [ ] Update Orchestrator to handle MT5 workflow
- [ ] Add verification loops (backtest result validation)
- [ ] Set up Hermes for Telegram-based strategy requests
- [ ] Create dashboard for tracking strategy performance

### Phase 4: Hardening (Week 4+)
- [ ] GEPA optimization for strategy parameters
- [ ] Memory integration (persist strategy results)
- [ ] Error handling for all MT5 edge cases
- [ ] Security: sandbox trade execution, position limits
- [ ] Documentation and skill library

---

## 7. File Structure

```
larger-lab/
├── .agents/
│   ├── AGENTS.md                    ← Team manifest (updated)
│   ├── orchestrator.agent.md        ← Workflow coordinator (updated)
│   ├── debugger.agent.md            ← Bug diagnosis
│   ├── architect.agent.md           ← System design
│   ├── memory-engineer.agent.md     ← Knowledge management
│   ├── qa-agent.agent.md            ← Testing & validation
│   ├── devops-agent.agent.md        ← Deployment & infra
│   ├── research-agent.agent.md      ← Investigation
│   ├── code-reviewer.agent.md       ← Code quality
│   └── WORKFLOW.md                  ← Process guide (updated)
├── .hermes/
│   ├── MEMORY.md                    ← Persistent memory
│   ├── USER.md                      ← User profile
│   ├── SOUL.md                      ← Identity layer
│   └── skills/
│       ├── goal-mode/SKILL.md       ← /goal execution
│       ├── hermes-maintenance/SKILL.md
│       └── github-backup/SKILL.md
├── mt5-mcp/
│   ├── mt5_mcp_server.py            ← MCP server (main implementation)
│   ├── controller_ea.mq5            ← Helper EA for terminal backtests
│   ├── requirements.txt             ← Python dependencies
│   └── README.md                    ← Setup guide
├── strategies/
│   ├── rsi_divergence_h4.mq5        ← Example strategy
│   └── ema_crossover.mq5            ← Example strategy
├── CLAUDE.md                         ← 12-rule behavioral contract
├── SOUL.md                           ← Root identity
└── .cursor/rules/karpathy-guidelines.mdc
```

---

## 8. OpenClaude MCP Configuration

Once the MT5 MCP server is built, connect it to OpenClaude:

```json
// ~/.claude/mcp.json
{
  "mcpServers": {
    "mt5": {
      "command": "python",
      "args": ["/path/to/larger-lab/mt5-mcp/mt5_mcp_server.py"]
    }
  }
}
```

Or for headless gRPC mode (CI/CD):
```bash
# Start OpenClaude as gRPC server
openclaude --grpc

# Client connects and uses MT5 tools through the agent
```

---

## 9. Bridging to Other Environments

The MCP pattern is environment-agnostic. Once the MT5 server works, the same architecture applies to:

| Environment | MCP Server | Tools |
|-------------|-----------|-------|
| **TradingView** | `tradingview-mcp` | Pine Script, alerts, charts |
| **MT5** | `mt5-mcp` (we're building) | MQL5, backtesting, trades |
| **Nautilus Trader** | Existing nautilus tools | Backtesting, data loading |
| **Python/Data** | Custom MCP server | Pandas, NumPy, VectorBT |
| **Web/API** | Browser MCP, Fetch MCP | Scraping, REST APIs |
| **DevOps** | Docker MCP, Git MCP | Deployment, version control |

The agent doesn't need to know the environment — it just calls MCP tools. The Orchestrator routes tasks to the right tools.