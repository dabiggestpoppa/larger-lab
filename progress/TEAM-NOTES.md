# Team Notes — Persistent Errors, Observations, and Troubleshooting

> **Purpose:** Shared knowledge base for errors that persist or caused trouble during building. All agents contribute here.
> **Format:** Date | Agent | Issue | Root Cause | Resolution
> **Current mission:** O2C × MAD LABS Sovereign Research Mesh (L1→L4). Plan: `docs/plans/O2C-RESEARCH-MESH.md`.

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
