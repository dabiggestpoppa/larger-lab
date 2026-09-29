# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL FIELD D7 DECISION RECORD

**Document ID:** CSIA-B5-D7-CLOSURE-001
**Version:** 0.1
**Status:** RECORDED OPERATOR DECISION — D7 CLOSED
**Decision session:** 2026-09-29 (operator selections supplied explicitly via the D7 directive)
**Decision-log entry:** `CSIA_OPERATOR_DECISION_LOG.md` — BOOK 5 DECISION (D7)
**Source packet:** `CSIA_BOOK_5_CAPITAL_FIELD_OPERATOR_DECISION_PACKET_v0.1.md`

---

# Decision record

```text
D7 = CLOSED

SELECTED_OPTION = B
DECISION = CAPITAL FIELD = BOOK 5 BLOC 5G DERIVED SYNTHESIS

CAPITAL_FIELD_CANONICAL_MEANING = BOOK 5 BLOC 5G DERIVED SYNTHESIS
CAPITAL_FIELD_INDEPENDENT_SUBSYSTEM = FALSE
CAPITAL_FIELD_CANONICAL_WRITE_AUTHORITY = FALSE

CANONICAL_BOOK5_WRITE_AUTHORITY = 5A–5F
5G_DERIVED_AUTHORITY = COMPOSITION ONLY
5G_BINDING_INVARIANT_1 = 5G MAY DERIVE FROM CANONICAL CAPITAL FACTS
5G_BINDING_INVARIANT_2 = 5G MAY NOT CREATE CANONICAL CAPITAL FACTS

HISTORICAL_ARTIFACT_DISPOSITION = ABSORBED
  (scope incorporated into Book 5 / Bloc 5G planning; historical artifacts
   preserved as history; never deleted or rewritten; no separate governance,
   implementation, or epistemic authority retained)

5G_NAME = Capital Field synthesis
5G_EXIT_SEMANTICS = DESCRIPTIVE_ECONOMIC_TOPOLOGY_ONLY
  ("exit" = capital leaves the modeled system boundary — redemption, burn,
   off-ramp, transfer beyond modeled topology; NEVER a trade exit
   recommendation, execution instruction, market-timing state, SELL signal,
   or prescriptive operator guidance)

DOUBLE_COUNTING_INVARIANT =
  economic principal != representation != claim/liability !=
  gross exposure != net exposure
  and none may be summed interchangeably

CONSTITUTION_AMENDMENT_REQUIRED = FALSE
BOOK_1_AMENDMENT_REQUIRED = FALSE
BOOK_2_AMENDMENT_REQUIRED = FALSE
BOOK_3_AMENDMENT_REQUIRED = FALSE
BOOK_4_AMENDMENT_REQUIRED = FALSE

BOOK_5_PLANNING_AUTHORITY = TRUE
BOOK_5_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE

EPISTEMIC_AUTHORITY = BOOK 2 (unchanged — all capital facts are
Book 2 claim-evidence pairs)
```

---

# Effect

1. Constitution v0.2 §4.3's reconciliation gate no longer blocks Book 5 planning; D7 is closed by this recorded decision per §5.4.
2. Book 5 planning may begin under `BOOK_5_PLANNING_AUTHORITY = TRUE` with implementation authority and live acquisition still FALSE.
3. All Book 5 planning must honor the D7 invariants above, the 5G must-not/may lists from the decision log, and the operator's exit-semantics limits.
4. `binding_commit_sha` is assigned at the D7 closure commit and recorded in the Program Ledger at the planning-close checkpoint.

No implementation, acquisition, RPC, database, graph database, or Books 1–4 mutation is authorized by this record.
