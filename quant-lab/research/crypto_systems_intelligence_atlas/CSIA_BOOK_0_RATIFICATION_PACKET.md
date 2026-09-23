# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 0 — CONSTITUTION, EPISTEMICS, AND PROGRAM GOVERNANCE
## Ratification Packet

**Document ID:** CSIA-B0-PACKET-001
**Version:** 0.1
**Status:** FROZEN_FOR_REVIEW — AWAITING OPERATOR RATIFICATION
**Depends on:** `CSIA_CONSTITUTION_v0.2.md`, `CSIA_CONSTITUTION_REVIEW_v0.1.md`
**Covers Roadmap:** Book 0 (Blocs 0A, 0B, 0C)
**Planning branch:** `agent/crypto-systems-intelligence-atlas-plan`
**Implementation authority:** NONE — this is a governance packet, not code

---

# 0. Purpose of this packet

Book 0 exists to freeze what CSIA is allowed to mean before anything is built.

This packet consolidates everything the operator must ratify to close Book 0, and states exactly which decisions only the operator can make.

It is organized as the ratifiable contract itself: each section below, once ratified, becomes the governing rule. Where the Constitution v0.2 already carries the rule, this packet binds it into Book 0 scope and names the open decision.

---

# 1. Mission

**Ratified text (from Constitution §1–2):**

CSIA is the **right hemisphere** of a two-hemisphere crypto intelligence system, paired with Crypto Sensor Fabric (left hemisphere).

- CSIA = investor-fundamental / structural intelligence.
- Crypto Sensor = trader-mechanical / market-state intelligence.
- CSIA's mission: a living, evidence-backed, temporally versioned world model of the crypto ecosystem — chains, ledgers, rollups, appchains, DAG networks, modular systems, protocols, middleware, bridges, interoperability, oracles, stablecoins, DeFi, payments, storage, compute, identity, DePIN, RWA, wallets, developer infrastructure, governance, tokens, entities, integrations, dependencies, capital routes, events, narratives, and ecosystem evolution.
- CSIA answers: *what is this system, how is it connected, what changed, and why could that change matter?*
- Crypto Sensor answers: *what is the market doing?*
- The Context Bridge eventually answers: *did structural change produce measurable network, capital, and market confirmation?*

**Mission boundaries (Constitution §4, §5.3, §5.3a):** no trading, no execution, no prescriptive output, no recommendation engine. CSIA is a structural intelligence substrate.

**Operator decision required:** none beyond ratification itself. The mission is fully specified in Constitution v0.2 §1–2.

---

# 2. Authority

**Ratified text (Constitution §5):**

## 2.1 Operator authority
Final authority over: constitutional ratification; amendments; bloc authorization; source classes requiring cost or credentials; promotion of experimental states; external publication; integration into trading or portfolio systems; CSIA↔Sensor boundary assignments; Capital Field reconciliation.

## 2.2 Research authority
CSIA may: discover, ingest public evidence, classify, map, compare, calculate, test, generate hypotheses, detect change, produce research summaries.

## 2.3 Absent authority
CSIA may not: trade, route capital, sign transactions, manage wallets, execute governance votes, bridge funds, alter protocol state, publish investment recommendations, silently promote inference into fact.

## 2.4 Descriptive/Prescriptive boundary (Constitution §5.3a)
Descriptive outputs (states, evidence, relationships) are permitted. Prescriptive outputs (rankings, scores, targets, advice) are forbidden. Prescriptive intent smuggled through naming is a constitutional violation.

## 2.5 Operator Decision Log (Constitution §5.4)
All binding operator decisions are recorded in the Operator Decision Log. Unrecorded decisions are not binding. Recorded decisions are reversed only by later recorded decisions, never silently.

**Operator decision required:** none beyond ratification.

---

# 3. Epistemic hierarchy

**Ratified text (Constitution §6):**

Five evidence tiers by role:

```text
E0  Native technical truth      specs, source code, deployed state,
                                genesis/config, RPC/explorer state,
                                governance execution records
E1  Native operational truth    first-party dashboards/APIs, validator data,
                                foundation status pages, treasury records,
                                first-party registries
E2  Independent high-quality    audited research, reputable analytics,
                                academic work, independent technical
                                security analysis, audited security reports
E3  Aggregator / secondary      discovery, corroboration, comparison only
E4  Narrative                   news, social, marketing — establishes that
                                a narrative exists, never that the claimed
                                change is true
```

## 3.1 Tier-to-claim-state promotion matrix (Constitution §6.1)

| Target state | Minimum evidence | Independence |
|---|---|---|
| OBSERVED | E0 | 1 source (deterministic facts) / 2 (behavioral facts) |
| DECLARED | E1 or E2 | 1 source; stays DECLARED until E0 verification |
| CORROBORATED | ≥1 E1 + second independent source | No shared origin |
| INFERRED | Any + explicit methodology | Never displayed as OBSERVED |
| CONTESTED | Conflicting credible evidence | Conflict is the evidence |
| REJECTED / SUPERSEDED | Explicit disposition | Operator or promotion rule |

E4-only evidence can never produce OBSERVED or CORROBORATED.

---

# 4. Claim states

**Ratified text (Constitution §7):**

```text
OBSERVED / DECLARED / INFERRED / CORROBORATED / CONTESTED /
UNRESOLVED / STALE (derived) / REJECTED / SUPERSEDED
```

- Claim states are properties of **claim-evidence pairs**, not nodes.
- Legal transition machine fixed in Constitution §7.1; illegal transitions (notably `INFERRED→OBSERVED`, `DECLARED→CORROBORATED`, any E4→OBSERVED) must be prevented or flagged by the system.
- Dependent-claim propagation: rejection/supersession of a claim forces every dependent claim to `UNRESOLVED`; dependents can never display stronger than their weakest dependency.
- `STALE` is computed from temporal policy, never asserted.

---

# 5. Contradiction handling

**Ratified rules:**

1. Conflicting credible evidence creates `CONTESTED` — never an averaged truth, never a silent winner.
2. `CONTESTED` requires recording both (all) sides with their evidence.
3. Resolution requires new evidence (per §7.1 transitions) or an operator decision recorded in the Decision Log.
4. Ontology tests (Constitution §32) must include adversarial contradiction cases.
5. Contradictions must remain visible to the operator on every surface that displays the affected claim.

---

# 6. Causality language

**Ratified rules (Constitution §23.1, §25):**

- Sequence ≠ causality. CSIA records temporal precedence, correlation, dependency, plausible mechanism, and event-study results as distinct evidence classes.
- "Caused / drove / led to" require mechanism evidence; "preceded" and "associated with" are the default vocabulary.
- `CONFIRMED_*` states mean "response was observed on that axis" — never a causal assertion.
- Causal claims are only valid inside event-study outputs with explicit, inspectable methodology.

---

# 7. Uncertainty

**Ratified rules (Constitution §12, §26):**

- Missing is not false: `UNKNOWN`, `UNSUPPORTED`, `INACCESSIBLE`, `UNRESOLVED`, `STALE`, and `ZERO` are distinct states.
- Unknown valid time is represented as bounded intervals or explicit UNKNOWN markers — never fabricated exact dates.
- Confidence may be expressed as evidence count, source class, unresolved conflicts, bands, or qualitative scales — each with an inspectable methodology ID.
- Confidence never hides contradiction.

---

# 8. Source hierarchy

**Ratified rules (Constitution §6, §C4 of IACER, Book 2 scope):**

Preference order for acquisition planning:

```text
1. protocol / chain official documentation     (E0)
2. repositories and technical specs            (E0)
3. explorer / RPC / indexer data               (E0)
4. first-party dashboards / APIs / registries  (E1)
5. foundation / governance publications        (E1)
6. audited deployment / security data          (E2)
7. high-quality independent research           (E2)
8. aggregators                                 (E3 — corroboration only)
9. social / news                               (E4 — narrative evidence only)
```

- A claim about architecture or dependency must be source-backed per the §6.1 matrix.
- Social narrative is never canonical architecture truth.
- Security doctrine (§30) and cost doctrine (§31) compliance are Book 2 exit-gate requirements.

---

# 9. Amendment procedure

**Ratified rules (Constitution §36):**

A constitutional amendment must include: amendment ID; affected clauses; reason; new language; migration impact; compatibility impact; supporting evidence; operator ratification.

Historical constitutions are preserved unmodified.

Amendments are recorded in the Operator Decision Log.

---

# 10. Anti-drift rules

**Ratified rules (Constitution §37):**

Standing audit questions — any persistent "no" requires correction:

1. Are we building a world model or a news feed?
2. Are we representing systems or merely tokens?
3. Are we preserving native architecture?
4. Are we distinguishing narrative from action?
5. Are capital routes actual or merely possible?
6. Are facts temporally versioned?
7. Are uncertainty and contradiction visible?
8. Are we duplicating Crypto Sensor?
9. Are we accidentally creating investment rankings?
10. Can the operator inspect why a relationship exists?
11. Is native modeling atrophying in favor of comparison-layer convenience?
12. Are operator surfaces eroding token/protocol/chain/entity distinctions?
13. Are temporal views collapsing to current-state-only snapshots?

Plus structural drift guards ratified in v0.2:

- Program Ledger is the sole authority for the current next step (Constitution §G).
- Bloc isolation (§35): no silent scope absorption.
- Bloc Ratification Records (§34.1): unratified output is non-canonical by construction.
- Narrative-evidence firewall (§20.1).
- Capability/capacity/flow distinction (§19.1).
- Descriptive/Prescriptive boundary (§5.3a).

**Anti-drift audit cadence:** at every book ratification and at every program-phase boundary, the operator (or a delegated review) answers questions 1–13 in a recorded audit entry.

---

# 11. Explicit operator decisions required

The following decisions are reserved to the operator and are **not** resolvable by any agent:

| # | Decision | Context | Blocking? |
|---|---|---|---|
| D1 | Ratify Constitution v0.2 (with or without per-correction objections to CR-01..CR-07) | `CSIA_CONSTITUTION_v0.2.md` | YES — blocks Book 0 closure |
| D2 | Accept the claim-state machine (§7.1) as fixed, or propose amendments | Book 0 §4 | YES |
| D3 | Accept the tier-promotion matrix (§6.1) as fixed, or propose amendments | Book 0 §3.1 | YES |
| D4 | Confirm descriptive/prescriptive boundary (§5.3a) wording | Book 0 §2.4 | YES |
| D5 | Confirm anti-drift cadence (per-book + per-phase audits) | Book 0 §10 | YES |
| D6 | Confirm Program Ledger as sole next-step authority (§G) | Constitution §G | YES |
| D7 | (Deferred) Capital Field reconciliation decision | Before Book 5 planning | NO — Book 1 unaffected |
| D8 | (Deferred) CSIA↔Sensor shared-seam ownership assignments | Before Book 8 planning | NO |

**Blocking set = D1–D6.** All are single-ratification decisions over already-written text; none require new research.

---

# 12. Exit gate

```text
PASS_CSIA_B0_PROGRAM_CONSTITUTION_RATIFIED

Requires:
  - Operator decisions D1–D6 recorded in the Operator Decision Log
  - Book 0 status = RATIFIED
  - Book 1 planning remains authorized under D1 (BOOK_PLANNING_AUTHORITY = TRUE)
```

---

# 13. Verdict

All constitutional critical issues (CR-01..CR-07) are addressed in Constitution v0.2. No critical blockers remain **in the text**. The single remaining dependency is operator ratification itself (D1–D6).

```text
READY_FOR_OPERATOR_RATIFICATION = TRUE
```

Book 1 planning (already prepared in `CSIA_BOOK_1_IDENTITY_ONTOLOGY_TEMPORAL_GRAPH_PLAN_v0.1.md`) proceeds on the assumption that D1–D6 are ratified as written; any operator objection to the six decisions above flows into a Book 1 plan revision, not into a constitutional deadlock.

End of Book 0 ratification packet.
