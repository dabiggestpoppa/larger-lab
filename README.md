# 🦉 LARGER-LAB — AI Agent Harness & Quantitative Trading Workspace

> **Owner:** dabiggestpoppa | **Branch:** master | **Phase:** OCE Phase 3 (Observer Runtime)

---

## 🚀 Quick Start

```bash
# 1. Clone & enter
git clone https://github.com/dabiggestpoppa/larger-lab.git
cd larger-lab

# 2. Python environment (uv recommended)
uv venv .venv
.venv\Scripts\activate  # Windows

# 3. Install deps
uv pip install -r requirements.txt

# 4. Run SRRA-OPH tests
python -m srrs_opc.tests.test_phase2_e2e
python -m srrs_opc.tests.test_phase3_e2e
python -m srrs_opc.tests.test_phase4_e2e
```

---

## 📁 Workspace Structure

```
larger-lab/
  ├── 📄 CLAUDE.md              ← 12-rule behavioral contract (read first)
  ├── 📄 AGENTS.md              ← Team manifest & phase status
  ├── 📄 SYSTEM_ARCHITECTURE.md ← System constitution
  ├── 📄 WORKFLOW_PROTOCOL.md   ← Task lifecycle & handoff rules
  ├── 📄 CODEMAP.md             ← Code map with Mermaid diagrams
  ├── 📄 KEYS.md                ← API keys reference
  │
  ├── 📁 system-arch/           ← 📊 All Mermaid diagrams (consolidated)
  │   ├── README.md             ← Index + alignment checklist
  │   ├── 01-system-overview.md ← All 5 architecture levels
  │   ├── 02-agent-workflow.md  ← Agent communication + workflow state machine
  │   ├── 03-srra-topology.md   ← SRRA-OPH technical architecture (Phases 1-9)
  │   └── 04-data-and-storage.md← Data pipeline + storage + memory sync
  │
  ├── 📁 srrs_opc/              ← SRRA-OPH core (33 Python files, 77 tests)
  │   ├── tests/                ← Test suites (Phase 2-4)
  │   ├── docs/                 ← Design docs per phase
  │   └── README.md             ← SRRA-OPH documentation
  │
  ├── 📁 nautilus/              ← NautilusTrader backtesting
  │   ├── strategies/           ← Strategy implementations
  │   ├── data/                 ← Parquet data files
  │   └── reports/              ← Backtest reports
  │
  ├── 📁 agent-lab/             ← Agent infrastructure
  │   └── agents/
  │       ├── hermes/           ← Hermes (Telegram execution agent)
  │       └── openclaw/         ← OpenClaw (CLI analysis agent)
  │
  ├── 📁 skills/                ← Workspace-level skills
  ├── 📁 .agents/skills/        ← Agent-specific skills (40+)
  ├── 📁 .github/skills/        ← GitHub skills
  │
  ├── 📁 progress/              ← Agent sub-progress files
  │   ├── claude-code-progress.md
  │   ├── openclaw-progress.md
  │   ├── hermes-progress.md
  │   ├── assistant-progress.md
  │   └── polymorph-progress.md
  │
  ├── 📁 all-mermaids/          ← 📊 All Mermaid diagrams
  │   ├── phase1-5-original/    ← Original Phase 1-5 diagrams
  │   ├── phase1-5-updated/     ← Updated Phase 1-5 diagrams
  │   └── phase6-9-resources/   ← Phase 6-9 topology & integration
  │
  ├── 📁 docs/                  ← Documentation & resources
  │   ├── images/               ← Diagrams & screenshots
  │   └── phases/               ← Phase progress docs
  │
  ├── 📁 tools/                 ← Automation & utilities
  │   ├── scripts/              ← PowerShell & batch scripts
  │   ├── bin/                  ← Binaries (cloudcli, TVBridge)
  │   └── workspaces/           ← VS Code workspace files
  │
  └── 📁 shared-conversations/  ← Team coordination
      └── team-chat.md          ← Agent chat hub
```

---

## 🤖 Agent Network

| Agent | Tag | Role | Interface | Status |
|-------|-----|------|-----------|--------|
| 🔵 Claude Code | CC | Overseer / Architecture | VS Code | 🟢 Active |
| 🟣 OpenClaw | OC | Analysis / Planning | CLI Gateway :18789 | 🟢 Active |
| 🟢 Hermes | HR | Execution / Backtesting | Telegram | 🟢 Active (v2) |
| 🟡 Assistant Mgr | AS | Context / Quality | Workspace | 🟢 Active |
| 🔴 Polymorph (Hawk) | PM | Debugger / Tool Builder | Workspace | 🟢 Standby |

---

## 📊 SRRA-OPH Build Status

| Phase | Status | Tests | Description |
|-------|--------|-------|-------------|
| Phase 1 | ✅ Complete | 3/3 | Foundational Observer Mesh |
| Phase 2 | ✅ Complete | 7/7 | Reconstruction + Recoverability |
| Phase 3 | ✅ Complete | 4/4 | Emergent Topology |
| Phase 3 Book 2 | ✅ Complete | 6/6 | Updated Architecture |
| Phase 4 | ✅ Complete | 6/6 | Workspace Integration |
| Phase 5-9 | ✅ Complete | 426 | Post-Deployment Upgrades |
| **Total** | | **446 tests** | |

## 🚀 V3 Cognitive Field Status

| Phase | Name | Status | Tests |
|-------|------|--------|-------|
| V3 Phase 1 | Resonant Signal Substrate (RSS) | ✅ Complete | 139 |
| V3 Phase 2 | Reconstructive Continuity Manifold (RCM) | ✅ Complete | 52 |
| V3 Phase 3 | Resonant Topology & BSP Emergence | ⏳ Pending | — |

**V3 Total: 191 tests passing**

---

## 📈 Trading Stack

- **Backtesting:** NautilusTrader (Python) — MT5 fully deprecated
- **Strategies:** P90 CEREBUS, Symmetry Trap, EMA Cross
- **Data:** 29 CSV files (M1/M5, 2022-2026) → Parquet
- **Analysis:** VectorBT, pandas, scikit-learn

---

## 🔧 Key Commands

```bash
# Run all SRRA-OPH tests
python -m srrs_opc.tests.test_phase2_e2e
python -m srrs_opc.tests.test_phase3_e2e
python -m srrs_opc.tests.test_phase4_e2e

# Run Nautilus backtest
python nautilus/run_backtest.py

# Sync progress files
python tools/progress-sync.py --force

# Check phase status
python tools/phase-gate.py --status
```

---

## 📚 Documentation

- `CLAUDE.md` — 12-rule behavioral contract (read by all agents)
- `SYSTEM_ARCHITECTURE.md` — System constitution & data flow
- `WORKFLOW_PROTOCOL.md` — Task lifecycle & agent handoff rules
- `CODEMAP.md` — Code map with Mermaid architecture diagrams
- `all-mermaids/` — All Mermaid diagrams organized by phase
- `srrs_opc/docs/` — SRRA-OPH design docs per phase

---

## 🔐 Security

- All API keys stored in `C:\Users\wifik\Downloads\keys.txt` (NEVER in repo)
- Agent credentials scoped per-agent, least privilege
- GitHub PAT in `KEYS.md` for repo operations

---

## 📝 License

See `LICENSE` file. All agent code follows the 12-rule CLAUDE.md contract.
