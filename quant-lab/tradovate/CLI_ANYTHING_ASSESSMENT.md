# CLI-Anything Assessment for NinjaTrader 8 + Tradovate

**Date:** 2026-05-31
**Assessor:** OWL subagent (cli-assessment)
**Verdict: CLI-Anything is NOT the right tool for this use case. Use the alternatives below instead.**

---

## 1. What CLI-Anything Actually Is

CLI-Anything (HKUDS/CLI-Anything) is a **framework + registry for building CLI harnesses** that make GUI applications accessible to AI agents. It has two components:

1. **CLI-Hub** (`pip install cli-anything-hub`): A package manager/registry where agents can browse and install community-built CLIs.
2. **7-phase harness generator**: A process where an AI coding agent analyzes a GUI app's source code, maps its backend engine/data model/file formats, and generates a Python Click CLI that wraps the app.

### Critical Architectural Point

CLI-Anything harnesses **do NOT wrap GUI applications via screen scraping, accessibility APIs, or pixel automation**. The HARNESS.md is explicit:

> *"Do not screen-scrape GUI windows... bypass the screen entirely. No more brittle GUI automation that breaks the moment a window moves."*

Instead, CLI-Anything works by:
- **Finding the backend engine** underlying the GUI (e.g., MLT for Shotcut, ImageMagick for GIMP)
- **Manipulating native data formats** directly (project files, XML, JSON, binary formats)
- **Calling real CLI/headless entry points** of the backend (e.g., `libreoffice --headless`, `blender --background`, `ffmpeg`)
- Generating a stateful Python CLI with REPL that talks to these backends

**In short: it targets the engine underneath the dashboard, not the GUI itself.**

---

## 2. Why It Won't Work for NinjaTrader 8

NinjaTrader 8 has **none of the characteristics** CLI-Anything needs:

| CLI-Anything Requirement | NinjaTrader 8 Reality |
|---|---|
| Open-source or accessible source code | **Closed-source proprietary C#/.NET** |
| Separate backend engine with CLI entry points | **Monolithic WPF app; no headless mode** |
| Manipulable project/data files as interface | **Internal state lives in running process memory** |
| Existing CLI or headless interface | **None exists** |
| Cross-platform (Linux headless servers) | **Windows-only desktop application** |

NT8 is a **closed, monolithic Windows desktop application**. There is no headless backend to call, no project file format to manipulate, no CLI interface to wrap. The only way to interact with a running NT8 instance is through its internal NinjaScript engine (C#) or its ATI (Automated Trading Interface) file/DDE signal protocol.

Even if someone built a CLI-Anything harness for NT8, it would have to resort to something CLI-Anything explicitly prohibits: screen scraping or GUI automation. That would be brittle, fragile, and against the project's own design principles.

**Maturity note:** CLI-Anything is relatively young (active development in 2026, ~100+ harnesses in registry). It's gaining traction in the AI agent community, but it's not a battle-tested enterprise solution. Even in its ideal use case (open-source apps with headless backends), harnesses require significant manual effort and community contribution.

---

## 3. NinjaTrader 8 Native Automation Options

NT8 does have legitimate programmatic interfaces — just not ones CLI-Anything can wrap:

### 3.1 NinjaScript (C#) — Primary Native API
- Full access to orders, positions, indicators, chart data
- Runs *inside* the NT8 platform as strategies, indicators, or add-ons
- **Best for:** execution logic that needs to be tightly integrated with NT8's order management
- **Downside:** Must learn C#/NinjaScript; no Python

### 3.2 ATI (Automated Trading Interface)
- Enabled via Options → Automated trading interface
- Sends trade signals from external apps into NT8 via **file or DDE** protocols
- Supports Buy/Sell/Exit signals to NT8 accounts
- **Best for:** simple signal → order routing from an external system
- **Downside:** Not REST/HTTP; limited to trade signals (no rich data queries)

### 3.3 CrossTrade NT8 Add-On (REST API) ← Best Third-Party Option
- CrossTrade provides a **REST API add-on** that exposes NT8 externally
- Endpoints: accounts, positions, orders, executions, quotes
- Flow: Your code → HTTPS to CrossTrade server → CrossTrade NT8 Add-On → NT8 desktop
- ~50ms latency; reportedly handles 100K+ orders/day
- Bearer token authentication
- **Best for:** Python/external bot integration with a running NT8 instance
- **Links:** [CrossTrade API docs](https://crosstrade.io/blog/introducing-the-crosstrade-api/) | [NT8 forum thread](https://forum.ninjatrader.com/forum/ninjatrader-8/add-on-development/1320387-introducing-crosstrade-s-rest-api-for-ninjatrader-8)

### 3.4 NinjaTrader Trader APIs (Infrastructure REST API)
- Separate from the desktop platform; REST with Swagger definitions
- Targets NinjaTrader's brokerage/infrastructure layer
- **Best for:** Direct broker environment integration without a desktop GUI
- **Link:** [developer.ninjatrader.com/products/api](https://developer.ninjatrader.com/products/api)

---

## 4. Tradovate Direct API — The Better Path

**This is the most important finding: Tradovate has a fully REST + WebSocket API that can bypass NinjaTrader entirely for trading execution.** If your primary goal is to execute futures trades programmatically, you may not need NT8 at all.

### What It Does
- **REST API** for orders, positions, accounts, instruments
- **WebSocket API** for real-time market data streaming
- Demo environment: `demo.tradovateapi.com`
- Production: `live.tradovateapi.com`
- Auth: API key + CID + access token flow

### How It Works
1. Create API key/CID in Tradovate platform (Settings → API)
2. Request access token via REST with credentials
3. Use token for subsequent REST calls (submit orders, query positions, etc.)
4. Connect WebSocket for market data streams
5. Full algorithmic order management from any language (Python, Node, C#, etc.)

### Advantages Over NT8 for CEREBUS Integration
- **Python-native** — works directly with your existing Python trading infrastructure
- **Headless** — runs on a VPS; no Windows desktop required
- **No GUI to automate** — it's already an API
- **OpenAPI spec** available for client generation
- **Replay/simulation** endpoints for backtesting (`/initializeClock`)
- **Direct broker execution** — no middleman

### Caveats
- CME market data licensing: Real-time CME data via API requires CME sub-vendor status (~$100-$1000/month). Workaround: use external data vendors (DataBento, etc.) for signals, Tradovate API only for execution.
- API add-on may need to be enabled on your Tradovate account

### Resources
- [API docs (demo)](https://api-d.tradovate.com)
- [API docs (production)](https://api.tradovate.com)
- [Partner API docs](https://partner.tradovate.com/overview/welcome/introduction-to-tradovate-partner-api)
- [Example Node.js trading bot](https://github.com/tradovate/example-api-Trading-strategy)

---

## 5. Recommendation

### For CEREBUS → Futures Execution, ranked:

1. **🥇 Tradovate REST API (direct)** — Best option. Python-native, headless, purpose-built for programmatic trading. CEREBUS signals in Python → REST API → Tradovate execution. Skip NT8 entirely for execution. Use external data vendor if CME data via API is cost-prohibitive.

2. **🥈 CrossTrade NT8 Add-On** — If you specifically need NT8's charting/analysis features alongside execution. Install the add-on, call REST endpoints from Python. Adds ~50ms latency and a dependency on a running NT8 desktop instance.

3. **🥉 NinjaScript C#** — Only if you want to build strategies entirely within NT8's ecosystem and don't need Python integration.

### Architecture Recommendation:
```
CEREBUS (Python) → Tradovate REST API → Futures Execution
                     ↑
              External data feed (DataBento, etc.)
```

**Skip CLI-Anything entirely for this use case.** Skip NinjaTrader 8 for execution if you don't need its charting/backtesting engine. Use the Tradovate API directly — it's what you're actually looking for.

---

## 6. Summary

| Approach | Works? | Recommendation |
|---|---|---|
| CLI-Anything wrapping NT8 | ❌ No | NT8 has no CLI/backend to wrap |
| NT8 NinjaScript C# | ✅ Yes | Only if building inside NT8 |
| CrossTrade REST API for NT8 | ✅ Yes | Good if NT8 specifically needed |
| Tradovate Direct REST API | ✅ **Best** | Python-native, headless, no GUI needed |
| NT8 ATI file/DDE signals | ⚠️ Limited | Simple signals only; not robust |

---

*End of assessment.*
