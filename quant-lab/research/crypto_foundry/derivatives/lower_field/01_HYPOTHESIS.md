# CRYPTO-ALT-LOWER-FIELD-0 — HYPOTHESIS
## Lower-Cap Response Geometry & Speculative-Horizon Anatomy

**Checkpoint:** `CRYPTO-ALT-LOWER-FIELD-0`
**Agent:** AGENT 2 — CRYPTO DERIVATIVE / SIDE-LANE EXPLORER
**Branch:** `agent/crypto-quant-foundry`
**Status:** SIDE-LANE HYPOTHESIS — terrain research only. NO strategy, NO PnL, NO execution.
**Anchors:** Constitution `d030a1c1`, Definitions `bae722a1`, Idea Update `34b592f7`,
Lower-Field Hypothesis `85030bc4`, Dual-Agent Architecture `04a09016`,
MECH-1 `b3083df1`, MECH-2 `8636370a`, ALT-MECH-1 (rank migration), ALT-MECH-2 (conditional propagation).
**Parent decision:** `PASS_ALT_TERRAIN_WITH_LIMITATIONS` (MECH-2, `8636370a`).

---

## 1. Governing question

> Does capitalization / rank alter the market response function, participant horizon,
> explanatory hierarchy, persistence, reversal, and local-vs-global dependence of a
> crypto asset?

The existing Top-500 panel (`alt_rotation/data_1_1`) cannot answer this. It only
observes ranks 1-500. ALT-MECH-2 found **no sustained SMALL_CAP_ROTATION state inside
the Top-500** (6 of 2,196 days) and concluded small-cap rotation is not a real state
*within that window of the field*. This lane tests the corollary: the phenomenon may
have been searched for in the wrong region of the field.

**Do not conclude that small-cap rotation does not exist below rank 500.**

## 2. Working hypothesis (candidate interpretation only)

Lower-ranked crypto assets may represent a different participant ecology:

- upper-rank assets: more persistent holding / investing / institutional exposure;
- lower-rank assets: more short- and medium-horizon speculative capital seeking
  larger convex returns.

Preferred wording (no participant-type claim from price behavior alone):

> Lower-ranked assets may exhibit behavior consistent with shorter-horizon
> speculative capital.

This is a hypothesis. It may fail.

## 3. Testable derivatives (all preregistered in 02_PREREGISTRATION.md)

| ID | Derivative | Observable prediction if hypothesis holds | Falsifiable alternative |
|----|-----------|------------------------------------------|------------------------|
| D1 | Rank-dependent elasticity | Conditional response amplitude (median/p75/p95, both signs) expands as rank falls | Flat or non-monotone response by rank |
| D2 | Up/down asymmetry | Negative elasticity grows faster than positive as rank falls (b > a) | Symmetric amplification |
| D3 | Explanatory hierarchy shift | Global-field explanatory share decays with rank; chain/sector/idiosyncratic share rises | Global dominance persists |
| D4 | Horizon shortening | Short-horizon (1-7D) momentum carries more incremental information at lower ranks; medium (30-60D) less | Horizon structure rank-invariant |
| D5 | Faster decay / reversal | Post-extreme-move persistence shortens as rank falls; winners reverse faster | Persistence rank-invariant |
| D6 | Amplifier vs decoupled | Lower ranks remain tied to global field with larger amplitude (AMPLIFIER) vs weakened tie (PARTIAL_DECOUPLING / INDEPENDENT_SUBFIELD) | NO_DISTINCT_STRUCTURE |

Four allowed outcomes for the field as a whole (do not privilege any):

1. **AMPLIFIER** — lower ranks tied to global field, greater amplitude both signs.
2. **PARTIAL_DECOUPLING** — global explanatory power decays; chain/sector/local rise.
3. **INDEPENDENT_SUBFIELD** — local liquidity islands, weak global dependence.
4. **NO_DISTINCT_STRUCTURE** — behavior reduces to ordinary beta / illiquidity /
   survivorship / stale pricing / bad data / listing artifacts / random variation.

## 4. Why the canonical Top-500 null does not transfer

- ALT-MECH-2 tested rank bands 1-10 … 301-500. The 501+ region is unobserved in the
  canonical panel.
- MECH-2's own finding — conditional reversals (e.g., 51-100→101-200 rank velocity:
  unconditional −0.30, BTC_DOWN +0.64, VOL_HIGH +0.67) — shows aggregate relationships
  can be mixtures of distinct field states. The lower field may exhibit a *different*
  mixture.
- Data-quality and liquidity regimes below rank 500 differ structurally (single-venue
  pricing, thin volume, listing distortions, higher delisting rates). Those are
  controlled-for confounds, not the phenomenon.

## 5. Data requirement (PIT, survivorship-free)

True point-in-time lower-rank universe, ranks **501-2000** (minimum target 501-1000),
same calendar (2,196 dates) as the canonical panel, source = same CMC internal
historical-listings endpoint already verified as
`PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT` (DATA-0 / DATA-1).

PIT by construction (dated snapshots) preserves dead assets, delisted assets,
collapsed projects, rebrands, migrations, temporary listings, rank changes, and
missing historical periods. No modern-survivor universe is created or backfilled.

If PIT truth cannot be established for the reachable region, the lane stops and
classifies **DATA_BLOCKED** — it does not improvise.

## 6. Epistemic discipline (from Constitution)

- Never claim more resolution than the observation layer supports.
- Categories (chain, sector, narrative, liquidity, age, rank) are **lenses**, not
  filters. Analysis begins "this event occurred; what coordinates describe it?" —
  never "only analyze Solana memecoins".
- Redundancy is measured, not assumed. The goal is the smallest NON-REDUNDANT
  representation, not the smallest dimension.
- Negative evidence is preserved. Every tested derivative gets a verdict:
  NEW_NODE / MERGE / DISSOLVE / NULL / DATA_BLOCKED.
- Seasonality is NOT sliced at the start; it is only tested as a residual
  explanation downstream.
- Latent-state / HMM work is downstream, authorized only if observable-state
  conditioning leaves structured residuals (see 02_PREREGISTRATION §10).

## 7. Strategy boundary

NO entry/exit/stop optimization, NO Kelly, NO sizing, NO PF/Sharpe selection,
NO strategy mining, NO live deployment. This is terrain and mechanism research.
PASS here means "structurally distinct enough to deserve deeper mapping", not
"profitable".
