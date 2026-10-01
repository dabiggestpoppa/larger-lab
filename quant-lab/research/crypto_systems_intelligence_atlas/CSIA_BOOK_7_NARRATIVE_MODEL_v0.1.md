# CSIA — BOOK 7 NARRATIVE MODEL v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Binding predecessors:** Boundary Review v0.1 (AB-1..AB-3); Event Grammar v0.1.
> **Scope:** Bloc 7B planning — narrative identity, origin/propagation,
> evidence firewall mechanics, contradiction handling. Constitution §20 is the
> governing doctrine; this document operationalizes it.

---

## 1. Narrative grammar (Phase 9 — seven terms, non-collapsible)

```text
NARRATIVE          a circulating story connecting claims, events, and objects
NARRATIVE CLAIM    a factual assertion carried by the narrative (a Book 2-class
                   claim routed through Book 2; e.g., "X is live")
MESSAGE            a specific phrasing/variant of the narrative emitted by a source
SOURCE UTTERANCE   the concrete observed artifact (post, article, speech) — the
                   E4-class evidence unit; the only thing directly observed
THEME              a broad topic area many narratives share (e.g., "RWA")
THESIS             a narrative with an explicit position/prediction attached
EVENT              a world occurrence — never a narrative, though narratives
                   reference events (Event Grammar v0.1 §1)
```

The observed primitive is the SOURCE UTTERANCE. Messages are phrasings grouped
into narratives; narratives may carry many claims; themes group narratives.
Nothing here creates a second epistemic engine: narrative claims of fact are
Book 2 claims; narrative existence is a Book 7 record.

### 1.1 Narrative identity doctrine (the hard problem)

Narrative identity answers: when are two phrasings the same narrative?

Planned doctrine (candidate operator decision `D7N-2` — methodology selection
is the operator's, not planning's):

- **Planned identity key:** `(narrative_core, subject_scope, temporal_lineage)`
  where `narrative_core` is the canonicalized claim-structure of the story
  (who does what to which object, with what asserted outcome) — deliberately
  *not* keyword identity (phrasing varies; core may persist across wording).
- **SAME NARRATIVE:** same core + same subject scope, propagated or paraphrased.
  "Protocol X is becoming the RWA chain" in two languages = one narrative.
- **MERELY RELATED:** shared theme or shared referenced objects, different
  core. "RWA adoption is accelerating" vs "Protocol X is the RWA winner" are
  related narratives (THEME link), not one.
- **SPLIT:** one narrative develops divergent cores (e.g., the story forks into
  competing versions). Planned semantics: new narrative identity for the
  divergent core, with `SPLIT_FROM` lineage to the parent; the parent persists.
- **MERGE:** two lineages converge on one core (planned `MERGED_INTO`; the
  merged narrative carries both lineages; nothing is deleted).
- **CONTRADICTION:** not an identity event — a relation (§4 below). A
  contradicted narrative is not automatically a new narrative.
- **REAPPEARANCE:** an old core re-circulating later = same narrative identity,
  new propagation epoch (planned `propagation_epoch` on the origin/propagation
  record; reactivation is descriptive, never "confirmed").

All identity operations (split/merge/relapse) are **recorded, versioned,
evidence-linked decisions** — derivation rules may later automate detection,
but no rule is ratified in planning (§ Narrative-State Governance).

## 2. Origin and propagation (Phase 10 — descriptive only)

Planned record: `NarrativePropagation` (per narrative identity):

```text
origin_source_ref            earliest-resolvable source (may be UNKNOWN —
                             origin is often unobservable; UNKNOWN is honest)
earliest_observed_at         first utterance CSIA observed (transaction time)
propagating_source_refs[]    who circulated it (typed: media, aggregator,
                             institutional account, first-party account,
                             community)
amplification_events         descriptive circulation milestones (reached venue
                             class Y at time T) — counts with explicit
                             methodology, never a quality score
cross_community_links        propagation across distinct venue/community classes
institutional_propagation    propagation by institutional-class sources
first_party_adoption         the referenced project/actor itself adopting the
                             third-party narrative — recorded as a distinct
                             propagation relation, never silently merged with
                             third-party circulation
propagation_epoch[]          distinct circulation periods (supports reappearance)
```

**Prohibited outputs (until separately authorized):** influence score, truth
score, investment score, virality-quality score, any conversion of propagation
volume into importance. Propagation is descriptive circulation history (AB-3).

## 3. Narrative evidence firewall (Phase 11 — mechanical plan)

E4 evidence may establish exactly:

```text
"Narrative N exists"
"Source S emitted message M (said claim C)"
"Claim C is circulating (with propagation attributes)"
```

E4 may never establish:

```text
deployment / integration truth        → Book 4 + Book 2 (E0-E2)
usage truth                           → Book 6 measurement
capital response                      → Book 5 + Book 6
security-event fact                   → security evidence bar (Event Grammar §8.1)
market response                       → Sensor/Book 8 (D8 seam, untouched)
any structural truth                  → the owning book + Book 2 authority
```

Mechanical plan (implementation-time, testable):

- **FW-1:** narrative records may hold structural references only — no field of
  a narrative object can carry a claim state, and no function in the Book 7
  namespace can write one (type-level AB-2 mirror of the Book 6 anti-score
  firewall approach).
- **FW-2:** `NARRATIVE_EXTRINSIC_STATE` (circulation-derived, e.g., EXPANDING)
  and `STRUCTURAL_CLAIM_STATE` are distinct types with no conversion path;
  §20.1's rule is enforced in the type system, not by convention.
- **FW-3:** `NARRATIVE EXISTENCE != NARRATIVE CLAIM TRUTH` — a narrative's
  existence record and the truth-status of any claim it carries are stored in
  separate objects with separate lifecycles; a narrative object citing a claim
  does not inherit or display a truth value derived from circulation.
- **FW-4:** propagation counts are propagation attributes; no aggregation over
  them may appear in any state input without a separately ratified derivation
  rule (AB-3 mechanical mirror).

## 4. Contradiction handling (Phase 12)

Planned record: `NarrativeContradiction` (typed, both lines preserved —
nothing averaged, Book 2 D2-3 contradiction doctrine respected):

```text
NARRATIVE_VS_STRUCTURAL_EVIDENCE   narrative asserts change; owning book's
                                   records contradict it
NARRATIVE_VS_DEPLOYMENT            narrative says deployed; Book 2/4 says not
NARRATIVE_VS_USAGE                 narrative says adopted; Book 6 shows
                                   measurement absence/contradiction
NARRATIVE_VS_CAPITAL               narrative says capital flowing; Book 5/6
                                   records contradict
SOURCE_VS_SOURCE                   two source classes assert opposing cores
NARRATIVE_REVISION                 same lineage, core mutated (recorded as
                                   revision history on the identity)
NARRATIVE_REVERSAL                 core inverted (pro→anti, bull→bear) —
                                   recorded as reversal relation, not overwrite
```

Rules:

- Conflicting narratives and narrative-vs-evidence conflicts are **preserved
  as first-class rows** — never averaged, never resolved by volume, never
  silently superseded (Axiom 3; D2-3 spirit).
- A contradiction row may feed *narrative* state rules (if later ratified) but
  may never touch structural claim state (FW-2).
- Resolution of a contradiction, when it arrives, arrives as new evidence in
  Book 2 or new records in owning books — the contradiction row is then marked
  resolved-by-reference, preserving its history.

## 5. Verdict

```text
NARRATIVE_GRAMMAR        = PLANNED (7 terms; identity doctrine drafted)
ORIGIN_PROPAGATION       = PLANNED (descriptive only; zero scores)
EVIDENCE_FIREWALL        = PLANNED (FW-1..FW-4, mechanically checkable)
CONTRADICTION            = PLANNED (7 typed forms; preserve-both-lines law)
OPEN_DECISIONS           = D7N-2 (narrative identity methodology)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
