# TB-R1 — PRIOR-LIVE-STACK AUDIT REPORT

**Branch:** `tb-forward-engine` · **Base:** `d665ea04` · **Canonical research:** `6769ad31`

## Verdict

**tb_r1_audit_pass = true.** Every prior TB-live component is classified; the R0 contract was
compared exactly; no hidden strategy drift is left unidentified; exit semantics are proven
(and the single-`EXIT_Z` limitation demonstrated); weighting parity is measured; atomic
execution behavior is mapped; session/time semantics are known; market-data synchronization
and persistence gaps are identified; execution remains disabled.

## What is trustworthy (adopt)

| Component | Classification | Evidence |
|---|---|---|
| normalization engine | ADOPT_AS_IS | live wrapper z == canonical to **2.25e-12**, **0/265,809** entry mismatches |
| execution contract | ADOPT_AS_IS | typed, model_weight ≠ lots, dynamic broker metadata |
| atomic execution layer | ADOPT_AS_IS | full state machine, 3-fill verify, BROKEN_HEDGE flatten, order_check-all-first |
| broker metadata layer | ADOPT_AS_IS | `mt5.symbol_info` dynamic read |
| session/time layer | ADOPT_AS_IS | fixed UTC−5 consistent everywhere |
| parity harness | ADOPT_AS_IS (control) | independent replay, PASS 405/405 |
| shadow + guard | ADOPT_AS_IS | order_send monkeypatched off, non-bypassable |

## What needs mechanical repair (adopt with repair)

| Component | Repair |
|---|---|
| strategy wrapper forward config | entry 2.5 → 3.0; exit 0.0 → **signed** SHORT z≤−0.25 / LONG z≥+0.25; add −500 pips daily-loss cap |
| weight engine | wire canonical `project_basket(eps=0)` (TB-B) as the weight **input**; translation mechanics already correct |
| market-data layer | add fail-closed tick snapshot + max_quote_age/max_cross_leg_skew gates + runtime symbol probe |
| execution safety | `--mode` default must be **shadow**; trade requires explicit flag; demo-identity failure must fail closed; netting-overlap fail closed; hard LIVE disable |
| parity harness | extend to P7 config (3.0 / signed −0.25) |

## What is missing / replace

- **persistence layer = REPLACE/MISSING** — no append-only ledger; filled tickets never
  persisted; OPEN baskets not fully reconstructible from broker + local state alone.

## Key measured numbers

- z parity: max |z| diff **2.252e-12**, entry mismatches **0** (265,809 bars).
- weights: live raw inverse-ATR residual **34.84%** median vs TB-B exact-neutral **0.021%**
  median (405/405 solved) — the live stack **measures** neutrality but does **not** construct
  the exact-neutral basket.
- prior parity harness: **PASS** (old 2.5/0 config, 405/405).
- $500 notional sizing: **0/405** baskets pass (raw weights hit MIN_LOT_HEDGE_DISTORTION).

## Exit-semantics proof (synthetic)

SHORT path `[+2,+1,0,−0.10,−0.25]`: canonical signed P7 exit = **−0.25**; wrapper with
`EXIT_Z=−0.25` exits SHORT at −0.25 (correct). LONG path `[−2,−1,0,+0.10,+0.25]`: canonical
signed P7 exit = **+0.25**; wrapper with `EXIT_Z=−0.25` exits LONG at **0.0** (premature) —
proving the single `BASIS_EXIT_Z` interface cannot express the signed P7 geometry. See
`TB_R1_EXIT_SEMANTICS_AUDIT.json`.

## Next recommended checkpoint

The evidence selects two checkpoints ahead of the original numbering:

1. **TB-R1.1-PRIOR-STACK-MECHANICAL-REPAIR** (small) — fix the fail-open `--mode default=trade`
   and the other execution-safety defects before any further execution work.
2. **TB-R2-SYNCHRONIZED-MARKET-DATA** — build the fail-closed tick-level `TriangleSnapshot`
   (the only genuine greenfield gap).

## Scientific changes

**NONE.** Old drift was discovered (live stack uses old 2.5/0 config + raw weights, not TB-B),
but nothing was repaired — per this checkpoint's rule.

## Execution authorization

**NOT_AUTHORIZED** (no broker orders sent during this audit; shadow/seal only).
