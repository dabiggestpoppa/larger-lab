# CSIA Book 2 — Source Authority Matrix — v0.1

Status: PLANNING DRAFT — NOT RATIFIED
Companion to: `CSIA_BOOK_2_SOURCE_EVIDENCE_ACQUISITION_PLAN_v0.1.md` (Bloc 2E P-2, Bloc 2F F-1)
Doctrine: **authority is claim-type dependent.** This is NOT a universal
ranking table. Each claim family resolves its own preference order; a
source class that is authoritative for one family may be near-worthless for
another.

## How to read this matrix

For each claim family: the evidence classes that can carry promotion weight
(preferred → supporting), what can never carry it alone, and the default
staleness policy reference (Bloc 2G).

| Claim family | Preferred evidence classes | Supporting | Never sufficient alone | Staleness (2G) |
|---|---|---|---|---|
| CHAIN ARCHITECTURE | technical specs (NATIVE_TECHNICAL), source REPOSITORY, official docs | ACADEMIC, SECURITY_AUDIT (design rationale) | NEWS, SOCIAL, AGGREGATOR | supersession-oriented |
| DEPLOYMENT (deployed state) | deployed-state observation: RPC, verified contract state, EXPLORER (post-lag check) | first-party announcement (timing context only) | press releases, AGGREGATOR, SOCIAL | SHORT |
| GOVERNANCE EXECUTION | on-chain governance state / executed on-chain change | GOVERNANCE forum, official docs (phase context) | forum sentiment, NEWS | event-driven |
| GOVERNANCE PROPOSAL (pre-execution) | GOVERNANCE system (proposal text, vote state) | NEWS/SOCIAL (narrative existence) | nothing proves execution except execution | event-driven |
| INTEGRATION | deployed integration state (RPC/explorer) + first-party confirmation | official docs of both parties | announcements, AGGREGATOR, NEWS | MEDIUM |
| NARRATIVE | NEWS, SOCIAL, interviews, official blog | AGGREGATOR (existence only) | — (narrative IS this family) | fast decay |
| SECURITY EVENT | chain state (exploit txs), incident report, SECURITY_AUDIT, postmortem | official comms, STATUS_SYSTEM | SOCIAL rumor, NEWS alone | event-driven |
| TOKEN ROLE / MECHANICS | protocol docs (mechanics as specified) + deployed mechanics (RPC/state) | REPOSITORY, governance records | AGGREGATOR, SOCIAL | MEDIUM; supersession for spec parts |
| BRIDGE / ROUTE STATE | deployed route state (RPC/explorer) | STATUS_SYSTEM (outages), official docs | NEWS, SOCIAL | SHORT–MEDIUM |
| VALIDATOR SET / EPOCH STATE | chain state (RPC, epoch queries) | explorer, chain-specific dashboards | NEWS | chain-specific |
| HISTORICAL GENESIS / SPEC | genesis data, original specs, archival captures | ACADEMIC | — (never "stale"; only supersession) | none (historical) |
| IDENTITY ATTRIBUTES (names, tickers, logos) | first-party docs, REPOSITORY, verified listings | AGGREGATOR (quarantined per S-4) | SOCIAL unverified | MEDIUM |
| MARKET DATA (out of CSIA structural scope) | — | AGGREGATOR, exchanges | never promotes structural claims | fast decay |

## Cross-family rules

- A-1: deployed state and documentation answer different questions. For
  "what IS", deployed state outranks docs; for "what is SPECIFIED",
  docs outrank deployed state. Neither universally wins (Bloc 2F F-1).
- A-2: AGGREGATOR evidence can corroborate identity attributes but can
  never be the sole line for structural claims (Bloc 2A S-4, 2E P-2).
- A-3: NEWS/SOCIAL evidence promotes only narrative-existence
  propositions — never the structural claims they may embed (2E P-3).
- A-4: RPC and EXPLORER both observe chain state, but RPC is primary;
  explorer disagreement routes to Bloc 2F with lag awareness (stress 14).
- A-5: an unregistered source cannot contribute authority at any tier
  (Bloc 2I I-1) — no exceptions for "obviously true" content.

## Family definitions feed

This matrix defines the tier-resolution function referenced by:
Bloc 2E P-2 (tier requirements per promotion), Bloc 2F F-1 (conflict
classification), Bloc 2H H-3 (candidate-change routing).

## Operator review points

- Ratify the family list (add/remove families before ratification).
- Ratify A-1 (dual-key docs/deployed-state doctrine).
- Confirm MARKET DATA remains out of structural scope.
