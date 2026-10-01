# CSIA — BOOK 7 ACTION LADDER AND CAUSALITY v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Binding predecessors:** Boundary Review v0.1; Event Grammar v0.1; Narrative
> Model v0.1; Narrative State Governance v0.1.
> **Scope:** Bloc 7C planning — ladder transitions, each rung's authority and
> evidence bar, causality doctrine, link contract, response-absence semantics,
> lag/window governance. Constitution §21 (the ladder) and §25 (causality) are
> the governing doctrine.

---

## 1. The canonical ladder and its transitions (Phases 15–17)

```text
CLAIM → DECLARED ACTION → DEPLOYED ACTION → USAGE RESPONSE → CAPITAL RESPONSE → MARKET RESPONSE
```

**Constitutional reading:** each arrow is a *linked observation* — the
existence of a resolvable record on the next rung, linked by recorded relation
and timeline — never a guaranteed or implied causation, and never a completion
implication. A CLAIM does not cause DEPLOYMENT by definition; it merely
precedes it in the one recorded instance the link row describes. A ladder may
stop at any rung; a stopped ladder is a complete observation of what exists,
not a failure (§4 below).

### 1.1 DECLARED ACTION (rung 2 — Phase 16)

A declaration of intent by a responsible actor:

```text
roadmap commitment · governance proposal · company announcement
protocol announcement · foundation commitment
```

Planned record `DeclaredAction`: actor_ref, declaration content (verbatim,
preserved), declaration channel/source class, declared scope, declared timing,
family-typed evidence requirements (a governance proposal cites the proposal
record; a roadmap commitment cites the utterance), valid/observed time,
supersession.

Invariants: `DECLARED != EXECUTED` (D2-6 full length); required evidence
differs by action family and is recorded per family in the candidate matrix;
a declaration is an event-lifecycle input (`DECLARED` state) and a ladder rung
— never evidence of the thing declared.

### 1.2 DEPLOYED ACTION (rung 3 — Phase 17)

A deployment/execution must resolve to **Book 2-backed structural truth**
through the owning book:

```text
contract deployed → Book 2 E0 deployment evidence + Book 3/1 deployment identity
feature activated → Book 3 architecture record + E0/E1
integration live  → Book 4 DependencyRecord + Book 2 authority
migration completed → Book 3 MIGRATED_FROM/TO lineage + continuity evidence
governance executed → execution tx (E0) + Book 3/4 record of the change
```

**Never inferring DEPLOYED from:** announcement, press release, roadmap, social
post — E4/E3 alone cannot promote the rung (§20.1; D2-5 doc-vs-chain downgrade
spirit). A rung-3 row that lacks owning-book resolution stays at
`CHANGE_CLAIMED` in the Event → structural seam (Event Grammar §7) and the
ladder honestly stops between rungs 2 and 3.

### 1.3 USAGE RESPONSE (rung 4 — Phase 18)

Book 7 consumes Book 6; D2-6 is not reopened:

```text
USAGE RESPONSE OBSERVED = a Book 6 MeasurementObservation ref whose valid time
follows the action's effective time, linked by recorded relation
```

Planned semantics: the rung records *that measured change followed* — direction
and magnitude live in the Book 6 records Book 7 cites. Book 7 may NOT say
healthy / successful / strong adoption; may not select or invent thresholds;
may not override missingness (Axiom 6); may not reinterpret a
`NOT_SUPPORTED`/missing measurement as zero or as absence-of-usage
(D6M-5 = OPEN_DEFERRED; `USAGE RESPONSE OBSERVED != USAGE HEALTH`).

### 1.4 CAPITAL RESPONSE (rung 5 — Phase 19)

Same pattern, consuming Books 5 and 6:

```text
capital inflow · liquidity change · staking change · credit usage
stablecoin supply change
```

Book 7 may link measured responses to the action timeline (timeline linkage is
Book 7's own product); it may not rewrite Book 5 principal topology, re-derive
capital facts, or total across Book 5 records (BOOK5 read-only, AB-1).

### 1.5 MARKET RESPONSE (rung 6 — Phase 20, the boundary hazard)

During Book 7, rung 6 is a **reference-only seam**:

```text
MARKET_RESPONSE_REF — a forward pointer reserved for the Book 8 Context Bridge
```

Book 7 may represent the placeholder and record that a ladder awaits market
confirmation; it may NOT define market-regime semantics, combine CSIA+Sensor
into confirmation states, finalize lag windows, or perform any D8 action.
Sensor market observations are not consumed, interpreted, or joined by Book 7.
Ownership: Sensor retains mechanical market observation; Book 8 owns the
formal bridge (`D8` gate: before Book 8 planning). Candidate decision `D7N-5`
records the ref-only ceiling as the intended permanent Book 7 boundary.

## 2. Causality doctrine (Phase 21)

Create at implementation time — and bind in planning — the required
separation:

```text
TEMPORAL ORDER != ASSOCIATION != MECHANISTIC LINK != CAUSAL CLAIM
```

Book 7 may say: "usage increased after event E" (temporal order + observed
rung). Book 7 may NOT say: "event E caused usage to increase." Causal language
("caused", "drove", "led to") requires an explicit, operator-ratified
event-study methodology (Constitution §23.1 + §25) — no causal inference by
timeline adjacency alone, ever. Full doctrine delivered in the companion
`CSIA_BOOK_7_CAUSALITY_DOCTRINE_v0.1.md`.

## 3. Action link contract (Phase 22 — stressed, not blindly adopted)

Planned record `NarrativeActionLink` (fields evaluated; several made mandatory/
optional after stress):

```text
narrative_ref            optional (ladders may exist without a narrative)
claim_ref                the originating Book 2 claim (optional — a ladder may
                         start at a declared action with no circulating claim)
declared_action_ref      optional (ladder may start at rung 3 for retroactively
                         observed deployments)
deployed_action_ref      optional (ladder may legally stop before deployment)
usage_response_refs[]    zero or more Book 6 measurement refs
capital_response_refs[]  zero or more Book 5/6 refs
market_response_ref      REF-ONLY (Book 8 seam; no semantics)
link_type                typed relation (e.g., ANNOUNCED_THEN_DEPLOYED,
                         DEPLOYED_THEN_USED) — describes observed sequence,
                         never causation
methodology_ref          required — the linkage rule identity (which
                         sequence/timing rules produced this link)
valid_time / observed_at bitemporal per Constitution §12.2
evidence_refs[]          required — Book 2 evidence for each asserted rung
causal_status            closed vocabulary: NONE | TEMPORAL_PRECEDENCE_ONLY |
                         ASSOCIATION_ONLY | MECHANISM_ASSERTED_BY_SOURCES |
                         CAUSAL_PER_RATIFIED_METHODOLOGY
                         (last value unreachable until D7N-4 closes with a
                         ratified methodology)
```

Stress results folded in: **ladders stop at any stage legitimately**; missing
later rungs are recorded with the §4 absence vocabulary — never as negative
responses; every rung assertion independently evidence-bound (a corrupt rung-3
row never upgrades rung 2).

## 4. Response absence semantics (Phase 23)

Six distinct states — absence is never failure, never zero:

```text
NO_RESPONSE_OBSERVED        window elapsed, measurement exists, no change recorded
RESPONSE_NOT_MEASURED       no measurement methodology covers the response axis
RESPONSE_DATA_UNAVAILABLE   methodology exists, data missing (Axiom 6 distinctions preserved)
TOO_EARLY_TO_ASSESS         within the declared assessment window (window ref cited)
NOT_APPLICABLE              response axis meaningless for this action family
UNKNOWN                     cannot be established — preserved
```

Rule: none of these converts to a negative/failed/absent response narrative;
none feeds any score or ranking; `TOO_EARLY_TO_ASSESS` resolves only by a
recorded re-assessment, never by silence aging into an answer.

## 5. Lag / window governance (Phase 24)

**No universal windows.** The candidate numerals (24h/7d/30d/90d) are rejected
as universal event-response windows. Lag is a function of event family, system
type, measurement type, chain/protocol cadence, and capital mechanism.

Planned doctrine: a `ResponseWindowMethodology` (versioned, operator-ratified
at implementation-authorization time) with family-typed default *ranges* and
explicit inputs — e.g., usage-response windows keyed to measurement cadence
(Book 6 window classes), capital-response windows keyed to Book 5 record
cadence, governance windows keyed to execution stages. Every window instance
cites its methodology ref. Book 8 may later own market-specific lag alignment
(explicitly out of Book 7 scope). No numeric default is chosen in planning —
choosing one would be an unauthorized empirical parameter.

## 6. Verdict

```text
ACTION_LADDER           = PLANNED (6 rungs; per-rung authority and evidence bars)
DECLARED_ACTION         = PLANNED (DECLARED != EXECUTED preserved)
DEPLOYED_ACTION         = PLANNED (Book 2-backed structural truth required; no E4 inference)
USAGE_RESPONSE          = PLANNED (Book 6 consumed; D2-6/D6M-5 untouched)
CAPITAL_RESPONSE        = PLANNED (Book 5 read-only)
MARKET_RESPONSE         = REF-ONLY SEAM (Book 8/D8 untouched)
CAUSALITY               = DOCTRINE BOUND (companion doc; D7N-4 open)
ACTION_LINK_CONTRACT    = PLANNED (stressed; causal_status vocabulary closed)
RESPONSE_ABSENCE        = PLANNED (6 states; absence != failure)
LAG_WINDOWS             = GOVERNANCE PLANNED (no universal numerals; methodology ref required)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
