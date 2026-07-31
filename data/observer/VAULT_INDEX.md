# 🧠 OBSIDIAN VAULT — OC2 Memory Spine
> **Vault Root:** `data/observer/`
> **Last Updated:** 2026-05-31 02:30 EDT
> **Mode:** UNIFIED FIELD ORCHESTRATION

---

## Vault Structure

```
data/observer/
├── VAULT_INDEX.md          ← You are here
├── bible/
│   └── QUANTLAB_BIBLE.md   ← Central navigation hub
├── ontology/
│   ├── ONTOLOGY_CORE.md    ← Single source of truth
│   ├── ONTOLOGY_P90.md     ← P90 Kinetic definitions
│   ├── ONTOLOGY_ST.md      ← Symmetry Trap definitions
│   └── ONTOLOGY_DUAL_ENGINE.md ← Dual engine convergence
├── strategies/
│   ├── ACTIVE_STRATEGIES.md ← What's deployed + performance
│   └── ENGINES_INDEX.md    ← Strategy code registry
├── deployment/
│   └── DEPLOYMENT_STATUS.md ← What's live on broker
├── optimization/
│   └── OPTIMIZATION_LOG.md ← Tuning history + next steps
├── failures/
│   └── FAILURE_INDEX.md    ← What broke + how fixed
├── memory/
│   └── continuity_memory.json ← Machine-readable state
└── chat/
    └── chat_log.json       ← Conversation history
```

---

## Knowledge Graph

```
[[ONTOLOGY_CORE]]
  ├── [[ONTOLOGY_P90]] → [[ENGINE_P90]] → [[ACTIVE_STRATEGIES]]
  ├── [[ONTOLOGY_ST]] → [[ENGINE_ST]] → [[ACTIVE_STRATEGIES]]
  └── [[ONTOLOGY_DUAL_ENGINE]] → [[BACKTEST_RESULTS]]

[[ACTIVE_STRATEGIES]]
  ├── [[ENGINES_INDEX]] → quant-lab/engines/
  ├── [[DEPLOYMENT_STATUS]] → quant-lab/mt5/
  └── [[OPTIMIZATION_LOG]] → quant-lab/reports/

[[BACKTEST_RESULTS]]
  ├── 19 individual asset reports
  ├── 4 group reports
  ├── Multi-asset combined
  └── Top 5 + Major 6 deep-dive

[[FAILURE_INDEX]]
  ├── Strategy failures (MT5, Pine, DMR)
  ├── Orchestration failures (auto-work, execution)
  └── System failures (CLI, Nautilus divergence)
```

---

## Obsidian Behaviors (Mandatory)

1. **Research Persistence** — every discovery stored in vault
2. **Agent Memory Chains** — agents leave operational notes
3. **Knowledge Graphing** — link ontology ↔ telemetry ↔ strategies ↔ results
4. **Failure Indexing** — repeated bugs tracked structurally
5. **Artifact-Centric** — reports, manifests, configs primary. Conversation secondary.

---

## Key Files Outside Vault (referenced)
- `quant-lab/QUANTLAB_BIBLE.md` — Full bible (source of truth)
- `quant-lab/CEREBUS_ONTOLOGY.md` — Complete ontology (locked reference)
- `quant-lab/reports/INDEX.md` — Master report index
- `quant-lab/engines/` — Strategy code (TRUTH SOURCE)
- `quant-lab/configs/asset_configs.py` — Per-asset calibration

---

*Vault maintained by OWL — O2C Unified Field Operator*
*Every session: read VAULT_INDEX.md first, update continuity_memory.json last*
