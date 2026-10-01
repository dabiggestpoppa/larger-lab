# CSIA — BOOK 7 EVENT CANDIDATE MATRIX v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Binding predecessors:** Boundary Review v0.1; Event Grammar v0.1 (identity
> doctrine §3, lifecycle §5, temporal §6, family stress notes §8).
> **Scope:** every candidate event family, fully specified, with disposition.
> Dispositions: **KEEP** (family as planned) · **REVISE** (refold before
> implementation) · **DEFER** (parked with reason) · **REJECT** (with reason).
> Evidence-class vocabulary is Book 2's (E0–E4). Lifecycle/temporal vocab is
> Event Grammar §5–6. "Owning book" = the book whose canonical record the
> event's structural impact resolves through (Event Grammar §7) — never Book 7.

---

## 1. UPGRADE — **KEEP**

| Aspect | Plan |
|---|---|
| Definition | a system-initiated change to its own architecture/protocol (planned or executed software/parameter upgrade on subject's own stack) |
| Identity semantics | `(subject, upgrade_id/signature, stage)`; staged programs (proposal→activation) are one series with per-stage events; a hard-fork-like divergence re-resolves identity through D3-1 |
| Temporal fields | announced_at, scheduled_for, began_at, effective_at, completed_at |
| Owning structural book | Book 3 (architecture dossier change); Book 1 (deployment identity where applicable) |
| Required Book 2 evidence | stage-typed: announcement (E3/E4 ok for DECLARED); activation (E0/E1 required for CONFIRMED_OCCURRENCE) |
| Narrative links | narratives claim upgrade significance/competition; EventClaimLink rows |
| Action links | full ladder eligible: declared (announcement) → deployed (activation) → usage/capital responses (Book 6 refs) |
| Status model | lifecycle full subset incl. ONGOING, RESOLVED, REVERSED (rollback) |

## 2. INTEGRATION — **KEEP**

| Aspect | Plan |
|---|---|
| Definition | formation/change of a dependency or service relationship between distinct systems (subject adopts provider / venue / stack) |
| Identity semantics | `(subject, counterparty, relation_type, occurrence_signature)`; announcement and live-integration are distinct events (or stages); listing events do NOT belong here (see corpus #14) |
| Temporal fields | reported_at, announced_at, began_at (live), effective_at |
| Owning structural book | Book 4 (DependencyRecord); Book 2 for evidence |
| Required Book 2 evidence | E0/E1 for EDGE formation; E3/E4 only ever reaches CHANGE_CLAIMED |
| Narrative links | partnership/integration narratives; strong false-positive surface (corpus #4, #14) |
| Action links | declared → deployed (Book 4 record) → usage response (measured flow) eligible |
| Status model | full subset; CONFIRMED_OCCURRENCE gated on Book 4 record existence |

## 3. LAUNCH — **REVISE**

| Aspect | Plan |
|---|---|
| Definition | candidate covering new-object launches (new chain, new product, new token) |
| Why REVISE | "launch" conflates three mechanisms: new identity coming into existence (Book 1/3 event), a feature going live (= UPGRADE-class), and a market listing (venue event). One family would flatten unlike mechanisms |
| Refold plan | split: NEW_OBJECT_LAUNCH → identity-bearing event family (consumes Book 1 identity minting); FEATURE_LAUNCH → UPGRADE subfamily; LISTING → venue/market event family (dependency on Book 8/Sensor seams, DEFER market-facing semantics) |
| Identity/temporal/evidence | per refolded families; none unique |
| Owning structural book | Book 3 (+ Book 1 identity) for new-object; venue records for listings |
| Narrative/action links | launch narratives are heavy (hype cycles); ladder from DECLARED eligible |
| Status model | resolved per refolded family |

## 4. MIGRATION — **KEEP**

| Aspect | Plan |
|---|---|
| Definition | movement of state/assets/components between identities/venues/mechanisms with continuity questions (chain migration, bridge migration, contract migration) |
| Identity semantics | `(migrating_scope, origin_ref, destination_ref, stage)`; identity outcome resolved ONLY by Book 3 (D3-1/D3-2/D3-7); dual-running is a valid-time window, not a new object |
| Temporal fields | announced_at, scheduled_for, began_at, completed_at, resolved_at (dual-running window = [began, completed)) |
| Owning structural book | Book 3 (MIGRATED_FROM/TO lineage); Book 4 (affected relations) |
| Required Book 2 evidence | E0/E1 for migration occurrence; partial-migration evidence per stage |
| Narrative links | "the big migration" narratives; corpus #12/#19 false positives |
| Action links | declared → deployed → usage response on destination eligible |
| Status model | ONGOING (dual-running), RESOLVED, REVERSED (rollback) required |

## 5. EXPLOIT — **KEEP**

| Aspect | Plan |
|---|---|
| Definition | adversarial extraction/failure event (hack, drain, manipulation) against a system |
| Identity semantics | `(victim_scope, occurrence_signature [tx set / incident id], stage)`; one incident, many victims = one event + N impacts; rumor vs incident strictly separated |
| Temporal fields | reported_at, began_at, completed_at, resolved_at (recovery) |
| Owning structural book | Book 3/4 (affected components/dependencies); amounts via Book 2 evidence only |
| Required Book 2 evidence | highest bar: REPORT (E3/E4) ≠ CONFIRMED INCIDENT (E0/E1); loss amount needs its own evidence binding (corpus #11) |
| Narrative links | blame/attribution narratives preserved as narratives |
| Action links | rarely ladder-complete; declared action = incident response commitments (DECLARED only until evidenced) |
| Status model | REPORTED → CONFIRMED_OCCURRENCE → RESOLVED; CONTESTED for disputed attribution/amount |

## 6. OUTAGE — **KEEP**

| Aspect | Plan |
|---|---|
| Definition | availability failure of a live system (downtime, halt, degraded consensus) |
| Identity semantics | per-occurrence identity + EventSeries for recurrence (Event Grammar §3); `(subject, start_signature)` with series link |
| Temporal fields | began_at, completed_at, resolved_at; recurrence window |
| Owning structural book | Book 3 (system state), Book 4 (dependent-impact via records) |
| Required Book 2 evidence | E0/E1 (chain halt heights, status records E1); media REPORT insufficient |
| Narrative links | reliability narratives; "chain down" propagation records |
| Action links | usage response during/after outage measurable via Book 6 |
| Status model | ONGOING → RESOLVED; REVERSED N/A; series-aware |

## 7. GOVERNANCE — **KEEP**

| Aspect | Plan |
|---|---|
| Definition | staged self-governance occurrences: proposal, vote, approval, execution, activation, rollback |
| Identity semantics | `(subject, proposal_id, stage)`; one program, per-stage events (Event Grammar §3/§8.2); rejected proposals are RESOLVED occurrences, not non-events |
| Temporal fields | announced_at, scheduled_for (vote), began_at (vote open), completed_at (vote close), effective_at (activation) |
| Owning structural book | Book 3/4 for executed change; proposal/vote records are Book 2-evidence-backed Book 7 occurrences |
| Required Book 2 evidence | per stage: proposal record (E1/E2), tally (E1/E2), execution tx (E0) |
| Narrative links | governance-season narratives; corpus #2/#3 |
| Action links | the canonical staged ladder: declared (proposal) → deployed (execution) → usage response |
| Status model | per-stage lifecycle; passed-but-unexecuted gap recorded honestly |

## 8. REGULATORY_EVENT — **KEEP**

| Aspect | Plan |
|---|---|
| Definition | legal/regulatory occurrence concerning a subject: proposal, guidance, rule, law, court decision, enforcement action |
| Identity semantics | `(instrument_id, jurisdiction, stage)`; jurisdiction is an identity component (Event Grammar §8.3); same text, two jurisdictions = two events |
| Temporal fields | announced_at, scheduled_for, effective_at (may lag years), resolved_at (appeals) |
| Owning structural book | Book 7 occurrence + Book 2 evidence; effects on subjects resolve through owning books (e.g., delisting → venue records) |
| Required Book 2 evidence | stage-typed primary documents (E1/E2); commentary (E3) never advances stage |
| Narrative links | "regulation FUD/positive" narratives; corpus #17 |
| Action links | declared action = compliance commitments; structural effect only via owning books |
| Status model | stage-typed status; PROPOSED≠EFFECTIVE law; cross-jurisdiction generalization prohibited |

## 9. INSTITUTIONAL_ADOPTION — **REVISE**

| Aspect | Plan |
|---|---|
| Definition | candidate: institutions adopting/piloting/allocating to a subject |
| Why REVISE | as a family it invites announcement→adoption collapse (corpus #13). The *occurrence* classes inside it are already covered: announcement/pilot = DECLARED ACTION; custody/integration = INTEGRATION; production usage = rung-4 measurement; capital allocation = CAPITAL RESPONSE |
| Refold plan | keep as a *tag/cross-cutting attribute* on events and ladder rungs (actor_class = INSTITUTIONAL), not a standalone occurrence family; adoption confirmation requires explicit recorded criteria (candidate operator decision, see §D7N note in plan) |
| Identity/temporal/evidence | inherited from refolded hosts |
| Owning structural book | per host |
| Narrative links | "institutional adoption" narratives — the classic E4 volume trap |
| Action links | full ladder eligible with actor_class tag |
| Status model | per host; ADOPTION status never emitted without criteria-gated evidence |

## 10. TOKENOMICS_CHANGE — **KEEP**

| Aspect | Plan |
|---|---|
| Definition | executed or scheduled economic-parameter/supply events: issuance change, burn, staking parameter, unlock, treasury action |
| Identity semantics | `(subject, parameter/program, stage)`; proposal ≠ scheduled ≠ executed (Event Grammar §8.5) |
| Temporal fields | announced_at, scheduled_for, effective_at (unlock schedules), completed_at |
| Owning structural book | Book 5 (economic records), Book 6 (measured supply/consequences) |
| Required Book 2 evidence | E0 for executed parameter changes; schedule records (E1/E2) for scheduled; proposals stay DECLARED |
| Narrative links | supply-shock narratives; corpus #18 |
| Action links | declared → deployed (executed change) → capital response eligible |
| Status model | staged; measured consequences always by reference |

## 11. BRIDGE_CHANGE — **REVISE**

| Aspect | Plan |
|---|---|
| Definition | candidate: changes to bridge objects (new bridge, deprecation, route change, bridge exploit) |
| Why REVISE | a bridge is an object *class*, not a mechanism: bridge deployment = INTEGRATION/NEW_OBJECT; bridge deprecation = MIGRATION/DEPENDENCY_LOST; bridge exploit = EXPLOIT (victim_scope=bridge). One family would triple-count |
| Refold plan | treat BRIDGE as a subject-class attribute across families; no standalone family |
| Identity/temporal/evidence | per refolded host family |
| Owning structural book | Book 4 (bridge dependencies), Book 3 (bridge objects) |
| Narrative links | bridge-risk narratives (heavy after exploits) |
| Action links | per host |
| Status model | per host |

## 12. STABLECOIN_CHANGE — **REVISE**

| Aspect | Plan |
|---|---|
| Definition | candidate: stablecoin issuance/redemption/depeg/collateral events |
| Why REVISE | mixes three mechanisms: economic-parameter events (= TOKENOMICS_CHANGE subfamily: issuance/burn/backing changes), realization/capital-topology events (Book 5 REALIZES/issuance venue changes = capital-realization class), and market events (depeg = price fact → Sensor/Book 8 seam, not Book 7 semantics) |
| Refold plan | STABLECOIN as subject-class attribute; economic-parameter occurrences → TOKENOMICS_CHANGE; realization occurrences → capital-realization subfamily (Book 5 references); depeg observation stays out of Book 7 (market mechanics) |
| Identity/temporal/evidence | per refolded hosts |
| Owning structural book | Book 5 (capital topology/realization) |
| Narrative links | depeg/flight-safety narratives (recorded as narratives only) |
| Action links | per host |
| Status model | per host; no market-state semantics in Book 7 |

---

## 13. Disposition summary

```text
KEEP    (7): UPGRADE, INTEGRATION, MIGRATION, EXPLOIT, OUTAGE, GOVERNANCE,
             REGULATORY_EVENT, TOKENOMICS_CHANGE   (8 families; TOKENOMICS listed KEEP)
REVISE  (4): LAUNCH, INSTITUTIONAL_ADOPTION, BRIDGE_CHANGE, STABLECOIN_CHANGE
DEFER   (0)
REJECT  (0)
CROSS-CUTTING ATTRIBUTES INTRODUCED: subject_class (BRIDGE, STABLECOIN),
             actor_class (INSTITUTIONAL), venue_event class (LISTING -> deferred
             to venue/market seam; no Book 7 market semantics)
OPEN:     adoption-criteria gate (in INSTITUTIONAL_ADOPTION refold) rides with D7N packet
NOTE:     dispositions are planning recommendations; family vocabulary binds only
          via operator ratification of the Book 7 plan and later implementation
          authorization.
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
