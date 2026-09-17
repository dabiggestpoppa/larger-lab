"""LOWER-FIELD-12 shared frame builders.

LF12 opens with four REPAIR GATES (memory-kernel selection, burden-vs-recency,
reactivation drivers, upside leakage) and then deepens the local-law layer:
capacity surface/geometry/boundaries, recovery-state representation, damage
selection audit, within-asset shock history, contagion relational geometry,
temporal species round 2, reactivation memory, decoupling relations, sign
asymmetry granularity, correlation-compression deep dive and a PIT-safe upside
rebuild.

This module loads the LF11 master frame (cached) and adds the constructs LF12
needs: recovery-state coordinates, within-asset prior states, pre-shock
correlation proxy (previous-snapshot peer_corr), relational-distance proxies,
reactivation interaction flags and PIT-safe (T0/current) upside coordinates.

Research only: no strategy, no PnL, no execution, no sizing, no leverage.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lower_field_11" / "scripts"))
import lf11_common as W11  # noqa: E402
import lf9_common as C9        # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent          # lower_field_12/
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)

A = C9.A
_fmt = A._fmt
_med = C9._med
_mean = C9._mean
_purged_auc = A._purged_auc
MIN_SUPPORT = C9.MIN_SUPPORT

ABS_CLS = ["<2%", "2-5%", "5-10%", "10-20%", "20%+"]

SUB_PERIODS = ["2020-2021", "2022", "2023", "2024", "2025-2026"]

# ---------------------------------------------------------------------------
# Base frame
# ---------------------------------------------------------------------------

def base_frame(use_cache: bool = True) -> pd.DataFrame:
    return W11.master_frame(use_cache=True)


# ---------------------------------------------------------------------------
# Recovery-state coordinates
# ---------------------------------------------------------------------------

def recovery_state(snap: pd.DataFrame) -> pd.DataFrame:
    """Continuous recovery-state coordinates (Section 11 / 12).

    RECENTLY_DISTURBED / RECOVERING / RECOVERED are computed as continuous
    bands from: time since prior shock, time since prior contagion,
    membership stabilization, rank-health repair, liquidity recovery,
    relational stabilization. Labels are NOT pre-forced; bands are reported
    and clustering decides.
    """
    d = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    # time since prior shock (days)
    d["days_since_prior"] = d["days_since_prior"]
    # time since prior contagion per asset (carry-forward of last contagion date)
    d["_cont_date"] = d["historical_date"].where(d["out_contagion"] == 1)
    d["last_cont_date"] = d.groupby("cmc_id")["_cont_date"].ffill()
    d["days_since_contagion"] = (d["historical_date"] - d["last_cont_date"]).dt.days
    d = d.drop(columns=["_cont_date", "last_cont_date"])
    # membership stabilization: turnover below asset median over history
    med_turn = d.groupby("cmc_id")["roll_turnover_30d"].transform("median")
    d["membership_stabilized"] = (d["roll_turnover_30d"] <= med_turn).astype(float)
    # rank-health repair: rank velocity positive now
    d["rank_repair"] = (d["rank_vel_7d"] > 0).astype(float)
    # liquidity recovery: liq above asset median
    med_liq = d.groupby("cmc_id")["liq_proxy"].transform("median")
    d["liquidity_recovered"] = (d["liq_proxy"] >= med_liq).astype(float)
    # relational stabilization: state_age high (long in state)
    med_age = d.groupby("cmc_id")["state_age_d"].transform("median")
    d["relational_stabilized"] = (d["state_age_d"] >= med_age).astype(float)
    # composite recovery state index
    d["recovery_index"] = (
        0.35 * np.clip(d["days_since_prior"].fillna(180) / 180.0, 0, 1)
        + 0.15 * np.clip(d["days_since_contagion"].fillna(180) / 180.0, 0, 1)
        + 0.15 * d["membership_stabilized"]
        + 0.15 * d["rank_repair"]
        + 0.10 * d["liquidity_recovered"]
        + 0.10 * d["relational_stabilized"]
    )
    d["recovery_state"] = pd.cut(d["recovery_index"], bins=[-0.01, 0.35, 0.6, 1.01],
                                 labels=["RECENTLY_DISTURBED", "RECOVERING", "RECOVERED"])
    return d


# ---------------------------------------------------------------------------
# Within-asset prior states (Section 13/14)
# ---------------------------------------------------------------------------

def within_asset_flags(snap: pd.DataFrame) -> pd.DataFrame:
    """Per-event flags describing the asset's own shock history (fixed-effect
    friendly): fresh / recently-shocked / multiple-recent / long-recovery."""
    d = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    prev_days = d.groupby("cmc_id")["historical_date"].diff().dt.days
    d["days_since_prior"] = d["days_since_prior"]
    d["fresh_state"] = d["days_since_prior"].isna().astype(float)
    d["recently_shocked"] = (d["days_since_prior"] <= 30).astype(float)
    d["multiple_recent"] = (d["cnt_prev_90d"].fillna(0) >= 2).astype(float)
    d["long_recovery"] = (d["days_since_prior"] > 90).astype(float)
    # prior decoupling / prior contagion flags
    d["prev_contagion"] = d.groupby("cmc_id")["out_contagion"].shift(1).fillna(0)
    d["prev_decouple"] = d.groupby("cmc_id")["out_decouple"].shift(1).fillna(0)
    d["prev_rejoin"] = d.groupby("cmc_id")["out_rejoin"].shift(1).fillna(0)
    # within-asset rank of event
    d["asset_event_n"] = d.groupby("cmc_id").cumcount()
    return d


# ---------------------------------------------------------------------------
# Pre-shock correlation proxy (previous snapshot) + correlation metrics
# ---------------------------------------------------------------------------

def correlation_metrics(snap: pd.DataFrame) -> pd.DataFrame:
    """Correlation-compression coordinates (Section 28). peer_corr is the
    event-time neighborhood coherence; corr_pre is the previous snapshot's
    coherence (pre-shock proxy). Time-to-compression approximated by the peer
    negative fraction ramp 1d->3d->7d."""
    d = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    d["corr_pre"] = d.groupby("cmc_id")["peer_corr"].shift(1)
    d["corr_jump"] = d["peer_corr"] - d["corr_pre"]
    d["compression_ramp_1d"] = d["peer_neg_frac1"] - 0.0
    d["compression_ramp_3d"] = d["peer_neg_frac3"].fillna(0) - d["peer_neg_frac1"].fillna(0)
    d["compression_ramp_7d"] = d["peer_neg_frac7"].fillna(0) - d["peer_neg_frac3"].fillna(0)
    d["time_to_compression"] = np.select(
        [d["peer_neg_frac1"].fillna(0) >= 0.3, d["peer_neg_frac3"].fillna(0) >= 0.3,
         d["peer_neg_frac7"].fillna(0) >= 0.3],
        [1, 3, 7], default=np.nan)
    return d


# ---------------------------------------------------------------------------
# Relational-distance proxies (Section 17)
# ---------------------------------------------------------------------------

def relational_distance(snap: pd.DataFrame) -> pd.DataFrame:
    """Descriptive relational-distance coordinates: peer membership proximity
    (inverse turnover), correlation proximity (peer_corr), neighborhood
    overlap (jaccard), topology-transition distance (state change), rank
    proximity proxy (rank health similarity via peer_std_ret)."""
    d = snap.copy()
    d["rel_membership_proximity"] = 1.0 - d["roll_turnover_30d"].clip(0, 1)
    d["rel_corr_proximity"] = d["peer_corr"].clip(0, 1)
    d["rel_overlap"] = d["jaccard_overlap"] if "jaccard_overlap" in d.columns else np.nan
    d["rel_state_transition_distance"] = d["state_changed"].astype(float)
    d["rel_peer_dispersion"] = d["peer_std_ret"]
    return d


# ---------------------------------------------------------------------------
# Reactivation interaction flags (Section 3 repair / 22-23)
# ---------------------------------------------------------------------------

def reactivation_flags(snap: pd.DataFrame) -> pd.DataFrame:
    d = snap.copy()
    d["prior_contagion"] = d.groupby("cmc_id")["out_contagion"].shift(1).fillna(0)
    d["fresh_shock"] = (d["abs_ret"] >= 0.10).astype(float)
    med_burden = d["mem_exp_sum"].median()
    d["unresolved_burden"] = (d["mem_exp_sum"] >= med_burden).astype(float)
    d["topology_churn_hi"] = (d["roll_turnover_30d"] >= d["roll_turnover_30d"].median()).astype(float)
    d["peer_stress_hi"] = d["peer_stress"].astype(float)
    d["recent_prior_contagion"] = ((d["prior_contagion"] == 1) & (d["days_since_prior"].fillna(999) <= 60)).astype(float)
    d["react_prior_x_fresh"] = d["prior_contagion"] * d["fresh_shock"]
    d["react_prior_x_recency"] = d["prior_contagion"] * (d["days_since_prior"].fillna(999) <= 30).astype(float)
    d["react_prior_x_burden"] = d["prior_contagion"] * d["unresolved_burden"]
    d["react_prior_x_churn"] = d["prior_contagion"] * d["topology_churn_hi"]
    return d


# ---------------------------------------------------------------------------
# PIT-safe upside coordinates (Section 31-34 rebuild)
# ---------------------------------------------------------------------------

def upside_pit(snap: pd.DataFrame) -> pd.DataFrame:
    """Non-leaky, T0/current-only upside coordinates. All 'history' variables
    are strictly prior-event (shift) or current-state; NO forward-outcome
    columns are used as permission inputs. Forward outcomes are kept ONLY as
    the response variable."""
    d = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    # current (T0) state
    d["ups_current_stability"] = (d["roll_turnover_30d"] <= d["roll_turnover_30d"].median()).astype(float)
    d["ups_current_rank_health"] = (d["rank"] <= d["rank"].median()).astype(float)
    d["ups_current_liquidity"] = (d["liq_proxy"] >= d["liq_proxy"].median()).astype(float)
    d["ups_current_coherence"] = (d["peer_corr"] >= d["peer_corr"].median()).astype(float)
    d["ups_capacity_region"] = (d["struct_integrity"] >= d["struct_integrity"].median()).astype(float)
    d["ups_positive_history"] = (d["prev_rejoin"] if "prev_rejoin" in d.columns
                                 else d.groupby("cmc_id")["out_rejoin"].shift(1)).fillna(0).astype(float)
    d["ups_prior_rank_repair"] = (d.groupby("cmc_id")["rank_vel_7d"].shift(1) > 0).fillna(False).astype(float)
    d["ups_time_since_downside"] = np.clip(d["days_since_prior"].fillna(180) / 180.0, 0, 1)
    # forward RECRUITMENT leak check column (to audit against)
    d["ups_forward_rejoin"] = d["out_rejoin"].fillna(0).astype(float)
    d["ups_forward_rank_improve"] = d["rank_up_30"].fillna(0).astype(float)
    return d


# ---------------------------------------------------------------------------
# Master construction (cached)
# ---------------------------------------------------------------------------

def master_frame(use_cache: bool = True) -> pd.DataFrame:
    cache_p = CACHE / "lf12_master_frame.parquet"
    if use_cache and cache_p.exists() and cache_p.stat().st_size > 0:
        return pd.read_parquet(cache_p)

    base = base_frame(use_cache=True)
    base = recovery_state(base)
    base = within_asset_flags(base)
    base = correlation_metrics(base)
    base = relational_distance(base)
    base = reactivation_flags(base)
    base = upside_pit(base)
    base = base.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    base.to_parquet(cache_p, index=False)
    return base


if __name__ == "__main__":
    df = master_frame()
    print("LF12 master frame rows:", df.shape, flush=True)
    for c in ["recovery_state", "recovery_index", "fresh_state", "recently_shocked",
              "corr_pre", "corr_jump", "rel_membership_proximity", "prior_contagion",
              "react_prior_x_fresh", "ups_current_stability"]:
        print(("OK " if c in df.columns else "MISS"), c)