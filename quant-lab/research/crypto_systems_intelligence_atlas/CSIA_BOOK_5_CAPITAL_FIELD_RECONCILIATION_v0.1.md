# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL FIELD RECONCILIATION (D7 RECONNAISSANCE)

**Document ID:** CSIA-B5-D7-RECON-001
**Version:** 0.1
**Status:** PLANNING ANALYSIS — NOT A DECISION — NOT A BOOK 5 PLAN
**Gate:** Constitution v0.2 §4.3; Operator Decision **D7** (`CSIA_OPERATOR_DECISION_LOG.md`, DEFERRED DECISIONS — **OPEN**)
**Session branch:** `agent/crypto-systems-intelligence-atlas-plan` @ `247b8ac39fea482022bb6fbd819a6f7e156952b7`
**Planning authority:** BOOK_5_PLANNING_AUTHORITY = TRUE; BOOK_5_IMPLEMENTATION_AUTHORITY = FALSE; LIVE_ACQUISITION_AUTHORITY = FALSE
**Supersedes:** nothing. **Is superseded by:** nothing. This artifact creates no canonical truth and decides nothing.

---

# 0. Purpose and non-goals

Constitution v0.2 §4.3 requires that Book 5 planning **begin** with an operator decision (D7) on how the historically deferred "Capital Field" concept relates to CSIA Book 5. This document is the reconnaissance for that decision: it inventories every historically attested meaning of "Capital Field" in program doctrine, maps the ambiguity, and stages the analysis the operator needs.

**This document does NOT decide D7.** It does not rank the options, does not select a reconciliation winner, does not modify any doctrine, and does not authorize Book 5 planning, implementation, or acquisition.

Non-goals:

- No Book 5 plan artifact is created by this session.
- No Book 1–4 mutation; no constitutional amendment.
- No implementation code; no acquisition; no RPC; no database.
- No trading signal, execution, or prescriptive semantics of any kind (Constitution §5.3a).

---

# 1. Verified governance state at session start

```text
BOOK_1 = FROZEN_ACCEPTED
BOOK_2 = FROZEN_ACCEPTED
BOOK_3 = FROZEN_ACCEPTED
BOOK_4 = FROZEN_ACCEPTED
BOOK_4_ACCEPTED_IMPLEMENTATION_ANCHOR = 1650ba7ce30633e2e4ddf141e439a13ed948c51b
BOOK_4_ACCEPTANCE_COMMIT = a2526e8220513b34967ab11f227ddbddc14e7e4a
BOOK_4_PLANNING_BRIDGE = 247b8ac39fea482022bb6fbd819a6f7e156952b7
BOOK_5_PLANNING_AUTHORITY = TRUE
BOOK_5_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
D7 = OPEN (Operator Decision Log, "DEFERRED DECISIONS (OPEN — NOT DECIDED THIS SESSION)")
D8 = OPEN (gate: before Book 8 planning) — out of scope this session
```

Gate verification: the canonical Operator Decision Log contains
`D7 — Capital Field reconciliation   gate: before Book 5 planning` and no
recorded D7 decision. Per §5.4, an unrecorded decision is not binding;
therefore no Book 5 planning packet exists or may be created this session.

---

# 2. Historical meaning inventory — where "Capital Field" appears

Every occurrence below was located by direct read/grep of the planning
directory on this branch. Nothing is inferred; quoted wording is verbatim.

## M-1 — IACER charter (pre-constitutional), §C2 "Existing queued Capital Field work"

> "The existing queued Capital Field/source-atlas concept already contains pieces such as: DEX/CEX mechanics; onchain flow; bridges; lending; yield; RWA; protocol economics; capital routing."
> "Capital Field should eventually become one major subsystem / lens inside CSIA rather than the entire right hemisphere."

And IACER §R3 (Relationship to other programs):

> "CAPITAL FIELD = capital-plumbing subsystem within broader CSIA"

and R3's anti-absorption rule: "No component silently gains authority over another."

**Reading:** a queued, separately-plannable **content domain** (capital plumbing) intended to live *inside* CSIA. Note the historical pieces list is materially the Book 5 bloc list.

## M-2 — Constitution v0.1 §4.3 (SUPERSEDED, preserved unmodified)

> "Capital Field is treated as a future major subsystem / lens inside CSIA, covering: cross-chain flow; bridge movement; stablecoin routes; credit; lending; vaults; staking/restaking; yield; RWA; capital concentration; capital routing."
> "Capital Field does not define the entire CSIA mission."

**Reading:** subsystem/lens **inside** CSIA, with a scope list that again maps ~1:1 onto the later Book 5 blocs.

## M-3 — Constitution review v0.1, CR-04 / SG-F (the collision finding)

> "Direct scope collision: Book 5 Blocs 5A–5F enumerate DEX, lending, staking, RWA — exactly the Capital Field queue items named in IACER §C2. Resolution gate required before Book 5 planning."
> "…if Capital Field is a separate program, CSIA Book 5 must not duplicate it; if it is a subsystem, Book 5 *is* it. Neither document resolves the scheduling conflict…"

**Reading:** the review found the two historical statements (separate queued program vs CSIA-internal subsystem) mutually unreconciled, and proposed the gate. This is the origin of D7.

## M-4 — Constitution v0.2 §4.3 (RATIFIED, operative law)

> "Capital Field is CSIA-internal in mission, but its existing and future planning artifacts are subject to a **reconciliation gate**… Book 5 (Capital Plumbing) planning **must begin** with an operator decision… on whether existing Capital Field planning artifacts are absorbed, referenced, or superseded by CSIA Book 5."
> "Capital Field does not define the entire CSIA mission."

**Reading:** three operator-selectable dispositions for *historical Capital Field artifacts* — **absorbed / referenced / superseded** — and an explicit CSIA-internal mission statement. §4.3 does not itself resolve whether "Capital Field" names the Book 5 domain, a synthesis layer, or a derived view.

## M-5 — Master Roadmap v0.1, Bloc 5G

> "## Bloc 5G — Capital Field synthesis" — Combine: issuance → routing → liquidity → credit → leverage → staking/yield → exit.
> Exit gate: `PASS_CSIA_B5_CAPITAL_FIELD_V1`.

**Reading:** inside Book 5 itself, the name "Capital Field" is attached specifically to the **synthesis bloc (5G)** and its exit gate — a second, narrower attestation distinct from M-1/M-2/M-4.

## M-6 — Book 4 accepted implementation boundary (`book4_boundary.py`, frozen at anchor `1650ba7c`)

```python
class BOOK4ScopeError(ValueError):
    """Book 5 capital-field content attempted to cross the Book 4 boundary."""
...
raise BOOK4ScopeError(f"Book 5 capital-field claim rejected from Book 4: {value}")
```

and the plan boundary (Book 4 plan v0.2, §boundary):

> "Book 5 owns capital routing, liquidity, collateral, stablecoin supply, credit, staking/yield, derivatives, economic flow, value locked, and capital concentration."

**Reading:** the frozen Book 4 code and plan both use "capital-field" as a name for **Book 5 domain content generally** (the thing that must not leak into Book 4). A third attestation, materially equivalent to M-1/M-2 scope-wise.

## M-7 — Book 1 adversarial review Q15 (identity-safety ruling)

> "Capital Field touches: capability edges (COLLATERAL_IN, LIQUIDITY_ON, ROUTED_THROUGH) already typed in 1C with capability/capacity/flow separation (Constitution §19.1) — flow events attach as *event objects referencing edges*, never mutating edge truth; INV-1C-4 forbids magnitudes on capability edges."
> "Capital Field reconciliation gate (Constitution §4.3, D7) governs scope, not identity; Book 1 identity is explicitly out of its blast radius."

**Reading:** "Capital Field" is treated as a future **data consumer** of Book 1 capability edges + Book 5 flow events, whose scope is governed by D7 but which cannot alter identity truth. Confirms Book 1 is boundary-safe under any D7 outcome.

## M-8 — Book 0 ratification packet (D7 as deferred operator authority)

> "D7 | Capital Field reconciliation decision | Before Book 5 planning | NO — Book 1 unaffected"
> Operator authority includes "Capital Field reconciliation."

**Reading:** D7 is reserved operator authority; it gates Book 5 planning only.

## M-9 — Program ledger and session guards

Ledger states "NO CAPITAL FIELD MUTATIONS = TRUE" in past-session guard blocks; Book 2/Book 1 ratification records list "no Capital Field mutation/implementation" among their exclusions.

**Reading:** historically, "Capital Field" has also functioned as the name of a **forbidden work category** in session guard language — i.e., "any capital-domain implementation not yet authorized."

## M-10 — No other canonical definition exists

No Capital Field plan, schema, source list, ontology, or implementation artifact exists anywhere in the repository (checked: `*CAPITAL*`, `capital field`, and the full planning-directory listing). The IACER's "existing queued Capital Field/source-atlas concept" refers to pre-CSIA operator queue notes that were **never imported** into the program's planning directory. Doctrine is exactly: M-1 through M-9. Anything else would be inference and is not asserted.

---

# 3. The ambiguity, precisely

The historical record supports **three different object-references** for "Capital Field":

1. **A content domain** — the whole capital-plumbing subject matter (M-1, M-2, M-4, M-6, M-9). Today this subject matter is, by roadmap and Book 4 plan boundary, exactly Book 5.
2. **A synthesis bloc inside that domain** — Bloc 5G "Capital Field synthesis" and exit gate `PASS_CSIA_B5_CAPITAL_FIELD_V1` (M-5).
3. **A subsystem/lens — i.e., a runtime consumer** — "one major subsystem / lens inside CSIA" (M-1, M-2), which in later architecture would be a *derived surface* over canonical capital data rather than the canonical data itself (Constitution §4.4/§4.5 pattern: lenses consume, canonical layers own).

These are not mutually exclusive as *names*, but they are mutually exclusive as *authority assignments*: if D7 declares "Capital Field = Book 5" the name becomes a synonym; if it declares "Capital Field = 5G lens" the name denotes a derived composition; if it declares a separate subsystem, Book 5 must not absorb it. The operator decision must pick the authority assignment; a name can remain a synonym, but authority cannot be split silently.

The candidate formal interpretations are analyzed in the decision packet
(`CSIA_BOOK_5_CAPITAL_FIELD_OPERATOR_DECISION_PACKET_v0.1.md`): the four the
directive requires (A = whole Book 5 domain; B = Bloc 5G synthesis layer;
C = derived read model above Book 5; D = independent first-class subsystem),
plus informational E (future operator surface rather than a data model) which
the directive also names. No option is endorsed there, and none is endorsed here.

---

# 4. Reconciliation principles (P1–P18) — application to the D7 question

These principles are directive-issued for D7 testing. Each is tested against the
canonical doctrine where it is grounded, and the grounding is cited. P1–P12 and
P14–P18 are application specializations of ratified doctrine; P13 and P15 are
explicitly stated in the D7 directive and are consistent with Constitution
§12 and §4.4 respectively.

| # | Principle | Grounding in ratified doctrine | Application to D7 |
|---|---|---|---|
| P1 | Capital truth must remain evidence-backed through Book 2 | Constitution §6, §13; D2-1..D2-6 | Under every option, capital facts are claims with claim-evidence pairs; no option may create a capital truth channel that bypasses Book 2 promotion. |
| P2 | Token ≠ chain ≠ protocol ≠ capital position | Axiom 2; §8 identity doctrine | A position/claim is not the token; candidate primitives must carry distinct object identities for asset vs position vs claim (see primitive matrix). |
| P3 | Technical route existence ≠ capital flow through that route | §19: "Possible capital route does not equal realized flow"; §19.1 capability/flow split | Book 4 `BRIDGES_TO`/`ROUTED_THROUGH` capability edges can never be recorded as moved value; Book 5 flows are event objects. |
| P4 | Liquidity presence ≠ economic ownership | §19: "TVL does not automatically equal productive capital"; §19.1 | Pool reserves are protocol-control balances, not attributable ownership; LP claims are separate claims. |
| P5 | Collateral eligibility ≠ collateral actually posted | §19.1 capability vs flow; roadmap 5C "collateral relationships" | `COLLATERAL_IN` capability edge (Book 1) vs a posted-collateral position record (Book 5) are different records. |
| P6 | Staking capability ≠ capital actually staked | §19.1; roadmap 5D | `STAKED_IN` capability vs StakePosition stock. |
| P7 | Bridge route ≠ capital transferred | §19; §19.1; roadmap 5F | Flow events reference bridge capability edges; never merged (INV-1C-4 doctrine; Q15). |
| P8 | DEX integration ≠ liquidity depth | §19.1 capability vs capacity (Book 6) | Integration edges (Book 4) vs pool reserves (Book 5 stock) vs depth metrics (Book 6). |
| P9 | Stablecoin deployment ≠ stablecoin circulating supply | §8.4 deployments; §19 | A deployment is issuance form; supply is a measured stock with issuer liability semantics. |
| P10 | Borrow-market existence ≠ debt outstanding | §19.1; roadmap 5C | Market existence is capability; debt is a stock record. |
| P11 | Yield mechanism ≠ realized yield | §19.1; roadmap 5D | Mechanism/capability vs realized flow records. |
| P12 | Open interest ≠ collateral value | roadmap 5E; §19.1 | Notional exposure is a distinct measured quantity; not additive to principal. |
| P13 | Capital state must be temporal | §12 bitemporal doctrine (directive-issued principle) | Every Book 5 candidate primitive carries valid time + transaction time; no current-state-only snapshots. |
| P14 | Historical capital flows must not be overwritten by current state | §12: "Current state must not overwrite prior state"; F-2 time-split | Flows are append-only events; stocks are temporally versioned; aggregation must not collapse history. |
| P15 | Derived synthesis must not become hidden authority | §4.4/§4.5 pattern (support layers gain no promotion authority); directive-issued principle | Any "field"/synthesis layer (Option B/C) must be marked derived, pointer-linked to canonical records, and hold no write authority over them. |
| P16 | Unknown capital state remains UNKNOWN, not zero | Axiom 6; P-1/P-3 evidence doctrine | Absence of an observed balance is UNKNOWN; zero is an observation. |
| P17 | Capital Field must not silently become a trading signal | §5.3a; D4 | No option may introduce prescriptive semantics; "exit" in 5G is an economic-topology state (capital leaving a system), not a trade recommendation (see §8.3 here and packet §7). |
| P18 | Book 5 remains descriptive, not prescriptive | §5.3a; §23.1; D4 | Descriptive facts and topology only; no rankings, scores, targets, timing. |

**Principle verdict:** all 18 are satisfiable under every D7 option *if* the
implementation follows them; the principles constrain the D7 consequence
analysis rather than pre-selecting an option. The packet records, per option,
where each option most risks violating a principle (esp. P15 for B/C/D; P3–P12
for any naive summation model).

---

# 5. Stock vs flow doctrine (Phase 7 mapping)

The stock/flow distinction is mandatory before Book 5 planning because naive
capital topology treats every balance as additive and every movement as a state.

## 5.1 STOCK examples (measured state at a valid time)

- circulating stablecoin supply (per deployment/realization, canonicalized per §12 stablecoin identity stress);
- locked balances (TVL-like, per protocol deployment, methodology-preserved);
- debt outstanding (per market);
- staked balance (per operator/delegator as observable);
- open interest (per venue);
- collateral posted (per position);
- vault assets under management (share-backed).

Stock identity requirements: asset identity (canonical + realization), holder/owner if observable (else UNKNOWN), protocol/venue identity, chain/deployment, quantity + unit, valid time, observation time, Book 2 claim refs, observed vs derived.

## 5.2 FLOW examples (temporally bounded events)

- bridge transfer; DEX swap volume (aggregated flow); borrow origination; repayment; liquidation; staking inflow/outflow; redemption; mint/burn; deposit/withdrawal.

Flow identity requirements: from-state/location, to-state/location, asset identity, quantity, valid-time interval or instant, observation time, evidence refs, and the capability edge referenced (if any).

## 5.3 Doctrine requirements (binding on whichever D7 option is chosen)

- Stocks and flows must be **different record classes**; a flow event is never a stock mutation that overwrites (P13/P14; Constitution §12, §19.1).
- Aggregation (netting, summing) is a **derived view** and must carry methodology and pointer lineage; primary data stays at record granularity (mirrors INV-1C-7's aggregation-is-derived rule for realizations).
- UNKNOWN ≠ zero (P16): a missing stock observation is UNKNOWN; zero requires an observation of zero.
- Whether the "Capital Field" object (under any option) contains stocks, flows, or both is a D7-consequence question, recorded per option in the packet. This analysis does not pre-select it.

---

# 6. Transformation semantics (Phase 8)

Capital frequently changes **form** without leaving the economic system. The
historic failure mode is collapsing all of these into "capital moved" or, worse,
into additive balances. Directive stress forms:

| Transformation | What changes | What must stay separate |
|---|---|---|
| USDC → LP token | custody/claim form: fungible claim on pool share | asset identity (USDC) vs realization/claim token identity; pool liability |
| ETH → stETH | liquid-staking claim issued | ETH principal vs stETH liability/claim; reward accrual mechanics |
| stETH → restaked position | delegation/second-order collateral | claim chain: ETH → stETH → restaked receipt; operator delegation |
| USDC collateral → borrowed ETH | claim swaps sides: deposit claim + debt liability | supplied claim vs debt liability vs borrowed asset position |
| ETH → perp collateral | margin posting | collateral position vs notional exposure vs unrealized PnL |
| BTC → wrapped BTC realization | chain-local representation | canonical asset vs REALIZATION (R-1A-5 doctrine) |
| Treasury token → lending collateral | RWA claim re-used | off-chain claim, token supply, posted collateral |
| Stablecoin → yield vault share | custody + strategy claim | stablecoin claim vs vault share liability vs strategy position |

Required separations (candidate record dimensions, not ratified names):

- **asset identity** — the canonical economic asset (Book 1);
- **realization identity** — chain-local manifestation (R-1A-5: REALIZATION; REALIZES/RECEIVED_VIA edges exist and are contractual);
- **position identity** — a holder's claim/liability in a protocol (Book 5 candidate);
- **claim on underlying** — what the token entitles (LP share, LST, vault share, RWA claim);
- **economic exposure** — what the holder gains/loses from (includes derivative exposure; not additive principal);
- **custody/control** — where control sits (self, protocol, custodian);
- **protocol liability** — what a protocol owes (debt, redeemable supply).

Rule: a transformation record references the input claim and output claim as
**distinct identities with a typed transformation relation**; it never nets to
"same capital, moved" nor double-mints value. This is Book 5-local typed-record
territory; Book 1's REALIZES/RECEIVED_VIA vocabulary covers asset-vs-realization
identity, not protocol-level positions.

---

# 7. Ownership vs location vs control vs liability vs use (Phase 10)

Directive axis set, applied to the standard stress cases:

| Case | Where it sits (location) | Who owns the economic claim (owner) | Who controls/custodies (control) | Who owes a liability (liability) | What protocol uses the asset (use) |
|---|---|---|---|---|---|
| Lending deposit | lending market contract | depositor | protocol contract | protocol/market (repayable) | as loanable liquidity |
| Custodial bridge escrow | bridge escrow contract | route user (wrapped-side holder holds claim) | bridge custodian/contract | bridge (redemption) | as transfer backing |
| Vault shares | vault contract | LP/user | vault strategy/contract | vault (share redemption) | as managed liquidity |
| CEX settlement assets | exchange custody | user (if segregable — often UNKNOWN) | exchange | exchange (if rehypothecated: debtor) | as market plumbing |
| Staking contracts | staking contract/slashing-eligible | staker/delegator | validator/operator (delegated control) | protocol only where redemption is owed (LST) | as security/economic weight |
| RWA SPV | off-chain SPV/custodian | token holder (claim on SPV) | SPV trustee/custodian | SPV/issuer (redemption) | as collateral/settlement |
| Perp collateral | venue margin account | trader | venue/contract | venue counterparty pool (PnL) | as margin |

Key observability notes (these constrain Book 5, they do not decide D7):

- On-chain positions are often attributable; **off-chain control (CEX custody, SPV, institutional routes) is frequently UNKNOWN and must remain UNKNOWN (P16), not imputed**.
- Book 1 identity doctrine (owner/control edges `OWNED_BY`, `OPERATED_BY`) covers entity-level ownership of *objects*, not per-position economic claims. Per-position claim/liability/custody distinctions are **not** expressible in Book 1 today and are Book 5-local candidate records → recorded as a BOOK_1_EXTENSION_CANDIDATE (see boundary review §6). No amendment is proposed or made automatically.

---

# 8. Capital route vs technical route (Phase 11 reconciliation with Book 4)

## 8.1 Frozen Book 4 vocabulary

Book 4 (technical dependency atlas) owns, per its frozen plan and allowlist:
`BRIDGES_TO`, `ROUTED_THROUGH`, `MESSAGES_TO` — i.e., **capability** facts:
a route exists, a message can pass, an asset is supported across a path.

## 8.2 Required Book 5 vocabulary (candidate)

Book 5 must separately represent: **"$X of asset Y moved from state/location A to B during valid time T"** — an observed, quantified, temporally bounded flow event.

Doctrine candidate (recorded, not ratified): `TECHNICAL ROUTE ≠ OBSERVED CAPITAL FLOW`; likewise `AVAILABLE ROUTE ≠ USED ROUTE`; `SUPPORTED ASSET ≠ TRANSFERRED ASSET`.

## 8.3 Is Book 1 sufficient?

- Book 1 provides the capability edge classes (`ROUTED_THROUGH`, `BRIDGES_TO`, `COLLATERAL_IN`, `LIQUIDITY_ON`) with INV-1C-4 forbidding magnitudes on capability edges, plus flow events as event objects referencing edges (Q15, Constitution §19.1). This is **structurally sufficient** for the route/flow split.
- What Book 1 does not carry: flow-event **field-level contracts** (quantity, unit, party/leg identities, liability effects, transformation typing). Roadmap assigns capital-flow modeling to Book 5; Book 1's non-goal line confirms: "No capital-flow modeling (Book 5) — only capability-edge vocabulary."
- Verdict: **no contradiction**; Book 5-local typed flow records referencing Book 1 capability edges is the compatible architecture. Recorded in the boundary review; no Book 1 or Book 4 amendment is required by the route/flow distinction itself.

## 8.4 5G "exit" semantics guard

The 5G sequence ends in "exit". Under P17/P18 and §5.3a, "exit" may mean only
the **economic-topology state where capital leaves the system boundary**
(redemption, burn, bridge-out to non-modeled venues, CEX off-ramp) as a
descriptive record class. It must never be implemented or surfaced as a trade
exit recommendation. This reading is consistent with the roadmap's framing
("where capital… exits") and is recorded as a boundary constraint for whichever
option wins D7 — it is a constraint, not a D7 choice.

---

# 9. Option impact register (summary — full analysis in the decision packet)

| Dimension | A: Capital Field = Book 5 | B: Capital Field = 5G synthesis | C: Capital Field = derived read model | D: Capital Field = independent subsystem |
|---|---|---|---|---|
| Roadmap change needed | none (name ≈ synonym) | none (matches 5G naming) | none strictly; naming convention needed | yes — 5G + Constitution §4.3 wording tension |
| Constitution amendment | no | no | no (derived-view rule suffices) | possibly (§4.3 says "CSIA-internal subsystem"; an independent governed subsystem needs boundary language) |
| Books 1–4 amendments | no | no | no | no (but Book 4 boundary consumers change meaning) |
| Duplication risk | lowest | low | low-moderate (two names for near-identical derived layers) | highest (parallel capital authority) |
| Hidden-authority risk (P15) | n/a | must mark 5G derived | must mark read model derived | structural risk |
| Migration impact | none | none | naming/derivation discipline | redesign of 5G + gate |

---

# 10. Result

```text
D7 = OPEN (unchanged)
BOOK_4_AMENDMENT_REQUIRED = FALSE  (no Book 4 contract contradiction found; see boundary review)
BOOK_1_AMENDMENT_REQUIRED = FALSE  (extension candidate recorded, not applied)
CAPITAL_FIELD_RECONCILIATION = READY_FOR_OPERATOR_REVIEW
DECISION_MADE_HERE = NONE
NEXT = OPERATOR DECISION D7 (via CSIA_BOOK_5_CAPITAL_FIELD_OPERATOR_DECISION_PACKET_v0.1.md)
```
