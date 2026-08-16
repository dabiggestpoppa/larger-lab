# MVE R0.5.1 — SCIENTIFIC-STUB CAUSAL REPAIR CONTRACT

> **Checkpoint:** MVE-R0.5.1-SCIENTIFIC-STUB-CAUSAL-REPAIR · 2026-08-15
> **Base:** `cb0020cee33a493abf358991effb1a7bf74d1c3f`
> **Rule:** `output known at t = f(info <= t)`. Repairs preserve the scientific
> concept and move knowledge/action time forward to the confirmation. No
> hindsight removed by weakening a hypothesis — confirmation logic is kept and
> its KNOWLEDGE TIME is made explicit.
>
> **Correction of prior record (R0.5 causality gate):** the previously reported
> "Model E references undefined variable n" blocker was a misreading of the
> `_calculate_occupancy(coords, step, n)` helper during the earlier partial
> read. Model E actually runs without a NameError. Its real defect is a
> full-sample scalar component (Q) that repaints historical signals — see
> Model E below. This supersedes, not erases, the earlier record.

## Component repair mapping

### 1. RKEY-B (rekey.py `_rekey_variant_b`)

| Field | Value |
|---|---|
| Current behavior | crossing detected at scan-origin i; scans future bars i+1..i+4 for retest evidence; writes `rekey_anchor = coord_i` and the anchor takes effect AT bar i |
| Why non-causal | anchor consumed at i uses evidence from i+1..i+4 — backdated/repainting (measured diff 1.033) |
| Intended scientific concept | "re-anchor only after breakout + successful retest" — the retest must confirm before the new origin is active |
| Authorized mechanical repair | anchor VALUE formula unchanged (`coord at scan-origin i`); **activation time moved from i to the retest bar j** — pending schedule, activated at j; bars i..j-1 keep the previous anchor |
| Forbidden scientific changes | retest horizon (4), retest definition (> boundary), threshold, boundary, anchor formula |
| Timing after repair | `rekey_event_time = i`, `rekey_evidence_complete_time = j`, `rekey_known_time = j`, `new_anchor_active_time = j` |
| Classification after | CAUSAL_DELAYED_CONFIRMATION (implementable) |

### 2. Signal Model A (`generate_sigma_escape_signals`)

| Field | Value |
|---|---|
| Current behavior | signal emitted at crossing bar i, but gated on bar i+1's close ("no immediate close back below boundary") |
| Why non-causal | signal at i uses bar i+1 |
| Intended scientific concept | LONG = +1σ crossing with no immediate close back below; SHORT = mirror (documented "SHORT = mirror") |
| Authorized mechanical repair | signal KNOWN TIME moved to i+1 (confirmation bar); long fires on +boundary crossing, short on −boundary crossing (docstring-specified mirror — the prior `elif` was dead code with an identical condition, so shorts could never fire) |
| Forbidden scientific changes | confirmation rule ("no immediate close back", `abs(next) <= boundary` invalidates), boundary, step |
| Timing after repair | `signal_event_time = i`, `signal_evidence_complete_time = i+1`, `signal_known_time = i+1`; execution per bar-timing conventions (after confirmation close / next-bar open) |
| Classification after | CAUSAL_DELAYED_CONFIRMATION (implementable) |

### 3. Signal Model B (`generate_accepted_sigma_breakout_signals`)

| Field | Value |
|---|---|
| Current behavior | emits 1 at every bar with `abs(coord) > boundary` and occupancy >= threshold; reads `next_coord = iloc[i+1]` but BOTH branches emit 1 (cosmetic read); last bar suppressed |
| Why non-causal | static next-bar pattern (`iloc[i+1]`) — behaviorally the output does not depend on bar i+1, but the pattern is a violation and the last-bar suppression is an off-by-one artifact |
| Intended scientific concept | accepted-breakout state (breach + occupancy acceptance) |
| Authorized mechanical repair | remove the cosmetic next-bar read and the last-bar suppression → realtime state signal known at bar i |
| Documented (not fabricated) | the "retest rejection / next close higher" ENTRY described in the docstring is NOT implemented in code (both branches identical) → `BLOCKED_LOGIC_SPEC` (retest-entry), excluded from execution |
| Timing after repair | `signal_event_time = signal_known_time = i` (realtime) |
| Classification after | CAUSAL_REALTIME (implementable); retest-entry semantic BLOCKED_LOGIC_SPEC |

### 4. Signal Model C (`generate_recursive_morphic_trend_signals`)

| Field | Value |
|---|---|
| Current behavior | entry at crossing bar i decided by bar i+1's coordinate (`abs(next_coord) > 2*boundary`) |
| Why non-causal | entry at i uses bar i+1 |
| Intended scientific concept | enter after +1σ acceptance confirmed by +2σ acceptance |
| Authorized mechanical repair | entry KNOWN TIME moved to i+1 (the +2σ confirmation bar); exit logic unchanged (trailing 3-bar window, already causal) |
| Forbidden scientific changes | boundary levels, +2σ confirmation rule, exit window |
| Timing after repair | `signal_event_time = i`, `signal_evidence_complete_time = i+1`, `signal_known_time = i+1` |
| Classification after | CAUSAL_DELAYED_CONFIRMATION (implementable) |

### 5. RKEY-C NaN robustness (`_rekey_variant_c`)

| Field | Value |
|---|---|
| Current behavior | conditional `int(NaN)` crash when current coordinate is beyond boundary and a required past coordinate is NaN (warm-up) |
| Why broken | crash, not a timing issue |
| Authorized mechanical repair | ready-guard: if required inputs contain NaN, emit NO rekey decision at that bar (keep prior anchor / identity); never coerce NaN, never invent default values |
| Tests required | first bar, partial warm-up, first fully valid window, intermittent NaN, valid post-warm-up |
| Classification after | CAUSAL_REALTIME (implementable) |

### 6. Signal Model D (audit-only)

| Field | Value |
|---|---|
| Current behavior | three candidate regimes with contradictory sign conditions (`d1>0 and ... d1<0` in condition 1; condition 3 opposite of its docstring); crashes on NaN (`int(NaN)`) |
| Why not repaired | the intended mapping of docstring's M_M/M_W/M_D to the two inputs (h1, d1) is ambiguous → SCIENTIFIC_INTENT_AMBIGUOUS |
| Authorized repair | NaN robustness guard ONLY (mechanical, no logic change); conditions untouched |
| Classification | BLOCKED_LOGIC_SPEC (contradictory conditions, ambiguous mapping) — excluded from future scientific execution |

### 7. Signal Model E (`generate_morphic_trend_score_signals`)

| Field | Value |
|---|---|
| Current behavior | computes TrendScore = wD·D + wV·V + wA·A + wP·P + wQ·Q; D/V/A causal (trailing), P constant placeholder, **Q = whole-sample scalar** (`(coords.diff().abs() > step).sum()/len`) broadcast into every bar |
| Why non-causal | Q is a full-sample statistic → perturbing future bars changes every historical score (repaint) |
| Authorized mechanical repair | NONE needed for NameError (prior claim corrected — no NameError exists) |
| Required | Q's per-bar causal formulation is scientifically ambiguous ("number of accepted same-direction sigma transitions") → `BLOCKED_LOGIC_SPEC` (Q), excluded from execution; placeholder subcomponents (V/P/Q "basic approximation") documented, not upgraded |
| Classification | BLOCKED_LOGIC_SPEC (Q whole-sample component) — runs, but excluded from future scientific execution |

## Global rules

- No P4/P5/P6/P7 science, no new signal models, no threshold/parameter changes,
  no holdout access.
- EX_POST_ONLY descriptive analyzers (forward-return labeling) are preserved
  unchanged (R0.5.1-N).
- All repaired causal components must show max historical future-mutation
  diff = 0 and pass truncation invariance on the same dev slice.
