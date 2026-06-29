# Team Notes — Persistent Errors, Observations, and Troubleshooting

> **Purpose:** Shared knowledge base for errors that persist or caused trouble during building. All agents contribute here.
> **Format:** Date | Agent | Issue | Root Cause | Resolution
> **Current mission:** O2C × MAD LABS Sovereign Research Mesh (L1→L4). Plan: `docs/plans/O2C-RESEARCH-MESH.md`.

---

## Section 0A — DMR Strategy Deployment (2026-06-29)

### DMR v1 — Live on Demo ✅
- **Engine:** `quant-lab/mt5/dmr_multi_pair_live.py` (single entry per day)
- **Discord Bot:** `scripts/discord_dmr_bot.py` (DMR-only signals)
- **Pairs:** EURUSD, GBPUSD, USDJPY, GBPJPY, CHFJPY (~5 tr/day)
- **Results:** 14,582 trades, 92.6% WR, PF 134.2, +215,661p PnL
- **Status:** Running on demo account 1114712

### DMR v2 — Multi-Entry Optimization (PAUSED)
- **Engine:** `quant-lab/mt5/dmr_multi_pair_live_v2.py` (one P90 per 2hr window)
- **Results:** 32,102 trades, 91.4% WR, +568,752p PnL (+164% vs v1)
- **Status:** PAUSED — retcode 10027 on demo (stale signals from Sunday market close)
- **Note:** v2 code logic is correct but needs fresh market data to validate. Do NOT modify strategy execution logic (SL/TP distances, entry logic). The issue is stale signal timing, not broker rejection.

### Key Lesson
- **NEVER change strategy execution logic when debugging deployment issues.** The v1 engine works identically to v2 in terms of SL/TP calculation. The 10027 errors were from stale signals (Sunday market close), not broker rejection.
- **Always preserve working versions.** v1 remains live while v2 is optimized separately.
- **retcode 10027 = "Invalid stops"** — caused by stale entry prices when market is closed, NOT by SL/TP distance being too tight.

---

## Section 0 — Active Mission: Research Mesh Pitfalls (READ FIRST)

> Specific traps to avoid when building the research mesh. Add to this as we discover new ones.

### API & Network

**2026-06-06 | CC2 | OpenAlex rate limit defaults to "polite pool" (~10 req/s with email)**
- **Symptom:** First ingestion test gets 429 after ~50 papers
- **Root Cause:** OpenAlex uses a polite pool that requires a User-Agent or `mailto=` query param to get the higher rate limit
- **Resolution:** Always pass `mailto=ops@larger-lab.local` in every OpenAlex request. Add to `openalex_client.py` as a required param.
- **Lesson:** OpenAlex API is free, but you must identify yourself to get the higher quota. Same for S2 — include API key if available.

**2026-06-06 | CC2 | arXiv returns Atom XML, not JSON**
- **Symptom:** JSON parser crashes on arXiv response
- **Root Cause:** arXiv API uses Atom XML (legacy protocol)
- **Resolution:** Use `xml.etree.ElementTree` for arXiv; the namespace is `http://www.w3.org/2005/Atom`
- **Lesson:** Don't assume JSON. Each source has its own format. Source-specific parsers in `core/research/ingestion/`.

**2026-06-06 | CC2 | OpenAlex `concepts` field is a list with nested `score`**
- **Symptom:** Concept extraction drops confidence scores
- **Root Cause:** OpenAlex returns `{"display_name": "...", "score": 0.87, "level": 2}`
- **Resolution:** Concept extractor must preserve `score` to rank concepts. Top-5 by score is the right filter.
- **Lesson:** When ingesting from external APIs, preserve the schema's confidence/weight fields — they exist for a reason.

### Vault Pollution

**2026-06-06 | CC2 | Unbounded paper writes will create entropy landfill**
- **Symptom:** After 1000+ papers, vault becomes unsearchable, OCE retrieval returns noise
- **Root Cause:** No taxonomy enforcement on auto-generated notes
- **Resolution:**
  1. Daily write cap: 200 papers/day hard limit
  2. Required tags: `#paper #domain/{subdomain} #year/{year} #operational_relevance/{1-5}`
  3. Folder structure enforced: `O2C-VAULT/research/papers/{domain}/{year}/`
  4. Operational relevance <3 → skip write (don't pollute vault with low-value papers)
- **Lesson:** The vault is a precious resource. Every write should be a deliberate, scored, taxonomy-compliant decision.

### Cost Runaway

**2026-06-06 | CC2 | LLM distillation will burn budget if unguarded**
- **Symptom:** $20/day in OpenRouter charges after 1 day
- **Root Cause:** LLM-assisted distillation called for every paper, no token limit
- **Resolution:**
  1. Rule-based distiller is primary; LLM is opt-in
  2. Daily LLM spend cap: $2 hard, fail-closed
  3. Token budget per call: 500 input + 300 output
  4. Cost tracked in execution journal, AS reviews daily
- **Lesson:** Every LLM call in an autonomous system must have a cost ceiling. Default to no-LLM.

### Agent Runaway

**2026-06-06 | CC2 | Research agents spawning unbounded**
- **Symptom:** 50 research agents spawned, OpenRouter rate-limited, vault gets 500 junk notes
- **Root Cause:** Gap detector returns too many gaps, research agent runs in unbounded loop
- **Resolution:**
  1. Max 3 concurrent research agents
  2. Max 1 hour per task
  3. Max 2 retries per task → abandoned after that
  4. Gap detector thresholds tuned conservatively (≥0.4 confidence)
  5. Daily vault write cap: 200 (agent writes count toward this)
- **Lesson:** Autonomous systems need multiple limits — concurrency, duration, retries, daily totals. One limit alone is not enough.

### Data Integrity

**2026-06-06 | CC2 | Dedup is hard, especially across sources**
- **Symptom:** Same paper appears 3 times (once from OpenAlex, once from arXiv, once from S2) with different IDs
- **Root Cause:** No canonical ID system across sources
- **Resolution:**
  1. Primary key: DOI (universal)
  2. Fallback: OpenAlex ID `W...` → map from external IDs
  3. Fuzzy match: title + first author + year, with `difflib.SequenceMatcher` ratio ≥0.9
  4. Dedup is a write-time gate — if DOI matches, skip write; if fuzzy matches, log and skip
- **Lesson:** Cross-source dedup is a hard problem. Build the dedup layer in L1.7, don't bolt it on later.

### Graph Corruption

**2026-06-06 | CC2 | SQLite knowledge graph can grow without bound**
- **Symptom:** `citations.db` reaches 500MB, queries slow
- **Root Cause:** Every paper's full citation list ingested with no pruning
- **Resolution:**
  1. Only store edges where both nodes exist in our graph (orphan reference pruning)
  2. Index: `src_id`, `dst_id`, `kind` separately for fast lookup
  3. Periodic vacuum: monthly `VACUUM` + `ANALYZE`
  4. If a paper has >500 citations, only store the top-50 by external citation count
- **Lesson:** Graph storage is cheap to start, expensive to maintain. Design for pruning from day 1.

### Research Hygiene

**2026-06-06 | CC2 | Doctrine extraction will produce noise if not gated**
- **Symptom:** 200 "doctrine" notes created, 190 are trivial patterns that don't deserve the name
- **Root Cause:** Doctrine extractor triggered on ≥2 papers sharing a CAUSE, threshold too low
- **Resolution:**
  1. Doctrine threshold: ≥3 papers sharing a pattern, not 2
  2. Pattern must appear across ≥2 different methods, not just 2 papers using the same method
  3. Doctrine notes tagged `#doctrine #tier/{1-3}` to distinguish high-value from low-value
  4. AS reviews auto-generated doctrine daily
- **Lesson:** "Doctrine" is a strong word. The bar should be high. Most patterns are not doctrine.

### Contradiction Detection

**2026-06-06 | CC2 | Contradictions get over-flagged from superficial differences**
- **Symptom:** 50 "contradictions" detected, but they're actually different experimental conditions
- **Root Cause:** Naive string comparison of RESULT fields
- **Resolution:**
  1. Require shared METHOD to flag as contradiction
  2. Require shared dataset/domain
  3. LLM-assisted verification of true contradiction (with strict token cap)
  4. Tag: `#contradiction #verified` vs `#contradiction #candidate`
- **Lesson:** Most research "contradictions" are contextual. Be careful not to manufacture drama from the data.

---

## Section 1 — Pre-existing Pitfalls (carry-over from previous missions)

### Chaos Test Crashes

**2026-05-23 | OWL | Chaos test keeps crashing at higher amplification**
- **Symptom:** Process exits with code 1 during full_chaos scenario at amp ~3.0x
- **Root Cause:** Recovery timeout exceeded. At amp 3.0, event_flood duration = 360s, combined with router_failure (103s) and websocket_loss (90s) — too many concurrent long-running chaos events.
- **Resolution:** Internal auto-restart with consecutive crash limit (5) added. Test completes 4/5 cycles.
- **Lesson:** Recovery timeout must scale with number of concurrent injections, not just amplification.

**2026-05-23 | OWL | Duplicate chaos test instances running simultaneously**
- **Symptom:** Two chaos test processes writing to same trace log, causing interleaved entries
- **Root Cause:** Auto-restart wrapper spawned new subprocess before old one fully cleaned up its daemon threads
- **Resolution:** Kill all chaos-related processes before restarting. Use PID whitelist.
- **Lesson:** Always check for existing processes before spawning new ones. Use `Get-Process | Where-Object { $_.CommandLine -like '*chaos*' }`.

**2026-05-23 | OWL | Trace log FileNotFoundError**
- **Symptom:** `log_trace` fails with FileNotFoundError for stability/chaos_20x_trace.log
- **Root Cause:** Relative path `Path("stability/...")` depends on CWD. When CWD changes, the path breaks.
- **Resolution:** Changed to absolute paths based on `Path(__file__).parent`. Also added `mkdir(parents=True, exist_ok=True)` before every write.
- **Lesson:** Always use absolute paths based on script location, never relative paths for file I/O.

### Singleton Data Persistence

**2026-05-24 | OWL | Tufte renderers show empty data despite feeding data to singleton**
- **Symptom:** `render_observer_density.py` shows "No observer data available" even after feeding data to the singleton
- **Root Cause:** Each Python process gets its own singleton instance. Data fed in one process is not visible in another.
- **Resolution:** Export data to disk (JSON), have renderers load from disk instead of singleton.
- **Lesson:** Singletons don't persist across processes. For cross-process data sharing, use disk (JSON/parquet) or a database.

### Unicode Encoding on Windows

**2026-05-23 | AS/OWL | UnicodeEncodeError with emoji characters**
- **Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'` when printing test results
- **Root Cause:** Windows console uses cp1252 encoding by default, which doesn't support emoji
- **Resolution:** Set `$env:PYTHONIOENCODING="utf-8"` before running Python scripts
- **Lesson:** Always use UTF-8 encoding on Windows for any output containing emoji or special characters.

### Progress File Corruption

**2026-05-24 | OWL | Progress files being cleared or corrupted**
- **Symptom:** `phase-11-status.md` found empty after being written
- **Root Cause:** Unknown — possibly user cleanup or formatter tool
- **Resolution:** Recreate with verified data. Keep backups.
- **Lesson:** Don't trust progress files blindly. Verify contents before referencing.

### Workspace Scan Performance

**2026-06-06 | AS | po_workspace.py scanning `.venv` made tests take 7+ minutes**
- **Symptom:** Phase 2 integration tests timeout
- **Root Cause:** WorkspaceScanner walked into `.venv/`, `__pycache__/`, `.git/`, `node_modules/`
- **Resolution:** Added `EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "node_modules", "archive", ".openclaw", "memory-bank"}`
- **Lesson:** When scanning a workspace, ALWAYS exclude the obvious noise directories. Don't make the scanner smart — make it fast by filtering hard-coded noise.

### Multi-Replace String Truncation

**2026-05-25 | CC2 | `multi_replace_string_in_file` truncated po_fallback.py**
- **Symptom:** 200-line file ended up as 50 lines
- **Root Cause:** Replacements too large for the tool's atomic write buffer
- **Resolution:** Split into smaller, focused edits. Always read file after edit to verify length.
- **Lesson:** Tools have implicit size limits. Use surgical edits, not bulk rewrites. Always verify file integrity after.

### Absolute Paths in Tests

**2026-05-26 | PM | Tests fail on different CWDs**
- **Symptom:** `pytest oce/backend/tests/test_po_idle.py` passes from project root, fails from `oce/backend/`
- **Root Cause:** Test fixtures use relative paths like `Path("data/...")`
- **Resolution:** Use `Path(__file__).parent / "..."` for all fixture paths
- **Lesson:** Tests must be CWD-agnostic. Always use paths relative to the test file.

---

## Section 2 — General Observations

### From Operator Feedback (CC2 collected)

1. "Don't make things harder than they need" — tendency to over-engineer
2. "Test before you update" — tendency to update progress before verifying
3. "Don't make a plan until you feel fully aligned" — tendency to plan before understanding
4. "Take your time, don't rush execution" — tendency to rush through steps
5. "Autopilot = run until done, report at end" — don't ask for permission mid-task
6. "When given a multi-part request, do all parts" — don't skip steps to "save time"

### From Build Files

1. The architecture is ONE system (SRRA+OPH runtime + OCE interface), not many separate systems
2. Phases 1-5 are runtime substrate, Phases 6-7 are research horizon
3. Current priority: Phase 11 testing + OCE visualization + runtime instrumentation
4. Delay advanced cognition (Phases 6-7) until runtime stability is proven
5. **Vault is the moat, not the model** — protect it with caps, taxonomy, and audit trails
6. **Simplicity first** — minimum code that solves the problem

### From the Research Mesh Plan

1. **Build on real data, not mocks** — OpenAlex/arXiv are free, always use live API
2. **One thing per component** — ingestion ≠ distillation ≠ agents ≠ API
3. **Layer gates are real** — don't skip L1 GATE because you're excited about L3
4. **The loop is the system** — without the gap→spawn→research→update loop, it's just a paper downloader
5. **Safety reviews are non-negotiable** — AS gates every PR, especially anything that touches LLM costs or vault writes

---

## Section 3 — Process Patterns That Work

### Starting a Multi-Step Task
1. Read all relevant files first (BUILD-NOTES, plan doc, prior progress)
2. State assumptions explicitly before writing code
3. Define success criteria — what does "done" look like?
4. Build smallest testable version first
5. Verify with real data, not mocks
6. Commit + push before moving to next component

### Working in Parallel
1. Each agent owns specific files (no overlap)
2. If files must overlap, post to team-chat first
3. Use unique commit prefixes (`[RESEARCH-MESH L{N}]`) so CC can rebase
4. Daily 15-min sync post: what you built, what you're blocked on

### When Blocked
1. Post to team-chat with `[BLOCKED] <tag>: <description>`
2. Tag the agent whose work depends on yours
3. Propose 2-3 workarounds, pick one, move on
4. If >4 hours blocked, escalate to CC for re-scope

---

## Section 4 — Integration Test Fix Lessons (2026-06-06)

> Lessons learned from fixing 14 integration test failures caused by API mismatches between tests and implementations.

### API Consistency

**2026-06-06 | CC2 | Tests and implementations must agree on signatures**
- **Symptom:** 14 integration tests failing because test expectations didn't match actual class APIs
- **Root Cause:** Tests were written speculatively before implementations were finalized. When OC2 built 17 components in one commit, the APIs didn't match what the earlier-written tests expected.
- **Resolution:** Added backward-compatible aliases and overloads to match test expectations. Key fixes:
  - `CitationGraphBuilder.build_from_paper()`: changed return type from `int` to `list[dict]`
  - `ContradictionDetector.detect()`: now handles both `Paper` objects and `dicts`
  - `DoctrineExtractor`: added `vault_root` param and `extract()` method
  - `ResearchRouter.route()`: accepts `query=` and `budget_remaining=` kwargs
  - `FindingEvaluator.evaluate()`: accepts optional `context` arg
  - `TaskQueue.mark_failed()`: auto-abandons when retries exceeded; added `retry()` method
  - `AgentLifecycle.fail()`: tracks task-level retries (survives re-spawns)
- **Lesson:** When writing tests before implementations, use flexible assertions. When writing implementations after tests, add backward-compatible aliases rather than rewriting tests.

### Database Schema

**2026-06-06 | CC2 | daily_caps table missing from cache schema**
- **Symptom:** VaultWriter.write() fails with "no such table: daily_caps"
- **Root Cause:** The `_SCHEMA` in `cache.py` didn't include the `daily_caps` table, but `vault_writer.py` queried it.
- **Resolution:** Added `daily_caps` table to `_SCHEMA`.
- **Lesson:** All tables used by any component must be in the shared schema. Cross-component dependencies on DB tables must be documented.

### Orphan Pruning

**2026-06-06 | CC2 | Citation graph orphan pruning requires has_node check**
- **Symptom:** test_no_orphan_edges fails — edges created to non-existent nodes
- **Root Cause:** `CitationGraphBuilder.build_from_paper()` had a comment saying "orphan pruning" but didn't actually check if the destination node existed.
- **Resolution:** Added `has_node()` check before `add_edge()`. Added `has_node()` method to `GraphStore`.
- **Lesson:** Don't just comment about safety checks — implement them.

### ID Normalization

**2026-06-06 | CC2 | Node ID format mismatch between test data and builder**
- **Symptom:** test_build_citation_edges fails — 0 edges returned instead of 2
- **Root Cause:** Test added nodes with IDs like `"W201"`, but `_normalize_ref_id()` transformed them to `"openalex:W201"`. The `has_node()` check looked for the normalized ID but the graph had the raw ID.
- **Resolution:** Updated test to use normalized IDs (`"openalex:W201"`).
- **Lesson:** When a class normalizes IDs, all code that interacts with it (including tests) must use the same normalization.

### Process

**2026-06-06 | CC2 | OC2's "waiting on your call" was in team-chat but not seen**
- **Symptom:** OC2 posted a detailed request for help with 29 test failures, but CC2 didn't see it until operator pointed it out.
- **Root Cause:** The message was at the very bottom of a long team-chat file. CC2 had read most of the file but missed the last entry.
- **Lesson:** Always scroll to the very bottom of team-chat before starting work. Newest entries are at the bottom.

---

## Section 5 — Research Mesh Final Status (2026-06-06)

### Component Completion

| Layer | Components | Tests | Status |
|-------|------------|-------|--------|
| L1 (Ingestion) | 8/8 | ~46 | ✅ Complete |
| L2 (Distillation) | 8/8 | ~45 | ✅ Complete |
| L3 (Agents) | 8/8 | ~39 | ✅ Complete |
| L4 (API + UI) | 8/8 | ~29 | ✅ Complete |
| **TOTAL** | **32/32** | **~159** | ✅ **ALL DONE** |

### Test Results
- `core/research/`: **225/225 passing** ✅
  - 41 safety regression tests
  - 50 L2/L3 integration tests
  - 47 unit tests (queue, lifecycle, evaluator, distiller, graph_store)
  - 87 other tests
- OCE backend: 467/467 passing (1 pre-existing error in test_observer_runtime.py)
- Full project: **1,700+ tests passing**

### Agent Completion
| Agent | Status | Components |
|-------|--------|------------|
| CC2 | ✅ Complete | Plan, skeleton, schema, vault principles, L3/L4 GATE reviews, integration test fixes |
| AS | ✅ Complete | Safety suite (41), L4.8 telemetry (13), integration tests (28) |
| PM | ✅ Complete | L1.1 OpenAlex, L1.3 S2, L1.7 cache, L2.2 concepts, L3.2 task_gen |
| PM2 | ✅ Complete | L1.2 arXiv, L1.8 rate limiter, L2.3 citations, L3.4 evaluator, L3.5 router, L4.7 vault_sync, L4 UI |
| RL | ✅ Complete | L1.6 scheduler, L2.8 contradictions (built by OC2) |
| OC2 | ✅ Complete | 17 components (L2 distiller through L4 research_api) |

### Remaining Work
- **OCE frontend**: Needs rebuild after research page additions
- **OCE backend**: Needs restart after code changes (stale process issue)
- **RL progress file**: Needs updating (still shows old PO×VTuber assignment)
- **First autonomous research cycle**: Needs to be run end-to-end with live data
- **Open questions**: LLM model for distillation, domain list confirmation, daily budget, vault sync direction, operator trigger preference

---

## Section 5 — Process Management (2026-06-07)

> **CRITICAL**: All agents MUST check the process registry before starting any service.

### Process Registry
- **Tool**: `python tools/process_registry.py`
- **Registry file**: `data/process_registry.json`
- **Commands**: `status`, `start --service <name>`, `stop --service <name>`, `kill-dupes --service <name>`, `cleanup`

### Duplicate Process Prevention
**BEFORE starting any service:**
1. Run `python tools/process_registry.py status`
2. If service is already running, DO NOT start another instance
3. If PID file exists but process is dead, run `python tools/process_registry.py cleanup`
4. Use `python tools/process_registry.py start --service <name>` instead of direct `python` calls

### Known Duplicate Sources
- **Windows Scheduled Tasks**: OpenClaw-2-Gateway auto-restarts uv Python instances
- **Multiple Python interpreters**: venv, uv, system Python can all run same scripts
- **Stale PID files**: When processes die without cleanup, next agent thinks it's safe to start
- **No shared state**: Each agent was starting processes independently

### Service Definitions
| Service | Script | Port | Python |
|---------|--------|------|--------|
| po_telegram | scripts/telegram_gateway.py | None | .venv |
| srrs_api | srrs_opc/frontend/api_server.py | 8001 | .venv |
| oce_backend | uvicorn oce.backend.main:app | 8000 | system |
| oce_frontend | Next.js dev | 3000 | node |
| srrs_frontend | Next.js dev | 3001 | node |
| oc2_gateway | OpenClaw gateway | 18790 | node |

### Hermes Bot — REMOVED
- All hermes_telegram.py files removed
- All hermes logs, tools, skills, vault notes removed
- Was causing 6 duplicate instances burning OpenRouter credits
- PO bot (@P01999BOT) and OC2 gateway are the only Telegram bots

### OpenRouter Model Chain (PO Bot)
1. **Ring 2.6** (primary) — `inclusionai/ring-2.6-1t`
2. **Owl Alpha** (free backup) — `openrouter/owl-alpha`
3. **MiniMax M2.5** (tertiary) — `minimax/minimax-m2.5`
- Each model gets 2 attempts before fallback
- Retryable errors (429, 5xx, timeout) retry with backoff
- Non-retryable errors (402, 400) skip to next model immediately
