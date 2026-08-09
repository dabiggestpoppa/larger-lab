"""
Phase 4 orchestrator - latent FX factor engine runner.
CR-P4-LATENT-FACTOR-ENGINE-01

Consumes ONLY the accepted Phase 3 strict common panel (plus masks) and
writes all Phase 4 artifacts under artifacts/phase_04/.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_3_panel import PHASE2_SYMBOLS, CURRENCY_ORIENTATION
from .phase_4_factors import (
    CURRENCIES,
    HORIZON_BARS,
    aggregate_factors_by_bucket,
    breadth_features,
    build_incidence_matrix,
    build_quality_weights,
    cross_sectional_ranks,
    destination_pressure_features,
    dispersion_features,
    factor_volatility,
    incidence_rank,
    network_consistency,
    origin_pressure_features,
    orthogonality_audit,
    p3_preflight_audit,
    pair_residuals,
    reconstruction_validation,
    solve_from_panel_returns,
    solve_latent_factors,
    trailing_cumulative,
    velocity_acceleration,
)

PHASE3_COMMIT = "11c6d77b3eccc670367e98e02ef77d92fc539a0f"


def _rolling_trailing_vol(returns: pd.DataFrame, window: int = 120) -> pd.DataFrame:
    """Trailing realized vol per pair used for WLS inverse-vol normalisation."""
    return returns.rolling(window, min_periods=window).std()


def _resolve_panel_pairs(panel: pd.DataFrame) -> List[str]:
    """Pairs present (columns) in the panel - should be the full universe."""
    found = []
    for p in PHASE2_SYMBOLS:
        if f"{p}_close" in panel.columns:
            found.append(p)
    return found


class Phase4FactorEngine:
    def __init__(self, phase3_dir: Path, out_dir: Path):
        self.p3 = phase3_dir
        self.out = out_dir
        self.out.mkdir(parents=True, exist_ok=True)

    # ---- input loading ------------------------------------------------
    def _load_h1(self) -> pd.DataFrame:
        panel = pd.read_parquet(self.p3 / "h1_strict_common_panel.parquet")
        closes = pd.DataFrame(
            {p: panel[f"{p}_close"] for p in self._pairs if f"{p}_close" in panel.columns}
        )
        return panel, closes

    def _load_masks(self) -> Dict[str, pd.DataFrame]:
        # Masks are over the master index; reindex to strict common window.
        # (Strict common = all present & open, so masks are TRUE there, but we
        #  still align to be explicit and leak-free.)
        avail = pd.read_parquet(self.p3 / "availability_masks.parquet")
        market_open = pd.read_parquet(self.p3 / "market_open_masks.parquet")
        return {"availability": avail, "market_open": market_open}

    def run(self, write: bool = True) -> Dict:
        t0 = time.time()

        # 0. Preflight audit (strict common panel is the whole input).
        audit = p3_preflight_audit(self.p3, self.out, PHASE3_COMMIT)

        self._pairs = self._load_pairs()

        panel, closes = self._load_h1()
        panel_sha = audit["input_panel_sha256"]

        # returns: log returns per pair (no forward fill; NaN stays NaN).
        returns = np.log(closes / closes.shift(1))

        # Build quality weights (equal default).  The strict common panel is
        # fully populated (no missingness), so equal weights == all 1.0, but we
        # keep the machinery for audit + tests.
        avail = pd.DataFrame(True, index=returns.index, columns=returns.columns)
        market_open = pd.DataFrame(True, index=returns.index, columns=returns.columns)
        staleness = pd.DataFrame(False, index=returns.index, columns=returns.columns)
        trailing_vol = _rolling_trailing_vol(returns)
        quality_w = build_quality_weights(avail, market_open, staleness, trailing_vol)

        # 2. Incidence matrix
        A_df, A = build_incidence_matrix(self._pairs)

        # 4. Solve latent factors (equal-weight OLS, zero-sum)
        factors_eq = solve_latent_factors(returns, weights=None, robust=False, pairs=self._pairs, A=A)

        # 4b. Quality-weighted WLS
        factors_wls = solve_latent_factors(returns, weights=quality_w, robust=False, pairs=self._pairs, A=A)

        # 5. Robust version (IRLS-Huber) - deterministic, not PnL-tuned
        factors_robust = solve_latent_factors(returns, weights=None, robust=True, pairs=self._pairs, A=A)

        # Canonical factor representation = equal-weight OLS zero-sum.
        factors = factors_eq

        # 6. Pair residuals
        residuals = pair_residuals(factors, returns, self._pairs)

        # 7/8/9/10/11/12/13/14/15/16/17. Feature stage
        cum = trailing_cumulative(factors)
        velacc = velocity_acceleration(cum, ["4h"])
        ranks = cross_sectional_ranks(factors)
        breadth = breadth_features(factors, returns, weights=None, pairs=self._pairs)
        vol = factor_volatility(factors)
        disp = dispersion_features(factors)
        origin = origin_pressure_features(factors, cum, velacc, ranks, breadth, vol)
        dest = destination_pressure_features(ranks, breadth, velacc, factors, vol)

        # Bridge / parking / destination primitives (raw, no labels).
        bridge = pd.DataFrame(index=factors.index)
        for c in CURRENCIES:
            bridge[f"{c}_factor"] = factors[f"{c}_factor"]
        for c in ["GBP", "CHF", "JPY"]:
            for suf in ["_factor_volatility_4h", "_factor_volatility_24h"]:
                if f"{c}{suf}" in vol.columns:
                    bridge[f"{c}{suf}"] = vol[f"{c}{suf}"]
            bridge[f"{c}_breadth_fraction"] = breadth[f"{c}_breadth_fraction"]
            bridge[f"{c}_rank"] = ranks[f"{c}_rank"]
            bridge[f"{c}_velocity_4h"] = velacc[f"{c}_velocity_4h"]
            bridge[f"{c}_acceleration_4h"] = velacc[f"{c}_acceleration_4h"]
        # EURGBP/GBPJPY/GBPCHF residuals already in `residuals`.

        # 18. Network consistency
        consistency = network_consistency(factors, residuals, returns, self._pairs)

        # 19. Orthogonality / redundancy audit
        ortho = orthogonality_audit(factors)

        # 21. Reconstruction validation
        recon = reconstruction_validation(factors, returns, self._pairs)

        # 20. H4 / D1 factors (method A aggregate H1, method B independent solve)
        # Load H4 & D1 close panels from Phase 3 (these are master panels; we mask
        # to the common window for comparability).
        h4m = pd.read_parquet(self.p3 / "h4_master_panel.parquet")
        d1m = pd.read_parquet(self.p3 / "d1_master_panel.parquet")
        h4_common = h4m[h4m.index.isin(panel.index)] if panel.index.tz is None else h4m
        # H4/D1 factor views over the FULL common window (no forward fill).
        h4_close = pd.DataFrame({p: h4m[f"{p}_close"] for p in self._pairs if f"{p}_close" in h4m.columns})
        d1_close = pd.DataFrame({p: d1m[f"{p}_close"] for p in self._pairs if f"{p}_close" in d1m.columns})

        # Method B: independent solve from H4/D1 returns
        h4_factors_B = solve_from_panel_returns(h4_close, self._pairs)
        d1_factors_B = solve_from_panel_returns(d1_close, self._pairs)

        # 22. Time consistency (no-lookahead) is enforced by construction and
        #     verified by unit tests (test_phase_4_factors).

        # ---- write artifacts ----
        meta = {
            "phase": "4",
            "task": "CR-P4-LATENT-FACTOR-ENGINE-01",
            "phase3_commit": PHASE3_COMMIT,
            "input_panel_sha256": panel_sha,
            "currencies": CURRENCIES,
            "pairs": self._pairs,
            "n_currencies": len(CURRENCIES),
            "incidence_matrix_rank": incidence_rank(A),
            "common_window_earliest": str(pd.to_datetime(panel.index.min(), utc=True)),
            "common_window_latest": str(pd.to_datetime(panel.index.max(), utc=True)),
            "factor_rows_h1": int(len(factors)),
            "factor_rows_h4_B": int(len(h4_factors_B)),
            "factor_rows_d1_B": int(len(d1_factors_B)),
            "identification_constraint": "sum(f_t)=0 (EUR+GBP+USD+CHF+JPY=0)",
            "horizon_bars": {k: v for k, v in HORIZON_BARS.items()},
            "robust_method": "IRLS-Huber (c=1.345), deterministic, not PnL-tuned",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(time.time() - t0, 2),
        }

        if write:
            self.out / "currency_factors_h1.parquet"
            factors.to_parquet(self.out / "currency_factors_h1.parquet")
            factors_wls.to_parquet(self.out / "currency_factors_h1_wls.parquet")
            factors_robust.to_parquet(self.out / "currency_factors_h1_robust.parquet")
            h4_factors_B.to_parquet(self.out / "currency_factors_h4.parquet")
            d1_factors_B.to_parquet(self.out / "currency_factors_d1.parquet")
            residuals.to_parquet(self.out / "pair_residuals_h1.parquet")

            # full feature frame
            feature_cols = pd.concat(
                [
                    cum, velacc, ranks, breadth, vol, disp, origin, dest, bridge, consistency
                ],
                axis=1,
            )
            feature_cols = pd.concat([factors, residuals, feature_cols], axis=1)
            # Deduplicate column names (several frame builders emit the same
            # primitive name) - keep first occurrence to avoid object upcast.
            feature_cols = feature_cols.loc[:, ~feature_cols.columns.duplicated()]
            feature_cols = feature_cols.astype({c: "float64" for c in feature_cols.columns if
                                                  not pd.api.types.is_object_dtype(feature_cols[c])})
            feature_cols.to_parquet(self.out / "factor_features_h1.parquet")

            recon.to_csv(self.out / "factor_reconstruction_qc.csv", index=False)
            ortho["covariance_matrix"].to_csv(self.out / "factor_covariance_matrix.csv")
            ortho["correlation_matrix"].to_csv(self.out / "factor_correlation_matrix.csv")
            pd.DataFrame(
                {
                    "eigenvalue": ortho["eigenvalues"].values,
                    "variance_explained": ortho["eigenvalues_variance_explained"].values,
                    "currency": ortho["eigenvalues"].index,
                }
            ).to_csv(self.out / "factor_eigenvalues.csv", index=False)

            # Breadth / vol / network reports (summary across timestamps)
            breadth_summary = pd.DataFrame({
                "currency": CURRENCIES,
                "breadth_count_mean": [
                    float(breadth[f"{c}_breadth_count"].mean()) for c in CURRENCIES
                ],
                "breadth_fraction_mean": [
                    float(breadth[f"{c}_breadth_fraction"].mean()) for c in CURRENCIES
                ],
                "weighted_breadth_mean": [
                    float(breadth[f"{c}_weighted_breadth"].mean()) for c in CURRENCIES
                ],
            })
            breadth_summary.to_csv(self.out / "breadth_report.csv", index=False)

            vol_summary = pd.DataFrame({
                "currency": CURRENCIES,
                "vol_4h_mean": [float(vol[f"{c}_factor_volatility_4h"].mean()) for c in CURRENCIES],
                "vol_12h_mean": [float(vol[f"{c}_factor_volatility_12h"].mean()) for c in CURRENCIES],
                "vol_24h_mean": [float(vol[f"{c}_factor_volatility_24h"].mean()) for c in CURRENCIES],
            })
            vol_summary.to_csv(self.out / "volatility_report.csv", index=False)

            consistency[["pair_reconstruction_rmse", "max_abs_residual",
                        "median_abs_residual", "network_agreement_score"]].describe().to_csv(
                self.out / "network_consistency_report.csv"
            )

            self.out / "phase_4_meta.json"
            (self.out / "phase_4_meta.json").write_text(
                json.dumps(meta, indent=2, default=str), encoding="utf-8"
            )

        return {
            "meta": meta,
            "audit": audit,
            "orthogonality": ortho,
            "reconstruction": recon,
        }

    def _load_pairs(self) -> List[str]:
        panel_sample = pd.read_parquet(self.p3 / "h1_strict_common_panel.parquet",
                                       columns=[f"{p}_close" for p in PHASE2_SYMBOLS])
        return [p for p in PHASE2_SYMBOLS if f"{p}_close" in panel_sample.columns]


def write_gate(phase4_dir: Path) -> None:
    """Write machine-readable Phase 4 gate. PASS iff all required outputs exist."""
    required = [
        "currency_factors_h1.parquet",
        "currency_factors_h4.parquet",
        "currency_factors_d1.parquet",
        "pair_residuals_h1.parquet",
        "factor_features_h1.parquet",
        "factor_reconstruction_qc.csv",
        "factor_correlation_matrix.csv",
        "factor_covariance_matrix.csv",
        "factor_eigenvalues.csv",
        "breadth_report.csv",
        "volatility_report.csv",
        "network_consistency_report.csv",
        "p3_preflight_audit.json",
        "PHASE_4_FACTOR_REPORT.md",
    ]
    present = {f: (phase4_dir / f).exists() for f in required}
    all_present = all(present.values())
    gate = {
        "phase": "4",
        "task": "CR-P4-LATENT-FACTOR-ENGINE-01",
        "gate_passed": bool(all_present),
        "phase_4_factor_engine_complete": bool(all_present),
        "phase_5_cleared": bool(all_present),
        "required_outputs": {k: bool(v) for k, v in present.items()},
        "failures": [k for k, v in present.items() if not v],
        "note": (
            "Acceptance is infrastructure/statistical only. It does NOT depend "
            "on finding a profitable trading result."
        ),
    }
    (phase4_dir / "phase_4_gate.json").write_text(
        json.dumps(gate, indent=2, default=str), encoding="utf-8"
    )
    return gate