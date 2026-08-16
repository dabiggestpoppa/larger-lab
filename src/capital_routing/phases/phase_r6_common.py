"""
CR-RISK-BLOCK2 R6 — Episode / Heat Sizing (shared primitives).

Answers: "when multiple valid A/B events occur close together, how should
account heat be represented and what is the risk/return effect of predefined
heat constraints?"

Key design decisions (all pre-registered in R6_PROTOCOL.md):

- Episode = the Block-I R1 12h cluster framework (`assign_cluster_ranks`,
  interval_h = 12). Episode ids reconcile with R1_ROUTING_EPISODES.csv at the
  same interval.
- Per-event f is the static fraction assigned to one R for that event. With a
  family allocation (w_A, w_B) the event's requested heat = base_f * w_family.
- Gross heat = sum of admitted f over active events; net directional heat =
  signed sum; family heat = per-family sums; episode heat = max gross heat
  inside a 12h cluster; CAE heat = worst portfolio adverse excursion.
- Admission is strictly CAUSAL: only information known at entry time (active
  heat from previously-entered events) decides ACCEPT_FULL / ACCEPT_SCALED /
  REJECT_HEAT_CAP. Never future outcome, future MAE/DD, or later performance.
- Admission decisions are INVARIANT to base_f (all caps and requested heat
  scale linearly with base_f), so one admission pass serves every f level;
  account PnL then scales linearly with f.

No alpha, entry, exit, trade-management, family-definition, or 1R change.
Only portfolio heat-admission is under study. No "best policy" is selected.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_7_5_audit import OOS_LABEL
from .phase_r4_common import RISK_UNIT_BPS, equity_metrics, span_years
from .phase_r5_common import load_r5_inputs
from .phase_r2_context import assign_cluster_ranks

EPISODE_INTERVAL_H = 12.0
HOLD_H = 6.0

# Family allocation reference set (frozen; X): 50/50 primary, 70/30, 100/0 ref.
ALLOC_SET: List[Tuple[int, int]] = [(50, 50), (70, 30), (100, 0)]
# f levels (VII reference scenarios)
F_GRID: List[float] = [0.25, 0.50, 0.75, 1.00, 1.50, 2.00]
F_GRID_MC: List[float] = [0.50, 1.00, 2.00]

# Policy grid (VIII): kind x cap_mult x treatment. REJECT_NEW tested on the
# full grid; SCALE_NEW_TO_REMAINING_CAP on a pre-registered subset. <= 50 core
# configurations before crossing with f (28 here).
POLICY_GRID: List[Dict] = [
    {"kind": "H0", "cap_mult": None, "treatment": "REJECT", "policy_id": "H0"},
    # H1 gross heat cap (1.0/1.5/2.0/3.0 x base f)
    *[{"kind": "H1", "cap_mult": m, "treatment": t, "policy_id": f"H1-{m:.2f}-{t[:3]}"}
      for m in [1.0, 1.5, 2.0, 3.0] for t in ["REJECT"]],
    *[{"kind": "H1", "cap_mult": m, "treatment": t, "policy_id": f"H1-{m:.2f}-{t[:3]}"}
      for m in [1.0, 1.5, 2.0] for t in ["SCALE"]],
    # H2 same-direction heat cap
    *[{"kind": "H2", "cap_mult": m, "treatment": t, "policy_id": f"H2-{m:.2f}-{t[:3]}"}
      for m in [1.0, 1.5, 2.0] for t in ["REJECT"]],
    *[{"kind": "H2", "cap_mult": m, "treatment": t, "policy_id": f"H2-{m:.2f}-{t[:3]}"}
      for m in [1.0, 1.5] for t in ["SCALE"]],
    # H3 family-B heat cap
    *[{"kind": "H3", "cap_mult": m, "treatment": t, "policy_id": f"H3-{m:.2f}-{t[:3]}"}
      for m in [0.5, 0.75, 1.0] for t in ["REJECT"]],
    *[{"kind": "H3", "cap_mult": m, "treatment": t, "policy_id": f"H3-{m:.2f}-{t[:3]}"}
      for m in [0.5, 0.75] for t in ["SCALE"]],
    # H4 episode budget (per 12h episode)
    *[{"kind": "H4", "cap_mult": m, "treatment": t, "policy_id": f"H4-{m:.2f}-{t[:3]}"}
      for m in [1.0, 1.5, 2.0, 3.0] for t in ["REJECT"]],
    *[{"kind": "H4", "cap_mult": m, "treatment": t, "policy_id": f"H4-{m:.2f}-{t[:3]}"}
      for m in [1.0, 1.5] for t in ["SCALE"]],
    # H5 hybrid: gross cap + same-direction cap (both constraints bind)
    *[{"kind": "H5", "cap_mult": m, "treatment": t, "policy_id": f"H5-{m:.2f}-{t[:3]}",
       "samedir_mult": s}
      for (m, s) in [(1.5, 1.0), (2.0, 1.5)] for t in ["REJECT", "SCALE"]],
]
POLICY_IDS: List[str] = [p["policy_id"] for p in POLICY_GRID]

# MC path counts (pre-registered): core policies get 8k block paths, the rest
# 4k; episode scheme 3k everywhere. Deterministic seeds.
MC_SEED = 20260815
MC_CORE = {"H0", "H1-1.50-REJ", "H2-1.50-REJ", "H3-0.75-REJ",
           "H4-1.50-REJ", "H5-1.50-REJ"}
MC_70_30 = {"H0", "H1-1.00-REJ", "H1-1.50-REJ", "H2-1.00-REJ",
            "H2-1.50-REJ", "H3-0.50-REJ", "H3-0.75-REJ", "H5-1.50-REJ"}
MC_F = [0.50, 1.00, 2.00]
EDGE_SCENARIOS: List[Tuple[float, float]] = [
    (1.00, 1.00), (0.75, 0.75), (0.50, 1.00), (1.00, 0.50),
    (0.50, 0.50), (0.25, 0.25), (0.75, 0.50), (0.50, 0.75)]


# ---------------------------------------------------------------------------
# Frozen-input load + per-event hourly incremental-R paths
# ---------------------------------------------------------------------------

def load_r6_inputs(root) -> Dict:
    """R5 rebuild (890-event sealed A/B book, cross-checked) plus the
    per-event hourly incremental R paths and R1 12h episode membership."""
    load = load_r5_inputs(root)
    ledger, paths = load["ledger"], load["paths"]
    # per-event hourly incremental net R (first bar carries the modeled cost)
    p = paths[["event_id", "mark_time", "h_since_entry", "net_R"]].copy()
    p = p.sort_values(["event_id", "h_since_entry"])
    p["mark_time"] = pd.to_datetime(p["mark_time"], utc=True)
    p["inc_R"] = p.groupby("event_id")["net_R"].diff()
    first = p.groupby("event_id")["h_since_entry"].transform("min") == p["h_since_entry"]
    p.loc[first, "inc_R"] = p.loc[first, "net_R"]
    p = p.dropna(subset=["inc_R"])
    hourly_inc = {eid: g[["mark_time", "inc_R"]].copy()
                  for eid, g in p.groupby("event_id")}
    # episodes (R1 12h framework) on event_ts
    ranks = assign_cluster_ranks(ledger, EPISODE_INTERVAL_H)
    cluster_of = dict(zip(ranks["event_id"], ranks["cluster_id"]))
    ledger["episode_id"] = ledger["event_id"].map(cluster_of)
    load["hourly_inc"] = hourly_inc
    load["episode_ranks"] = ranks
    # numeric book arrays in entry order (admission engine input)
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    entry = pd.to_datetime(tb["entry_ts"], utc=True).to_numpy(dtype="int64")
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True).to_numpy(dtype="int64")
    load["ba"] = {
        "tb": tb, "entry": entry, "exit_": exit_,
        "fam": tb["family"].to_numpy(),
        "dir": tb["dir"].to_numpy(dtype=float),
        "clus": tb["episode_id"].to_numpy(),
        "r_R": (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float),
    }
    load["risk1_cc"] = pd.read_csv(
        load["risk1_dir"] / "R1_CONCURRENCY_SUMMARY.csv")
    rh = pd.read_csv(load["risk1_dir"] / "R1_PORTFOLIO_HEAT.csv")
    rh["ts"] = pd.to_datetime(rh["ts"], utc=True)
    load["risk1_heat"] = rh
    load["episode_ledger"] = build_episode_ledger(ledger, load)
    # episode durations + sizes (hours from first entry to last exit)
    e_entry = pd.to_datetime(tb["entry_ts"], utc=True)
    e_exit = pd.to_datetime(tb["exit_ts"], utc=True)
    dur = {}
    sizes = {}
    for c, g in tb.groupby("episode_id"):
        d0 = e_entry.loc[g.index].min()
        d1 = e_exit.loc[g.index].max()
        dur[int(c)] = float((d1 - d0).total_seconds() / 3600.0)
        sizes[int(c)] = int(len(g))
    load["episode_durations"] = dur
    load["cluster_sizes"] = sizes
    return load


# ---------------------------------------------------------------------------
# Episode truth (V): R6_EVENT_EPISODE_LEDGER
# ---------------------------------------------------------------------------

def build_episode_ledger(ledger: pd.DataFrame,
                         load: Dict) -> pd.DataFrame:
    """Per-event episode/overlap frame. Exposure in R units (each event
    commits 1R): gross = active count, net = signed count. Unscaled by f."""
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    entry = pd.to_datetime(tb["entry_ts"], utc=True).to_numpy(dtype="int64")
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True).to_numpy(dtype="int64")
    fam = tb["family"].to_numpy()
    direc = tb["dir"].to_numpy(dtype=float)
    clus = tb["episode_id"].to_numpy()
    r_R = (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float)
    n = len(tb)
    hourly_inc = load["hourly_inc"]
    rows = []
    for i in range(n):
        eid = tb["event_id"].iloc[i]
        active = [j for j in range(i) if exit_[j] > entry[i]]
        concurrent = len(active)
        same_dir = sum(1 for j in active if direc[j] == direc[i])
        opposing = concurrent - same_dir
        a_cnt = sum(1 for j in active if fam[j] == "A")
        b_cnt = concurrent - a_cnt
        gross = float(concurrent)
        net = float(sum(direc[j] for j in active) + direc[i])
        # peak simultaneous count during the event's own active window
        # (events entering in [entry_i, exit_i), count active at each entry
        # instant; ties at equal timestamps count together; >= entry count+1)
        peak = concurrent + 1
        win = np.where((entry >= entry[i]) & (entry < exit_[i]))[0]
        for j in win:
            cnt = sum(1 for k in range(n) if entry[k] <= entry[j] < exit_[k])
            peak = max(peak, cnt)
        # episode window: [min entry, max exit] over members of the cluster
        members = np.where(clus == clus[i])[0]
        ep_start = entry[members].min()
        ep_end = exit_[members].max()
        # episode portfolio R path (unscaled): sum of net_R of active events
        ep_t = []
        for j in members:
            g = hourly_inc.get(tb["event_id"].iloc[j])
            if g is None:
                continue
            for t_, r_ in zip(pd.to_datetime(g["mark_time"], utc=True),
                              g["inc_R"].to_numpy()):
                ep_t.append((t_.value, float(r_)))
        if ep_t:
            t_ns = np.array([t for t, _ in ep_t])
            rr = np.array([v for _, v in ep_t])
            times = np.unique(t_ns)
            port = np.zeros(len(times))
            for t_, v in ep_t:
                port[np.searchsorted(times, t_)] += v
            cae = float(np.min(np.minimum.accumulate(port))) if len(port) else 0.0
            cfe = float(np.max(np.maximum.accumulate(port))) if len(port) else 0.0
        else:
            cae = cfe = 0.0
        # episode realized R = sum of final R of cluster members
        ep_real = float(r_R[members].sum())
        rows.append({
            "event_id": eid, "family": fam[i], "entry_time": tb["entry_ts"].iloc[i],
            "exit_time": tb["exit_ts"].iloc[i], "direction": direc[i],
            "return_R": r_R[i], "episode_id": int(clus[i]),
            "episode_start": pd.Timestamp(ep_start, tz="UTC"),
            "episode_end": pd.Timestamp(ep_end, tz="UTC"),
            "concurrent_position_count_at_entry": concurrent,
            "peak_concurrent_position_count": peak,
            "same_direction_active_count": same_dir,
            "opposite_direction_active_count": opposing,
            "A_active_count": a_cnt, "B_active_count": b_cnt,
            "gross_active_R": gross, "net_directional_R": net,
            "episode_peak_heat": None,  # f-dependent; filled in heat layer
            "episode_realized_R": ep_real,
            "episode_worst_CAE_R": cae, "episode_best_CFE_R": cfe,
        })
    out = pd.DataFrame(rows)
    # episode peak heat: max R1 hourly n_open inside the episode window
    r1 = load.get("risk1_heat")
    if r1 is not None and len(out):
        peaks = {}
        for c, g in out.groupby("episode_id"):
            t0 = pd.Timestamp(g["episode_start"].iloc[0]).tz_convert("UTC")
            t1 = pd.Timestamp(g["episode_end"].iloc[0]).tz_convert("UTC")
            win = r1[(r1.ts >= t0) & (r1.ts <= t1)]
            peaks[int(c)] = int(win["n_open"].max()) if len(win) else 0
        out["episode_peak_heat"] = out["episode_id"].map(peaks)
    return out


# ---------------------------------------------------------------------------
# Causal admission engine (XI): policies H0-H5
# ---------------------------------------------------------------------------

def _admit_sweep(entry: np.ndarray, exit_: np.ndarray, fam: np.ndarray,
                 direc: np.ndarray, clus: np.ndarray, req_mult: np.ndarray,
                 policy: Dict, base_f: float, full_output: bool = False):
    """Causal admission over events in processing order. Returns admitted f
    array (or a full record frame when full_output=True).

    entry/exit: numeric time (ns or path-time). req_mult = family weight
    (w_A / w_B); requested heat = base_f * req_mult. Only information known at
    entry time is used: active positions that entered earlier.
    """
    n = len(entry)
    kind = policy["kind"]
    cap = policy["cap_mult"]
    treat = policy["treatment"]
    if kind == "H0":
        # no constraint: every event admits its full requested heat
        admitted = base_f * np.asarray(req_mult, dtype=float)
        if not full_output:
            return admitted
        n = len(entry)
        return pd.DataFrame({
            "entry_t": np.asarray(entry), "admitted_f": admitted,
            "decision": np.full(n, "ACCEPT_FULL"), "reason": np.full(n, ""),
            "pre_gross_heat": np.zeros(n), "pre_same_direction_heat": np.zeros(n),
            "pre_opposite_direction_heat": np.zeros(n),
            "pre_A_heat": np.zeros(n), "pre_B_heat": np.zeros(n),
            "episode_budget_used": np.zeros(n), "remaining_heat": admitted,
        })
    # list-based fast sweep (max concurrency ~3; list ops are cheap)
    fam_is_A = np.asarray(fam) == "A"
    fam_idx = np.where(fam_is_A, 0, 1)
    direc_f = np.asarray(direc, dtype=float)
    clus_i = np.asarray(clus, dtype=np.int64)
    t0_list = np.asarray(entry, dtype=float)
    t1_list = np.asarray(exit_, dtype=float)
    req_list = (base_f * np.asarray(req_mult, dtype=float)).tolist()
    famA_list = fam_is_A.tolist()
    dir_list = direc_f.tolist()
    clus_list = clus_i.tolist()
    fam_idx_list = fam_idx.tolist()
    detailed = full_output
    admitted = np.zeros(n, dtype=float)
    if detailed:
        decisions = np.full(n, "ACCEPT_FULL", dtype=object)
        reasons = np.full(n, "", dtype=object)
        pre_gross = np.zeros(n)
        pre_samedir = np.zeros(n)
        pre_oppdir = np.zeros(n)
        pre_famA = np.zeros(n)
        pre_famB = np.zeros(n)
        pre_episode = np.zeros(n)
        remaining = np.zeros(n)
    from collections import deque
    cap_val = cap * base_f
    samedir_val = (policy.get("samedir_mult") or 0.0) * base_f
    # all holds are 6h, so exits ascend with entry order -> FIFO queue; the
    # head is always the next to expire. Active set max ~3.
    active: deque = deque()
    needs_ep = kind == "H4"
    episode_heat: Dict[int, float] = {}
    gross = samedir = famA = famB = 0.0
    samedir_p = samedir_m = 0.0
    for i in range(n):
        t0 = t0_list[i]
        while active and active[0][0] <= t0:
            e = active.popleft()
            gross -= e[1]
            if e[2] == 1:
                samedir_p -= e[1]
            else:
                samedir_m -= e[1]
            if e[3] == 0:
                famA -= e[1]
            else:
                famB -= e[1]
        d_i = dir_list[i]
        samedir = samedir_p if d_i == 1.0 else samedir_m
        oppdir = samedir_m if d_i == 1.0 else samedir_p
        fA_i = famA_list[i]
        ep_used = episode_heat.get(clus_list[i], 0.0) if needs_ep else 0.0
        req = req_list[i]
        if detailed:
            pre_gross[i] = gross
            pre_samedir[i] = samedir
            pre_oppdir[i] = oppdir
            pre_famA[i] = famA
            pre_famB[i] = famB
            pre_episode[i] = ep_used
        # determine remaining capacity for each active constraint
        if kind == "H1":
            rem = cap_val - gross
            reason = "gross_cap"
        elif kind == "H2":
            rem = cap_val - samedir
            reason = "same_direction_cap"
        elif kind == "H3":
            if not fA_i:
                rem = cap_val - famB
                reason = "family_B_cap"
            else:
                rem = req
                reason = ""
        elif kind == "H4":
            rem = cap_val - ep_used
            reason = "episode_budget"
        elif kind == "H5":
            r1 = cap_val - gross
            r2 = samedir_val - samedir
            rem = r1 if r1 < r2 else r2
            reason = "gross_and_same_direction_cap"
        else:
            raise ValueError(kind)
        if rem >= req - 1e-15:
            f_ = req
            decision = "ACCEPT_FULL"
        elif rem > 1e-15 and treat == "SCALE":
            f_ = rem
            decision = "ACCEPT_SCALED"
        else:
            f_ = 0.0
            decision = "REJECT_HEAT_CAP"
        admitted[i] = f_
        if detailed:
            decisions[i] = decision
            reasons[i] = reason if decision != "ACCEPT_FULL" else ""
            remaining[i] = rem
        if needs_ep:
            episode_heat[clus_list[i]] = ep_used + f_
        if f_ > 0:
            active.append((t1_list[i], f_, int(d_i), fam_idx_list[i], clus_list[i]))
            gross += f_
            if d_i == 1.0:
                samedir_p += f_
            else:
                samedir_m += f_
            if fA_i:
                famA += f_
            else:
                famB += f_
    if not full_output:
        return admitted
    return pd.DataFrame({
        "entry_t": entry, "admitted_f": admitted, "decision": decisions,
        "reason": reasons, "pre_gross_heat": pre_gross,
        "pre_same_direction_heat": pre_samedir,
        "pre_opposite_direction_heat": pre_oppdir,
        "pre_A_heat": pre_famA, "pre_B_heat": pre_famB,
        "episode_budget_used": pre_episode, "remaining_heat": remaining,
    })


def book_arrays(ledger: pd.DataFrame) -> Dict[str, np.ndarray]:
    """Precomputed numeric arrays over the chronological book (entry order)."""
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    entry = pd.to_datetime(tb["entry_ts"], utc=True).to_numpy(dtype="int64")
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True).to_numpy(dtype="int64")
    return {
        "tb": tb, "entry": entry, "exit_": exit_,
        "fam": tb["family"].to_numpy(), "dir": tb["dir"].to_numpy(dtype=float),
        "clus": tb["episode_id"].to_numpy(),
        "r_R": (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float),
        "r_R_final": (tb["pnl_bps"] / tb["risk_unit_bps"]).to_numpy(dtype=float),
    }


def run_policy(load: Dict, policy: Dict, w_A: float, w_B: float,
               base_f: float = 1.0, full_output: bool = False):
    """Admission for one (policy, allocation) on the historical book. Returns
    (admitted frame or f array, per-event req_mult)."""
    ba = load["ba"]
    req_mult = np.where(ba["fam"] == "A", w_A, w_B)
    res = _admit_sweep(ba["entry"], ba["exit_"], ba["fam"], ba["dir"],
                       ba["clus"], req_mult, policy, base_f, full_output)
    if full_output:
        res["event_id"] = ba["tb"]["event_id"].to_numpy()
        res["entry_ts"] = ba["tb"]["entry_ts"].to_numpy()
        res["family"] = ba["fam"]
        res["direction"] = ba["dir"]
        res["episode_id"] = ba["clus"]
        res["r_final"] = ba["r_R"]
        res["requested_f"] = base_f * req_mult
        if "split" in ba["tb"].columns:
            res["split"] = ba["tb"]["split"].to_numpy()
        return res
    return res, req_mult


# ---------------------------------------------------------------------------
# Portfolio accounting (XII-XIII): hourly overlap-exact paths
# ---------------------------------------------------------------------------

def hourly_portfolio(load: Dict, admitted_f: np.ndarray,
                     base_f: float) -> np.ndarray:
    """Overlap-exact hourly account return vector from admitted events.
    r_h = base_f * sum over active events of (admitted_f * inc_R_h), where
    admitted_f already carries the family weight (requested heat at base_f=1).
    Zeros outside the union of mark hours."""
    ba = load["ba"]
    tb = ba["tb"]
    hourly_inc = load["hourly_inc"]
    idx_min = idx_max = None
    cols = []
    for i, eid in enumerate(tb["event_id"]):
        f_ = admitted_f[i]
        if f_ <= 0:
            continue
        g = hourly_inc.get(eid)
        if g is None or len(g) == 0:
            continue
        ts = pd.to_datetime(g["mark_time"], utc=True)
        arr = (f_ * base_f * g["inc_R"].to_numpy(dtype=float)).astype(np.float64)
        cols.append((ts, arr))
        i0 = ts.min()
        i1 = ts.max()
        idx_min = i0 if idx_min is None else min(idx_min, i0)
        idx_max = i1 if idx_max is None else max(idx_max, i1)
    if not cols:
        return np.zeros(1)
    full = pd.date_range(idx_min, idx_max, freq="h")
    idx_int = full.to_numpy(dtype="int64")
    total = np.zeros(len(full))
    for ts, arr in cols:
        pos = np.searchsorted(idx_int, ts.to_numpy(dtype="int64"))
        for k, p in enumerate(pos):
            total[p] += arr[k]
    return total


def policy_metrics(load: Dict, admitted_f: np.ndarray, base_f: float,
                   years: float, w_A: float = 0.5, w_B: float = 0.5) -> Dict:
    """Full account metric set for a policy/allocation at base_f (hourly)."""
    r_h = hourly_portfolio(load, admitted_f, base_f)
    eq = np.concatenate([[1.0], np.cumprod(1.0 + r_h)])
    m = equity_metrics(eq, years, hourly=True)
    ba = load["ba"]
    tb = ba["tb"]
    # heat timeline (admitted f per active event per hour)
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True)
    active_f = admitted_f[admitted_f > 0]
    m["n_admitted"] = int(len(active_f))
    m["n_rejected"] = int((admitted_f <= 0).sum())
    # scaled = admitted but below the requested family weight (at base_f=1)
    req = np.where(ba["fam"] == "A", w_A, w_B)
    m["n_scaled"] = int(((admitted_f > 0) &
                         (admitted_f < req - 1e-12)).sum())
    # worst 12h cluster impact (sequential compounding of admitted f*r within cluster)
    clus = ba["clus"]
    fam = ba["fam"]
    direc = ba["dir"]
    r_R = ba["r_R"]
    order = np.argsort(entry.to_numpy(dtype="int64"), kind="stable")
    worst_ep = 0.0
    cluster_ret = {}
    for i in order:
        c = int(clus[i])
        if admitted_f[i] > 0:
            cluster_ret[c] = cluster_ret.get(c, 0.0) + admitted_f[i] * r_R[i]
    for c, v in cluster_ret.items():
        worst_ep = min(worst_ep, v)
    m["worst_episode_pct"] = worst_ep * base_f  # account fraction at base_f
    # heat stats over hours
    heat = _hourly_heat(tb, admitted_f)
    if len(heat):
        m["max_gross_heat"] = float(heat.max())
        m["p95_gross_heat"] = float(np.percentile(heat, 95))
        m["mean_gross_heat"] = float(heat.mean())
    else:
        m["max_gross_heat"] = m["p95_gross_heat"] = m["mean_gross_heat"] = 0.0
    return m


def _hourly_heat(tb: pd.DataFrame, admitted_f: np.ndarray) -> np.ndarray:
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True)
    idx_min = entry.min().floor("h")
    idx_max = exit_.max().ceil("h")
    full = pd.date_range(idx_min, idx_max, freq="h")
    heat = np.zeros(len(full))
    for i, f_ in enumerate(admitted_f):
        if f_ <= 0:
            continue
        e = int(entry.iloc[i].value)
        x = int(exit_.iloc[i].value)
        lo = np.searchsorted(full.to_numpy(dtype="int64"), e)
        hi = np.searchsorted(full.to_numpy(dtype="int64"), x)
        heat[lo:hi] += f_
    return heat


def admitted_returns(load: Dict, admitted_f: np.ndarray) -> np.ndarray:
    """Per-event admitted R contribution (f * r_R) for accounting rows."""
    ba = load["ba"]
    return admitted_f * ba["r_R"]


def hourly_heat_breakdown(tb: pd.DataFrame, admitted_f: np.ndarray) -> Dict[str, np.ndarray]:
    """Exact hourly heat vectors from the admitted book: gross, long (dir=1),
    short (dir=-1), A, B. All in admitted-f units at the reference f level."""
    entry = pd.to_datetime(tb["entry_ts"], utc=True)
    exit_ = pd.to_datetime(tb["exit_ts"], utc=True)
    fam = tb["family"].to_numpy()
    direc = tb["dir"].to_numpy(dtype=float)
    idx_min = entry.min().floor("h")
    idx_max = exit_.max().ceil("h")
    full = pd.date_range(idx_min, idx_max, freq="h")
    idx_int = full.to_numpy(dtype="int64")
    gross = np.zeros(len(full))
    long_h = np.zeros(len(full))
    short_h = np.zeros(len(full))
    a_h = np.zeros(len(full))
    b_h = np.zeros(len(full))
    for i, f_ in enumerate(admitted_f):
        if f_ <= 0:
            continue
        lo = np.searchsorted(idx_int, int(entry.iloc[i].value))
        hi = np.searchsorted(idx_int, int(exit_.iloc[i].value))
        gross[lo:hi] += f_
        if direc[i] == 1.0:
            long_h[lo:hi] += f_
        else:
            short_h[lo:hi] += f_
        if fam[i] == "A":
            a_h[lo:hi] += f_
        else:
            b_h[lo:hi] += f_
    return {"gross": gross, "long": long_h, "short": short_h,
            "A": a_h, "B": b_h}


def episode_peak_heat_from_hourly(tb: pd.DataFrame, admitted_f: np.ndarray,
                                  episode_ledger: pd.DataFrame) -> float:
    """Max gross heat reached inside any single episode (exact hourly)."""
    hv = hourly_heat_breakdown(tb, admitted_f)
    gross = hv["gross"]
    idx = pd.date_range(
        pd.to_datetime(tb["entry_ts"], utc=True).min().floor("h"),
        pd.to_datetime(tb["exit_ts"], utc=True).max().ceil("h"), freq="h")
    idx_int = idx.to_numpy(dtype="int64")
    best = 0.0
    for c, g in episode_ledger.groupby("episode_id"):
        t0 = pd.Timestamp(g["episode_start"].iloc[0]).tz_convert("UTC")
        t1 = pd.Timestamp(g["episode_end"].iloc[0]).tz_convert("UTC")
        lo = np.searchsorted(idx_int, int(t0.value))
        hi = np.searchsorted(idx_int, int(t1.value))
        if hi > lo:
            best = max(best, float(gross[lo:hi].max()))
    return best
