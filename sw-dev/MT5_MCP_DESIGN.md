# MT5 MCP Server — Design Document
> **Generated:** 2026-05-20
> **Author:** OWL Subagent (Research)
> **Status:** Design Complete — Ready for Implementation

---

## 1. Executive Summary

**Yes, an MCP server would significantly help with MT5 Strategy Tester automation.** However, existing MCP servers (Qoyyuum, ariadng, Cloudmeru, emerzon) focus on **live trading and market data** — none address the **Strategy Tester automation** problem (compiling EAs, launching backtests via `terminal64.exe /config:`, parsing results).

**Recommendation:** Build a purpose-built MT5 Strategy Tester MCP server (`mt5-tester-mcp`) that wraps the proven `terminal64.exe /config:` workflow with tools for compile → configure → launch → parse → iterate.

---

## 2. Existing MT5 MCP Servers — Survey

| Server | Author | Focus | Strategy Tester? | Notes |
|--------|--------|-------|------------------|-------|
| `mcp-metatrader5-server` | Qoyyuum | Live trading + market data | ❌ | Full trade/market tools, stdio+HTTP, well-documented |
| `metatrader-mcp-server` | ariadng/LangDB | Live trading + REST API | ❌ | pip installable, natural-language focused |
| `MetaTrader-5-MCP-Server` | Cloudmeru | Read-only market data | ❌ | Safe for research, no trading |
| `mt-data-mcp` | emerzon | Research + automation toolkit | ❌ | Windows-first, CLI+MCP, forecasting/regime/indicators |
| `mcpmt5` | sameerasulakshana | Trading + market data | ❌ | Fork/variant of Qoyyuum |
| `metatrader-mcp` | ali-rajabpour | Chart snapshots | ❌ | Visual chart capture from MT5 |
| `metatrader-5-for-Chatgpt-Desktop` | jorgearturoyap | ChatGPT Desktop | ❌ | Tailored for ChatGPT |
| `metatrader-mcp` | chymian | Distrobox automation | ❌ | DevOps workflow automation |

**Key Finding:** Zero existing MCP servers handle Strategy Tester automation. This is a gap.

---

## 3. Why Existing Approaches Don't Solve Our Problem

### 3.1 The MetaTrader5 Python Package (`pip install MetaTrader5`)
- **What it does:** Connects to a running MT5 terminal via Windows IPC. Provides `copy_rates_*`, `positions_get`, `order_send`, etc.
- **What it does NOT do:** Control the Strategy Tester. There is no `mt5.run_backtest()` API.
- **Limitation:** The Python package connects to the terminal's *live* session. Strategy Tester runs in a separate agent process that the Python API cannot reach.

### 3.2 StrategyTester5 (Python Framework)
- **What it does:** Simulates MT5 trading environment in Python using historical data from the terminal.
- **What it does NOT do:** Use the actual MT5 Strategy Tester engine. It's a Python simulation, not the real tester.
- **Limitation:** Cannot replicate intra-bar logic, exact tick modeling, or EA-specific MQL5 behavior.

### 3.3 The Actual Working Approach (from research)
The only way to run the **real** MT5 Strategy Tester programmatically is:
```
terminal64.exe /portable /config:"path\to\config.ini"
```
This is well-documented and works. The problem is **orchestration**, not capability.

---

## 4. Would an MCP Server Help?

### Yes, for these reasons:

| Use Case | Without MCP | With MCP |
|----------|-------------|----------|
| **Compile MQL5 EA** | Manual MetaEditor CLI or GUI | `mt5_compile(ea_path)` tool |
| **Configure backtest** | Hand-edit INI files | `mt5_create_config(params)` tool |
| **Launch backtest** | subprocess.run + wait | `mt5_run_backtest(config)` tool |
| **Parse results** | Custom HTML parser per project | `mt5_parse_report(report_path)` tool |
| **Iterate parameters** | Loop script with INI edits | `mt5_optimize(param_ranges)` tool |
| **AI-assisted tuning** | Not possible | LLM can call tools directly |

### The MCP Value Proposition:
1. **Standardized interface** — All MT5 backtest operations through typed tool calls
2. **AI-native** — LLMs can autonomously compile, test, analyze, and iterate
3. **Composable** — Tools chain together (compile → test → parse → adjust → repeat)
4. **Observable** — Every tool call is logged and structured
5. **Reusable** — One server serves all EA development workflows

---

## 5. Proposed Design: `mt5-tester-mcp`

### 5.1 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client (OWL)                      │
│         "Compile DMR, backtest on EURUSD M5,            │
│          parse results, adjust SL, repeat"               │
└──────────────────────┬──────────────────────────────────┘
                       │ MCP Protocol (stdio)
┌──────────────────────▼──────────────────────────────────┐
│                mt5-tester-mcp Server                     │
│                                                          │
│  Tools:                                                  │
│  ├── mt5_compile          → Compile .mq5 → .ex5          │
│  ├── mt5_validate_ea      → Check EA loads correctly     │
│  ├── mt5_create_config    → Generate tester INI          │
│  ├── mt5_run_backtest     → Launch terminal64.exe        │
│  ├── mt5_wait_for_result  → Poll for report completion   │
│  ├── mt5_parse_report     → Extract metrics from HTML    │
│  ├── mt5_parse_log        → Read MQL5 expert log         │
│  ├── mt5_get_symbols      → List available symbols       │
│  ├── mt5_get_history_info → Check data availability      │
│  └── mt5_optimize         → Parameter sweep orchestrator │
│                                                          │
│  Resources:                                              │
│  ├── mt5://config/schema   → INI config documentation    │
│  ├── mt5://report/template → Report parsing guide        │
│  └── mt5://troubleshooting → Common issues & fixes       │
└──────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
   MetaEditor64.exe      terminal64.exe       Report Files
   /compile              /config:ini          .htm/.xml
```

### 5.2 Tool Definitions

#### `mt5_compile`
```python
def mt5_compile(
    source_path: str,           # Path to .mq5 file
    metaeditor_path: str = "",  # Auto-detected if empty
    output_dir: str = ""        # Defaults to MQL5/Experts
) -> CompileResult:
    """
    Compile an MQL5 Expert Advisor using MetaEditor64.exe /compile.
    
    Returns:
        success: bool
        output_path: str | null    # Path to .ex5 file
        errors: list[CompileError] # Line, column, message
        warnings: list[CompileWarning]
        duration_ms: int
    """
```

#### `mt5_validate_ea`
```python
def mt5_validate_ea(
    ea_name: str,               # e.g., "DMR_FULL_BACKTEST.ex5"
    terminal_path: str = "",    # Auto-detected
    timeout_sec: int = 30
) -> ValidationResult:
    """
    Validate that an EA loads correctly in Strategy Tester.
    Uses a minimal INI config with 1-day range and checks:
    - EA file loads (log shows "EA.ex5 X64")
    - OnInit() executes (checks for Print output in log)
    - At least 1 bar is processed
    - No crash/early termination
    
    This is the KEY tool for debugging the OnInit() issue.
    """
```

#### `mt5_create_config`
```python
def mt5_create_config(
    ea_name: str,
    symbol: str,
    period: str,                # "M1","M5","M15","H1","H4","D1"
    from_date: str,             # "2024.01.01"
    to_date: str,               # "2024.01.31"
    model: int = 2,             # 0=Every tick, 1=1min OHLC, 2=Open prices
    spread: int = 0,
    deposit: float = 10000.0,
    leverage: str = "1:100",
    set_file: str = "",         # Path to .set file
    report_name: str = "",      # Auto-generated if empty
    optimization: bool = False,
    output_path: str = ""       # Where to save INI
) -> ConfigResult:
    """
    Generate a valid MT5 Strategy Tester INI config file.
    
    Handles the two INI formats:
    - [Common] + Test* keys (for terminal64.exe /config:)
    - [Tester] section (for tester profiles)
    
    Returns the path to the generated INI file.
    """
```

#### `mt5_run_backtest`
```python
def mt5_run_backtest(
    config_path: str,           # Path to INI file
    terminal_path: str = "",    # Auto-detected
    portable: bool = True,
    wait: bool = True,          # Block until complete
    timeout_sec: int = 600      # 10 min default
) -> BacktestResult:
    """
    Launch MT5 Strategy Tester via terminal64.exe /config:.
    
    If wait=True, blocks until terminal exits (TestShutdownTerminal=1).
    Monitors for:
    - Process start/stop
    - Report file creation
    - Error conditions (no bars, EA crash, etc.)
    
    Returns:
        success: bool
        duration_sec: float
        report_path: str | null
        error_message: str | null
    """
```

#### `mt5_wait_for_result`
```python
def mt5_wait_for_result(
    report_path: str,
    timeout_sec: int = 600,
    poll_interval_sec: float = 2.0
) -> WaitResult:
    """
    Poll for report file completion.
    Handles the case where terminal hasn't finished writing.
    Checks file size stability (not growing = complete).
    """
```

#### `mt5_parse_report`
```python
def mt5_parse_report(
    report_path: str,           # Path to .htm report
    parse_trades: bool = True   # Also extract trade list
) -> ReportData:
    """
    Parse MT5 Strategy Tester HTML report.
    
    Extracts:
    - Summary: Net profit, gross profit, gross loss, profit factor,
               expected payoff, max drawdown, total trades, win rate
    - Per-trade data: Time, type, volume, price, SL, TP, profit
    - Equity curve data
    - Test parameters: Symbol, period, model, dates, spread
    
    Returns structured JSON-like data.
    """
```

#### `mt5_parse_log`
```python
def mt5_parse_log(
    log_path: str = "",         # Auto-detected if empty
    ea_name: str = "",          # Filter by EA name
    last_n_lines: int = 200
) -> LogData:
    """
    Parse MT5 Strategy Tester log files.
    
    Reads from:
    - <DataFolder>/logs/YYYYMMDD.log (tester log)
    - <DataFolder>/MQL5/Logs/YYYYMMDD.log (expert log)
    
    Extracts:
    - EA load events
    - OnInit/OnDeinit calls
    - Print() output from EA
    - Error messages
    - Trade events
    - Test completion status
    """
```

#### `mt5_get_symbols`
```python
def mt5_get_symbols(
    terminal_path: str = ""     # Uses running terminal or launches temp
) -> list[str]:
    """
    Get list of available symbols from MT5 terminal.
    Requires MetaTrader5 Python package (pip install MetaTrader5).
    """
```

#### `mt5_get_history_info`
```python
def mt5_get_history_info(
    symbol: str,
    period: str
) -> HistoryInfo:
    """
    Check historical data availability for a symbol/period.
    Returns: first_date, last_date, bar_count
    Uses MetaTrader5 Python package.
    """
```

#### `mt5_optimize`
```python
def mt5_optimize(
    ea_name: str,
    symbol: str,
    period: str,
    from_date: str,
    to_date: str,
    param_ranges: dict,         # {"SL_pips": [10, 15, 20, 25], "TP_pips": [30, 40, 50]}
    set_file: str = "",
    max_workers: int = 1        # Sequential by default (MT5 limitation)
) -> OptimizationResult:
    """
    Run parameter sweep by generating multiple configs and running sequentially.
    
    For each parameter combination:
    1. Generate .set file with specific values
    2. Generate INI config
    3. Run backtest
    4. Parse results
    5. Store metrics
    
    Returns sorted results by profit factor (descending).
    """
```

### 5.3 Resource Definitions

#### `mt5://config/schema`
Documents the complete INI config format including:
- `[Common]` section keys (Login, Password, Server)
- `[Tester]` section keys (Expert, Symbol, Period, Model, etc.)
- `Test*` prefix format for `/config:` launches
- Period value mapping (M1=1, M5=5, M15=15, H1=16408, etc.)
- Model values (0=Every tick, 1=1min OHLC, 2=Open prices, 3=Close prices)

#### `mt5://troubleshooting`
Documents common issues and fixes:
- **OnInit() never executes** → Check EA code for early returns, missing includes
- **0 bars processed** → Check symbol name, period format, history availability
- **Period M0 in report** → Wrong period format in INI
- **"automated trading is disabled"** → Account change detection, enable algo trading
- **Test finishes instantly** → EA crash in OnInit, check log

### 5.4 Implementation Plan

#### Phase 1: Core Server (1-2 days)
```
mt5_tester_mcp/
├── server.py              # MCP server entry point (FastMCP)
├── tools/
│   ├── compile.py         # MetaEditor64.exe /compile wrapper
│   ├── config.py          # INI config generator
│   ├── backtest.py        # terminal64.exe launcher + monitor
│   ├── parse_report.py    # HTML report parser (BeautifulSoup)
│   ├── parse_log.py       # Log file parser
│   └── validate.py        # EA validation (minimal test run)
├── resources/
│   ├── config_schema.md   # INI format documentation
│   └── troubleshooting.md # Common issues
├── utils/
│   ├── mt5_paths.py       # Auto-detect MT5 installation paths
│   ├── ini_format.py      # INI read/write with proper encoding
│   └── process.py         # Subprocess management
├── config/
│   └── default_paths.json # Default MT5 paths per broker
├── requirements.txt
└── README.md
```

#### Phase 2: Advanced Tools (1 day)
- `mt5_optimize` — Parameter sweep orchestrator
- `mt5_get_symbols` / `mt5_get_history_info` — Market data queries
- `mt5_parse_log` — Enhanced log analysis with EA Print output extraction

#### Phase 3: Integration (0.5 day)
- Add to OpenClaw MCP config
- Test with OWL orchestrator
- Document usage patterns

### 5.5 Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **MCP Framework** | `fastmcp` (Python) | Same as Qoyyuum, well-supported, stdio+HTTP |
| **Transport** | stdio (default), HTTP (optional) | stdio for local AI clients, HTTP for remote |
| **INI Format** | `[Tester]` section with `Test*` prefix | Works with `terminal64.exe /config:` |
| **Report Parsing** | BeautifulSoup4 | MT5 HTML reports are well-structured |
| **Log Parsing** | Regex + line-by-line | MT5 logs have consistent format |
| **Process Management** | `subprocess.run()` with timeout | Simple, blocking, reliable |
| **MT5 Detection** | Registry + common paths | Auto-find terminal64.exe and MetaEditor64.exe |
| **Concurrency** | Sequential (1 terminal per data dir) | MT5 limitation — one instance per data folder |

### 5.6 Critical Fix for Current OnInit() Issue

Based on the debug report, the MCP server should include a **diagnostic tool** that:

1. Creates a minimal test INI (1-day range, Open prices model)
2. Runs the backtest
3. Parses the expert log for EA Print output
4. Checks for common failure patterns:
   - **"automated trading is disabled"** → Enable `AutoTrading` in terminal
   - **No EA log entries** → EA crashed in OnInit, likely missing include or array error
   - **"0 bars"** → Symbol name wrong or no history data
   - **Period M0** → Wrong period format (should be `5` not `M5` in `[Tester]` section)

The `mt5_validate_ea` tool would have caught the current issue immediately.

---

## 6. Alternative: Extend Existing MCP Server

Instead of building from scratch, we could **fork Qoyyuum's `mcp-metatrader5-server`** and add Strategy Tester tools:

**Pros:**
- Existing MT5 connection handling
- Established MCP patterns
- Community maintenance

**Cons:**
- Focused on live trading, different architecture
- Would need significant refactoring
- Adds trading tools we don't need

**Verdict:** Build standalone. The Strategy Tester workflow is fundamentally different from live trading (subprocess management vs. IPC connection).

---

## 7. Integration with Current Workflow

### Current Pipeline:
```
Idea → Python Backtest (optimizer_v2) → Monte Carlo → NATIVE MT5 BACKTEST → Report
```

### With MCP Server:
```
Idea → Python Backtest (optimizer_v2) → Monte Carlo → MCP:mt5_validate_ea → 
  MCP:mt5_compile → MCP:mt5_create_config → MCP:mt5_run_backtest → 
  MCP:mt5_parse_report → Analysis → Iterate
```

### OWL Orchestration Pattern:
```
OWL: "Validate that DMR_FULL_BACKTEST EA loads correctly"
  → MCP: mt5_validate_ea("DMR_FULL_BACKTEST.ex5")
  → Result: {success: false, error: "OnInit() no output, 0 bars processed"}

OWL: "Check the expert log for DMR_FULL_BACKTEST errors"
  → MCP: mt5_parse_log(ea_name="DMR_FULL_BACKTEST")
  → Result: {errors: ["automated trading is disabled because account changed"]}

OWL: "Fix: enable auto-trading and revalidate"
  → [Fix terminal settings]
  → MCP: mt5_validate_ea("DMR_FULL_BACKTEST.ex5")
  → Result: {success: true, bars_processed: 8640, trades: 42}
```

---

## 8. Recommendations

1. **Build `mt5-tester-mcp`** — No existing solution covers Strategy Tester automation
2. **Start with `mt5_validate_ea`** — This alone would solve the current OnInit() debugging nightmare
3. **Use `fastmcp`** — Proven framework, compatible with OpenClaw
4. **Auto-detect MT5 paths** — Support multiple broker installations
5. **Include troubleshooting resource** — Embed MT5 debugging knowledge for LLM consumption
6. **Keep it focused** — Strategy Tester only, no live trading (use Qoyyuum for that)

---

## 9. Quick Start (Once Built)

```bash
# Install
pip install mt5-tester-mcp

# Configure OpenClaw MCP
{
  "mcpServers": {
    "mt5-tester": {
      "command": "python",
      "args": ["-m", "mt5_tester_mcp.server"],
      "env": {
        "MT5_TERMINAL_PATH": "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
        "MT5_METAEDITOR_PATH": "C:\\Program Files\\MetaTrader 5\\MetaEditor64.exe",
        "MT5_DATA_FOLDER": "C:\\Users\\wifik\\AppData\\Roaming\\MetaQuotes\\Terminal\\..."
      }
    }
  }
}
```

---

## 10. References

- [Qoyyuum/mcp-metatrader5-server](https://github.com/Qoyyuum/mcp-metatrader5-server) — Reference MCP implementation
- [emerzon/mt-data-mcp](https://github.com/emerzon/mt-data-mcp) — Research/automation toolkit
- [MegaJoctan/StrategyTester5](https://github.com/MegaJoctan/StrategyTester5) — Python simulation framework
- [MQL5 Python Integration Docs](https://www.mql5.com/en/docs/integration/python_metatrader5)
- [MT5 Command Line Docs](https://www.metatrader5.com/en/terminal/help/start_advanced/start)
- [StackOverflow: Running MT5 Test from Script](https://stackoverflow.com/questions/73766843/)
- Current debug report: `sw-dev/MT5_BACKTEST_DEBUG_REPORT.md`
- Current skill: `.agents/skills/mt5-strategy-tester/SKILL.md`
