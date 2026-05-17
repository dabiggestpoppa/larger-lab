# Tool Installation Report

**Date:** May 16, 2026
**Platform:** Windows 11 (x64), Python 3.11

---

## Summary

| # | Tool | Status | Version | Notes |
|---|------|--------|---------|-------|
| 1 | TradingView MCP Server | ✅ Installed | 0.7.1 | Importable, config created |
| 2 | TensorTrade | ✅ Installed | 1.0.3 | Installs OK; runtime import triggers Gym deprecation warning + heavy TF load |
| 3 | Scientific Agent Skills | ❌ Not found | N/A | No PyPI package exists under this name |
| 4 | Supertonic TTS | ✅ Installed | 1.2.3 | Importable, ONNX-based TTS |
| 5 | Agent Hooks System | ✅ Created | N/A | 4 hook scripts in `tools/agent-hooks/` |
| 6 | LLM Wiki | ✅ Cloned | N/A | Cloned from GitHub to `projects/llm_wiki/` |

---

## Details

### 1. TradingView MCP Server ✅
- **Package:** `tradingview-mcp-server` v0.7.1
- **Import test:** `import tradingview_mcp` → OK
- **Config file:** `config/tradingview-mcp.json` created
- **Dependencies:** feedparser, mcp, tradingview-screener, tradingview-ta
- **Usage:** Run via `uvx --from tradingview-mcp-server tradingview-mcp`

### 2. TensorTrade ✅ (with caveats)
- **Package:** `tensortrade` v1.0.3
- **Pip show:** Confirmed installed
- **Runtime caveat:** Importing tensortrade pulls in `tensorflow` (350MB+) and `gym` (deprecated). The Gym library prints a deprecation warning about NumPy 2.0 incompatibility. Full import may cause OOM on memory-constrained systems.
- **Recommendation:** Consider upgrading `gym` → `gymnasium` or using TensorTrade in a dedicated environment with sufficient RAM.
- **Dependencies:** gym, ipython, matplotlib, numpy, pandas, plotly, pyyaml, stochastic, tensorflow

### 3. Scientific Agent Skills ❌
- **Package:** `scientific-agent-skills`
- **Status:** No matching distribution found on PyPI
- **Action needed:** Verify correct package name or source. May be a private/internal package or require installation from a different index (e.g., GitHub, private registry).

### 4. Supertonic TTS ✅
- **Package:** `supertonic` v1.2.3
- **Import test:** `import supertonic` → OK
- **Description:** High-quality Text-to-Speech synthesis with ONNX Runtime
- **Dependencies:** huggingface-hub, numpy, onnxruntime, soundfile
- **Source:** Supertone AI (supertone.ai)

### 5. Agent Hooks System ✅
Created `tools/agent-hooks/` with 4 standalone Python scripts:

| Hook | File | Purpose |
|------|------|---------|
| Pre-Tool-Use | `pre-tool-use.py` | Validates commands against a denylist of dangerous patterns (rm -rf, format, fork bombs, pipe-to-shell, etc.) |
| Post-Tool-Use | `post-tool-use.py` | Runs syntax checks after file edits (Python py_compile, JSON validation, YAML validation) |
| Session-Start | `session-start.py` | Loads project context (AGENTS.md, SOUL.md, phase state, agent tags) |
| Session-End | `session-end.py` | Writes audit log entry to `logs/session-audit.jsonl` |

All hooks follow the same protocol:
- Receive JSON via stdin
- Return JSON via stdout
- Exit 0 on success, 1 on failure

### 6. LLM Wiki ✅
- **Source:** Cloned from `https://github.com/nashsu/llm_wiki.git`
- **Location:** `projects/llm_wiki/`
- **Files:** 308 files checked out
- **Note:** Not found on USB cloud storage; cloned from GitHub instead.

---

## Next Steps for Integration

1. **TradingView MCP:** Add the MCP server config to your Claude Desktop or OpenClaw MCP configuration to enable trading chart analysis.
2. **TensorTrade:** Test with a simple trading agent script. Monitor RAM usage due to TensorFlow dependency. Consider `gym` → `gymnasium` migration.
3. **Scientific Agent Skills:** Research the correct package name/source. Check if it's available via `pip install git+https://...` or a private registry.
4. **Supertonic TTS:** Download voice models from HuggingFace. Test with `supertonic` CLI or Python API.
5. **Agent Hooks:** Integrate into agent workflow by calling hooks before/after tool use. Add to OpenClaw skill configuration if supported.
6. **LLM Wiki:** Review contents for relevant research. May contain useful LLM knowledge base material.
