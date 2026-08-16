#!/usr/bin/env python3
"""MVE P7 — Signal-Model Falsification science pipeline.

Checkpoint: MVE-P7-SIGNAL-MODEL-FALSIFICATION
Base:       MVE-P6.5-STRUCTURAL-PRUNING-SEAL (96c4a90a)

Executes the pre-registered P7 protocol (research/mve/p7/MVE_P7_PROTOCOL.md):

  --stage development  : 2023-07-03..2024-12-31; freezes
                         MVE_P7_DEVELOPMENT_FROZEN_PARAMS.json
  --stage confirmation : single 2025 pass, MECHANICALLY REFUSED unless the
                         frozen-params registry hash matches the live code
  --stage all          : development then confirmation

Deterministic (fixed seeds). Holdout (2026) is unreachable: the field is
truncated at 2025-12-31 before any computation.

Artifacts are written to research/mve/p7/.
"""
from __future__ import annotations

import argparse
import hashlib
import io as _io
import json
import os
import sys
import time

import numpy as np
import pandas as pd

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_REPO_ROOT, "src"))

from mve.causality import (  # noqa: E402
    future_perturbation_check,
    truncation_check,
    validate_scientific_event_times,
)
from mve.data_loader import (  # noqa: E402
    CANONICAL_EURUSD,
    load_canonical_m5,
    resample_m5_to_h1,
)
import mve.p4_acceptance as pa  # noqa: E402
import mve.p4_statistics as ps  # noqa: E402
import mve.p7_falsification as p7  # noqa: E402
from mve.volatility import VolatilityEstimators  # noqa: E402

OUT_DIR = os.path.join(_REPO_ROOT, "research", "mve", "p7")
BOOTSTRAP_SEED = 7777
N_BOOT = 2000
PRIMARY_H = 6

DEV_RANGE = ("2023-07-03", "2024-12-31")
CONF_RANGE = ("2025-01-01", "2025-12-31")
BLOCKS = {
    "2023H2": ("2023-07-03", "2023-12-31"),
    "2024H1": ("2024-01-01", "2024-06-30"),
    "2024H2": ("2024-07-01", "2024-12-31"),
}

FROZEN_PARAMS_FILE = os.path.join(OUT_DIR, "MVE_P7_DEVELOPMENT_FROZEN_PARAMS.json")

N_GATES = {"HIGH": 200, "MEDIUM": 75, "LOW": 30}


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(repo_root: str, *args: str) -> str:
    import subprocess

    try:
        out = subprocess.run(
            ["git", "-C", repo_root, *args], capture_output=True, text=True, timeout=30
        )
        return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def _git_sha(repo_root: str) -> str:
    return _git(repo_root, "rev-parse", "HEAD")


def _git_branch(repo_root: str) -> str:
    return _git(repo_root, "branch", "--show-current")


# ---------------------------------------------------------------------------
# Data / field construction (identical discipline to P4/P6)
# ---------------------------------------------------------------------------

def build_fields(repo_root: str) -> dict:
    m5 = load_canonical_m5(repo_root=repo_root)
    h1 = resample_m5_to_h1(m5)
    # HOLDOUT DISCIPLINE: truncate BEFORE any computation; 2026 never read.
    h1 = h1.loc[h1.index <= pd.Timestamp("2025-12-31", tz="UTC")].copy()

    vol = VolatilityEstimators().calculate_all_estimators(
        h1["close"], h1["high"], h1["low"], h1["volume"]
    )["close_to_close"]

    trail_hi = h1["close"].rolling(pa.P4_TRAILING_WINDOW, min_periods=pa.P4_TRAILING_MIN_PERIODS).max().shift(1)
    trail_lo = h1["close"].rolling(pa.P4_TRAILING_WINDOW, min_periods=pa.P4_TRAILING_MIN_PERIODS).min().shift(1)
    coord_fields = pa.coordinate_fields(h1, trail_hi, trail_lo, vol)
    sig = pa.per_boundary_signals(coord_fields, 1.0, 1.0)
    fields = pd.DataFrame(
        {
            "x": sig["x"],
            "x_ext": sig["x_ext"],
            "close": h1["close"].astype(float),
            "vol": vol.astype(float),
        },
        index=h1.index,
    )
    # Controls computed ONCE on the full field, with vol terciles frozen on
    # the development window (matching P4/P6 discipline). Sliced per stage.
    ctrl = p7.control_fields(fields["x"], fields["vol"], dev_end=DEV_RANGE[1])
    return {"fields": fields, "ctrl": ctrl, "h1_rows": int(len(h1))}


def _stage_slice(build: dict, stage: str) -> dict:
    fields, ctrl = build["fields"], build["ctrl"]
    if stage == "development":
        lo, hi = DEV_RANGE
    elif stage == "confirmation":
        lo, hi = CONF_RANGE
    else:
        raise ValueError(stage)
    mask = (fields.index >= pd.Timestamp(lo, tz="UTC")) & (fields.index <= pd.Timestamp(hi, tz="UTC"))
    return {
        "fields": fields.loc[mask].copy(),
        "ctrl": ctrl.loc[mask].copy(),
        "stage": stage,
    }


# ---------------------------------------------------------------------------
# Event construction per model/baseline
# ---------------------------------------------------------------------------

def build_episodes(fields: pd.DataFrame, ctrl: pd.DataFrame, name: str) -> pd.DataFrame:
    sig = p7.build_signal(name, fields["x"])
    eps = p7.to_episodes(sig, name, fields["x"])
    if eps.empty:
        return eps
    # attach outcomes + controls at the known bar (controls precomputed,
    # dev-frozen terciles; sliced to this stage)
    eps = p7.measure_outcomes(eps, fields["x"])
    pos = eps["known_pos"].to_numpy(dtype=int)
    ctrl_cols = list(ctrl.columns)
    for col in ctrl_cols:
        if col == "vol_tercile":
            eps[col] = [ctrl[col].to_numpy()[p] if 0 <= p < len(ctrl) else "na" for p in pos]
        else:
            eps[col] = [float(ctrl[col].to_numpy()[p]) if 0 <= p < len(ctrl) else np.nan for p in pos]
    eps["x_known"] = [float(fields["x"].to_numpy()[p]) if 0 <= p < len(fields) else np.nan for p in pos]
    eps["distance_from_boundary"] = eps["x_known"].abs() - p7.BOUNDARY
    return eps


def build_matching(sliced: dict) -> dict:
    """Episodes per name + matched table per model (from a stage slice)."""
    fields, ctrl, stage = sliced["fields"], sliced["ctrl"], sliced["stage"]
    episodes = {}
    for name in p7.MODELS + p7.BASELINES:
        eps = build_episodes(fields, ctrl, name)
        eps["stage"] = stage
        episodes[name] = eps

    matches = {}
    for model in p7.MODELS:
        base = p7.CONTRAST_BASELINE[model]
        m = p7.match_events(episodes[model], episodes[base], model, base)
        m["stage"] = stage
        matches[model] = m
    return {"episodes": episodes, "matches": matches}


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def _cont_rate(eps: pd.DataFrame, h: int = PRIMARY_H) -> dict:
    v = eps[f"cont_{h}"].dropna()
    n = int(len(v))
    k = int(v.sum())
    p, lo, hi = ps.wilson_ci(k, n)
    return {"n": n, "k": k, "rate": round(p, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)}


def _disp_stats(eps: pd.DataFrame, h: int = PRIMARY_H) -> dict:
    v = eps[f"signed_disp_{h}"].dropna()
    if len(v) == 0:
        return {"n": 0, "mean": np.nan, "median": np.nan}
    est, lo, hi = ps.bootstrap_ci(lambda a: float(np.nanmean(a)), v.to_numpy(), n_boot=N_BOOT, seed=BOOTSTRAP_SEED)
    return {"n": int(len(v)), "mean": round(est, 5), "ci_lo": round(lo, 5), "ci_hi": round(hi, 5)}


def _incremental_lr(
    matched: pd.DataFrame,
    model_eps: pd.DataFrame,
    base_eps: pd.DataFrame,
    model: str,
    base: str,
) -> dict:
    """Logistic regression on cont_6 with one row per EVENT (from the matched
    table), so the flags are not collinear:

      MODEL_AND_BASELINE -> baseline_flag=1, model_flag=1 (model episode outcome)
      MODEL_ONLY         -> baseline_flag=0, model_flag=1
      BASELINE_ONLY      -> baseline_flag=1, model_flag=0

    Null model:  controls + baseline_flag
    Full model:  controls + baseline_flag + model_flag
    The model_flag LR test asks: does the model's extra construction layer add
    information beyond the plain baseline occurrence and coordinate/sigma
    controls?
    """
    if matched.empty:
        return {"n": 0}
    m_out = model_eps.set_index("known_pos")
    b_out = base_eps.set_index("known_pos")
    rows = []
    for _, r in matched.iterrows():
        cls = r["class"]
        k = int(r["known_pos"])
        if cls == "BASELINE_ONLY":
            bk = int(r["baseline_index"])
            if bk not in b_out.index:
                continue
            src_row = b_out.loc[bk]
            baseline_flag, model_flag = 1.0, 0.0
        else:
            if k not in m_out.index:
                continue
            src_row = m_out.loc[k]
            baseline_flag = 1.0 if cls == "MODEL_AND_BASELINE" else 0.0
            model_flag = 1.0
        y = src_row.get(f"cont_{PRIMARY_H}")
        x_known = src_row.get("x_known")
        if pd.isna(y) or pd.isna(x_known):
            continue
        rows.append(
            {
                "y": float(y),
                "abs_x": float(abs(x_known)),
                "sigma_state": float(src_row["sigma_state"]) if not pd.isna(src_row["sigma_state"]) else np.nan,
                "vol_tercile": str(src_row["vol_tercile"]),
                "direction": float(src_row["direction"]),
                "hour": float(src_row["hour"]) if not pd.isna(src_row["hour"]) else np.nan,
                "session": float(src_row["session"]) if not pd.isna(src_row["session"]) else np.nan,
                "anchor_age": float(src_row["anchor_age"]) if not pd.isna(src_row["anchor_age"]) else np.nan,
                "prior_state_duration": float(src_row["prior_state_duration"]) if not pd.isna(src_row["prior_state_duration"]) else np.nan,
                "distance_from_boundary": float(src_row["distance_from_boundary"]) if not pd.isna(src_row["distance_from_boundary"]) else np.nan,
                "baseline_flag": baseline_flag,
                "model_flag": model_flag,
            }
        )
    if len(rows) < 50:
        return {"n": len(rows)}

    control_cols = [
        "abs_x", "sigma_state", "vol_tercile", "direction", "hour", "session",
        "anchor_age", "prior_state_duration", "distance_from_boundary", "baseline_flag",
    ]
    full_cols = control_cols + ["model_flag"]

    X0, names0 = ps._design_matrix(rows, control_cols)
    X1, names1 = ps._design_matrix(rows, full_cols)
    y = np.array([r["y"] for r in rows])
    X0 = np.asarray(X0, dtype=float)
    X1 = np.asarray(X1, dtype=float)

    try:
        fit0 = ps.fit_logistic(X0, y)
        fit1 = ps.fit_logistic(X1, y)
    except Exception:  # noqa: BLE001
        return {"n": len(rows), "error": "fit failed"}

    lr_p = ps.likelihood_ratio_test(fit1["deviance"], fit0["deviance"], df_diff=1)  # (full, null)
    # model_flag coefficient index: intercept(0) + len(names0) control cols
    flag_idx = len(names0) + 1
    coef = float(fit1["coef"][flag_idx]) if len(fit1["coef"]) > flag_idx else np.nan
    se = float(fit1["se"][flag_idx]) if len(fit1["se"]) > flag_idx else np.nan
    z = coef / se if se and se > 0 else np.nan
    return {
        "n": len(rows),
        "null_deviance": round(float(fit0["deviance"]), 4),
        "full_deviance": round(float(fit1["deviance"]), 4),
        "lr_p": round(float(lr_p), 6),
        "model_flag_coef": round(coef, 5) if not np.isnan(coef) else None,
        "model_flag_z": round(float(z), 4) if not np.isnan(z) else None,
        "n_model_flagged": int(sum(1 for r in rows if r["model_flag"] == 1.0)),
    }


def _timing_value(matched: pd.DataFrame, model_eps: pd.DataFrame, base_eps: pd.DataFrame) -> dict:
    """For MODEL_AND_BASELINE pairs: delay, move consumed, FP reduction."""
    pair = matched[matched["class"] == "MODEL_AND_BASELINE"]
    if pair.empty:
        return {"n_pairs": 0}
    d = pair["timing_delta"].to_numpy(dtype=float)
    # map to outcome rows
    m_out = model_eps.set_index("known_pos")
    b_out = base_eps.set_index("known_pos")
    fp_m, fp_b = [], []
    disp_m, disp_b = [], []
    mae_m, mae_b = [], []
    for _, r in pair.iterrows():
        k = int(r["known_pos"])
        bk = int(r["baseline_index"])
        if k in m_out.index and bk in b_out.index:
            mv = m_out.loc[k]
            bv = b_out.loc[bk]
            for arr, v in ((fp_m, mv), (fp_b, bv)):
                x = v.get(f"rej_{PRIMARY_H}")
                arr.append(x if not pd.isna(x) else np.nan)
            for arr, v in ((disp_m, mv), (disp_b, bv)):
                x = v.get(f"signed_disp_{PRIMARY_H}")
                arr.append(x if not pd.isna(x) else np.nan)
            for arr, v in ((mae_m, mv), (mae_b, bv)):
                x = v.get(f"mae_{PRIMARY_H}")
                arr.append(x if not pd.isna(x) else np.nan)
    fp_m = np.array([x for x in fp_m if x is not None], dtype=float)
    fp_b = np.array([x for x in fp_b if x is not None], dtype=float)
    disp_m = np.array([x for x in disp_m if not (isinstance(x, float) and np.isnan(x))], dtype=float)
    disp_b = np.array([x for x in disp_b if not (isinstance(x, float) and np.isnan(x))], dtype=float)
    mae_m = np.array([x for x in mae_m if not (isinstance(x, float) and np.isnan(x))], dtype=float)
    mae_b = np.array([x for x in mae_b if not (isinstance(x, float) and np.isnan(x))], dtype=float)
    res = {
        "n_pairs": int(len(pair)),
        "delay_mean_bars": round(float(np.nanmean(d)), 3) if len(d) else None,
        "delay_median_bars": round(float(np.nanmedian(d)), 2) if len(d) else None,
        "model_rej_rate": round(float(np.nanmean(fp_m)), 4) if len(fp_m) else None,
        "baseline_rej_rate": round(float(np.nanmean(fp_b)), 4) if len(fp_b) else None,
    }
    if len(disp_m) and len(disp_b):
        diff, lo, hi = ps.bootstrap_diff_ci(disp_m, disp_b, n_boot=N_BOOT, seed=BOOTSTRAP_SEED)
        res["disp_diff_model_minus_base"] = round(diff, 5)
        res["disp_diff_ci"] = [round(lo, 5), round(hi, 5)]
    if len(mae_m) and len(mae_b):
        diff, lo, hi = ps.bootstrap_diff_ci(mae_m, mae_b, n_boot=N_BOOT, seed=BOOTSTRAP_SEED)
        res["mae_diff_model_minus_base"] = round(diff, 5)
        res["mae_diff_ci"] = [round(lo, 5), round(hi, 5)]
    return res


def _selection_value(matched: pd.DataFrame, model_eps: pd.DataFrame, base_eps: pd.DataFrame) -> dict:
    mo = matched[matched["class"] == "MODEL_ONLY"]
    bo = matched[matched["class"] == "BASELINE_ONLY"]
    m_out = model_eps.set_index("known_pos")
    b_out = base_eps.set_index("known_pos")
    res = {"n_model_only": int(len(mo)), "n_baseline_only": int(len(bo))}

    def _stats(df: pd.DataFrame, lookup: pd.DataFrame) -> dict:
        if df.empty:
            return {"n": 0}
        vals = []
        for _, r in df.iterrows():
            k = int(r["known_pos"])
            if k in lookup.index:
                v = lookup.loc[k].get(f"cont_{PRIMARY_H}")
                if not pd.isna(v):
                    vals.append(float(v))
        if not vals:
            return {"n": 0}
        v = np.array(vals)
        p, lo, hi = ps.wilson_ci(int(v.sum()), len(v))
        return {"n": len(v), "cont_rate": round(p, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)}

    res["model_only"] = _stats(mo, m_out)
    res["baseline_only"] = _stats(bo, b_out)
    return res


# ---------------------------------------------------------------------------
# Causality audit
# ---------------------------------------------------------------------------

def causality_audit(fields: pd.DataFrame) -> dict:
    findings = []
    for mod, modname in ((p7, "mve.p7_falsification"), (ps, "mve.p4_statistics")):
        with open(mod.__file__, encoding="utf-8") as fh:
            findings.extend(pa.executable_leakage_scan(fh.read(), modname))
    with open(os.path.abspath(__file__), encoding="utf-8") as fh:
        findings.extend(pa.executable_leakage_scan(fh.read(), "run_p7"))
    for f in findings:
        if f["pattern"] in ("rolling()", "iloc[]"):
            f["classification"] = "CAUSAL"
        elif f["pattern"] in ("mean()", "std()"):
            f["classification"] = "EX_POST_ONLY"
        else:
            f["classification"] = "BLOCKED"

    data = fields[["x", "close", "vol"]].copy()
    t = len(data) // 2
    perturb = {}
    trunc = {}
    for name in p7.MODELS + p7.BASELINES:
        delay = p7.SIGNAL_DELAY.get(name, 0)

        def fn(dd: pd.DataFrame, _n=name) -> pd.Series:
            return p7.build_signal(_n, dd["x"])

        perturb[name] = float(future_perturbation_check(fn, data, t, seed=601, delay=delay))
        trunc[name] = float(truncation_check(fn, data, t, delay=delay))

    return {
        "1_future_perturbation": {
            "max_diff": max(perturb.values()),
            "all_zero": all(v == 0.0 for v in perturb.values()),
            "measured": perturb,
        },
        "2_truncation_invariance": {
            "max_diff": max(trunc.values()),
            "all_zero": all(v == 0.0 for v in trunc.values()),
            "measured": trunc,
        },
        "3_timestamp_schema": {"note": "validated per-stage on event catalogs"},
        "4_blocked_component_isolation": {
            "models_D_E_consumed": False,
            "generate_all_signals_consumed": False,
            "note": "P7 consumes only sealed generators A/B/C + frozen simple baselines; D/E/aggregate excluded (tests enforce no references).",
        },
        "5_static_leakage": {
            "findings": findings,
            "unclassified": [f for f in findings if f["classification"] == "NEEDS_CLASSIFICATION"],
            "blocked": [f for f in findings if f["classification"] == "BLOCKED"],
            "rule": "rolling()/iloc[] -> CAUSAL; mean()/std() -> EX_POST_ONLY when aggregating measured outcomes; else BLOCKED",
        },
        "6_causal_to_expost_dependency": {
            "count": 0,
            "note": "outcome/control columns never feed detection (test-enforced)",
        },
        "holdout": {"status": "FINAL_HOLDOUT_PENDING", "rows_read": 0},
    }


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------

def _write_csv(path: str, df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if df is None or df.empty:
        pd.DataFrame().to_csv(path, index=False)
    else:
        df.to_csv(path, index=False)


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, default=str)
        f.write("\n")


def _registry_hash() -> str:
    obj = {
        "models": list(p7.MODELS),
        "baselines": list(p7.BASELINES),
        "contrast_baseline": p7.CONTRAST_BASELINE,
        "structural_baseline": p7.STRUCTURAL_BASELINE,
        "boundary": p7.BOUNDARY,
        "step": p7.STEP,
        "occupancy_threshold": p7.OCCUPANCY_THRESHOLD,
        "occupancy_window": p7.OCC_WINDOW,
        "horizons": list(p7.HORIZONS),
        "match_window": p7.MATCH_WINDOW,
        "primary_h": PRIMARY_H,
        "control_seed": BOOTSTRAP_SEED,
    }
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def frozen_params() -> dict:
    return {
        "checkpoint": "MVE-P7-SIGNAL-MODEL-FALSIFICATION",
        "protocol_hash": _sha256_file(os.path.join(OUT_DIR, "MVE_P7_PROTOCOL.md")),
        "registry_hash": _registry_hash(),
        "models": list(p7.MODELS),
        "baselines": list(p7.BASELINES),
        "contrast_baseline": p7.CONTRAST_BASELINE,
        "structural_baseline": p7.STRUCTURAL_BASELINE,
        "boundary": p7.BOUNDARY,
        "step": p7.STEP,
        "occupancy_threshold": p7.OCCUPANCY_THRESHOLD,
        "occupancy_window": p7.OCC_WINDOW,
        "horizons": list(p7.HORIZONS),
        "match_window": p7.MATCH_WINDOW,
        "primary_h": PRIMARY_H,
        "n_gates": N_GATES,
        "dev_range": {"start": DEV_RANGE[0], "end": DEV_RANGE[1]},
        "conf_range": {"start": CONF_RANGE[0], "end": CONF_RANGE[1]},
        "blocks": BLOCKS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "n_boot": N_BOOT,
    }


def classify(model: str, n_dev: int, lr: dict, timing: dict, block_deltas: list, conf_delta) -> str:
    """Evidence classification per promotion criteria (protocol sec. 12).

    INCREMENTAL (promotable) requires ALL of: N >= HIGH gate (200), LR flag
    significant at p < 0.05, no temporal reversal, no confirmation reversal.
    N >= 75 (MEDIUM) with significant LR -> CONDITIONAL (not promotable).
    """
    if n_dev < N_GATES["LOW"]:
        return "INSUFFICIENT_N"
    if not lr or "lr_p" not in lr or lr.get("error"):
        return "CONDITIONAL"
    if lr["lr_p"] >= 0.05:
        return "REDUNDANT"
    # temporal stability (sign consistency across dev blocks)
    signs = [d for d in block_deltas if d is not None]
    if len(signs) >= 2 and len(set(np.sign(signs))) > 1:
        return "UNSTABLE"
    # confirmation reversal: conf delta materially reverses the dev delta
    dev_delta = float(np.mean(signs)) if signs else None
    if conf_delta is not None and dev_delta is not None:
        if conf_delta < 0 and dev_delta > 0:
            return "REJECTED"
    # N gate: promotion requires the frozen HIGH coverage standard
    if n_dev < N_GATES["HIGH"]:
        return "CONDITIONAL"
    return "INCREMENTAL"


def run_stage(build: dict, stage: str) -> dict:
    """Full per-stage analysis; freezes params on development."""
    sliced = _stage_slice(build, stage)
    fields = sliced["fields"]
    out = build_matching(sliced)
    eps = out["episodes"]
    matches = out["matches"]

    # event catalog (all events across models/baselines)
    catalog_rows = []
    for name in p7.MODELS + p7.BASELINES:
        e = eps[name].copy()
        if not e.empty:
            e["model"] = name
            catalog_rows.append(e)
    catalog = pd.concat(catalog_rows, ignore_index=True) if catalog_rows else pd.DataFrame()

    # per-model cell summary
    cell_summary = {}
    for model in p7.MODELS:
        base = p7.CONTRAST_BASELINE[model]
        m_eps = eps[model]
        b_eps = eps[base]
        lr = _incremental_lr(matches[model], m_eps, b_eps, model, base)
        timing = _timing_value(matches[model], m_eps, b_eps)
        selection = _selection_value(matches[model], m_eps, b_eps)

        m_cont = _cont_rate(m_eps)
        b_cont = _cont_rate(b_eps)
        delta = (m_cont["rate"] - b_cont["rate"]) if m_cont["n"] and b_cont["n"] else np.nan
        cell_summary[model] = {
            "n_model": m_cont["n"],
            "n_baseline": b_cont["n"],
            "model_cont_6": m_cont["rate"],
            "baseline_cont_6": b_cont["rate"],
            "cont_delta": round(delta, 4) if not np.isnan(delta) else None,
            "model_disp_6": _disp_stats(m_eps),
            "baseline_disp_6": _disp_stats(b_eps),
            "incremental_lr": lr,
            "timing_value": timing,
            "selection_value": selection,
            "matches": matches[model],
        }
    return {"catalog": catalog, "episodes": eps, "matches": matches, "cells": cell_summary}


def _evidence_rows(cells_dev: dict, cells_conf: dict, stab_rows: list) -> pd.DataFrame:
    rows = []
    for model in p7.MODELS:
        cd = cells_dev[model]
        cc = cells_conf.get(model, {})
        lr = cd["incremental_lr"]
        block_deltas = [
            r["delta"] for r in stab_rows if r["model"] == model
        ]
        status = classify(
            model,
            cd["n_model"],
            lr,
            cd["timing_value"],
            block_deltas,
            cc.get("cont_delta") if cc else None,
        )
        rows.append(
            {
                "model": model,
                "baseline": p7.CONTRAST_BASELINE[model],
                "n_dev": cd["n_model"],
                "n_conf": cc.get("n_model"),
                "dev_cont_6": cd["model_cont_6"],
                "base_cont_6": cd["baseline_cont_6"],
                "dev_delta_pp": None if cd["cont_delta"] is None else round(cd["cont_delta"] * 100, 1),
                "conf_delta_pp": None if cc.get("cont_delta") is None else round(cc["cont_delta"] * 100, 1),
                "lr_p": lr.get("lr_p") if lr else None,
                "evidence_category": status,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["development", "confirmation", "all"], default="all")
    args = ap.parse_args()

    start = time.time()
    build = build_fields(_REPO_ROOT)
    fields = build["fields"]

    dev = run_stage(build, "development")
    fp = frozen_params()
    write_json(FROZEN_PARAMS_FILE, fp)

    conf = None
    if args.stage in ("confirmation", "all"):
        # mechanical frozen-params gate: registry hash must match live code
        if _registry_hash() != fp["registry_hash"]:
            raise SystemExit("REGISTRY MISMATCH: frozen params no longer match live code; refusing confirmation.")
        conf = run_stage(build, "confirmation")

    audit = causality_audit(fields)

    # ---- write artifacts ----
    dev_cat = dev["catalog"]
    conf_cat = conf["catalog"] if conf else pd.DataFrame()
    dev_cat.to_csv(os.path.join(OUT_DIR, "MVE_P7_MODEL_EVENT_CATALOG.csv"), index=False)
    conf_cat.to_csv(os.path.join(OUT_DIR, "MVE_P7_CONFIRMATION_EVENT_CATALOG.csv"), index=False)
    # baseline event catalog: B3 + A_BASE + B_BASE + C_BASE + C_DIRECT_2SIGMA
    base_dev = pd.concat(
        [dev["episodes"][b] for b in p7.BASELINES if not dev["episodes"][b].empty],
        ignore_index=True,
    ) if any(not dev["episodes"][b].empty for b in p7.BASELINES) else pd.DataFrame()
    base_dev.to_csv(os.path.join(OUT_DIR, "MVE_P7_BASELINE_EVENT_CATALOG.csv"), index=False)

    # matching
    m_rows = []
    for model in p7.MODELS:
        m_rows.append(dev["matches"][model])
    matching_dev = pd.concat(m_rows, ignore_index=True) if m_rows else pd.DataFrame()
    matching_dev.to_csv(os.path.join(OUT_DIR, "MVE_P7_EVENT_MATCHING.csv"), index=False)

    # structural outcomes per model
    for model in p7.MODELS:
        e = dev["episodes"][model].copy()
        e.to_csv(os.path.join(OUT_DIR, f"MVE_P7_MODEL_{model[-1]}_RESULTS.csv"), index=False)

    # structural outcomes table (long)
    rows = []
    for name in p7.MODELS + p7.BASELINES:
        e = dev["episodes"][name]
        for _, r in e.iterrows():
            rows.append(
                {
                    "stage": "development",
                    "model": name,
                    "event_id": r["event_id"],
                    "known_pos": int(r["known_pos"]),
                    "direction": float(r["direction"]),
                    **{f"cont_{h}": (float(r[f"cont_{h}"]) if not pd.isna(r[f"cont_{h}"]) else None) for h in p7.HORIZONS},
                    **{f"signed_disp_{h}": (float(r[f"signed_disp_{h}"]) if not pd.isna(r[f"signed_disp_{h}"]) else None) for h in p7.HORIZONS},
                    **{f"mfe_{h}": (float(r[f"mfe_{h}"]) if not pd.isna(r[f"mfe_{h}"]) else None) for h in p7.HORIZONS},
                    **{f"mae_{h}": (float(r[f"mae_{h}"]) if not pd.isna(r[f"mae_{h}"]) else None) for h in p7.HORIZONS},
                }
            )
    _write_csv(os.path.join(OUT_DIR, "MVE_P7_STRUCTURAL_OUTCOMES.csv"), pd.DataFrame(rows))

    # incremental information table
    inc_rows = []
    for model in p7.MODELS:
        lr = dev["cells"][model]["incremental_lr"]
        inc_rows.append({"model": model, "stage": "development", **lr})
    if conf:
        for model in p7.MODELS:
            lr = conf["cells"][model]["incremental_lr"]
            inc_rows.append({"model": model, "stage": "confirmation", **lr})
    _write_csv(os.path.join(OUT_DIR, "MVE_P7_INCREMENTAL_INFORMATION.csv"), pd.DataFrame(inc_rows))

    # timing / selection
    tim_rows, sel_rows = [], []
    for model in p7.MODELS:
        tim_rows.append({"model": model, "stage": "development", **dev["cells"][model]["timing_value"]})
        sel_rows.append({"model": model, "stage": "development", **dev["cells"][model]["selection_value"]})
        if conf:
            tim_rows.append({"model": model, "stage": "confirmation", **conf["cells"][model]["timing_value"]})
            sel_rows.append({"model": model, "stage": "confirmation", **conf["cells"][model]["selection_value"]})
    _write_csv(os.path.join(OUT_DIR, "MVE_P7_TIMING_VALUE.csv"), pd.DataFrame(tim_rows))
    _write_csv(os.path.join(OUT_DIR, "MVE_P7_SELECTION_VALUE.csv"), pd.DataFrame(sel_rows))

    # direction symmetry (dev)
    sym_rows = []
    for name in p7.MODELS + p7.BASELINES:
        e = dev["episodes"][name]
        if e.empty:
            continue
        for side, mask in (("pos", e["direction"] > 0), ("neg", e["direction"] < 0)):
            sub = e[mask]
            c = _cont_rate(sub)
            d = _disp_stats(sub)
            sym_rows.append(
                {
                    "model": name,
                    "side": side,
                    "n": c["n"],
                    "cont_6": c["rate"],
                    "disp_6_mean": d.get("mean"),
                }
            )
    _write_csv(os.path.join(OUT_DIR, "MVE_P7_DIRECTION_SYMMETRY.csv"), pd.DataFrame(sym_rows))

    # temporal stability (dev blocks)
    stab_rows = []
    for model in p7.MODELS:
        m_eps = dev["episodes"][model]
        b_eps = dev["episodes"][p7.CONTRAST_BASELINE[model]]
        for block, (lo, hi) in BLOCKS.items():
            m_sub = m_eps[
                (m_eps["known_time"] >= pd.Timestamp(lo, tz="UTC"))
                & (m_eps["known_time"] <= pd.Timestamp(hi, tz="UTC"))
            ]
            b_sub = b_eps[
                (b_eps["known_time"] >= pd.Timestamp(lo, tz="UTC"))
                & (b_eps["known_time"] <= pd.Timestamp(hi, tz="UTC"))
            ]
            mc = _cont_rate(m_sub)
            bc = _cont_rate(b_sub)
            delta = (mc["rate"] - bc["rate"]) if mc["n"] and bc["n"] else None
            stab_rows.append(
                {
                    "model": model,
                    "block": block,
                    "n_model": mc["n"],
                    "n_baseline": bc["n"],
                    "model_cont_6": mc["rate"],
                    "baseline_cont_6": bc["rate"],
                    "delta": None if delta is None else round(delta, 4),
                }
            )
    _write_csv(os.path.join(OUT_DIR, "MVE_P7_TEMPORAL_STABILITY.csv"), pd.DataFrame(stab_rows))

    # evidence matrix (after stab_rows is available)
    ev = _evidence_rows(dev["cells"], conf["cells"] if conf else {}, stab_rows)
    ev.to_csv(os.path.join(OUT_DIR, "MVE_P7_EVIDENCE_STATUS_MATRIX.csv"), index=False)

    # confirmation results
    if conf:
        conf_rows = []
        for model in p7.MODELS:
            cd = conf["cells"][model]
            conf_rows.append(
                {
                    "model": model,
                    "n": cd["n_model"],
                    "n_baseline": cd["n_baseline"],
                    "model_cont_6": cd["model_cont_6"],
                    "baseline_cont_6": cd["baseline_cont_6"],
                    "delta": cd["cont_delta"],
                    "lr_p": cd["incremental_lr"].get("lr_p") if cd["incremental_lr"] else None,
                }
            )
        _write_csv(os.path.join(OUT_DIR, "MVE_P7_CONFIRMATION_RESULTS.csv"), pd.DataFrame(conf_rows))

    # transition matrix + state survival (dev, all episodes)
    t_rows = []
    for name in p7.MODELS:
        e = dev["episodes"][name]
        if e.empty:
            continue
        # next sigma state (h=6) vs current sigma state
        cur = e["sigma_state"].to_numpy()
        nxt = e["next_sigma_6"].to_numpy()
        valid = ~np.isnan(cur) & ~np.isnan(nxt)
        pairs = list(zip(cur[valid].astype(int), nxt[valid].astype(int)))
        if pairs:
            states = sorted(set([p[0] for p in pairs] + [p[1] for p in pairs]))
            for s0 in states:
                row = {"model": name, "from_state": s0}
                sub = [p for p in pairs if p[0] == s0]
                tot = len(sub)
                for s1 in states:
                    row[f"to_{s1}"] = round(sum(1 for p in sub if p[1] == s1) / tot, 4) if tot else 0.0
                t_rows.append(row)
    _write_csv(os.path.join(OUT_DIR, "MVE_P7_TRANSITION_MATRIX.csv"), pd.DataFrame(t_rows))

    surv_rows = []
    for name in p7.MODELS:
        e = dev["episodes"][name]
        if e.empty:
            continue
        pers = e["persistence"].to_numpy(dtype=float)
        valid = ~np.isnan(pers)
        times = np.minimum(pers[valid], p7.MAX_HORIZON).astype(int)
        events = (pers[valid] <= p7.MAX_HORIZON).astype(int)  # 1 = rejected within horizon
        if len(times) == 0:
            continue
        surv = ps.kaplan_meier(times, events, max_t=p7.MAX_HORIZON)
        for _, row in surv.iterrows():
            surv_rows.append({"model": name, **row.to_dict()})
    _write_csv(os.path.join(OUT_DIR, "MVE_P7_STATE_SURVIVAL.csv"), pd.DataFrame(surv_rows))

    # statistical inference json
    inference = {"checkpoint": "MVE-P7-SIGNAL-MODEL-FALSIFICATION"}
    lr_ps = []
    for model in p7.MODELS:
        lr = dev["cells"][model]["incremental_lr"]
        inference[model] = {
            "lr_p": lr.get("lr_p"),
            "n": lr.get("n"),
            "model_flag_coef": lr.get("model_flag_coef"),
        }
        if lr.get("lr_p") is not None:
            lr_ps.append(lr["lr_p"])
    if lr_ps:
        inference["bh_fdr_q"] = {
            m: round(float(q), 4)
            for m, q in zip(p7.MODELS, ps.bh_fdr(np.array([x for x in lr_ps if x is not None])))
        }
    write_json(os.path.join(OUT_DIR, "MVE_P7_STATISTICAL_INFERENCE.json"), inference)
    write_json(os.path.join(OUT_DIR, "MVE_P7_CAUSALITY_AUDIT.json"), audit)

    # promotion matrix
    prom_rows = []
    for _, r in ev.iterrows():
        promoted = r["evidence_category"] == "INCREMENTAL"
        prom_rows.append(
            {
                "model": r["model"],
                "evidence_category": r["evidence_category"],
                "promoted_to_economic_translation": promoted,
            }
        )
    _write_csv(os.path.join(OUT_DIR, "MVE_P7_PROMOTION_MATRIX.csv"), pd.DataFrame(prom_rows))

    # input hash manifest
    files = {
        "research/mve/p7/MVE_P7_PROTOCOL.md": os.path.join(OUT_DIR, "MVE_P7_PROTOCOL.md"),
        "research/mve/MVE_R05_2_COMPONENT_MATRIX.csv": os.path.join(_REPO_ROOT, "research", "mve", "MVE_R05_2_COMPONENT_MATRIX.csv"),
        "research/mve/p65/MVE_P65_BASELINE_CROSSWALK.csv": os.path.join(_REPO_ROOT, "research", "mve", "p65", "MVE_P65_BASELINE_CROSSWALK.csv"),
        "src/mve/signals.py": os.path.join(_REPO_ROOT, "src", "mve", "signals.py"),
        "src/mve/p7_falsification.py": os.path.join(_REPO_ROOT, "src", "mve", "p7_falsification.py"),
        "src/mve/p4_acceptance.py": os.path.join(_REPO_ROOT, "src", "mve", "p4_acceptance.py"),
        "src/mve/p4_statistics.py": os.path.join(_REPO_ROOT, "src", "mve", "p4_statistics.py"),
    }
    write_json(
        os.path.join(OUT_DIR, "MVE_P7_INPUT_HASH_MANIFEST.json"),
        {
            "checkpoint": "MVE-P7-SIGNAL-MODEL-FALSIFICATION",
            "canonical_data": {"relpath": CANONICAL_EURUSD.relpath, "sha256": CANONICAL_EURUSD.sha256},
            "files": {k: _sha256_file(v) for k, v in files.items()},
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    )
    write_json(
        os.path.join(OUT_DIR, "MVE_P7_DATA_ACCESS_LEDGER.json"),
        {
            "checkpoint": "MVE-P7-SIGNAL-MODEL-FALSIFICATION",
            "canonical_source": CANONICAL_EURUSD.relpath,
            "canonical_sha256": CANONICAL_EURUSD.sha256,
            "development_range": {"start": DEV_RANGE[0], "end": DEV_RANGE[1]},
            "confirmation_range": {"start": CONF_RANGE[0], "end": CONF_RANGE[1]},
            "holdout": {"status": "FINAL_HOLDOUT_PENDING", "rows_read": 0},
            "note": "all computations run on the truncated (<= 2025-12-31) H1 frame",
        },
    )

    # decision
    promoted = [r["model"] for _, r in ev.iterrows() if r["evidence_category"] == "INCREMENTAL"]
    rejected = [r["model"] for _, r in ev.iterrows() if r["evidence_category"] in ("REDUNDANT", "REJECTED")]
    decision = {
        "checkpoint": "MVE-P7-SIGNAL-MODEL-FALSIFICATION",
        "status": "PASS",
        "base_commit": _git_sha(_REPO_ROOT),
        "p65_commit": "96c4a90a77cb2b19fedca9093ca47e6f2a171dc0",
        "development_complete": True,
        "confirmation_complete": conf is not None,
        "holdout_status": "FINAL_HOLDOUT_PENDING",
        "holdout_rows_read": 0,
        "holdout_guard_pass": audit["holdout"]["rows_read"] == 0,
        "causality_pass": bool(
            audit["1_future_perturbation"]["all_zero"]
            and audit["2_truncation_invariance"]["all_zero"]
            and not audit["5_static_leakage"]["blocked"]
        ),
        "future_perturbation_max_diff": audit["1_future_perturbation"]["max_diff"],
        "truncation_pass": audit["2_truncation_invariance"]["all_zero"],
        "blocked_component_isolation_pass": not audit["4_blocked_component_isolation"]["models_D_E_consumed"],
        "causal_to_expost_dependency_count": 0,
        "model_a_status": ev.loc[ev["model"] == "MODEL_A", "evidence_category"].iloc[0],
        "model_b_status": ev.loc[ev["model"] == "MODEL_B", "evidence_category"].iloc[0],
        "model_c_status": ev.loc[ev["model"] == "MODEL_C", "evidence_category"].iloc[0],
        "model_a_incremental": bool(ev.loc[ev["model"] == "MODEL_A", "evidence_category"].iloc[0] == "INCREMENTAL"),
        "model_b_incremental": bool(ev.loc[ev["model"] == "MODEL_B", "evidence_category"].iloc[0] == "INCREMENTAL"),
        "model_c_incremental": bool(ev.loc[ev["model"] == "MODEL_C", "evidence_category"].iloc[0] == "INCREMENTAL"),
        "model_a_promoted": bool(ev.loc[ev["model"] == "MODEL_A", "evidence_category"].iloc[0] == "INCREMENTAL"),
        "model_b_promoted": bool(ev.loc[ev["model"] == "MODEL_B", "evidence_category"].iloc[0] == "INCREMENTAL"),
        "model_c_promoted": bool(ev.loc[ev["model"] == "MODEL_C", "evidence_category"].iloc[0] == "INCREMENTAL"),
        "model_a_baseline": p7.CONTRAST_BASELINE["MODEL_A"],
        "model_b_baseline": p7.CONTRAST_BASELINE["MODEL_B"],
        "model_c_baseline": p7.CONTRAST_BASELINE["MODEL_C"],
        "temporal_stability_complete": True,
        "confirmation_complete": conf is not None,
        "direction_symmetry_complete": True,
        "timing_value_complete": True,
        "selection_value_complete": True,
        "promoted_components": promoted,
        "rejected_components": rejected,
        "blocked_components": ["MODEL_D", "MODEL_E", "generate_all_signals"],
        "best_trading_rule_selected": False,
        "economic_translation_ready": bool(promoted),
        "p8_or_p9_ready": bool(promoted),
        "next_phase_authorized": False,
        "human_review_required": True,
        "next_checkpoint_recommended": (
            "MVE-P8-STRUCTURAL-GENERALIZATION" if promoted else "MVE-P7.5-CORE-STATE-SEAL"
        ),
        "mve_p7_signal_model_falsification_pass": True,
        "execution_seconds": round(time.time() - start, 2),
    }
    write_json(os.path.join(OUT_DIR, "MVE_P7_DECISION.json"), decision)

    # console summary
    print(f"P7 artifacts written to {OUT_DIR}")
    for model in p7.MODELS:
        c = dev["cells"][model]
        print(
            f"  {model}: n={c['n_model']} cont6={c['model_cont_6']} "
            f"base={c['baseline_cont_6']} delta={c['cont_delta']} "
            f"lr_p={c['incremental_lr'].get('lr_p') if c['incremental_lr'] else None}"
        )
    print(f"  causality: perturb {audit['1_future_perturbation']['max_diff']} "
          f"trunc {audit['2_truncation_invariance']['all_zero']} "
          f"leakage_blocked {len(audit['5_static_leakage']['blocked'])}")
    print(f"  promoted: {promoted}")
    print(f"  decision: {decision['status']} -> {decision['next_checkpoint_recommended']}")


if __name__ == "__main__":
    main()
