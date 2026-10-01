# CSIA — BOOK 7 NARRATIVE / ACTION FALSE-POSITIVE CORPUS v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Binding predecessors:** Boundary Review v0.1; Event Grammar v0.1; Narrative
> Model v0.1; Action Ladder v0.1.
> **Scope:** 20 stress cases that a naive narrative-to-action implementation
> fails. Each row: the naive interpretation, why it fails, correct Book
> ownership, required evidence, and the exact boundary between what Book 7 may
> and may not conclude. This corpus becomes the exit-evidence core for Bloc 7C
> (and seeds Bloc 7A/7B adversarial families).

**Row key:** NAIVE = what a careless system concludes · FAIL = the failure mode
· OWN = owning authority · EVID = required evidence · ALLOWED = Book 7's
permitted conclusion · PROHIBITED = Book 7's forbidden conclusion.

---

### Case 1 — Announcement never deployed
- **NAIVE:** announcement → integration exists.
- **FAIL:** E4 speech promoted to a Book 4 structural fact (§20.1; D2-6).
- **OWN:** Book 4 (edge) + Book 2 (evidence).
- **EVID:** Book 4 DependencyRecord with E0/E1 backing.
- **ALLOWED:** "integration announced on date T; ladder stops between DECLARED and DEPLOYED; `CHANGE_CLAIMED`."
- **PROHIBITED:** integration edge, DEPLOYED rung, "integration live."

### Case 2 — Governance proposal rejected
- **NAIVE:** "proposal to do X" → X-related change recorded.
- **FAIL:** proposal existence read as change occurrence; rejected proposals are outcomes too.
- **OWN:** governance records (Book 2 evidence) + Book 3/4 (change).
- **EVID:** vote tally record with outcome REJECTED.
- **ALLOWED:** "proposal P rejected at T; no change; narrative may persist."
- **PROHIBITED:** any change row; treating the proposal as pending-forever.

### Case 3 — Vote passed but execution delayed
- **NAIVE:** passed vote → executed change.
- **FAIL:** stage collapse (proposal≠vote≠execution≠activation; Event Grammar §8.2).
- **OWN:** governance stage records; change owned by Books 3/4.
- **EVID:** execution tx + activation evidence for DEPLOYED; delay is a recorded stage gap.
- **ALLOWED:** "vote passed T1; execution not yet observed (`TOO_EARLY_TO_ASSESS` / stage gap recorded)."
- **PROHIBITED:** executing the change narratively; backdating execution to the vote.

### Case 4 — Integration announced, no on-chain evidence
- **NAIVE:** multiple credible outlets → integration real.
- **FAIL:** report count ≠ occurrence truth (AB-3); E3/E4 cannot mint E0.
- **OWN:** Book 4 + Book 2.
- **EVID:** E0 on-chain deployment/usage evidence or owning-book record.
- **ALLOWED:** `CHANGE_CLAIMED` + propagation record; contradiction row if Book 4 shows nothing.
- **PROHIBITED:** EDGE_ADDED in any diff; integration event beyond REPORTED/DECLARED.

### Case 5 — Feature deployed but unused
- **NAIVE:** deployment → adoption narrative confirmed.
- **FAIL:** rung-3 does not imply rung-4 (ANNOUNCED≠DEPLOYED≠USED full length).
- **OWN:** Book 6 (usage measurement).
- **EVID:** Book 6 MeasurementObservation showing the usage axis (or its absence via proper missingness).
- **ALLOWED:** "deployed at T; usage response `NO_RESPONSE_OBSERVED`/`RESPONSE_NOT_MEASURED` per measurement state."
- **PROHIBITED:** "adoption confirmed"; usage health language; treating unmeasured as zero.

### Case 6 — Usage spike from incentives
- **NAIVE:** usage up after action → action succeeded.
- **FAIL:** attribution leap; incentive-driven usage is still usage, but its cause is not established by sequence (Causality §1).
- **OWN:** Book 6 (measurement); incentive mechanism owned by Books 3/5 records.
- **EVID:** measurement refs + mechanism evidence (at most Level 3).
- **ALLOWED:** "usage increased after T (Level 1); incentive program live (record)."
- **PROHIBITED:** "the action drove adoption"; success/adoption-quality language.

### Case 7 — Usage rises before announcement
- **NAIVE:** usage rose, then announcement → announcement "worked."
- **FAIL:** temporal order violated even for the naive reading; pre-trends break adjacency causality (Causality §3).
- **OWN:** Book 6 (measurement timeline).
- **EVID:** measurement valid times vs announcement time.
- **ALLOWED:** "usage increase preceded the announcement (recorded pre-trend)."
- **PROHIBITED:** any causal link from action to pre-existing trend.

### Case 8 — Capital inflow without narrative
- **NAIVE:** no narrative found → inflow unexplained/anomalous.
- **FAIL:** absence of observed narrative is not absence of cause; narratives CSIA has not observed are UNKNOWN, not nonexistent (Axiom 6).
- **OWN:** Book 5/6 (capital records); Book 7 propagation records.
- **EVID:** Book 5/6 measurement refs; propagation search status.
- **ALLOWED:** "capital response observed; no narrative propagation observed (`RESPONSE` without narrative linkage)."
- **PROHIBITED:** inventing a narrative; treating unlinked response as invalid.

### Case 9 — Narrative persists after project abandonment
- **NAIVE:** circulating narrative → project active.
- **FAIL:** narrative existence ≠ subject viability; E4 outranked by structural evidence.
- **OWN:** Books 3/4/5 (structural state); Book 7 (propagation).
- **EVID:** owning-book records showing abandonment; propagation epochs.
- **ALLOWED:** "narrative N still propagating (epoch E3); subject state per owning books (inactive)."
- **PROHIBITED:** hiding the contradiction; letting circulation imply activity.

### Case 10 — Exploit rumor disproved
- **NAIVE:** initial reports → exploit event confirmed.
- **FAIL:** REPORT ≠ CONFIRMED INCIDENT (Event Grammar §8.1); disproof must supersede, not be averaged.
- **OWN:** Book 2 (contradiction/promotion) + security evidence bar.
- **EVID:** E0/E1 disproof (no anomalous flows; project attestation class).
- **ALLOWED:** "exploit reported at T1; occurrence not confirmed; later evidence contradicts (lifecycle RESOLVED as non-occurrence / CONTESTED→resolved-by-reference)."
- **PROHIBITED:** retaining CONFIRMED_OCCURRENCE; deleting the rumor row (history preserved).

### Case 11 — Exploit confirmed but loss estimate wrong
- **NAIVE:** media loss figure → confirmed impact.
- **FAIL:** LOSS CLAIM ≠ confirmed impact; estimates are source-classed and revisable.
- **OWN:** Book 2 + on-chain analysis (E0 where possible).
- **EVID:** occurrence confirmation (separate) + amount evidence (separate binding).
- **ALLOWED:** "incident confirmed; loss claims recorded per source (claim_A: X, claim_B: Y, un-averaged); confirmed amount per E0 evidence if/when available."
- **PROHIBITED:** single canonical media-sourced loss figure; collapsing estimates by majority.

### Case 12 — Bridge migration partially completed
- **NAIVE:** migration announced/started → migration event RESOLVED.
- **FAIL:** partial migration and dual-running are first-class states (Evolution §3).
- **OWN:** Book 3 (identity/continuity) + Book 4 (affected relations).
- **EVID:** per-asset/per-component migration records; valid-time spans.
- **ALLOWED:** "migration ONGOING; dual-running window [T1,T2); portion complete per owning records."
- **PROHIBITED:** wholesale RESOLVED; new-object minting by migration itself.

### Case 13 — Institutional pilot described as adoption
- **NAIVE:** "bank pilots protocol" → INSTITUTIONAL_ADOPTION event.
- **FAIL:** pilot ≠ production adoption (Event Grammar §8.4); adoption needs explicit criteria.
- **OWN:** Book 2 evidence classing + family evidence bar.
- **EVID:** pilot record (DECLARED) vs production-usage evidence (rung 4).
- **ALLOWED:** "pilot declared (declared action); adoption status `CHANGE_CLAIMED`/not established."
- **PROHIBITED:** INSTITUTIONAL_ADOPTION confirmation from announcement.

### Case 14 — Listing mistaken for protocol integration
- **NAIVE:** exchange lists token → protocol integrated with exchange.
- **FAIL:** family confusion: listing is a venue/market event, not an INTEGRATION (mechanism classes, not news sections).
- **OWN:** venue records; Book 4 only if a real dependency forms.
- **EVID:** listing record; separate dependency evidence if claimed.
- **ALLOWED:** "asset listed on venue V (event family per matrix); no dependency change claimed."
- **PROHIBITED:** EDGE_ADDED; "protocol integrated with V."

### Case 15 — Social narrative copied by aggregators
- **NAIVE:** 50 aggregator echoes → narrative strongly validated.
- **FAIL:** propagation ≠ truth; echoes are one origin + relay fan-out (Event identity: REPORT_COUNT != EVENT_COUNT; propagation AB-3).
- **OWN:** Book 7 (propagation records); truth stays with owning books.
- **EVID:** origin/earliest observation; venue-class propagation; content identity.
- **ALLOWED:** "narrative N propagated widely (descriptive); truth status unchanged (per owning books)."
- **PROHIBITED:** propagation count as epistemic weight; narrative "confidence" score.

### Case 16 — Same event reported by 50 outlets
- **NAIVE:** 50 events / heavy event-day.
- **FAIL:** report fan-out duplicates identity (Event Grammar §3).
- **OWN:** Book 7 identity resolution; Book 2 for occurrence truth.
- **EVID:** occurrence signature match across reports; one EventIdentity, N report rows.
- **ALLOWED:** "one occurrence, 50 reports (propagation/duplication resolved by identity key)."
- **PROHIBITED:** event count inflation; report volume feeding any state input (AB-3).

### Case 17 — Regulatory proposal mistaken for law
- **NAIVE:** "regulator proposes rules" → regulation effective.
- **FAIL:** staged legal status (proposal≠guidance≠rule≠law≠enforcement) + jurisdiction + effective date.
- **OWN:** regulatory records (Book 7 family) + Book 2 evidence.
- **EVID:** stage-typed document + jurisdiction + effective_at.
- **ALLOWED:** "proposal in jurisdiction J stage=PROPOSED effective_at=UNKNOWN."
- **PROHIBITED:** "regulation now in force"; cross-jurisdiction generalization.

### Case 18 — Tokenomics proposal mistaken for executed supply change
- **NAIVE:** "protocol to burn 40% of supply" → supply changed.
- **FAIL:** proposal ≠ executed parameter change (Event Grammar §8.5).
- **OWN:** Book 5/6 (economic records/measurements).
- **EVID:** execution evidence + Book 5 parameter record + Book 6 measured supply.
- **ALLOWED:** "burn proposed (DECLARED); executed status per owning records; measured supply unchanged per Book 6 (or as measured)."
- **PROHIBITED:** projecting the proposed change into any economic state.

### Case 19 — Migration creates temporary dual-running topology
- **NAIVE:** dual-running read as ecosystem "growth" (two objects!).
- **FAIL:** continuity window misread as new object and as expansion (Evolution §3, §5).
- **OWN:** Book 3 (identity) + Book 4 (records on both endpoints).
- **EVID:** Book 3 lineage + valid-time windows.
- **ALLOWED:** "dual-running [T1,T2); MIGRATED rows; no object-count growth claim."
- **PROHIBITED:** NODE_ADDED for the destination; expansion state from migration window.

### Case 20 — Market response exists before structural action
- **NAIVE:** price moved before event → market "anticipated" it → predictive story.
- **FAIL:** pre-event market movement is a Sensor-domain observation with no Book 7 semantics; anticipating narratives are narratives (E4), not structure.
- **OWN:** Sensor/Book 8 (market observation; D8 untouched); Book 7 records the narrative only.
- **EVID:** none consumable by Book 7 beyond the narrative/utterance records.
- **ALLOWED:** "narrative N claims market anticipation (recorded); MARKET_RESPONSE_REF remains unbound (Book 8 seam)."
- **PROHIBITED:** market-response rung binding; confirmation-state construction; any predictive/anticipation semantics.

---

## Corpus verdict

```text
CASES                  = 20 (all bound to AB-1..AB-3, D2-6, §20.1, §25, D6M-5)
RECURRING_FAILURE_MODES = stage-collapse, count-to-truth, valence-attachment,
                          identity-duplication, seam-violation
STATUS                 = PLANNING-RESOLVED (exit evidence for B7A/B7B/B7C)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
