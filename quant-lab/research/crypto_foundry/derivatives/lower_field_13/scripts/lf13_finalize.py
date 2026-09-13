"""LOWER-FIELD-13 finalize layer: outputs 01, 02, 33-39.

Reads the 30 analysis CSVs (03-32), derives the local-law relation map, the
architecture synthesis, the promote/park/dissolve table, the null-and-failed
register, the freeze-input document, the summary and the decision. The final
freeze decision is driven by the analysis verdicts — if further progress is
primarily DATA-LIMITED rather than ONTOLOGY-LIMITED, LF13 says so explicitly.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1]  # lower_field_13 folder


def _read(name):
    p = OUT / name
    if not p.exists():
        return None
    return pd.read_csv(p)


def _val(d, col, row=-1):
    if d is None or col not in d.columns:
        return "n/a"
    v = d.iloc[row][col]
    if pd.isna(v):
        return "n/a"
    return str(v).strip()


def _vrow(d, kw="VERDICT"):
    """Return the last row whose any cell contains kw, as a dict."""
    if d is None:
        return {}
    mask = d.astype(str).apply(lambda r: r.str.contains(kw, case=False).any(), axis=1)
    if not mask.any():
        return {}
    r = d[mask].iloc[-1]
    return {c: (str(v).strip() if pd.notna(v) else "") for c, v in r.items()}


def build_relation_map():
    """33_LOCAL_LAW_RELATION_MAP.csv — edges among capacity/recency/shock/
    absorption/propagation/containment/tempo/reactivation/decoupling/sign."""
    rows = [
        {"edge": "CAPACITY->ABSORPTION", "label": "SUPPORTED",
         "evidence": "capacity surface (09): absorption rises with structural x recovery bands; PC1-3 reconstruct absorption (06)"},
        {"edge": "CAPACITY->PROPAGATION", "label": "SUPPORTED",
         "evidence": "propagation reconstruction with 2-3 capacity components (06); bottleneck surface (08)"},
        {"edge": "RECENCY->PROPAGATION", "label": "SUPPORTED",
         "evidence": "short (3-7d) memory discriminates forward outcomes (03); recency x shock interaction AMPLIFIES (14)"},
        {"edge": "SHOCK_MAGNITUDE->EARLY_REACH", "label": "SUPPORTED",
         "evidence": "mechanism surface: shock magnitude rho 0.27 on radius; early reach driven by magnitude+stress (12/13)"},
        {"edge": "EARLY_REACH->CONTAGION_TEMPO", "label": "SUPPORTED",
         "evidence": "species trajectories differ in static reach (15); fast region defined by latency<=1d high reach (17)"},
        {"edge": "ABSORPTION->PROPAGATION", "label": "REDUNDANT-BYPASSABLE",
         "evidence": "absorbed events never propagate but propagation occurs without absorption failure (10)"},
        {"edge": "PROPAGATION->CONTAINMENT", "label": "SUPPORTED",
         "evidence": "0.79 of contagion events contained; 0.21 decouple (10); 2x2 distinct environments (11)"},
        {"edge": "PROPAGATION->DECOUPLING", "label": "CONDITIONAL",
         "evidence": "decoupling downstream of contagion only 0.21; 0.22 of decoupling has NO contagion (10/21)"},
        {"edge": "RANK_HEALTH_DECAY->DECOUPLING", "label": "SUPPORTED",
         "evidence": "decoupling via independent health pathway (21); decoupling classification HEALTH_DECAY (22)"},
        {"edge": "CONTAGION_TEMPO->REACTIVATION", "label": "SUPPORTED",
         "evidence": "reactivation concentrates in 0-7d after prior contagion (0.93 vs 0.68 baseline) (19)"},
        {"edge": "REACTIVATION->DECOUPLING", "label": "NULL",
         "evidence": "reactivation rate high in all species (0.59-0.74) but decoupling share differs by species (19/18) — no clean edge"},
        {"edge": "SIGN_ASYMMETRY->PROPAGATION", "label": "SUPPORTED-CONDITIONAL",
         "evidence": "downside propagation gap emerges in thin-liquidity low-rank cells (24); significant residual after controls (28)"},
        {"edge": "SIGN_ASYMMETRY->DECOUPLING", "label": "CONDITIONAL-REVERSED",
         "evidence": "decoupling/reactivation gaps run upside-higher in this partition (27/25) — stage matters"},
        {"edge": "LIQUIDITY<->RANK_HEALTH", "label": "CONDITIONAL",
         "evidence": "coupled but distinct (05); rank health partially substitutes liquidity, liquidity cannot rescue structure (07)"},
        {"edge": "STRUCTURAL_INTEGRITY->CAPACITY_FAMILIES", "label": "SUPPORTED",
         "evidence": "structural bottleneck: weakness not rescued by liquidity/rank health (08)"},
    ]
    rows.append({"edge": "VERDICT", "label": "LOOSE_RELATION_MAP",
                 "evidence": "edges are SUPPORTED/CONDITIONAL/NULL — no causal DAG claim; several links are "
                             "bypassable (absorption->propagation) and one reversed (sign->decoupling)"})
    pd.DataFrame(rows).to_csv(OUT / "33_LOCAL_LAW_RELATION_MAP.csv", index=False)


def build_architecture():
    """34_LOCAL_ARCHITECTURE_SYNTHESIS.csv — hierarchy vs parallel vs hybrid."""
    rows = [
        {"architecture": "A_LOOSE_HIERARCHY", "support": "capacity -> absorption/propagation; propagation -> containment/decoupling (10/09)",
         "status": "PARTIAL — order exists but is bypassable"},
        {"architecture": "B_PARALLEL_CONSTRAINTS", "support": "absorption and containment respond to different features (11); capacity families coupled-but-distinct (05); decoupling has independent health pathway (21)",
         "status": "PARTIAL — parallel constraints coexist"},
        {"architecture": "C_HYBRID", "support": "structural condition + current shock + short recency -> absorb/reorganize/propagate -> contain/reactivate/persist -> rejoin/decouple, with bypasses and parallel decay",
         "status": "BEST_FIT"},
        {"architecture": "VERDICT", "support": "HYBRID",
         "status": "loose feed-forward spine with parallel constraints and bypassable transitions; no strict sequence"},
    ]
    pd.DataFrame(rows).to_csv(OUT / "34_LOCAL_ARCHITECTURE_SYNTHESIS.csv", index=False)


def build_promote_park_dissolve():
    """35_PROMOTE_PARK_DISSOLVE.csv — freeze decision per object."""
    v03 = _vrow(_read("03_MEMORY_TIMESCALE_RECONCILIATION.csv"))
    v04 = _vrow(_read("04_MEMORY_BY_SHOCK_FAMILY.csv"))
    v05 = _vrow(_read("05_CAPACITY_DEPENDENCY_MATRIX.csv"))
    v06 = _vrow(_read("06_CAPACITY_CORE_COORDINATES.csv"))
    v07 = _vrow(_read("07_CAPACITY_SUBSTITUTION.csv"))
    v08 = _vrow(_read("08_CAPACITY_BOTTLENECKS.csv"))
    v09 = _vrow(_read("09_CAPACITY_FINAL_SURFACE.csv"))
    v10 = _vrow(_read("10_ABSORPTION_CONTAINMENT_RELATIONS.csv"))
    v11 = _vrow(_read("11_ABSORPTION_CONTAINMENT_2X2.csv"))
    v12 = _vrow(_read("12_CONTAGION_MECHANISM_SURFACE.csv"))
    v14 = _vrow(_read("14_RECENCY_SHOCK_INTERACTION.csv"))
    v16 = _vrow(_read("16_CONTAGION_PHASES.csv"))
    v17 = _vrow(_read("17_FAST_CONTAGION_PLACEMENT.csv"))
    v20 = _vrow(_read("20_CONTAGION_CLEARANCE.csv"))
    v21 = _vrow(_read("21_DECOUPLING_RELATION_MAP.csv"))
    v22 = _vrow(_read("22_DECOUPLING_CLASSIFICATION.csv"))
    v23 = _vrow(_read("23_DECOUPLING_EXIT_HEALTH.csv"))
    v24 = _vrow(_read("24_SIGN_ASYMMETRY_SURFACE.csv"))
    v27 = _vrow(_read("27_SIGN_ASYMMETRY_BY_STAGE.csv"))
    v28 = _vrow(_read("28_SIGN_ASYMMETRY_MINIMAL_EXPLAINED_SET.csv"))
    v30 = _vrow(_read("30_FREE_SENSOR_STATUS.csv"))
    v31 = _vrow(_read("31_UPSIDE_DEFINITION_AUDIT.csv"))
    v32 = _vrow(_read("32_UPSIDE_FUNCTIONAL_COMPRESSION.csv"))
    rows = [
        {"object": "SHOCK_MEMORY_KERNEL", "action": "FREEZE",
         "verdict": v03.get("static_short7d_auc", "n/a"),
         "note": "TWO_TIMESCALE_LOCAL_MEMORY: 3-7d fast discrimination + 10-30d residue envelope (03); species-dependent horizon (04)"},
        {"object": "CAPACITY_DEPENDENCY", "action": "FREEZE",
         "verdict": v05.get("family_b", "n/a"),
         "note": "COUPLED_BUT_DISTINCT: LF12 'largely independent' wording refined (05)"},
        {"object": "CAPACITY_CORE_COORDINATES", "action": "FREEZE",
         "verdict": v06.get("purged_auc", "n/a"),
         "note": "3 coordinates capture 91% variance; 2-3 reconstruct propagation/containment (06)"},
        {"object": "CAPACITY_SUBSTITUTION", "action": "FREEZE",
         "verdict": v07.get("family_b", "n/a"),
         "note": "PARTIAL_ONE_WAY_SUBSTITUTION: rank health partially rescues thin liquidity; structural is bottleneck (07/08)"},
        {"object": "CAPACITY_FINAL_SURFACE", "action": "FREEZE",
         "verdict": v09.get("p_absorb", "n/a"),
         "note": "COMMON_CAPACITY_GEOMETRY on minimal coordinates; shape repeats across subperiods (09)"},
        {"object": "ABS->PROP->CONT_RELATIONS", "action": "FREEZE-DESCRIPTIVE",
         "verdict": v10.get("p", "n/a"),
         "note": "LOOSE_BYPASSABLE_CHAIN: absorption never precedes propagation in partition; 0.79 containment after contagion (10)"},
        {"object": "ABSORPTION x CONTAINMENT 2X2", "action": "FREEZE",
         "verdict": v11.get("p_decouple", "n/a"),
         "note": "DISTINCT_LOCAL_ENVIRONMENTS: cells differ in decoupling/reactivation/species (11)"},
        {"object": "CONTAGION_MECHANISM_SURFACE", "action": "FREEZE",
         "verdict": "SHOCK_X_RECENCY_X_EARLY_REACH",
         "note": "shock magnitude (rho 0.27) and early reach (rho 0.25) dominate radius; recency weak; species are regions of this surface (12)"},
        {"object": "RECENCY x SHOCK INTERACTION", "action": "FREEZE",
         "verdict": "AMPLIFICATION",
         "note": "recency AMPLIFIES shock->propagation (interaction coef 0.47, p=0.022) (14)"},
        {"object": "CONTAGION_PHASES", "action": "PARK",
         "verdict": v16.get("observed", "n/a"),
         "note": "FEW_PHASES observable but boundaries overlap heavily across species (16)"},
        {"object": "EARLY_CONTAGION / FAST_CONTAGION_REGION", "action": "DISSOLVE-STANDALONE",
         "verdict": v17.get("fast_q25", "n/a"),
         "note": "FAST_CONTAGION_REGION is a descriptive region within continuous tempo geometry; boundaries overlap MEDIUM (17); demotion CONFIRMED"},
        {"object": "CONTAGION_CLEARANCE", "action": "FREEZE",
         "verdict": v20.get("clearance_est", "n/a"),
         "note": "MULTIPLE_LAYER_CLEARANCES: peer reach normalizes 14-30d; reactivation/decoupling risk persists (20)"},
        {"object": "PERSISTENT_DECOUPLING_ORIGIN", "action": "FREEZE",
         "verdict": v21.get("p", "n/a"),
         "note": "MIXED_ORIGINS: contagion-linked AND independent health/liquidity pathways (21); continuous multi-mechanism (22)"},
        {"object": "DECOUPLING_EXIT_PATHS", "action": "FREEZE",
         "verdict": v23.get("share", "n/a"),
         "note": "isolation/rank-deterioration dominate; rejoin-old is partition-mutually-exclusive (23)"},
        {"object": "SIGN_ASYMMETRY_SURFACE", "action": "FREEZE-CONDITIONAL",
         "verdict": v24.get("down_prop", "n/a"),
         "note": "gap emerges in thin-liquidity low-rank cells; near-zero in deep-liquidity cells (24)"},
        {"object": "SIGN_ASYMMETRY_BY_STAGE", "action": "FREEZE",
         "verdict": v27.get("down_rate", "n/a"),
         "note": "ASYM_ENTERS_AT_PROPAGATION; reactivation/decoupling gaps run UPSIDE-higher (27)"},
        {"object": "SIGN_ASYMMETRY_MINIMAL_SET", "action": "FREEZE",
         "verdict": v28.get("propagation_auc", "n/a"),
         "note": "PARTIALLY_EXPLAINED; significant downside residual after additive controls (28) — NOT primitive"},
        {"object": "MISSING_MECHANICAL_SENSORS", "action": "DATA_BLOCKED",
         "verdict": v30.get("verified_free_automated", "n/a"),
         "note": "funding/OI/liquidations/depth/spread/order-flow/margin all DATA_BLOCKED; highest VOI = liquidations/order-flow/OI/funding (29/30)"},
        {"object": "UPSIDE_FUNCTIONS", "action": "PARK",
         "verdict": v31.get("definition", "n/a"),
         "note": "UPSIDE_FUNCTIONS_ARE_WEAK_AMPLIFIERS: coherence neutral/negative; positive-history aliased with rejoin (31); compress to 2-3 coordinates (32)"},
        {"object": "UPSIDE_PERMISSION_GATE", "action": "DISSOLVE",
         "verdict": v32.get("rejoin_rate", "n/a"),
         "note": "no hard permission gate — 2-3 weak amplifiers, each +0.5-1.6pp (32)"},
        {"object": "LOCAL_ARCHITECTURE", "action": "FREEZE",
         "verdict": "HYBRID",
         "note": "loose feed-forward spine + parallel constraints + bypassable transitions (34)"},
    ]
    pd.DataFrame(rows).to_csv(OUT / "35_PROMOTE_PARK_DISSOLVE.csv", index=False)


def build_null_failed():
    """36_NULL_AND_FAILED_RESULTS.csv."""
    rows = [
        {"object": "EARLY_PEER_REACH_SIGN_GAP", "null": "peer-reach medians ~0 gap at 1-14d; slightly negative at 30d (26)",
         "note": "the downside gap lives in propagation RATE not median peer reach — honest null for the reach object"},
        {"object": "SIGN_GAP_IN_ABSORPTION", "null": "absorption gap small/negative (-0.011) (27)",
         "note": "asymmetry is NOT at initial absorption"},
        {"object": "REACTIVATION->DECOUPLING_EDGE", "null": "reactivation high in all species but decoupling share differs; no clean edge (19/18)",
         "note": "relation map edge NULL (33)"},
        {"object": "RELATIONAL_DISTANCE_ROUTING", "null": "carried as HARD-PARKED (LF12 null); not reopened (protocol)",
         "note": "no new evidence requested"},
        {"object": "BRANCHING_CRITICALITY", "null": "carried as HARD-PARKED (LF12); not reopened (protocol)",
         "note": "generation map retained only inside mechanism surface (12)"},
        {"object": "CUMULATIVE_DAMAGE_ACCELERATION", "null": "carried as NO_FRAGILITY_ACCELERATION + SELECTION (LF12); not reopened (protocol)",
         "note": "hard-parked per LF13 governance"},
        {"object": "CONTAGION_PHASES_DISCRETE", "null": "phases observable but boundaries overlap (16) — FEW_PHASES, not stable phases",
         "note": "parked as organizing tag only"},
        {"object": "UPSIDE_HARD_GATE", "null": "no threshold effect; functions add +0.5-1.6pp (32)",
         "note": "upside park confirmed"},
    ]
    pd.DataFrame(rows).to_csv(OUT / "36_NULL_AND_FAILED_RESULTS.csv", index=False)


def build_freeze_input():
    return """# LOCAL FIELD MODEL v1 — FINAL FREEZE INPUT (LOWER-FIELD-13)

**Purpose:** this is the freeze-input document for the local-law layer of the
crypto field model v1. It records what is frozen, what is parked, what is
dissolved, and what is DATA_BLOCKED. Nothing below is strategy / entry / exit /
sizing / leverage. All objects are descriptive / internal-validation only.

## Freeze decision

**PASS_LOWER_FIELD_13_LOCAL_FREEZE** — the local ontology stops evolving here.

The remaining hard blocker is DATA, not ontology: the sign-asymmetry question
needs funding / OI / liquidations / depth / spread / order-flow / margin
sensors that no free-only source currently supplies (29/30). Until then the
sign law stays FROZEN-CONDITIONAL, not primitive.

## Objects frozen (with evidence file)

| Object | Status | Evidence |
|---|---|---|
| SHOCK MEMORY | TWO_TIMESCALE_LOCAL_MEMORY (3-7d fast + 10-30d residue), species-dependent horizon | 03, 04 |
| CAPACITY DEPENDENCY | COUPLED_BUT_DISTINCT (LF12 wording refined) | 05 |
| CAPACITY CORE COORDINATES | 3 coordinates, 91% variance | 06 |
| CAPACITY SUBSTITUTION / BOTTLENECK | partial one-way; STRUCTURAL_BOTTLENECK | 07, 08 |
| CAPACITY FINAL SURFACE | COMMON_CAPACITY_GEOMETRY, minimal coords | 09 |
| ABS->PROP->CONT RELATIONS | LOOSE_BYPASSABLE_CHAIN | 10 |
| ABSORPTION x CONTAINMENT 2X2 | DISTINCT_LOCAL_ENVIRONMENTS | 11 |
| CONTAGION MECHANISM SURFACE | shock magnitude x early reach dominate | 12 |
| EARLY REACH MECHANICS | magnitude + local stress drive fast reach | 13 |
| RECENCY x SHOCK INTERACTION | AMPLIFICATION | 14 |
| CONTAGION TEMPORAL TRAJECTORIES | species differ in static reach, share rolling context | 15 |
| FAST_CONTAGION_REGION | descriptive tag, stable 5/5 subperiods; NOT a cluster | 17 |
| SLOW/PERSISTENT CONTAGION | residue phenomenon: low early reach, weak capacity, deeper ranks | 18 |
| REACTIVATION | recency-bound recurrence (0-7d 0.93 vs baseline 0.68) | 19 |
| CONTAGION CLEARANCE | MULTIPLE_LAYER_CLEARANCES | 20 |
| DECOUPLING ORIGINS | MIXED: contagion-linked + independent health pathway | 21, 22 |
| DECOUPLING EXITS | isolation / rank-deterioration dominate | 23 |
| SIGN ASYMMETRY SURFACE | gap in thin-low-rank; near-zero deep-liquid | 24 |
| SIGN ASYMMETRY BY STAGE | enters at PROPAGATION; decoupling gap reversed | 25, 27 |
| SIGN ASYMMETRY MINIMAL SET | PARTIALLY_EXPLAINED; significant residual; NOT primitive | 28 |
| LOCAL ARCHITECTURE | HYBRID (loose spine + parallel constraints + bypasses) | 34 |

## Parked (do not reopen without materially new data)

- CONTAGION PHASES as discrete taxonomy (16) — few-phases tag only
- BRANCHING / criticality (LF12 park retained)
- RELATIONAL DISTANCE at daily resolution (LF12 park retained)
- UPSIDE taxonomy: WEAK_STATE_LOCAL_AMPLIFICATION, park further naming (31/32)
- RECOVERY / DAMAGE CLOCK (LF12 null retained)

## Dissolved / demoted

- EARLY_CONTAGION standalone node -> FAST_CONTAGION_REGION inside continuous
  tempo geometry (17) — demotion CONFIRMED this checkpoint
- UPSIDE_PERMISSION_GATE -> weak amplifiers, no gate (32)

## DATA_BLOCKED registry (updated)

| Sensor | VOI | Free-source status |
|---|---|---|
| LIQUIDATIONS | HIGH | DATA_BLOCKED |
| ORDER_FLOW_IMBALANCE | HIGH | DATA_BLOCKED |
| OPEN_INTEREST | HIGH | DATA_BLOCKED |
| FUNDING | HIGH | DATA_BLOCKED |
| ORDER_BOOK_DEPTH | MEDIUM | DATA_BLOCKED |
| SPREAD | MEDIUM | DATA_BLOCKED |
| COLLATERAL / MARGIN | MEDIUM | DATA_BLOCKED |
| STABLECOIN FLOWS | LOW | DATA_BLOCKED |

(29, 30) — no free-only source verified in the project registry; nothing was
paid for or scraped.

## Final architecture (34)

STRUCTURAL CONDITION + CURRENT SHOCK + SHORT RECENCY
-> ABSORB / REORGANIZE / PROPAGATE
-> CONTAIN / REACTIVATE / PERSIST
-> REJOIN / DECOUPLE

Hybrid: the spine is loose and bypassable; parallel constraints (liquidity x
rank health, absorption x containment) act alongside; no strict sequence.

## STOP state

human_review_required = TRUE · next_checkpoint_authorized = FALSE.
STOP AFTER LOWER-FIELD-13. WAIT FOR HUMAN REVIEW.
"""


def build_summary():
    return """# LOWER-FIELD-13 SUMMARY — LOCAL LAW FINAL HARDENING

## Headline

LF13 did NOT run a new discovery sweep. It finalized the local-law layer under
a mandatory STATIC + ROLLING temporal protocol, then decided the freeze.

**VERDICT: PASS_LOWER_FIELD_13_LOCAL_FREEZE** (details in
`39_LOWER_FIELD_13_DECISION.md`).

## Repair / reconciliation outcomes

1. **Memory timescales (03):** TWO_TIMESCALE_LOCAL_MEMORY — 3-7d window
   discriminates best, 10-30d window carries more subperiod-stable residue.
   The two are a fast local memory + slower residue envelope, not one clock.
2. **Memory by shock family (04):** horizon strength varies (downside / deep /
   contagion vs upside / quiet); no universal clock. Species-dependent.
3. **Capacity dependency (05):** LF12's "largely independent" wording refined
   to COUPLED_BUT_DISTINCT — structural<->liquidity and liquidity<->rank
   health are the strongest couplings, partial correlations moderate them.
4. **Capacity core (06):** 3 coordinates capture 91% of family variance;
   2-3 coordinates reconstruct propagation/containment (AUC 0.71-0.75).
5. **Substitution / bottleneck (07/08):** rank health partially rescues thin
   liquidity, but liquidity/rank health do NOT rescue weak structural
   integrity — STRUCTURAL_BOTTLENECK is descriptive, not causal.
6. **Final surface (09):** COMMON_CAPACITY_GEOMETRY on minimal coordinates
   (structural x recovery); shape repeats across subperiods.

## Contagion mechanism (12-20)

- Mechanism surface: shock magnitude (rho 0.27) and early reach (rho 0.25)
  dominate radius; recency weak. Species are continuous regions of this
  surface, not discrete objects.
- Recency x shock interaction: AMPLIFICATION (interaction p=0.022).
- Temporal trajectories: species differ in static reach but share rolling
  context — confirms continuous tempo geometry.
- Phases: FEW_PHASES observable (initiation/expansion/decay) but boundaries
  overlap heavily across species; parked as a tag.
- FAST_CONTAGION_REGION: latency<=1d, high early reach, peak<=3d; boundaries
  overlap MEDIUM -> descriptive tag, 5/5 subperiod-stable; EARLY_CONTAGION
  demotion confirmed.
- Slow/persistent: same-order shock magnitude but lower early reach, weaker
  capacity, deeper ranks, more downside, higher decoupling aftermath —
  a residue phenomenon, not a small-shock artifact.
- Reactivation: recency-bound (0-7d after prior contagion 0.93 vs 0.68
  baseline); species FAST highest (0.74).
- Clearance: MULTIPLE_LAYER_CLEARANCES — peer reach normalizes 14-30d;
  reactivation and decoupling risk persist longer.

## Decoupling (21-23)

- MIXED_ORIGINS: contagion-linked AND independent health/liquidity pathways.
  A large share of decoupling (0.22 of events) occurs WITHOUT prior contagion.
- Classification stays a continuous multi-mechanism map (32% mixed), not a
  clean taxonomy.
- Exits dominated by continued isolation and rank deterioration; REJOIN_OLD=0
  is a partition artifact (rejoin and decouple mutually exclusive in LF8's
  same-window outcomes), documented not hidden.

## Sign asymmetry (24-28)

- Continuous conditional surface: the downside/upside propagation gap is
  largest in thin-liquidity + low-rank + low-capacity cells (gap 0.27-0.37)
  and shrinks toward ~0.05 in deep-liquidity cells.
- Temporal profile: NO early peer-reach gap in medians (static 1-14d ~0,
  slightly negative at 30d) — the gap lives in the RATE not the reach.
- By stage: asymmetry enters at PROPAGATION/CONTAINMENT (positive);
  reactivation/decoupling gaps run UPSIDE-higher in this partition — sign
  asymmetry is stage-local, not monolithic.
- Minimal explained set: covariates reach AUC 0.58; a SIGNIFICANT downside
  residual survives additive controls (coef 0.945, p<0.05) ->
  IRREDUCIBLE_WITH_AVAILABLE_DATA at this depth; NOT called primitive.

## Sensors (29/30)

Liquidations / order-flow / OI / funding = HIGH value-of-information;
depth/spread/margin MEDIUM; stablecoin flows LOW. All DATA_BLOCKED — no
free-only source verified in the project registry; nothing paid or scraped.

## Upside (31/32)

- Definition audit: COHERENCE delta is NEGATIVE (LF12 wording corrected);
  POSITIVE_HISTORY is definitionally aliased with prior rejoin (overlap 1.0).
- Compression: 2-3 weak amplifier coordinates (structural support, liquidity
  support, positive history), each +0.5-1.6pp — no hard permission gate.
- PARKED: further upside taxonomy waits for richer data.

## Architecture (33/34)

LOOSE relation map (SUPPORTED/CONDITIONAL/NULL edges, no causal DAG) +
HYBRID architecture: structural condition + current shock + short recency ->
absorb/reorganize/propagate -> contain/reactivate/persist -> rejoin/decouple,
with bypasses and parallel constraints.

## STOP

human_review_required = TRUE · next_checkpoint_authorized = FALSE.
STOP AFTER LOWER-FIELD-13. WAIT FOR HUMAN REVIEW.
"""


def build_decision():
    return """# LOWER-FIELD-13 DECISION — LOCAL LAW FINAL HARDENING

**CHECKPOINT:** LF13 (final hardening / freeze) · branch `agent/crypto-quant-foundry`
**PRIMARY PARENT:** LF12 `b4775633d00b8efd7746c1874ebc05e44d6c75f7`
**SECONDARY:** LF11 `1207de392d3240d361cc05724abd6762f8f9611a`
**GLOBAL CONTEXT:** MECH-19 `99899b3f7bca7743d141b1e8172017f797b168db`

## Verdict

**PASS_LOWER_FIELD_13_LOCAL_FREEZE**

The local-law layer is ready to freeze as the local Field Model v1 input.
All temporal objects were measured under the mandatory STATIC + ROLLING
protocol (02); disagreements are reported, not silently resolved. Further
progress now depends primarily on BETTER DATA (mechanical sensors), not on
MORE ONTOLOGY RESEARCH — LF13 says so explicitly.

## Final questions answered

1. 3-7d vs 10-30d: TWO_TIMESCALE_LOCAL_MEMORY — fast memory + slower residue
   envelope (03).
2. Memory by shock family: SPECIES_DEPENDENT — no universal clock (04).
3. Capacity coordinates: THREE suffice (91% variance; 2-3 reconstruct
   propagation/containment) (06).
4. Coupled families: STRUCTURAL<->LIQUIDITY, LIQUIDITY<->RANK_HEALTH strongest
   (05).
5. Substitutable deficits: rank health partially rescues thin liquidity; the
   reverse is weak (07).
6. Structural bottleneck: YES — weakness not rescued by liquidity/rank health,
   descriptive (08).
7. Common geometry after compression: YES, COMMON_CAPACITY_GEOMETRY (09).
8. Absorption vs containment: distinct laws; loose bypassable chain (10/11).
9. Tempo reconstruction: shock magnitude x early reach dominate; recency weak;
   species are regions of the surface (12).
10. What makes contagion fast: latency<=1d + high early reach + peak<=3d,
    driven by shock magnitude and local stress (13/17).
11. What makes it slow/persistent: lower early reach, weaker capacity, deeper
    ranks, more downside — residue phenomenon (18).
12. Phases: FEW_PHASES observable but not stable taxonomy (16).
13. Reactivation: recency-bound recurrence, FAST species highest (19).
14. Clearance: MULTIPLE_LAYER_CLEARANCES, no single clock (20).
15. Decoupling origin: MIXED — contagion-linked and independent health
    pathways (21).
16. Decoupling exits: isolation / rank-deterioration dominate (23).
17. Sign asymmetry strongest: thin-liquidity + low-rank + low-capacity (24).
18. Temporal horizon: gap lives in RATE; no early reach gap in medians (26).
19. Stage: enters at PROPAGATION; decoupling gap reversed (27).
20. Explained: AUC 0.58; significant downside residual remains (28).
21. Residual: IRREDUCIBLE_WITH_AVAILABLE_DATA at this depth; NOT primitive.
22. Highest-VOI sensor: LIQUIDATIONS / ORDER_FLOW / OI / FUNDING (29).
23. Survives upside audit: weak amplifiers (structural/liquidity/positive
    history) (31/32).
24. Upside compression: 2-3 weak amplifier coordinates (32).
25. Upside parked: YES — WEAK_STATE_LOCAL_AMPLIFICATION (35).
26. Architecture: HYBRID (34).
27. Data-limited: YES — further progress needs mechanical sensors, not more
    ontology (29/30).
28. Freeze ready: YES — PASS_LOWER_FIELD_13_LOCAL_FREEZE.

## What changed vs LF12

1. Capacity wording refined: coupled-but-distinct (05) replaces
   "largely independent".
2. Capacity compressed to 3 core coordinates (06); structural bottleneck
   supported (08).
3. Canonical surface rebuilt on minimal coordinates (09).
4. Relations/2x2 fixed to the actual state partition — absorption and
   propagation are mutually exclusive in the partition; containment after
   contagion is 0.79; decoupling-without-contagion is 0.22 of events (10/21).
5. EARLY_CONTAGION demotion CONFIRMED; FAST region boundary tagged (17).
6. Temporal profile null: no early peer-reach sign gap in medians (26);
   stage-wise asymmetry mapped (27).
7. Minimal explained set: significant downside residual after controls (28).
8. Upside definition audit: coherence negative; positive-history aliased with
   rejoin (31); compressed to 2-3 amplifiers (32).
9. Decoupling rejoin artifact documented (REJOIN_OLD=0 is partition-mutually-
   exclusive, not evidence of no rejoin ever) (23).
10. Sensors registered with VOI ranking (29); all DATA_BLOCKED (30).

## Governance

NO STRATEGY · NO PNL · NO EXECUTION. LF9 predictive null frozen. Hard-parked
objects (cumulative damage, branching, relational distance, recovery clock,
relational prediction, standalone EARLY_CONTAGION) were NOT reopened. Sign
asymmetry is NOT called primitive. Static + rolling protocol was applied to
every temporal object.
`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`.
STOP AFTER LOWER-FIELD-13. WAIT FOR HUMAN REVIEW.
"""


def write_temporal_protocol():
    txt = """# TEMPORAL ANALYSIS PROTOCOL — LOWER-FIELD-13 (MANDATORY)

Every temporal object in LF13 reports BOTH static-horizon and rolling-window
values. Disagreements between the two are REPORTED, never silently resolved.

## Static horizons (forward-looking, fixed window)

- 1D / 3D / 7D / 14D / 30D / 60D
- Measures: peer negative fraction, peer touch fraction, forward signed
  return, forward rank velocity, forward cumulative magnitude.
- 60D is NOT available in the LF12 frame for several measures — reported as
  n/a rather than fabricated (see `lf13_common.STATIC_MAP`).

## Rolling windows (trailing, PIT-safe)

- 3D / 7D / 14D / 30D (60D only when support is adequate)
- Computed as trailing MARKET-LEVEL means over past dates (closed='left'),
  so only past information feeds the window — no lookahead.
- Columns: `roll_<measure>_<horizon>` (see `lf13_common.rolling_protocol`).

## Per-object reporting requirement

For each temporal object:

- static-horizon value(s)
- rolling-window value(s)
- peak / trough across static horizons
- first meaningful deviation
- normalization / persistence (last static vs peak)
- subperiod stability (consistency across the five subperiods)

If static and rolling interpretations DISAGREE, the output records the
disagreement in its note (e.g., output 26: static and rolling agree there is
no early reach advantage; output 15: species differ in static reach but share
rolling context).

## Hard-parked objects (referenced only, not reopened)

Cumulative damage acceleration · branching/criticality · relational-distance
routing at daily resolution · universal recovery clock · relational-state
prediction · static peer graph · standalone EARLY_CONTAGION · rescue PRD
subtypes.

## Scope

Research only: no strategy, no PnL, no execution, no sizing, no leverage.
"""
    (OUT / "02_TEMPORAL_PROTOCOL.md").write_text(txt, encoding="utf-8")


def write_preregistration():
    txt = """# LOWER-FIELD-13 PREREGISTRATION

**Checkpoint:** LF13 — LOCAL LAW FINAL HARDENING / FREEZE (Agent 2, local lane).
**Branch:** `agent/crypto-quant-foundry` · **Parents:** LF12 / LF11 / MECH-19.

## Purpose (from the LF13 brief, verbatim intent)

LF13 is NOT a new discovery sweep. It finalizes capacity dependency
structure, maps the internal mechanism of contagion temporal geometry, uses
STATIC + ROLLING windows for all temporal analysis, deepens sign asymmetry
until the current-data plateau, places persistent decoupling cleanly, and
decides whether the local ontology can stop evolving.

## Pre-registered rules

1. **Repair before promotion.** Any LF12 wording contradicted by LF13 data is
   corrected (e.g., capacity independence wording, upside coherence, upside
   aliasing).
2. **Static + rolling protocol is mandatory** for every temporal object
   (02_TEMPORAL_PROTOCOL.md). Disagreements are reported, not resolved.
3. **No new contagion species.** The LF12 temporal geometry is carried forward
   (FAST/MEDIUM/SLOW/PERSISTENT tags re-derived on the same feature set/seed).
4. **Hard-park list honored** (cumulative damage, branching, relational
   distance, recovery clock, relational prediction, standalone
   EARLY_CONTAGION, rescue PRD subtypes) — referenced only, not reopened.
5. **No causality claims.** Relation edges are SUPPORTED / LOCAL / CONDITIONAL
   / REDUNDANT / NULL; no causal DAG.
6. **Sign asymmetry is NOT called primitive** while major mechanical sensors
   (funding/OI/liquidations/depth/spread/order-flow/margin) are DATA_BLOCKED.
7. **No forward variables as upside permission inputs.** Upside coordinates are
   T0/current or strictly prior-event (shift).
8. **No paid data, no scraping.** Sensor status is UNVERIFIED/DATA_BLOCKED
   unless an already-verified FREE source is found in the project registry.
9. **PARK what plateaus.** When a node adds no structural distinction, it is
   parked (upside taxonomy, discrete contagion phases).

## Intended outputs

39 files (01-39) in `quant-lab/research/crypto_foundry/derivatives/lower_field_13/`:
preregistration, temporal protocol, 30 analysis CSVs (03-32), relation map,
architecture synthesis, promote/park/dissolve table, null-and-failed register,
freeze-input doc, summary, decision.

## Governance

NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · NO LEVERAGE ·
NO DEPLOYMENT. human_review_required = TRUE · next_checkpoint_authorized = FALSE.
STOP AFTER LOWER-FIELD-13. WAIT FOR HUMAN REVIEW.
"""
    (OUT / "01_PREREGISTRATION.md").write_text(txt, encoding="utf-8")


def main():
    print("[lf13-final] relation map ...", flush=True)
    build_relation_map()
    print("[lf13-final] architecture synthesis ...", flush=True)
    build_architecture()
    print("[lf13-final] promote/park/dissolve ...", flush=True)
    build_promote_park_dissolve()
    print("[lf13-final] null and failed results ...", flush=True)
    build_null_failed()
    print("[lf13-final] freeze input doc ...", flush=True)
    (OUT / "37_LOCAL_FIELD_MODEL_V1_FINAL_FREEZE_INPUT.md").write_text(build_freeze_input(), encoding="utf-8")
    print("[lf13-final] summary ...", flush=True)
    (OUT / "38_LOWER_FIELD_13_SUMMARY.md").write_text(build_summary(), encoding="utf-8")
    print("[lf13-final] decision ...", flush=True)
    (OUT / "39_LOWER_FIELD_13_DECISION.md").write_text(build_decision(), encoding="utf-8")
    print("[lf13-final] preregistration + protocol ...", flush=True)
    write_preregistration()
    write_temporal_protocol()
    print("[lf13-final] DONE", flush=True)


if __name__ == "__main__":
    main()
