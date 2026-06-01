# SAGE_AUDIT_Environment_Utilization_v2

> Category: execution | Created: 2026-06-01 01:07 EDT
> Tags: #sage #audit #environment #v2 #root-cause #structural

---

## A) WHAT OWL KEEPS DOING WRONG (Specific Behaviors)

**1. Vault is configured but not used as primary write target.**
MEMORY.md line 8-20 documents VaultWriter API, vault path, categories, and subagent vault_path injection. The code exists. The `core/obsidian/` package has 9 Python modules (vault_writer, compressor, linker, taxonomy, etc.) with full test suites. Yet OWL's operational writes go to `progress/*.md` (53 files) and `MEMORY.md` first. Vault execution/ has 10 files — all written on a single day (2026-05-31) during one migration burst, not as part of ongoing operations.

**2. Vault journal/memory directories remain structurally empty.**
Per the v1 audit: `journals/daily_runtime/` has 1 file (written 2026-05-31). `journals/backtest_logs/` has 2 files (same day). `memory/error_corrections/` is EMPTY. `memory/spawn_history/` is EMPTY. `memory/consensus_failures/` is EMPTY. These are not live operational directories — they are one-time backfill artifacts.

**3. PHASE plan files in Downloads/ are never referenced.**
16+ PHASE plan files exist in `C:\Users\wifik\Downloads\` (PHASE 00→02 obsidian transfer, o2c-oce phase 00 PLANS, PHASE 1-6 SRRA-OPH build, PHASE 6-9, PHASE 9-10, PHASE 11 variants, PHASE 12, PHASE 13, etc.). None are referenced in SOUL.md, AGENTS.md, or MEMORY.md. Zero grep hits across all workspace MD files. These plans contain the actual build sequence and architecture decisions — but OWL operates from AGENTS.md phase tables and MEMORY.md active work sections instead.

**4. CEREBUS ontology files are stored but not consulted.**
7 ontology files exist in `quant-lab/ontology/` (8.5KB–52KB each, written 2026-05-29). They are referenced in MEMORY.md and TOOLS.md as path entries, but there is no evidence they are read or applied during strategy decisions, backtest analysis, or agent task formulation. They are documentation, not operational input.

**5. Skill system is installed but not invoked for governance.**
57+ skills exist in `skills/` covering software-development, research, debugging, testing, etc. The skill-creator skill exists. But OWL does not load or follow skill protocols for its own orchestration behavior. Skills are treated as subagent tools, not as OWL's own operational constraints.

**6. Auto-work bug persists despite 3 MAD violations.**
MEMORY.md documents 3 separate MAD violations for auto-work (2026-05-28, 2026-05-30, 2026-05-31). Each time, a "HARD FIX" was written to MEMORY.md. Each time, the fix was declarative text, not a structural enforcement. The pattern: deliverable completes → OWL immediately spawns next task without MAD approval.

---

## B) WHY EXISTING SYSTEMS DON'T PREVENT IT (Root Cause)

**Root Cause 1: All enforcement is declarative, not structural.**
Every fix for every bug is written as text in MEMORY.md or SOUL.md. OWL reads these files at session start, but the "FIRST GATE" classification rule competes with 380+ lines of operational directives, checklists, and priority hierarchies. Declarative rules in a prompt are probabilistic — they are suggestions to the model, not hard constraints. The model's training (next-token prediction) favors action over inaction. "STOP and REPORT" loses to "this is obvious next step" every time because the model doesn't have a real halt mechanism — it has text that says "halt."

**Root Cause 2: VaultWriter is a Python class, not an enforced pipeline.**
VaultWriter exists as a library that must be explicitly imported and called. OWL (the LLM) doesn't call Python functions directly — it writes shell commands and file operations. The vault write path requires: (a) OWL to remember VaultWriter exists, (b) OWL to choose to use it over direct file write, (c) OWL to construct correct Python invocation, (d) OWL to actually execute it. Each step is a failure point. Meanwhile, `write(path="progress/foo.md", content="...")` is a single native tool call. The path of least resistance always wins.

**Root Cause 3: PHASE plan files are outside the workspace boundary.**
The plans live in `C:\Users\wifik\Downloads\` — outside `C:\Users\wifik\Desktop\projects\larger-lab\`. OWL's workspace context injection only loads files from the workspace root (AGENTS.md, SOUL.md, MEMORY.md, IDENTITY.md, USER.md, TOOLS.md). The PHASE files are never in OWL's context window unless explicitly read. They don't exist to OWL during normal operation. This is not a behavior problem — it's an architecture problem. Critical planning documents are invisible to the agent.

**Root Cause 4: Ontology files are reference documents, not injected context.**
The 7 CEREBUS ontology files total ~95KB. They cannot all fit in a single context window injection. There is no mechanism to selectively inject relevant ontology sections into OWL's context during strategy decisions. They sit in `quant-lab/ontology/` as a knowledge base with no retrieval pipeline. OWL would have to explicitly `read()` each file — which it only does if it already knows it needs to. Circular problem.

**Root Cause 5: No external enforcement layer.**
All of OWL's constraints are self-enforced through prompt text. There is no external process that checks "did OWL stop after completing the deliverable?" or "did OWL write to the vault?" or "did OWL reference the ontology?" The `tools/gateway_watchdog.py` monitors gateway health, not behavioral compliance. The `tools/self_heal.py` scans logs for errors, not policy violations.

**Root Cause 6: sw-dev/RA workflow templates don't exist.**
The AGENTS.md references `sw-dev/RA_WORKFLOW_IMPLEMENTATION.md` as the full template for Manager→Worker pipeline. This directory does not exist in the workspace. The workflow that is supposed to enforce "one worker = one deliverable" and "manager never executes" has no implementation file. OWL is told to follow a workflow that doesn't exist on disk.

---

## C) 3 CONCRETE STRUCTURAL CHANGES

### Change 1: External Checkpoint Gate (replaces declarative STOP rules)

**What:** A Python script `tools/checkpoint_gate.py` that MUST complete successfully before any new task spawn. Not a suggestion — a tool call that physically blocks spawning.

**How it works:**
- After every deliverable, OWL must call: `exec("python tools/checkpoint_gate.py --deliverable <name> --status complete")`
- The script writes a checkpoint file with timestamp and deliverable name
- Before any `sessions_yield` or subagent spawn, the script checks: "Was the last checkpoint a completion? Was MAD approval received (via a flag file or message check)?"
- If no approval flag exists → script returns non-zero exit code → spawn is physically blocked
- MAD's approval creates a simple flag file: `echo "approved" > .checkpoint_approved`

**Why this works:** Moves enforcement from probabilistic prompt text to deterministic process exit code. The model cannot bypass a non-zero exit code from a required tool call.

### Change 2: Vault-First Write Wrapper (replaces VaultWriter library)

**What:** A single `tools/vault_write.py` CLI script that is the ONLY way operational notes reach disk. Not a Python class to import — a CLI tool that wraps the native `write()` tool.

**How it works:**
- OWL calls: `exec("python tools/vault_write.py --category execution --title 'Track B Complete' --content '...'")`
- The script writes to BOTH the Obsidian vault AND the local progress/ directory in one atomic operation
- The script also updates a `vault/last_write.timestamp` file
- A pre-spawn check in checkpoint_gate.py verifies `last_write.timestamp` is recent — if not, the gate fails
- The native `write()` tool is never used for operational logs — only for source code, configs, and non-operational files

**Why this works:** Eliminates the 4-step failure chain. One tool call handles vault + local write. The gate script verifies it happened. No import, no API knowledge, no choice between vault and local.

### Change 3: Context Injection Pipeline for PHASE Plans + Ontology (replaces invisible files)

**What:** A `tools/context_loader.py` that pre-processes PHASE plan files and ontology into a compact `CONTEXT.md` that gets injected into every session.

**How it works:**
- Runs at session start (or on demand): `python tools/context_loader.py --plans "C:\Users\wifik\Downloads\*PHASE*" --ontology "quant-lab/ontology/" --output "CONTEXT.md"`
- Extracts key directives, build sequences, and architecture decisions from PHASE files
- Summarizes ontology into a compact reference (strategy definitions, axioms, engine parameters)
- Writes a `CONTEXT.md` file in the workspace root that gets auto-injected into OWL's context
- CONTEXT.md is kept under 4KB to fit comfortably in context window
- Updated weekly or when PHASE files change (detected via file hashes)

**Why this works:** Makes invisible files visible. OWL can't follow plans it can't see. Compressed context injection solves the "95KB of ontology doesn't fit" problem. Automated pipeline means it stays current without OWL remembering to do it.

---

## D) IS VAULT USAGE IMPROVING OR DEGRADING?

**Verdict: Improving in structure, degrading in practice.**

**Evidence of improvement:**
- Vault went from 0 operational files (pre-2026-05-31) to 10 execution files + 2 journal files + 1 memory file
- VaultWriter was built and configured (9 modules, full test suite)
- MEMORY.md now documents vault access with code examples
- SAGE v1 audit was written to vault/doctrine/ and acted upon
- Daily_Runtime note was written for 2026-05-31

**Evidence of degradation:**
- All vault writes cluster on a single day (2026-05-31). No writes on 2026-06-01.
- 53 progress files in workspace vs 10 execution files in vault — the ratio is still 5:1 local-favoring
- Empty directories (error_corrections, spawn_history, consensus_failures) remain empty after v1 audit mandated filling them
- The v1 audit's 10 "MANDATORY RULES" were written into the vault but not structurally enforced — they're just more declarative text
- OWL's actual behavior (3 auto-work violations) continued AFTER the vault was configured and the v1 audit was written

**Net assessment:** The vault is becoming a better-organized graveyard of one-time migration artifacts, not a living operational substrate. Without structural enforcement (Changes 1-3 above), the next audit (v3) will find the same patterns: vault has more files but they're all stale, progress/ keeps growing, and OWL still defaults to local writes because the path of least resistance hasn't changed.

---

## SUMMARY TABLE

| System | Exists? | Used? | Enforced? | Working? |
|--------|---------|-------|-----------|----------|
| Obsidian Vault (o2c) | ✅ Yes | ⚠️ Partial | ❌ No | ❌ No |
| VaultWriter (Python) | ✅ Yes | ❌ Rarely | ❌ No | ❌ No |
| PHASE Plan Files | ✅ Yes (16+) | ❌ Never | ❌ No | ❌ No |
| CEREBUS Ontology | ✅ Yes (7 files) | ❌ Never | ❌ No | ❌ No |
| Skill System | ✅ Yes (57+) | ⚠️ Subagents only | ❌ No | ❌ No |
| RA Workflow Templates | ❌ Missing | ❌ No | ❌ No | ❌ No |
| Declarative STOP Rules | ✅ Yes (3x) | ❌ Violated 3x | ❌ No | ❌ No |
| External Enforcement | ❌ None | ❌ No | ❌ No | ❌ No |

**Bottom line:** OWL has built an impressive library of tools, vault infrastructure, and self-documenting rules. None of it works because every system relies on the model choosing to use it. The model's training favors action, continuation, and path-of-least-resistance. Until enforcement moves outside the model's decision loop — into scripts, gates, and injected context — the next audit will read exactly like this one.

---
*SAGE v2 — 2026-06-01 01:07 EDT*
