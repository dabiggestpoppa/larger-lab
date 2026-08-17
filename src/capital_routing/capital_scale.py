"""
CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN — capital-scale engine (D0/DESIGN).

Builds the reusable laboratory for the next frontier run
(CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER). This checkpoint constructs and
VALIDATES the engine; it does NOT declare the production capital frontier.

The problem under study:

    HOW MUCH CAPITAL / BASE TOTAL-F CAN THE STATIC ARCHITECTURE SUPPORT
    BEFORE MARGINAL TAIL RISK BECOMES DISPROPORTIONATE TO MARGINAL RETURN?

Design decisions (all pre-registered in CR_RISK_BLOCK3_SCALE_PROTOCOL.md):

- The primary sizing variable is f_total = TOTAL PORTFOLIO BASE RISK FRACTION
  (percent units; 1.0 == 1% of account). Allocation distributes f_total:
  event fraction = family_weight(family) * f_total.
- Admission ALWAYS routes through the sealed Block-II static architecture
  (`static_risk_architecture.admit_book`) — no second admission implementation.
  Admission is invariant to f_total (caps and requested heat scale linearly),
  so admission runs at base_f = 1.0 and the accounting applies f_total.
- Historical accounting is OVERLAP-EXACT hourly compounding (the frozen R6
  primitive `phase_r6_common.hourly_portfolio`), preserving sealed H0 parity.
- MC resampling reuses the frozen R6 path layouts (block / episode / iid);
  per-path equity = cumprod(1 + f_total * admitted_w * r) on the path layout.
- Edge degradation is a STRESS TRANSFORM on realized outcome streams
  (positive returns scaled per family — the sealed R5/R6 semantics). It never
  feeds back into admission.
- Empirical Kelly is computed ONLY as a diagnostic reference (expected
  log-growth on the event return distribution) with bootstrapped uncertainty.
  Kelly is never executed, never selected, never authorized.
- No PnL-conditioned sizing, no drawdown adaptation, no future episode
  membership, no future returns, no future DD in any admission/size decision.

This module MUST NOT calculate alpha, change entries/exits, perform broker
execution, or select a production configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .static_risk_architecture import (
    DECISIONS,
    TREATMENTS,
    AdmissionResult,
    FamilyAllocation,
    StaticRiskConfig,
    admit_book,
)

# ---------------------------------------------------------------------------
# Frozen research grid (pre-registered; no new caps / allocations)
# ---------------------------------------------------------------------------

# Frozen scale ladder (Block-III: broad scale regions, not fine optimization).
SCALE_LADDER_PCT: List[float] = [0.25, 0.50, 0.75, 1.00, 1.50, 2.00]
OUTER_STRESS_PCT: float = 3.00

# Allocation references (frozen): 50/50, 70/30, 100/0 A. 0/100 B diagnostic.
ALLOCATION_REFERENCES: Dict[str, FamilyAllocation] = {
    "A0_50_50": FamilyAllocation({"A": 0.5, "B": 0.5}),
    "A1_70_30": FamilyAllocation({"A": 0.7, "B": 0.3}),
    "A2_100_0_A": FamilyAllocation({"A": 1.0, "B": 0.0}),
    "A3_0_100_B": FamilyAllocation({"A": 0.0, "B": 1.0}),  # diagnostic only
}

# Heat references: H0 (unconstrained diagnostic) + previously frozen R6 H1
# gross-cap configurations ONLY (cap units are multiples of f_total).
HEAT_REFERENCES: Dict[str, Dict] = {
    "H0": {"gross_heat_cap_mult": None, "treatment": "REJECT"},
    "H1-1.00-REJ": {"gross_heat_cap_mult": 1.0, "treatment": "REJECT"},
    "H1-1.50-REJ": {"gross_heat_cap_mult": 1.5, "treatment": "REJECT"},
    "H1-2.00-REJ": {"gross_heat_cap_mult": 2.0, "treatment": "REJECT"},
    "H1-3.00-REJ": {"gross_heat_cap_mult": 3.0, "treatment": "REJECT"},
}

# Edge retention states (scenario states, no subjective probabilities).
EDGE_STATES: List[float] = [1.00, 0.75, 0.50, 0.25]

# MC schemes: block + episode primary (dependency-aware), iid diagnostic only.
MC_SCHEMES: Tuple[str, ...] = ("block", "episode", "iid")

# Frozen MC path requirement for the frontier checkpoint (pre-registered).
PRIMARY_MC_PATHS = 10_000
MC_SEED = 20260815

# Risk envelopes (research envelopes; human review picks the production
# tolerance later — no single DD threshold is chosen here).
RISK_ENVELOPES_PCT: List[float] = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]

# DD threshold ladder exposed in MC outputs (complete ladder; no single
# tolerance selected).
DD_THRESHOLD_LADDER_PCT: List[float] = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]

# Survival capital floors (fraction of initial capital).
SURVIVAL_FLOORS: List[float] = [0.90, 0.80, 0.75, 0.50]


# ---------------------------------------------------------------------------
# Typed immutable configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScaleConfig:
    """Full Block-III scale configuration (no hidden global config).

    allocation       : frozen family allocation (FamilyAllocation).
    f_total_pct      : TOTAL portfolio base risk fraction (percent units;
                       1.0 == 1% of account). Event fraction =
                       family_weight * f_total_pct / 100.
    gross_heat_cap_mult : H1 gross-cap multiplier RELATIVE TO f_total
                       (cap units = multiples of one event-unit at total-f;
                       the cap scales linearly with f_total). None = H0.
    treatment        : "REJECT" or "SCALE" (frozen H1 semantics).
    """

    allocation: FamilyAllocation
    f_total_pct: float = 1.0
    gross_heat_cap_mult: Optional[float] = None
    treatment: str = "REJECT"

    def __post_init__(self) -> None:
        if self.f_total_pct <= 0.0:
            raise ValueError("f_total_pct must be > 0")
        if self.gross_heat_cap_mult is not None and self.gross_heat_cap_mult <= 0.0:
            raise ValueError("gross_heat_cap_mult must be > 0")
        if self.treatment not in TREATMENTS:
            raise ValueError(f"treatment must be one of {TREATMENTS}")

    @property
    def policy_id(self) -> str:
        if self.gross_heat_cap_mult is None:
            return "H0"
        return f"H1-{self.gross_heat_cap_mult:.2f}-{self.treatment[:3].upper()}"

    def to_static_config(self) -> StaticRiskConfig:
        """Admission runs at base_f = 1.0 (admission is invariant to f_total);
        f_total is applied at accounting time."""
        return StaticRiskConfig(
            allocation=self.allocation,
            base_f=1.0,
            gross_heat_cap_mult=self.gross_heat_cap_mult,
            treatment=self.treatment,
        )

    def event_fraction_pct(self, family: str) -> float:
        """Event account fraction in percent units = weight * f_total."""
        return self.allocation.weight(family) * self.f_total_pct

    def gross_cap_pct(self) -> Optional[float]:
        """Cap in percent units (multiples of f_total)."""
        if self.gross_heat_cap_mult is None:
            return None
        return self.gross_heat_cap_mult * self.f_total_pct


# ---------------------------------------------------------------------------
# Admission (canonical static architecture only)
# ---------------------------------------------------------------------------

def admit(entry: Sequence, exit_: Sequence, family: Sequence,
          config: ScaleConfig,
          direction: Optional[Sequence] = None) -> AdmissionResult:
    """Causal admission through the sealed Block-II static architecture."""
    return admit_book(entry, exit_, family, config.to_static_config(),
                      direction=direction)


# ---------------------------------------------------------------------------
# Edge-retention stress transform (sealed R5/R6 semantics)
# ---------------------------------------------------------------------------

def edge_transform(r: np.ndarray, family: np.ndarray,
                   edge_A: float, edge_B: float) -> np.ndarray:
    """Scale POSITIVE returns per family (the frozen R5/R6 winner-edge-
    degradation transform). Negative returns are untouched. edge in {1.0,
    0.75, 0.50, 0.25}. Never feeds back into admission."""
    fam = np.asarray(family)
    pos = np.asarray(r) > 0.0
    out = np.asarray(r, dtype=float).copy()
    out[pos & (fam == "A")] *= edge_A
    out[pos & (fam == "B")] *= edge_B
    return out


# ---------------------------------------------------------------------------
# Historical accounting (overlap-exact hourly compounding)
# ---------------------------------------------------------------------------

def historical_scale(load: Dict, config: ScaleConfig) -> Dict:
    """Deterministic historical account metrics for one ScaleConfig.

    Admission through the static architecture; accounting through the frozen
    R6 overlap-exact hourly primitive (policy_metrics) so sealed H0 parity is
    preserved exactly. Extends the R6 metric set with Block-III fields:
    worst week, worst 3m / 12m, yearly return distribution, capital
    utilization, rejection / scaling fractions, average gross heat.
    """
    from .phases.phase_r6_common import policy_metrics

    ba = load["ba"]
    adm = admit(ba["tb"]["entry_ts"], ba["tb"]["exit_ts"], ba["fam"], config,
                direction=ba["dir"])
    years = load["years"]
    wA = config.allocation.weight("A")
    wB = config.allocation.weight("B")
    m = policy_metrics(load, adm.admitted_f, config.f_total_pct / 100.0,
                       years, wA, wB)

    # --- Block-III extended fields ---------------------------------------
    n = int(len(adm.admitted_f))
    req = np.where(ba["fam"] == "A", wA, wB)
    m["n_events"] = n
    m["n_admitted_full"] = int(adm.n_accept_full)
    m["n_admitted_scaled"] = int(adm.n_accept_scaled)
    m["n_rejected"] = int(adm.n_rejected)
    m["rejection_fraction"] = float(adm.n_rejected / n)
    m["scaling_fraction"] = float(adm.n_accept_scaled / n)
    m["admission_fraction"] = float((n - adm.n_rejected) / n)
    m["max_requested_f_pct"] = float(adm.requested_f.max())
    m["mean_admitted_f_pct"] = float(adm.admitted_f.mean())
    m["capital_utilization"] = float(
        adm.admitted_f.sum() / max(req.sum(), 1e-12))
    m["max_gross_heat_pct"] = float(adm.max_gross_heat)
    m["max_gross_heat_rel"] = float(adm.max_gross_heat / max(config.f_total_pct, 1e-12))
    m["p95_gross_heat"] = m.get("p95_gross_heat", 0.0)
    m["mean_gross_heat"] = m.get("mean_gross_heat", 0.0)

    # calendar extensions on the hourly equity path
    eq = _equity_from_r_hourly(load, adm.admitted_f, config)
    m["worst_week_pct"] = _rolling_loss_pct(eq, 7 * 24)
    m["worst_3m_pct"] = _rolling_loss_pct(eq, 90 * 24)
    m["worst_12m_pct"] = _rolling_loss_pct(eq, 365 * 24)
    y = _yearly_returns(eq)
    m["median_yearly_return_pct"] = float(np.median(y)) if len(y) else np.nan
    m["worst_yearly_return_pct"] = float(np.min(y)) if len(y) else np.nan
    m["positive_year_fraction"] = float((y > 0).mean()) if len(y) else np.nan
    m["time_under_water_h"] = m.get("longest_dd_duration_h", 0)
    m["insolvent"] = bool(eq[-1] <= 0.0 or np.any(eq <= 0.0))
    # risk envelopes (historical): clear if max DD < envelope
    for e in RISK_ENVELOPES_PCT:
        m[f"envelope_E{int(e)}"] = bool(m["max_dd"] < e / 100.0)
    for fl in SURVIVAL_FLOORS:
        m[f"survival_floor_{int(fl * 100)}"] = bool(eq[-1] >= fl)
    return m


def _equity_from_r_hourly(load: Dict, admitted_f: np.ndarray,
                          config: ScaleConfig) -> np.ndarray:
    from .phases.phase_r6_common import hourly_portfolio
    r_h = hourly_portfolio(load, admitted_f, config.f_total_pct / 100.0)
    return np.concatenate([[1.0], np.cumprod(1.0 + r_h)])


def _rolling_loss_pct(equity: np.ndarray, hours: int) -> float:
    """Worst rolling `hours`-hour loss on the hourly equity path."""
    if len(equity) < 2:
        return 0.0
    rets = np.diff(equity) / equity[:-1]
    w = int(hours)
    if len(rets) < w:
        return float((np.prod(1.0 + rets) - 1.0))
    # worst compound return over every contiguous w-hour window
    wins = np.take(rets, np.arange(len(rets) - w + 1)[:, None] + np.arange(w))
    return float(np.prod(1.0 + wins, axis=1).min() - 1.0)


def _yearly_returns(equity: np.ndarray) -> np.ndarray:
    """Return per calendar-year equity growth (fractional)."""
    n = len(equity)
    hours_per_year = 365.25 * 24.0
    n_years = int(np.ceil(n / hours_per_year))
    out = []
    for k in range(n_years):
        i0 = int(k * hours_per_year)
        i1 = min(n - 1, int((k + 1) * hours_per_year) - 1)
        if i1 <= i0:
            break
        out.append(equity[i1] / equity[i0] - 1.0)
    return np.asarray(out, dtype=float)


# ---------------------------------------------------------------------------
# Monte Carlo (dependency-aware; deterministic seeds; frozen schemes)
# ---------------------------------------------------------------------------

def _mc_path_stats(eq: np.ndarray, years: float) -> Dict[str, np.ndarray]:
    """Per-path stats + complete DD threshold ladder (5..30) + survival."""
    from .phases.phase_r4_mc import _simulate_stats
    st = _simulate_stats(eq, years)
    dd = st["dd"]
    rows: Dict[str, np.ndarray] = {
        "max_dd": st["max_dd"], "terminal": st["terminal"],
        "cagr": st["cagr"], "min_eq": st["min_eq"], "dur": st["dur"],
    }
    for thr in DD_THRESHOLD_LADDER_PCT:
        rows[f"P_dd_ge_{int(thr)}"] = (st["max_dd"] >= thr / 100.0)
    rows["P_technical_ruin"] = st["terminal"] <= 0.0
    for fl in SURVIVAL_FLOORS:
        rows[f"P_below_{int(fl * 100)}"] = (st["min_eq"] < fl)
    return rows


def _path_admitted_weights(layouts: List[Dict], config: ScaleConfig) -> List[np.ndarray]:
    """Admission per path through the sealed static architecture (base_f=1.0,
    invariant to f_total and to returns)."""
    out = []
    for lay in layouts:
        res = admit(lay["entry"], lay["exit"], lay["fam"], config,
                    direction=lay["dir"])
        out.append(res.admitted_f)
    return out


def mc_scale(load: Dict, config: ScaleConfig, scheme: str, n_paths: int,
             seed: int = MC_SEED,
             edge_A: float = 1.0, edge_B: float = 1.0) -> pd.DataFrame:
    """One (config, scheme, n_paths, edge) MC batch.

    Path layout conventions are the frozen R6 ones (block = 25-event
    stationary blocks; episode = R1 12h clusters with quiet gaps; iid =
    reference only). Per-path equity = cumprod(1 + f_total * admitted_w * r_e).
    Returns one row of percentile stats + DD-threshold probabilities.
    """
    from .phases.phase_r6_mc import _path_layouts
    ba = load["ba"]
    n = len(ba["tb"])
    years = load["years"]
    layouts, lay = _path_layouts(load, scheme, n_paths, n, seed)
    r_mat = np.stack([lay["r_R"][l["idx"]] for l in layouts])
    fam_mat = np.stack([lay["fam"][l["idx"]] for l in layouts])
    w_mat = np.stack(_path_admitted_weights(layouts, config))
    if edge_A < 1.0 or edge_B < 1.0:
        pos = r_mat > 0.0
        r_mat = r_mat.copy()
        r_mat[pos & (fam_mat == "A")] *= edge_A
        r_mat[pos & (fam_mat == "B")] *= edge_B
    eq = np.cumprod(1.0 + (config.f_total_pct / 100.0) * w_mat * r_mat, axis=1)
    st = _mc_path_stats(eq, years)
    row: Dict = {
        "policy_id": config.policy_id,
        "w_A_pct": config.allocation.weight("A") * 100.0,
        "w_B_pct": config.allocation.weight("B") * 100.0,
        "f_pct": config.f_total_pct,
        "scheme": scheme, "n_paths": n_paths, "seed": seed,
        "edge_A": edge_A, "edge_B": edge_B,
    }
    for key in ["max_dd", "terminal", "cagr", "min_eq", "dur"]:
        for p in [5, 25, 50, 75, 90, 95, 99]:
            row[f"{key}_p{p}"] = float(np.percentile(st[key], p))
    row["exp_cagr"] = float(np.mean(st["cagr"]))
    row["median_cagr"] = float(np.median(st["cagr"]))
    row["exp_max_dd"] = float(np.mean(st["max_dd"]))
    row["median_terminal"] = float(np.median(st["terminal"]))
    for k, v in st.items():
        if k.startswith("P_"):
            row[k] = float(v.mean())
    return pd.DataFrame([row])


def mc_grid(load: Dict, configs: List[ScaleConfig],
            scheme_paths: Dict[str, int],
            seed: int = MC_SEED) -> pd.DataFrame:
    """Small deterministic MC batch (validation use). The full 10k-path
    frontier is executed in the NEXT checkpoint."""
    frames = []
    for cfg in configs:
        for scheme, n_paths in scheme_paths.items():
            if scheme not in MC_SCHEMES:
                raise ValueError(f"unknown scheme {scheme}")
            frames.append(mc_scale(load, cfg, scheme, n_paths, seed))
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Empirical Kelly (DIAGNOSTIC ONLY — never executed / selected / authorized)
# ---------------------------------------------------------------------------

def empirical_kelly(r: np.ndarray, weight: np.ndarray,
                    f_grid: Optional[np.ndarray] = None,
                    n_boot: int = 1000, seed: int = MC_SEED) -> Dict:
    """Empirical expected-log-growth Kelly reference on the event return
    distribution. Objective: g(f) = mean(log(1 + f * w_i * r_i)); f* =
    argmax g over a feasible grid (1 + f*w*r > 0 for all sampled events).

    Returns the point estimate, the 1/2 - 1/4 - 1/8 fractions, and the
    bootstrapped uncertainty interval (median / p10 / p25 / p75 / p90).
    Classification UNSTABLE_REFERENCE when the bootstrap spread is wide or
    the argmax sits at a grid boundary (no forced number).
    """
    r = np.asarray(r, dtype=float)
    w = np.asarray(weight, dtype=float)
    if f_grid is None:
        f_grid = np.arange(0.001, 0.301, 0.001)
    # feasible domain: 1 + f*w*r > 0 for every event
    neg = r < 0.0
    max_feas = 1e9
    if neg.any():
        with np.errstate(divide="ignore"):
            max_feas = float(np.min(-1.0 / (w[neg] * r[neg]))) * 0.999
    grid = f_grid[f_grid < max_feas]
    if len(grid) == 0:
        return {"f_star": np.nan, "fractional": {"half": np.nan, "quarter": np.nan,
                "eighth": np.nan}, "uncertainty": {"median": np.nan, "p10": np.nan,
                "p25": np.nan, "p75": np.nan, "p90": np.nan},
                "classification": "UNSTABLE_REFERENCE", "grid_max_feasible": float(max_feas)}

    def _argmax(rr: np.ndarray, ww: np.ndarray) -> float:
        # vectorized: inside[f, i] = 1 + f * w_i * r_i; skip infeasible cols
        inside = 1.0 + grid[:, None] * (ww[None, :] * rr[None, :])
        with np.errstate(invalid="ignore"):
            vals = np.where(inside > 0.0, np.log(inside), -np.inf)
        mean = np.where(np.isfinite(vals).all(axis=1), vals.mean(axis=1), -np.inf)
        return float(grid[int(np.argmax(mean))])

    f_star = _argmax(r, w)
    # bootstrap uncertainty (iid resample of event indices)
    rng = np.random.default_rng(seed)
    n = len(r)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boots[b] = _argmax(r[idx], w[idx])
    med = float(np.median(boots))
    p10, p25, p75, p90 = (float(np.percentile(boots, q)) for q in [10, 25, 75, 90])
    iqr = p75 - p25
    boundary = (f_star >= float(grid[-1]) - 1e-9) or (f_star <= float(grid[0]) + 1e-9)
    unstable = (iqr > 0.03) or boundary or not np.isfinite(f_star)
    return {
        "f_star": f_star,
        "fractional": {"half": f_star / 2.0, "quarter": f_star / 4.0,
                       "eighth": f_star / 8.0},
        "uncertainty": {"median": med, "p10": p10, "p25": p25, "p75": p75,
                        "p90": p90},
        "classification": "UNSTABLE_REFERENCE" if unstable else "STABLE_REFERENCE",
        "grid_max_feasible": float(max_feas),
        "n_boot": n_boot,
    }


def kelly_reference(load: Dict, config: ScaleConfig,
                    edges: Sequence[float] = (1.00, 0.75, 0.50, 0.25),
                    n_boot: int = 500, seed: int = MC_SEED) -> pd.DataFrame:
    """Diagnostic Kelly references: pooled (allocation-weighted) + per-family
    (A-only, B-only) at each retained edge. NEVER executed / selected."""
    ba = load["ba"]
    r = ba["r_R"]
    fam = ba["fam"]
    w = np.where(fam == "A", config.allocation.weight("A"),
                 config.allocation.weight("B"))
    rows = []
    for edge in edges:
        r_e = edge_transform(r, fam, edge, edge)
        pooled = empirical_kelly(r_e, w, n_boot=n_boot, seed=seed)
        a_only = empirical_kelly(r_e[fam == "A"], np.ones(int((fam == "A").sum())),
                                 n_boot=n_boot, seed=seed + 1)
        b_only = empirical_kelly(r_e[fam == "B"], np.ones(int((fam == "B").sum())),
                                 n_boot=n_boot, seed=seed + 2)
        for label, k in [("pooled", pooled), ("A_only", a_only), ("B_only", b_only)]:
            rows.append({
                "edge_retained": edge, "scope": label,
                "kelly_f_star_pct": k["f_star"] * 100.0,
                "half_kelly_pct": k["fractional"]["half"] * 100.0,
                "quarter_kelly_pct": k["fractional"]["quarter"] * 100.0,
                "eighth_kelly_pct": k["fractional"]["eighth"] * 100.0,
                "unc_median_pct": k["uncertainty"]["median"] * 100.0,
                "unc_p10_pct": k["uncertainty"]["p10"] * 100.0,
                "unc_p25_pct": k["uncertainty"]["p25"] * 100.0,
                "unc_p75_pct": k["uncertainty"]["p75"] * 100.0,
                "unc_p90_pct": k["uncertainty"]["p90"] * 100.0,
                "classification": k["classification"],
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Survival / loss-streak diagnostics (descriptive)
# ---------------------------------------------------------------------------

def loss_streak_stats(load: Dict) -> Dict:
    """Observed serial-dependence summaries: longest loss sequence, worst
    clustered R loss, worst family-specific streak. Descriptive only."""
    ba = load["ba"]
    r = ba["r_R"]
    fam = ba["fam"]
    longest = best = 0
    for v in r:
        if v < 0:
            best += 1
            longest = max(longest, best)
        else:
            best = 0
    # worst clustered R loss: most negative sum over consecutive runs
    runs: List[float] = []
    cur = 0.0
    for v in r:
        if v < 0:
            cur += v
        else:
            if cur < 0:
                runs.append(cur)
            cur = 0.0
    if cur < 0:
        runs.append(cur)
    worst_cluster = float(min(runs)) if runs else 0.0
    fam_streak = {}
    for f in ["A", "B"]:
        best = cur = 0
        for v, ff in zip(r, fam):
            if v < 0 and ff == f:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        fam_streak[f] = best
    return {
        "longest_loss_streak": int(longest),
        "worst_clustered_R_loss": float(worst_cluster),
        "longest_family_streak": fam_streak,
    }
