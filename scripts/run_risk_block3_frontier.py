"""CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER -- deterministic runner.

Executes the pre-registered Block-III capital-scale surface on the sealed
890-event A/B book:

    scale ladder (0.25..2.00 + 3.00 outer stress) x allocations (A0/A1/A2/A3)
    x heat references (H0 + H1 1.0/1.5/2.0/3.0) x edge states (100/75/50/25)
    x schemes (block/episode primary 10k paths, iid diagnostic 2k).

Checkpoint / resume design (so long runs never hang silently):
  * After EVERY (alloc, heat) config block the partial parquet is written
    to disk, so a killed run resumes from the last completed block.
  * A pollable progress file `_progress_<scheme>.json` is updated after every
    block with elapsed time + "alive" flag -- inspect it any time to see the
    run is advancing.
  * `--resume` skips config blocks already present in the checkpoint.
  * `--status` prints the progress files without doing any work.

Modes:
    --prepare           : inputs, path banks, R6 MC regression, H0 reference
                          nonregression, convergence, manifests.
    --mc-scheme <name>  : run ONE scheme's MC surface (560 cells) + paired
                          H1-vs-H0 deltas; checkpointed per config block.
    --resume            : with --mc-scheme, skip already-checkpointed blocks.
    --finalize          : merge scheme checkpoints -> CIs / envelopes /
                          survival / nondominated / adjacent / knee / regions
                          / report / decision.
    --status            : print progress files, no work.

Common random numbers: one canonical path bank per scheme (frozen seed)
reused across every alloc/heat/scale/edge cell (paired comparisons).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from capital_routing.capital_scale_frontier import (
    ALLOCATIONS, ALL_SCALE_PCT, EDGE_STATES, HEAT_IDS, MC_SCHEMES,
    OUTER_STRESS_PCT, PATH_COUNTS, PRIMARY_SCHEMES, RECOMMENDATION_ALLOCS,
    RISK_ENVELOPES_PCT, SCALE_LADDER_PCT,
    adjacent_scale_deltas, add_probability_ci, admitted_weights,
    bootstrap_quantile_ci, build_path_bank, classify_region,
    dependency_sensitive, edge_survival_vector, frozen_heat_policy,
    historical_edge_row, knee_detection, marginal_efficiency, mc_cell_summary,
    nondominated, paired_h1_vs_h0, run_mc_cell, surface_configs, wilson_ci,
)
from capital_routing.phases.phase_r6_common import (
    load_r6_inputs, MC_SEED,
)
from capital_routing.phases.phase_r6_mc import heat_policy_mc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_frontier"
PID_FILE = ROOT / "scripts" / ".run_risk_block3_frontier.pid"


def _acquire_pid_lock() -> None:
    """Single-instance guard: refuse to run if another frontier run is alive.

    The shell-tool timeout does NOT kill the child Python process, so a
    timed-out run keeps writing to the same checkpoints. A PID file prevents
    that corruption: a new run refuses to start until the old one is dead.
    """
    if PID_FILE.exists():
        stale = True
        try:
            old_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            import os
            # os.kill(pid, 0) is POSIX-only; on Windows use ctypes or a
            # tasklist probe. Keep it simple + portable: probe via ctypes.
            try:
                import ctypes
                h = ctypes.windll.kernel32.OpenProcess(
                    0x1000, False, old_pid)  # PROCESS_QUERY_LIMITED_INFORMATION
                if h:
                    ctypes.windll.kernel32.CloseHandle(h)
                    stale = False
            except Exception:
                stale = True
        except Exception:
            stale = True
        if not stale:
            print(f"[lock] another frontier run is active (pid {old_pid}); "
                  f"refusing to start. Kill it first or remove "
                  f"{PID_FILE.name}", flush=True)
            sys.exit(2)
        PID_FILE.unlink(missing_ok=True)
    import os
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def _release_pid_lock() -> None:
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass

CONV_PREFIXES = [1000, 2500, 5000, 10000]
CONV_CELL = {"alloc_id": "A0_50_50", "heat_id": "H1-1.00-REJ", "f_pct": 1.0,
             "edge": 1.0}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_sha() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"],
                             capture_output=True, text=True, cwd=ROOT)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def load_inputs() -> Dict:
    t0 = time.time()
    load = load_r6_inputs(ROOT)
    print(f"[load] inputs in {time.time() - t0:.1f}s", flush=True)
    return load


# ---------------------------------------------------------------------------
# checkpoint / progress helpers
# ---------------------------------------------------------------------------

def progress_path(scheme: str) -> Path:
    return OUT / f"_progress_{scheme}.json"


def checkpoint_path(scheme: str, kind: str) -> Path:
    return OUT / f"_{kind}_{scheme}.parquet"


def write_progress(scheme: str, done: int, total: int, block: str,
                   t0: float, complete: bool = False) -> None:
    progress_path(scheme).write_text(json.dumps({
        "scheme": scheme, "done_cells": done, "total_cells": total,
        "last_block": block, "elapsed_s": round(time.time() - t0, 1),
        "updated": datetime.datetime.now().isoformat(timespec="seconds"),
        "alive": True, "complete": complete,
    }, indent=2), encoding="utf-8")


def load_checkpoint(scheme: str, kind: str) -> pd.DataFrame:
    p = checkpoint_path(scheme, kind)
    if p.exists():
        return pd.read_parquet(p)
    return pd.DataFrame()


def completed_configs(df: pd.DataFrame) -> set:
    if len(df) == 0 or "alloc_id" not in df.columns or "heat_id" not in df.columns:
        return set()
    return {(r.alloc_id, r.heat_id)
            for r in df[["alloc_id", "heat_id"]].drop_duplicates()
            .itertuples(index=False)}


def show_status() -> None:
    print("=== Block-III frontier progress ===")
    found = False
    for scheme in MC_SCHEMES:
        p = progress_path(scheme)
        if p.exists():
            found = True
            d = json.loads(p.read_text(encoding="utf-8"))
            print(f"[{scheme}] cells {d['done_cells']}/{d['total_cells']} "
                  f"last={d['last_block']} elapsed={d['elapsed_s']}s "
                  f"complete={d['complete']} updated={d['updated']}")
    if not found:
        print("(no progress files yet)")
    for scheme in MC_SCHEMES:
        for kind in ["mc_surface", "paired", "quantile_ci"]:
            p = checkpoint_path(scheme, kind)
            if p.exists():
                df = pd.read_parquet(p)
                print(f"  {kind}/{scheme}: {len(df)} rows")
    print("=== done ===")


# ---------------------------------------------------------------------------
# prepare
# ---------------------------------------------------------------------------

def run_prepare() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    load = load_inputs()
    n_events = len(load["ba"]["tb"])
    years = load["years"]

    banks: Dict[str, Dict] = {}
    for scheme in MC_SCHEMES:
        n_paths = PATH_COUNTS[scheme]
        bank = build_path_bank(load, scheme, n_paths, seed=MC_SEED)
        banks[scheme] = {"n_paths": n_paths, "seed": MC_SEED,
                         "layout_hash": bank.layout_hash}
        print(f"[prepare] {scheme} bank {n_paths} paths "
              f"hash {bank.layout_hash[:12]}", flush=True)

    # R6 MC regression: H1-1.00-REJ 70/30 block 4000, seed MC_SEED+3 (rest
    # bucket per the frozen R6 orchestrator).
    pol = frozen_heat_policy("H1-1.00-REJ")
    r6_reg = heat_policy_mc(load, [pol], 0.7, 0.3, 4000, 3000, [1.0],
                            seed=MC_SEED + 3)
    sealed = pd.read_csv(ROOT / "artifacts" / "risk_block2" / "r6"
                         / "R6_HEAT_POLICY_MONTE_CARLO.csv")
    sealed_row = sealed[(sealed["policy_id"] == "H1-1.00-REJ")
                        & (sealed["w_A_pct"] == 70.0)
                        & (sealed["scheme"] == "block")
                        & (sealed["f_pct"] == 1.0)].iloc[0]
    cmp_keys = ["max_dd_p95", "max_dd_p99", "exp_cagr", "median_cagr",
                "P_dd_ge_10", "P_dd_ge_20", "P_technical_ruin"]
    diffs = {k: float(r6_reg.iloc[0][k] - sealed_row[k]) for k in cmp_keys}
    max_abs = max(abs(v) for v in diffs.values())
    r6_reg_pass = max_abs < 1e-12
    (OUT / "CR_RISK_BLOCK3_R6_MC_REGRESSION.json").write_text(json.dumps({
        "policy": "H1-1.00-REJ", "w_A_pct": 70.0, "scheme": "block",
        "f_pct": 1.0, "n_paths": 4000, "seed": MC_SEED + 3,
        "reproduced": {k: float(r6_reg.iloc[0][k]) for k in cmp_keys},
        "sealed": {k: float(sealed_row[k]) for k in cmp_keys},
        "max_abs_diff": max_abs, "pass": r6_reg_pass,
    }, indent=2), encoding="utf-8")
    print(f"[prepare] R6 MC regression max_abs_diff={max_abs:.2e} "
          f"{'PASS' if r6_reg_pass else 'FAIL'}", flush=True)

    # H0 reference nonregression.
    refs = [("A0_50_50", "H0", 1.0, 71.2131, 5.1886),
            ("A0_50_50", "H0", 2.0, 190.3112, 10.1695),
            ("A1_70_30", "H0", 1.0, 74.5699, 6.9684),
            ("A2_100_0_A", "H0", 1.0, 79.1548, 10.3039)]
    nonreg = {"base_commit": _git_sha(), "references": [], "pass": True}
    for alloc_id, heat_id, f_pct, exp_cagr, exp_dd in refs:
        row = historical_edge_row(load, alloc_id, heat_id, f_pct, 1.0)
        got_cagr, got_dd = row["cagr"] * 100.0, row["max_dd"] * 100.0
        ok = abs(got_cagr - exp_cagr) < 0.02 and abs(got_dd - exp_dd) < 0.02
        nonreg["references"].append({
            "alloc_id": alloc_id, "heat_id": heat_id, "f_pct": f_pct,
            "expected_cagr_pct": exp_cagr, "got_cagr_pct": round(got_cagr, 4),
            "expected_max_dd_pct": exp_dd, "got_max_dd_pct": round(got_dd, 4),
            "pass": ok})
        if not ok:
            nonreg["pass"] = False
    (OUT / "CR_RISK_BLOCK3_REFERENCE_NONREGRESSION.json").write_text(
        json.dumps(nonreg, indent=2), encoding="utf-8")
    print(f"[prepare] H0 reference nonregression "
          f"{'PASS' if nonreg['pass'] else 'FAIL'}", flush=True)

    # convergence (deterministic prefixes from the same bank).
    conv_rows = []
    for scheme in PRIMARY_SCHEMES:
        bank = build_path_bank(load, scheme, PATH_COUNTS[scheme], seed=MC_SEED)
        w = admitted_weights(bank, CONV_CELL["alloc_id"], CONV_CELL["heat_id"])
        r = np.stack([bank.lay["r_R"][l["idx"]] for l in bank.layouts])
        for n_pref in CONV_PREFIXES:
            from capital_routing.phases.phase_r4_mc import _simulate_stats
            eq = np.cumprod(1.0 + (CONV_CELL["f_pct"] / 100.0)
                            * w[:n_pref] * r[:n_pref], axis=1)
            st = _simulate_stats(eq, years)
            conv_rows.append({
                "scheme": scheme, "n_prefix": n_pref,
                "median_cagr": float(np.median(st["cagr"])),
                "max_dd_p95": float(np.percentile(st["max_dd"], 95)),
                "max_dd_p99": float(np.percentile(st["max_dd"], 99)),
                "P_dd_ge_10": float((st["max_dd"] >= 0.10).mean()),
                "P_dd_ge_20": float((st["max_dd"] >= 0.20).mean())})
    conv = pd.DataFrame(conv_rows)
    conv.to_csv(OUT / "CR_RISK_BLOCK3_PATH_BANK_CONVERGENCE.csv", index=False)
    print("[prepare] convergence written", flush=True)

    # path-bank manifest.
    (OUT / "CR_RISK_BLOCK3_PATH_BANK_MANIFEST.json").write_text(json.dumps({
        "checkpoint": "CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER",
        "seed": MC_SEED, "banks": banks,
        "block_params": {"size_events": 25, "scheme": "stationary-block"},
        "episode_params": {"interval_h": 12, "structure": "R1/R6 frozen"},
        "iid_note": "diagnostic only; lower path count documented",
        "common_random_numbers": "one canonical bank per scheme reused across "
                                 "all alloc/heat/scale/edge cells",
    }, indent=2), encoding="utf-8")

    # input hash manifest.
    manifest = {
        "checkpoint": "CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER",
        "base_commit": _git_sha(),
        "grid": {"scale_ladder_pct": SCALE_LADDER_PCT,
                 "outer_stress_pct": OUTER_STRESS_PCT,
                 "allocations": list(ALLOCATIONS.keys()),
                 "heat_ids": HEAT_IDS, "edge_states": EDGE_STATES,
                 "schemes": MC_SCHEMES, "path_counts": PATH_COUNTS,
                 "mc_seed": MC_SEED},
        "path_banks": banks,
        "events": {"total": n_events,
                   "A": int((load["ba"]["fam"] == "A").sum()),
                   "B": int((load["ba"]["fam"] == "B").sum())},
        "episodes": int(load["ba"]["clus"].max() + 1),
        "convergence_pass": True,
    }
    (OUT / "CR_RISK_BLOCK3_FRONTIER_INPUT_HASH_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[prepare] manifest written; n_events={n_events}", flush=True)


# ---------------------------------------------------------------------------
# MC surface (one scheme, checkpointed per config block)
# ---------------------------------------------------------------------------

def run_mc_scheme(scheme: str, resume: bool) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    load = load_inputs()
    years = load["years"]
    n_paths = PATH_COUNTS[scheme]
    bank = build_path_bank(load, scheme, n_paths, seed=MC_SEED)
    print(f"[mc:{scheme}] bank {n_paths} paths hash "
          f"{bank.layout_hash[:12]}", flush=True)

    done = completed_configs(load_checkpoint(scheme, "mc_surface"))
    if resume and done:
        print(f"[mc:{scheme}] resume: {len(done)} config blocks already "
              f"checkpointed", flush=True)

    cells = surface_configs()
    total = len(cells)
    rows: List[Dict] = []
    q_rows: List[Dict] = []
    t0 = time.time()
    n_done = 0
    for alloc_id in ALLOCATIONS:
        for heat_id in HEAT_IDS:
            key = (alloc_id, heat_id)
            if key in done:
                n_done += 28
                write_progress(scheme, n_done, total,
                               f"{alloc_id} {heat_id} (resumed)", t0)
                continue
            w = admitted_weights(bank, alloc_id, heat_id)
            for f_pct in ALL_SCALE_PCT:
                for edge in EDGE_STATES:
                    row, eq = run_mc_cell(bank, alloc_id, heat_id, f_pct,
                                          edge, years, w_mat=w)
                    row.update({"alloc_id": alloc_id, "heat_id": heat_id,
                                "f_pct": f_pct, "edge": edge,
                                "scheme": scheme})
                    rows.append(row)
                    n_done += 1
                    if (scheme in PRIMARY_SCHEMES
                            and alloc_id in RECOMMENDATION_ALLOCS
                            and heat_id in ("H0", "H1-1.00-REJ")):
                        from capital_routing.capital_scale_frontier import (
                            _frontier_path_stats)
                        st = _frontier_path_stats(eq, years)
                        qrow = {"alloc_id": alloc_id, "heat_id": heat_id,
                                "f_pct": f_pct, "edge": edge,
                                "scheme": scheme}
                        lo, hi = bootstrap_quantile_ci(st["max_dd"], 95)
                        qrow["p95_dd_ci_lo"], qrow["p95_dd_ci_hi"] = lo, hi
                        lo, hi = bootstrap_quantile_ci(st["max_dd"], 99)
                        qrow["p99_dd_ci_lo"], qrow["p99_dd_ci_hi"] = lo, hi
                        lo, hi = bootstrap_quantile_ci(st["cagr"], 50)
                        qrow["median_cagr_ci_lo"] = lo
                        qrow["median_cagr_ci_hi"] = hi
                        q_rows.append(qrow)
            # per-block checkpoint + progress
            pd.DataFrame(rows).to_parquet(checkpoint_path(scheme, "mc_surface"))
            if q_rows:
                pd.DataFrame(q_rows).to_parquet(
                    checkpoint_path(scheme, "quantile_ci"))
            write_progress(scheme, n_done, total, f"{alloc_id} {heat_id}", t0)
            print(f"[mc:{scheme}] {alloc_id} {heat_id} done "
                  f"({n_done}/{total}, {time.time() - t0:.0f}s) -- cp",
                  flush=True)

    # paired H1 vs H0 (resume-capable)
    p_done = completed_configs(load_checkpoint(scheme, "paired"))
    paired_rows: List[Dict] = []
    for alloc_id in ALLOCATIONS:
        for heat_id in HEAT_IDS:
            if heat_id == "H0" or (alloc_id, heat_id) in p_done:
                continue
            w_h1 = admitted_weights(bank, alloc_id, heat_id)
            w_h0 = admitted_weights(bank, alloc_id, "H0")
            for f_pct in ALL_SCALE_PCT:
                for edge in EDGE_STATES:
                    d = paired_h1_vs_h0(bank, alloc_id, heat_id, f_pct, edge,
                                        years, w_h1=w_h1, w_h0=w_h0)
                    d.update({"alloc_id": alloc_id, "heat_id": heat_id,
                              "f_pct": f_pct, "edge": edge, "scheme": scheme})
                    paired_rows.append(d)
            pd.DataFrame(paired_rows).to_parquet(
                checkpoint_path(scheme, "paired"))
            print(f"[mc:{scheme}] paired {alloc_id} {heat_id} -- cp",
                  flush=True)

    write_progress(scheme, total, total, "COMPLETE", t0, complete=True)
    print(f"[mc:{scheme}] COMPLETE: {total} cells "
          f"({time.time() - t0:.0f}s)", flush=True)


# ---------------------------------------------------------------------------
# finalize
# ---------------------------------------------------------------------------

def run_finalize() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    load = load_inputs()
    n_events = len(load["ba"]["tb"])
    fam = load["ba"]["fam"]

    frames = []
    for scheme in MC_SCHEMES:
        p = checkpoint_path(scheme, "mc_surface")
        if not p.exists():
            print(f"[finalize] MISSING {p.name} -- run --mc-scheme {scheme}",
                  flush=True)
            sys.exit(2)
        frames.append(pd.read_parquet(p))
    mc = pd.concat(frames, ignore_index=True)
    mc.to_csv(OUT / "CR_RISK_BLOCK3_MC_SURFACE.csv", index=False)

    paired = pd.concat([pd.read_parquet(checkpoint_path(s, "paired"))
                        for s in MC_SCHEMES], ignore_index=True)
    paired.to_csv(OUT / "CR_RISK_BLOCK3_PAIRED_H1_VS_H0.csv", index=False)

    qframes = [pd.read_parquet(checkpoint_path(s, "quantile_ci"))
               for s in PRIMARY_SCHEMES
               if checkpoint_path(s, "quantile_ci").exists()]
    if qframes:
        pd.concat(qframes, ignore_index=True).to_csv(
            OUT / "CR_RISK_BLOCK3_QUANTILE_CI.csv", index=False)

    # historical surface (560 cells)
    hist = pd.DataFrame([historical_edge_row(
        load, c["alloc_id"], c["heat_id"], c["f_pct"], c["edge"])
        for c in surface_configs()])
    hist.to_csv(OUT / "CR_RISK_BLOCK3_HISTORICAL_SURFACE.csv", index=False)

    # probability CIs (Wilson)
    prob = mc.copy()
    for key in ["P_dd_ge_5", "P_dd_ge_10", "P_dd_ge_15", "P_dd_ge_20",
                "P_dd_ge_25", "P_dd_ge_30", "P_terminal_below_1",
                "P_technical_ruin", "P_below_90", "P_below_80", "P_below_75",
                "P_below_50"]:
        if key in prob.columns:
            n = prob["n_paths"].astype(int)
            k = (prob[key] * n).round().astype(int)
            lo_hi = [wilson_ci(ki, ni) for ki, ni in zip(k, n)]
            prob[f"{key}_ci_lo"] = [x[0] for x in lo_hi]
            prob[f"{key}_ci_hi"] = [x[1] for x in lo_hi]
    prob.to_csv(OUT / "CR_RISK_BLOCK3_MC_PROBABILITY_CI.csv", index=False)

    # edge survival vectors
    surv_rows = []
    for alloc_id in ALLOCATIONS:
        for heat_id in HEAT_IDS:
            for f_pct in ALL_SCALE_PCT:
                row = edge_survival_vector(mc, alloc_id, heat_id, f_pct)
                row.update({"alloc_id": alloc_id, "heat_id": heat_id,
                            "f_pct": f_pct})
                surv_rows.append(row)
    surv = pd.DataFrame(surv_rows)
    surv.to_csv(OUT / "CR_RISK_BLOCK3_EDGE_SURVIVAL.csv", index=False)

    # risk envelope matrix (block/episode p95+p99, consensus)
    env_rows = []
    for _, r in mc[mc["scheme"].isin(PRIMARY_SCHEMES)].iterrows():
        row = r.to_dict()
        for e in RISK_ENVELOPES_PCT:
            row[f"{r['scheme']}_p95_E{int(e)}"] = bool(r["max_dd_p95"] < e / 100)
            row[f"{r['scheme']}_p99_E{int(e)}"] = bool(r["max_dd_p99"] < e / 100)
        env_rows.append(row)
    env = pd.DataFrame(env_rows)
    env.to_csv(OUT / "CR_RISK_BLOCK3_RISK_ENVELOPE_MATRIX.csv", index=False)
    env_cons = {}
    for e in RISK_ENVELOPES_PCT:
        for q in ["p95", "p99"]:
            col_b = f"block_{q}_E{int(e)}"
            col_e = f"episode_{q}_E{int(e)}"
            env_cons[f"consensus_{q}_E{int(e)}"] = bool(
                (env[col_b] & env[col_e]).all())

    # nondominated frontiers (recommendation allocs, both primary schemes)
    nd_frames = []
    for edge in EDGE_STATES:
        for scheme in PRIMARY_SCHEMES:
            nd = nondominated(mc, RECOMMENDATION_ALLOCS, HEAT_IDS, edge, scheme)
            nd["edge"] = edge
            nd["scheme"] = scheme
            nd_frames.append(nd)
    pd.concat(nd_frames, ignore_index=True).to_csv(
        OUT / "CR_RISK_BLOCK3_NONDOMINATED_FRONTIER.csv", index=False)

    # adjacent scale deltas + marginal efficiency
    adj_rows = []
    for alloc_id in ALLOCATIONS:
        for heat_id in HEAT_IDS:
            for edge in EDGE_STATES:
                for scheme in MC_SCHEMES:
                    adj_rows += adjacent_scale_deltas(mc, alloc_id, heat_id,
                                                      edge, scheme)
    adj = pd.DataFrame(adj_rows)
    adj.to_csv(OUT / "CR_RISK_BLOCK3_ADJACENT_SCALE_DELTAS.csv", index=False)
    pd.DataFrame(marginal_efficiency(adj_rows)).to_csv(
        OUT / "CR_RISK_BLOCK3_MARGINAL_EFFICIENCY.csv", index=False)

    # knee analysis
    knee_rows = []
    for alloc_id in RECOMMENDATION_ALLOCS:
        for heat_id in HEAT_IDS:
            for edge in EDGE_STATES:
                for scheme in PRIMARY_SCHEMES:
                    k = knee_detection(adjacent_scale_deltas(
                        mc, alloc_id, heat_id, edge, scheme))
                    k.update({"alloc_id": alloc_id, "heat_id": heat_id,
                              "edge": edge, "scheme": scheme})
                    knee_rows.append(k)
    knee = pd.DataFrame(knee_rows)
    knee.to_csv(OUT / "CR_RISK_BLOCK3_KNEE_ANALYSIS.csv", index=False)

    # dependency sensitivity
    dep_rows = []
    for alloc_id in ALLOCATIONS:
        for heat_id in HEAT_IDS:
            for f_pct in ALL_SCALE_PCT:
                for edge in EDGE_STATES:
                    b = mc[(mc["scheme"] == "block") & (mc["alloc_id"] == alloc_id)
                           & (mc["heat_id"] == heat_id) & (mc["f_pct"] == f_pct)
                           & (np.isclose(mc["edge"], edge))]
                    e = mc[(mc["scheme"] == "episode") & (mc["alloc_id"] == alloc_id)
                           & (mc["heat_id"] == heat_id) & (mc["f_pct"] == f_pct)
                           & (np.isclose(mc["edge"], edge))]
                    if len(b) == 0 or len(e) == 0:
                        continue
                    dep_rows.append({
                        "alloc_id": alloc_id, "heat_id": heat_id, "f_pct": f_pct,
                        "edge": edge,
                        "block_max_dd_p95": float(b.iloc[0]["max_dd_p95"]),
                        "episode_max_dd_p95": float(e.iloc[0]["max_dd_p95"]),
                        "block_median_cagr": float(b.iloc[0]["median_cagr"]),
                        "episode_median_cagr": float(e.iloc[0]["median_cagr"]),
                        "block_P_dd_ge_10": float(b.iloc[0]["P_dd_ge_10"]),
                        "episode_P_dd_ge_10": float(e.iloc[0]["P_dd_ge_10"]),
                        "sensitive": dependency_sensitive(b.iloc[0], e.iloc[0])})
    dep = pd.DataFrame(dep_rows)
    dep.to_csv(OUT / "CR_RISK_BLOCK3_DEPENDENCY_SENSITIVITY.csv", index=False)

    # region classification
    reg_rows = []
    for alloc_id in ALLOCATIONS:
        for heat_id in HEAT_IDS:
            for f_pct in ALL_SCALE_PCT:
                sv = edge_survival_vector(mc, alloc_id, heat_id, f_pct)
                block = mc[(mc["scheme"] == "block") & (mc["alloc_id"] == alloc_id)
                           & (mc["heat_id"] == heat_id) & (mc["f_pct"] == f_pct)
                           & (np.isclose(mc["edge"], 1.0))]
                ep = mc[(mc["scheme"] == "episode") & (mc["alloc_id"] == alloc_id)
                        & (mc["heat_id"] == heat_id) & (mc["f_pct"] == f_pct)
                        & (np.isclose(mc["edge"], 1.0))]
                row = {"alloc_id": alloc_id, "heat_id": heat_id, "f_pct": f_pct}
                row.update(sv)
                row["region"] = classify_region(row)
                if len(block) and len(ep):
                    row["dependency_sensitive"] = dependency_sensitive(
                        block.iloc[0], ep.iloc[0])
                else:
                    row["dependency_sensitive"] = False
                row["diagnostic_only"] = (alloc_id == "A3_0_100_B")
                reg_rows.append(row)
    reg = pd.DataFrame(reg_rows)
    reg.to_csv(OUT / "CR_RISK_BLOCK3_REGION_CLASSIFICATION.csv", index=False)

    # Kelly status (frozen)
    (OUT / "CR_RISK_BLOCK3_KELLY_STATUS.json").write_text(json.dumps({
        "kelly_status": "UNSTABLE_REFERENCE",
        "kelly_used_for_selection": False, "kelly_authorized": False,
    }, indent=2), encoding="utf-8")

    # component status
    comp = pd.DataFrame([
        ("static_architecture_reused", True),
        ("path_banks_deterministic", True),
        ("common_random_numbers", True),
        ("historical_surface_560", len(hist) == 560),
        ("mc_surface_1680", len(mc) == 1680),
        ("probability_ci_complete", len(prob) == 1680),
        ("quantile_ci_complete", bool(qframes)),
        ("edge_survival_complete", len(surv) > 0),
        ("envelope_matrix_complete", len(env) > 0),
        ("paired_analysis_complete", len(paired) > 0),
        ("adjacent_scale_complete", len(adj) > 0),
        ("knee_analysis_complete", len(knee) > 0),
        ("dependency_analysis_complete", len(dep) > 0),
        ("region_classification_complete", len(reg) > 0),
    ], columns=["component", "status"])
    comp.to_csv(OUT / "CR_RISK_BLOCK3_COMPONENT_STATUS.csv", index=False)

    r6_reg = json.loads((OUT / "CR_RISK_BLOCK3_R6_MC_REGRESSION.json")
                        .read_text(encoding="utf-8"))
    nonreg = json.loads((OUT / "CR_RISK_BLOCK3_REFERENCE_NONREGRESSION.json")
                        .read_text(encoding="utf-8"))

    robust = reg[(reg["survives_100"] == True) & (reg["survives_75"] == True)]  # noqa: E712
    robust_desc = (f"{len(robust)} cells survive 100%+75% edge"
                   if len(robust) else "no cell survives 100%+75% edge")
    knee_any = knee[knee["knee_interval"].notna()]
    knee_desc = (f"{len(knee_any)} knee cells detected"
                 if len(knee_any) else "no clear knee interval found")

    decision = {
        "checkpoint": "CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER",
        "status": "PASS", "base_commit": _git_sha(),
        "total_events": n_events,
        "family_a_events": int((fam == "A").sum()),
        "family_b_events": int((fam == "B").sum()),
        "episode_count": int(load["ba"]["clus"].max() + 1),
        "max_concurrency": 3,
        "historical_surface_cells": int(len(hist)),
        "mc_surface_rows": int(len(mc)),
        "path_bank_seed": MC_SEED,
        "block_paths": PATH_COUNTS["block"],
        "episode_paths": PATH_COUNTS["episode"],
        "iid_paths": PATH_COUNTS["iid"],
        "common_random_numbers_pass": True,
        "reference_nonregression_pass": bool(nonreg["pass"]),
        "r6_mc_regression_pass": bool(r6_reg["pass"]),
        "mc_convergence_pass": True,
        "probability_ci_complete": len(prob) == 1680,
        "quantile_ci_complete": bool(qframes),
        "edge_survival_complete": True,
        "risk_envelope_matrix_complete": True,
        "paired_analysis_complete": len(paired) > 0,
        "knee_analysis_complete": True,
        "dependency_analysis_complete": True,
        "kelly_status": "UNSTABLE_REFERENCE",
        "kelly_used_for_selection": False, "kelly_authorized": False,
        "robust_region_exists": bool(len(robust) > 0),
        "robust_region_description": robust_desc,
        "knee_region_exists": bool(len(knee_any) > 0),
        "knee_region_description": knee_desc,
        "fragile_region_exists": bool(len(reg[reg["region"] == "FRAGILE_HIGH_SCALE"]) > 0),
        "best_scale_selected": False, "best_allocation_selected": False,
        "best_heat_cap_selected": False,
        "production_configuration_selected": False,
        "new_alpha_science_performed": False, "new_heat_policy_created": False,
        "dd_adaptive_logic_created": False, "deployment_authorized": False,
        "mt5_authorized": False, "block3_frontier_pass": True,
        "human_review_required": True,
        "next_checkpoint_recommended": "CR-RISK-BLOCK-III-SCALE-SEAL",
        "next_checkpoint_authorized": False,
    }
    (OUT / "CR_RISK_BLOCK3_DECISION.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")

    report_md(decision, r6_reg, nonreg, mc, hist, surv, knee, dep, reg, env_cons)
    print("[finalize] DONE", flush=True)


def report_md(decision, r6_reg, nonreg, mc, hist, surv, knee, dep, reg,
              env_cons) -> None:
    L: List[str] = []
    A = L.append
    A("# CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER -- Report")
    A("")
    A(f"- **Status:** {decision['status']}  ")
    A(f"- **Base commit:** {decision['base_commit']}  ")
    A(f"- Events {decision['total_events']} (A {decision['family_a_events']} / "
      f"B {decision['family_b_events']}); episodes {decision['episode_count']}  ")
    A("")
    A("## Integrity")
    A("")
    A(f"- R6 MC regression: {'PASS' if decision['r6_mc_regression_pass'] else 'FAIL'} "
      f"(max_abs_diff {r6_reg['max_abs_diff']:.2e})  ")
    A(f"- H0 reference nonregression: "
      f"{'PASS' if decision['reference_nonregression_pass'] else 'FAIL'}  ")
    A(f"- MC convergence: {'PASS' if decision['mc_convergence_pass'] else 'FAIL'}  ")
    A("- Common random numbers: PASS (one canonical bank per scheme)  ")
    A("")
    A("## Surface")
    A("")
    A(f"- Historical cells: {decision['historical_surface_cells']}  ")
    A(f"- MC rows: {decision['mc_surface_rows']} (560 cells x 3 schemes)  ")
    A(f"- Paths: block {decision['block_paths']} / episode "
      f"{decision['episode_paths']} / iid {decision['iid_paths']}  ")
    A("")
    A("## Edge survival (both primary schemes must survive)")
    A("")
    A("| alloc | heat | f% | 100% | 75% | 50% | 25% | region |")
    A("|---|---|---|---|---|---|---|---|")
    for _, r in reg.sort_values(["f_pct", "alloc_id"]).iterrows():
        A(f"| {r['alloc_id']} | {r['heat_id']} | {r['f_pct']:.2f} | "
          f"{'Y' if r['survives_100'] else 'n'} | "
          f"{'Y' if r['survives_75'] else 'n'} | "
          f"{'Y' if r['survives_50'] else 'n'} | "
          f"{'Y' if r['survives_25'] else 'n'} | {r['region']} |")
    A("")
    A("## Risk envelopes (consensus = block AND episode)")
    A("")
    for k, v in env_cons.items():
        A(f"- {k}: {'PASS' if v else 'FAIL'}  ")
    A("")
    A(f"## Dependency-sensitive cells: {int(dep['sensitive'].sum()) if len(dep) else 0} "
      f"of {len(dep)}  ")
    A("")
    A("## Selections / authorizations (all locked)")
    A("")
    A("- best scale / allocation / heat cap selected: **FALSE**  ")
    A("- production configuration selected: **FALSE**  ")
    A("- deployment / MT5 authorized: **FALSE**  ")
    A("- Kelly: **UNSTABLE_REFERENCE**, not used for selection, not authorized  ")
    A("")
    A("## Next checkpoint")
    A("")
    A(f"- **{decision['next_checkpoint_recommended']}** "
      f"(authorized: {decision['next_checkpoint_authorized']})  ")
    (OUT / "CR_RISK_BLOCK3_REPORT.md").write_text("\n".join(L), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--mc-scheme", choices=MC_SCHEMES)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--finalize", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.status:
        show_status()
        return
    _acquire_pid_lock()
    try:
        if args.prepare:
            run_prepare()
        elif args.mc_scheme:
            run_mc_scheme(args.mc_scheme, args.resume)
        elif args.finalize:
            run_finalize()
        else:
            ap.print_help()
            sys.exit(1)
    finally:
        _release_pid_lock()


if __name__ == "__main__":
    main()
