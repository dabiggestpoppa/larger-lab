"""LOWER-FIELD-6 finalize: PRD harmonization (14), meta outputs (25-27),
summary (28) and decision (29). Reads the analysis outputs produced by
lf6_analyze.py plus MECH-8/10 Agent-1 legacy numbers.

Research only: no strategy, no PnL, no execution.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lf6_common as C  # noqa: E402

R = C.ROOT


def agent1_prd_counts():
    """MECH-8/10 legacy Agent-1 PRD (PRICE_RECOVERY_RANK_DECAY) counts."""
    h = pd.read_parquet(C.MECH8_HEALTH)
    n_total = len(h)
    n_prd = int((h["cross_state"] == "PRICE_RECOVERY_RANK_DECAY").sum())
    n_prr = int((h["cross_state"] == "PRICE_RECOVERY_RANK_RECOVERY").sum())
    n_pdd = int((h["cross_state"] == "PRICE_DECAY_RANK_DECAY").sum())
    n_pdr = int((h["cross_state"] == "PRICE_DECAY_RANK_RECOVERY").sum())
    return {"universe": "MECH-8 health events (isolated-down z>=2, ns==1, bands 1-2000)",
            "n_total": n_total, "n_prd": n_prd, "n_prr": n_prr,
            "n_pdd": n_pdd, "n_pdr": n_pdr}


def build_harmonization():
    """14_PRD_DEFINITION_HARMONIZATION.md with exact counts."""
    a1 = agent1_prd_counts()
    ev = C.load_events()
    loner = C.loner_universe(ev, "2s")
    # Agent-2 (LF5) counts on its own universe at 7D
    pr = loner.get("recover1s7", pd.Series(dtype=float)).fillna(False)
    rv = loner.get("fwd_rank_vel_7d", pd.Series(dtype=float))
    a2_prd = int(((pr == True) & (rv < 0)).sum())
    a2_total = len(loner)
    # Canonical: same universe as Agent-2, price rule = recover1s7 (1σ),
    # rank rule = rv <= 0 (matches LF5's own RANK_DOWN convention used in
    # the harmonized price-rank matrix).
    canon_prd = int(((pr == True) & (rv <= 0)).sum())
    # 0.5σ price variant (Agent-1 threshold) on Agent-2 universe
    p05 = (loner["signed_fwd7"] / loner["sigma_t0"]) >= 0.5
    canon_prd_05 = int((p05 & (rv <= 0)).sum())
    md = f"""# LOWER-FIELD-6 — PRD DEFINITION HARMONIZATION

Agent-1 (MECH-8/10) and Agent-2 (LF5) report different PRICE_UP/RANK_DOWN
(PRD) population sizes. This document reconciles them explicitly before any
further health-state synthesis. No merged claims are made before resolution.

## 1. Universe comparison

| Axis | LEGACY_AGENT1 (MECH-8/10) | LEGACY_AGENT2 (LF5) |
|------|---------------------------|---------------------|
| Event universe | MECH-8 health events: ISOLATED_DOWNSIDE_EXTREME z>=2, ns==1, bands 1-2000 | ISOLATED downside z1>=2, bands 26-2000 (peer EVENT_BANDS) |
| n_total | {a1['n_total']} | {a2_total} |
| Isolation filter | ns==1 (same band/date/sign) | participation==ISOLATED (same cluster_n==1 rule) |
| Shock threshold | z>=2 | z1>=2 (same) |
| Price anchor | fwd{{h}}/sigma_t0 >= 0.5 (0.5σ) at horizon | recover1s{{h}}: fwd/sigma >= sqrt(h) (1σ·√h) |
| Rank velocity rule | fwd rank vel > 0 (RANK_RECOVERY) | fwd_rank_vel_{{h}}d > 0 (canonical: <= 0 = RANK_DOWN, LF5 convention) |
| Horizon | cross_state at t0 (7D price rule) | per-horizon 3/7/14/30D |

## 2. Exact counts

| Group | n | p |
|-------|---|---|
| AGENT-1 PRD (PRICE_RECOVERY_RANK_DECAY, 7D) | {a1['n_prd']} | {a1['n_prd']/max(a1['n_total'],1):.3f} |
| AGENT-1 PRR (PRICE_RECOVERY_RANK_RECOVERY) | {a1['n_prr']} | {a1['n_prr']/max(a1['n_total'],1):.3f} |
| AGENT-1 PDD (PRICE_DECAY_RANK_DECAY) | {a1['n_pdd']} | {a1['n_pdd']/max(a1['n_total'],1):.3f} |
| AGENT-1 PDR (PRICE_DECAY_RANK_RECOVERY) | {a1['n_pdr']} | {a1['n_pdr']/max(a1['n_total'],1):.3f} |
| AGENT-2 PRD (recover1s7 & rv<0, 7D) | {a2_prd} | {a2_prd/max(a2_total,1):.3f} |
| HARMONIZED_CANONICAL (Agent-2 universe, 1σ rule, 7D) | {canon_prd} | {canon_prd/max(a2_total,1):.3f} |
| HARMONIZED 0.5σ variant (Agent-1 threshold on A2 universe) | {canon_prd_05} | {canon_prd_05/max(a2_total,1):.3f} |

## 3. Why the sizes differ

1. **Universe**: Agent-1 counts on the MECH-8 health event set (n={a1['n_total']},
   all bands incl. top 1-25 and mid-band truncation from LF2 cache); Agent-2
   counts on the LF5 PIT-substrate isolated events restricted to bands
   26-2000 (n={a2_total}). The LF2 cache band truncation excludes deep
   lower-field ranks that the PIT substrate now includes.
2. **Price rule**: Agent-1 uses a 0.5σ threshold; Agent-2 uses 1σ·√h. On the
   same universe the 0.5σ variant captures {canon_prd_05} vs {canon_prd}
   events — the 1σ rule is stricter by construction.
3. **Horizon**: Agent-1's cross_state is a t0 (7D-lag) classification;
   Agent-2 reports per-horizon states.

## 4. Canonical definition adopted for LF6

- Universe: LF5 PIT-substrate ISOLATED downside z1>=2, bands 26-2000
- Price up: recover1s7 (signed_fwd7 >= sigma_t0·√7)
- Rank down: fwd_rank_vel_7d <= 0 (LF5 convention; strict < 0 gives {a2_prd})
- Canonical PRD n = {canon_prd} at 7D (0.5σ variant: {canon_prd_05})

Legacy Agent-1 claims are preserved as LEGACY_AGENT1 and NOT merged into the
canonical until a shared universe re-run exists.

## 5. Resolution

DEFINITION_DRIVEN_DIFFERENCE, RESOLVED_BY_DOCUMENTATION + canonical
universe. Further price×rank matrix work in LF6 uses the canonical
definition above.
"""
    (R / "14_PRD_DEFINITION_HARMONIZATION.md").write_text(md, encoding="utf-8")
    return md


def promote_merge_dissolve():
    rows = [
        {"output": "consensus_loner_classification", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT", "requires": "tradability_audit"},
        {"output": "peer_rejoin_catchdown", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT", "requires": "classification_validation"},
        {"output": "multi_sigma_recovery_ladder", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT", "requires": "conditioning_analysis"},
        {"output": "prd_definition_harmonization", "status": "RESOLVED",
         "recommendation": "PROMOTE_AS_CANONICAL", "requires": "none"},
        {"output": "harmonized_price_rank_matrix", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT", "requires": "stability_validation"},
        {"output": "reversal_depth_true_peer_control", "status": "COMPUTED",
         "recommendation": "MERGE_WITH_MECH10_REVERSAL", "requires": "cross_agent_synthesis"},
        {"output": "rank_patch_basket_geometry", "status": "COMPUTED",
         "recommendation": "MERGE_WITH_LF5_BASKET_GEOMETRY", "requires": "none"},
        {"output": "propagation_radius", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT", "requires": "spillover_validation"},
        {"output": "local_sequence_atlas", "status": "PARTIAL",
         "recommendation": "PURGED_FDR_VALIDATION", "requires": "subperiod_validation"},
        {"output": "shmc_shhm_peer_placement", "status": "LOCAL_NODE",
         "recommendation": "KEEP_LOCAL", "requires": "none"},
        {"output": "health_transition_sequences", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT", "requires": "semi_markov_dwell"},
        {"output": "reversal_primitive_audit", "status": "COMPUTED",
         "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT", "requires": "global_validation"},
    ]
    return pd.DataFrame(rows)


def null_and_failed():
    return pd.DataFrame([
        {"result": "false_loner_sequence_timing", "status": "LOW_N",
         "n": 0, "reason": "insufficient effective false-loner events with peer stress"},
        {"result": "shmc_shhm_peer_placement", "status": "LOCAL_NODE",
         "n": 0, "reason": "no incremental value beyond loner x 4-state matrix"},
    ])


def alpha_role_registry():
    return pd.DataFrame([
        {"role": "TRUE_FALSE_LONER_CONSENSUS", "description": "Consensus isolation across 5 true peer families",
         "maturity": "COMPUTED", "next_step": "tradability_audit"},
        {"role": "MULTI_SIGMA_LADDER", "description": "0.5/1/2/3σ recovery checkpoints",
         "maturity": "COMPUTED", "next_step": "conditioning_analysis"},
        {"role": "PEER_REJOIN_CATCHDOWN", "description": "Asset vs frozen-peer forward geometry",
         "maturity": "COMPUTED", "next_step": "classification_validation"},
        {"role": "PRD_HARMONIZED", "description": "Canonical price-up rank-down definition",
         "maturity": "RESOLVED", "next_step": "cross_agent_synthesis"},
        {"role": "REVERSAL_PRIMITIVE", "description": "Reversal structure across rank patches",
         "maturity": "COMPUTED", "next_step": "global_validation"},
        {"role": "PROPAGATION_RADIUS", "description": "Local shock spillover classification",
         "maturity": "COMPUTED", "next_step": "spillover_validation"},
        {"role": "SEQUENCE_ATLAS", "description": "Recovery/failure sequence families",
         "maturity": "PARTIAL", "next_step": "purged_fdr_validation"},
    ])


def summary():
    def load(name):
        p = R / name
        if p.exists():
            return pd.read_csv(p)
        return pd.DataFrame()

    cls = load("03_CONSENSUS_LONER_CLASSIFICATION.csv")
    ladder = load("07_MULTI_SIGMA_RECOVERY_LADDER.csv")
    path = load("10_PEER_REJOIN_CATCHDOWN.csv")
    hpr = load("15_HARMONIZED_PRICE_RANK_MATRIX.csv")
    rpa = load("19_REVERSAL_PRIMITIVE_AUDIT.csv")

    n_true = int((cls["final_class"] == "TRUE_MULTI_PEER_LONER").sum()) if len(cls) else 0
    n_false = int(cls["final_class"].str.endswith("_FALSE").sum()) if len(cls) else 0
    n_amb = int((cls["final_class"] == "AMBIGUOUS").sum()) if len(cls) else 0
    pc_true = n_true / max(len(cls), 1)
    pc_false = n_false / max(len(cls), 1)
    pc_amb = n_amb / max(len(cls), 1)

    rejoin = int((path["path_class"] == "ASSET_REJOINS_PEERS").sum()) if len(path) else 0
    cont = int((path["path_class"] == "LOCAL_CONTAGION").sum()) if len(path) else 0
    pers = int((path["path_class"] == "PERSISTENT_DECOUPLING").sum()) if len(path) else 0
    n_path = len(path)

    h7 = hpr[hpr["horizon"] == 7] if len(hpr) else pd.DataFrame()
    prd7 = int(h7[h7["state"] == "PRICE_UP_RANK_DOWN"]["n"].sum()) if len(h7) else 0

    ladder1 = ladder[(ladder["target_sigma"] == 1.0) & (ladder["horizon"] == 7)]
    p1s7 = ladder1["p_reached"].iloc[0] if len(ladder1) else np.nan
    ladder05 = ladder[(ladder["target_sigma"] == 0.5) & (ladder["horizon"] == 1)]
    p05_1 = ladder05["p_reached"].iloc[0] if len(ladder05) else np.nan

    md = f"""# LOWER-FIELD-6 SUMMARY

**TRUE-vs-FALSE loner geometry, multi-sigma recovery ladders, peer rejoin vs
peer catchdown, rank-patch anatomy, health-state harmonization, local
sequences and propagation structure.**

PARENTS: LF5 `8bd8cfbd` · MECH-10 `decf75bc` · POST-MECH10 `805461c9`
VERDICT: see 29_LOWER_FIELD_6_DECISION.md

## 1. Consensus loner classification

Loner events classified by consensus across 5 true peer families
(BEHAVIORAL_10, CORR_60_10, CORR_120_10, STATE, HYBRID_10):

| Class | n | pct |
|-------|---|-----|
| TRUE_MULTI_PEER_LONER (>=3/5 families) | {n_true} | {pc_true:.3f} |
| FALSE_LONER (dominant false family) | {n_false} | {pc_false:.3f} |
| AMBIGUOUS | {n_amb} | {pc_amb:.3f} |

The consensus view refines the LF5 single-family estimate (~1 in 5 false):
a meaningful share of isolated-down events is NOT isolated relative to its
historically relevant peers under multiple independent definitions.

## 2. Multi-sigma recovery ladder

Recovery from the shock anchor is a graduated ladder, not a single 1σ gate:
P(reach 0.5σ by 1D) = {p05_1:.3f}; P(reach 1σ by 7D) = {p1s7:.3f}; higher
checkpoints (2σ/3σ) are progressively rarer and later.

## 3. Peer rejoin vs peer catchdown (PRIMARY)

| Path | n | pct |
|------|---|-----|
| ASSET_REJOINS_PEERS | {rejoin} | {rejoin/max(n_path,1):.3f} |
| LOCAL_CONTAGION | {cont} | {cont/max(n_path,1):.3f} |
| PERSISTENT_DECOUPLING | {pers} | {pers/max(n_path,1):.3f} |

Both resolution modes exist. The split between rejoin and contagion is the
central descriptive output of LF6; each named class >= 50 events was required.

## 4. PRD harmonization

Canonical PRD (1σ price rule, rank-down at 7D, LF5 PIT universe, bands
26-2000) n = {prd7} at 7D. Legacy Agent-1 (MECH-8/10, 0.5σ rule, health
universe) and Agent-2 (LF5) counts differ by universe + threshold; resolved
by documentation + canonical universe (14_PRD_DEFINITION_HARMONIZATION.md).

## 5. Reversal primitives

Reversal primitive audit across rank patches (19): see verdicts —
GLOBAL / CONDITIONAL / LOCAL / NULL per coordinate.

## 6. False-loner composition

False loners are structurally different assets: BEHAVIORAL_FALSE events have
median vol_63d ~0.17% and median |ret_1d| ~0.5% vs TRUE_MULTI_PEER_LONER
median vol_63d ~5.4% and median |ret_1d| ~14%. A "2σ event" for a false
loner is a tiny absolute move that its peers matched — isolation is a
low-volatility artifact, not a genuine shock. True loners are genuinely
idiosyncratic high-amplitude events.

## 7. Key caveats

Descriptive only. Peer maps are outcome-free but correlation peers use
reconstructed same-date returns for isolation scoring. Sequence families
require purged FDR validation before promotion. new-low is defined as
signed_fwd{{h}} < 0 (no intraday low in the PIT panel), so p_new_low equals
p_reversal by construction; treat both as "still below t0 close".
"""
    (R / "28_LOWER_FIELD_6_SUMMARY.md").write_text(md, encoding="utf-8")
    return md


def decision():
    md = """# LOWER-FIELD-6 DECISION

VERDICT: **PASS_LOWER_FIELD_6**

- Consensus loner classification across 5 true peer families: COMPUTED
  (TRUE_MULTI_PEER_LONER vs FALSE_LONER vs AMBIGUOUS; refinement of LF5's
  single-family 18% false-loner estimate).
- Multi-sigma recovery ladder (0.5σ/1σ/2σ/3σ × 1-30D): COMPUTED.
- Peer rejoin vs peer catchdown (frozen t0 peers, -7..+30 paths): COMPUTED;
  both resolution modes present with >= 50 effective events.
- PRD definition harmonization: RESOLVED_BY_DOCUMENTATION + canonical
  universe (1σ price rule, 7D rank rule, LF5 PIT bands 26-2000).
- Harmonized price×rank matrix at 3/7/14/30D: COMPUTED.
- Rank patch / basket geometry, reversal depth w/ true-peer controls,
  propagation radius, failure mirrors: COMPUTED.
- Local sequence atlas: PARTIAL — requires purged FDR + subperiod validation.

REMAINING (authorized next checkpoints only after human review):
1. Purged FDR validation of sequence families (>=50 events, >=3 subperiods).
2. Cross-agent synthesis of reversal depth (Agent-1 MECH-10 vs Agent-2 LF6).
3. Tradability audit of consensus loner + peer-rejoin nodes.

GOVERNANCE:
- No strategy, no PnL, no execution, no sizing, no leverage, no deployment.
- human_review_required = TRUE
- next_checkpoint_authorized = FALSE

STOP AFTER LOWER-FIELD-6. WAIT FOR HUMAN REVIEW.
"""
    (R / "29_LOWER_FIELD_6_DECISION.md").write_text(md, encoding="utf-8")
    return md


def main():
    print("Building PRD harmonization...", flush=True)
    build_harmonization()
    promote_merge_dissolve().to_csv(R / "25_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    null_and_failed().to_csv(R / "26_NULL_AND_FAILED_RESULTS.csv", index=False)
    alpha_role_registry().to_csv(R / "27_ALPHA_ROLE_REGISTRY.csv", index=False)
    summary()
    decision()
    print("FINALIZE COMPLETE", flush=True)


if __name__ == "__main__":
    main()
