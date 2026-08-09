"""
Generate PHASE_4_FACTOR_REPORT.md from the Phase 4 artifacts.
CR-P4-LATENT-FACTOR-ENGINE-01
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .phase_4_factors import CURRENCIES, PHASE2_SYMBOLS


def _fmt(x) -> str:
    try:
        return f"{float(x):,.6g}"
    except (TypeError, ValueError):
        return str(x)


def generate_phase4_report(out_dir: Path) -> Path:
    factors = pd.read_parquet(out_dir / "currency_factors_h1.parquet")
    residuals = pd.read_parquet(out_dir / "pair_residuals_h1.parquet")
    recon = pd.read_csv(out_dir / "factor_reconstruction_qc.csv")
    breadth = pd.read_csv(out_dir / "breadth_report.csv")
    meta = __import__("json").loads(
        (out_dir / "phase_4_meta.json").read_text(encoding="utf-8")
    )

    lines = []
    lines.append("# Phase 4 — Latent FX Factor Engine")
    lines.append("")
    lines.append(f"**Task:** CR-P4-LATENT-FACTOR-ENGINE-01")
    lines.append(f"**Input:** Phase 3 strict common panel `{meta['input_panel_sha256'][:16]}…`")
    lines.append(f"**Canonical window:** {meta['common_window_earliest']} → {meta['common_window_latest']}")
    lines.append(f"**Factor rows (H1):** {meta['factor_rows_h1']}")
    lines.append(f"**Incidence matrix rank:** {meta['incidence_matrix_rank']} (n-1, zero-sum constraint)")
    lines.append("")

    # Per-currency diagnostics
    lines.append("## Per-Currency Factor Diagnostics")
    lines.append("")
    lines.append("| Currency | Mean | Std | P1 | P5 | P50 | P95 | P99 | AC(1) | Vol24h |")
    lines.append("|----------|------|-----|----|----|-----|-----|-----|-------|--------|")
    for c in CURRENCIES:
        f = factors[f"{c}_factor"].dropna()
        if f.empty:
            continue
        ac = f.autocorr(1)
        lines.append(
            f"| {c} | {f.mean():.6g} | {f.std():.6g} | "
            f"{f.quantile(.01):.6g} | {f.quantile(.05):.6g} | {f.quantile(.50):.6g} | "
            f"{f.quantile(.95):.6g} | {f.quantile(.99):.6g} | {ac:.4f} | "
            f"{fstd(f, 24):.6g} |"
        )
    lines.append("")

    # Pair residual diagnostics
    lines.append("## Pair Residual Diagnostics")
    lines.append("")
    lines.append("| Pair | Mean | Std | Kurtosis | P95\\|res\\| | P99\\|res\\| |")
    lines.append("|------|------|-----|----------|------------|------------|")
    for p in PHASE2_SYMBOLS:
        col = f"{p}_residual"
        if col not in residuals.columns:
            continue
        r = residuals[col].dropna()
        if r.empty:
            continue
        kurt = r.kurt() if len(r) > 3 else np.nan
        lines.append(
            f"| {p} | {r.mean():.6g} | {r.std():.6g} | {kurt:.4f} | "
            f"{np.abs(r).quantile(.95):.6g} | {np.abs(r).quantile(.99):.6g} |"
        )
    lines.append("")

    # Reconstruction QC
    lines.append("## Factor Reconstruction (by pair)")
    lines.append("")
    lines.append("| Pair | N | R² | RMSE | MAE | Corr |")
    lines.append("|------|---|----|------|-----|------|")
    for _, row in recon.iterrows():
        lines.append(
            f"| {row['pair']} | {int(row['n'])} | {row['r2']:.4f} | "
            f"{row['rmse']:.6g} | {row['mae']:.6g} | {row['corr']:.4f} |"
        )
    lines.append("")
    lines.append(f"Network RMSE distribution: min={factors['network_fit_rmse'].min():.6g}, "
                 f"median={factors['network_fit_rmse'].median():.6g}, "
                 f"max={factors['network_fit_rmse'].max():.6g}")
    lines.append("")

    report = "\n".join(lines)
    out_file = out_dir / "PHASE_4_FACTOR_REPORT.md"
    out_file.write_text(report, encoding="utf-8")
    return out_file


def fstd(s: pd.Series, w: int) -> float:
    """Trailing std helper."""
    return float(s.rolling(w, min_periods=w).std().mean())