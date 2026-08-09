"""
Phase 3 orchestrator - build canonical synchronized H1/H4/D1 research panel
and write all Phase 3 artifacts.

CR-P3-COMMON-PANEL-01
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .phase_3_panel import (
    PHASE2_SYMBOLS,
    ASSET_CLASS,
    CURRENCY_ORIENTATION,
    CROSS_RATE_IDENTITIES,
    build_input_manifest,
    load_accepted_h1,
    build_h1_master_panel,
    build_availability_masks,
    build_market_open_masks,
    missingness_mask,
    build_h4_panel,
    build_d1_panel,
    build_price_transforms,
    cross_rate_residuals,
    staleness_flag,
    outlier_report,
    coverage_matrix,
    common_overlap,
)


class Phase3Panel:
    """Builds the canonical Phase 3 panel from accepted Phase 2 data."""

    def __init__(self, base_dir: str | Path, normalized_h1_dir: str | Path | None = None):
        self.base_dir = Path(base_dir)
        self.normalized_h1_dir = (
            Path(normalized_h1_dir) if normalized_h1_dir else self.base_dir / "data" / "normalized" / "h1"
        )
        self.out_dir = self.base_dir / "artifacts" / "phase_03"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.symbols = PHASE2_SYMBOLS

    # -- dataset loaders (accepted-only) ---------------------------------
    def _load_all_h1(self):
        frames = {s: load_accepted_h1(s, self.normalized_h1_dir) for s in self.symbols}
        return frames

    # -- main build -------------------------------------------------------
    def run(self, write: bool = True) -> Dict:
        t0 = time.time()

        # 1. Input manifest
        manifest = build_input_manifest(self.normalized_h1_dir, self.symbols)

        # 2. Canonical H1 master panel
        master_h1, per_sym = build_h1_master_panel(self.normalized_h1_dir, self.symbols)
        closes = pd.DataFrame(
            {s: per_sym[s]["close"].reindex(master_h1.index) for s in self.symbols}
        )

        # 3. Availability & market-open & missingness masks
        availability = build_availability_masks(master_h1, self.symbols)
        market_open = build_market_open_masks(master_h1, self.symbols)
        missingness = missingness_mask(availability, market_open)

        # Master panel union (each timestamp = same canonical UTC observation)
        master_panel = master_h1.copy()
        master_panel["calendar_market_open_any"] = market_open.any(axis=1)

        # 4. H4 & D1 panels
        h4 = build_h4_panel(master_h1, self.symbols)
        d1 = build_d1_panel(master_h1, self.symbols)

        # 5. Transforms (raw OHLC untouched - separate columns)
        transforms = build_price_transforms(closes)

        # 6./7. Cross-rate identity & staleness & outliers
        residuals = cross_rate_residuals(closes)
        stale = staleness_flag(master_h1, self.symbols)
        outliers = outlier_report(master_h1, self.symbols)

        # 8. Coverage matrix
        cov = coverage_matrix(master_h1.index, availability, market_open, self.symbols)

        # 8b. Per-symbol coverage over the strict common window
        # Denominator = timestamps within the actual common research window
        # (earliest→latest where ALL symbols present & open), and the symbol
        # is market-open. Matches Phase 2 audit meaning.
        overlap = common_overlap(availability, market_open, self.symbols)
        lo = None
        hi = None
        if overlap.get("earliest_common_ts"):
            lo = pd.Timestamp(overlap["earliest_common_ts"])
            hi = pd.Timestamp(overlap["latest_common_ts"])
            in_common_bounds = (master_h1.index >= lo) & (master_h1.index <= hi)
            common_coverage_pct = {}
            for sym in self.symbols:
                mo = market_open[sym] & in_common_bounds
                expected = int(mo.sum())
                present = int((availability[sym] & mo).sum())
                common_coverage_pct[sym] = round(100.0 * present / expected, 2) if expected else 0.0
        else:
            common_coverage_pct = {s: 0.0 for s in self.symbols}

        overlap["per_symbol_common_window_coverage_pct"] = common_coverage_pct

        elapsed = time.time() - t0

        summary = {
            "phase": "3",
            "task": "CR-P3-COMMON-PANEL-01",
            "built_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(elapsed, 2),
            "universe": self.symbols,
            "n_symbols": len(self.symbols),
            "master_h1_rows": int(len(master_h1)),
            "h4_rows": int(len(h4)),
            "d1_rows": int(len(d1)),
            "h1_first": str(master_h1.index.min()),
            "h1_last": str(master_h1.index.max()),
            "earliest_common_ts": str(pd.Timestamp(overlap["earliest_common_ts"])) if overlap["earliest_common_ts"] else None,
            "latest_common_ts": str(pd.Timestamp(overlap["latest_common_ts"])) if overlap["latest_common_ts"] else None,
            "common_intersection_valid_hours": overlap["intersection_valid_hours"],
            "per_symbol_coverage_pct": _coverage_pct_map(cov),
            "largest_unexpected_gap_hours": _largest_unexpected_gap_hours(missingness, market_open),
            "cross_rate_identity": _cross_rate_summary(residuals),
            "stale_flag_count": {s: int(stale[s].sum()) for s in self.symbols},
            "outlier_counts": {
                s: {
                    "impossible_ohlc": int(outliers[f"{s}_impossible_ohlc"].sum()),
                    "nonpositive": int(outliers[f"{s}_nonpositive"].sum()),
                    "extreme_return": int(outliers[f"{s}_extreme_return"].sum()),
                }
                for s in self.symbols
            },
        }

        if write:
            self._write_all(
                manifest, master_h1, h4, d1, availability, market_open,
                missingness, transforms, residuals, stale, outliers, cov,
                overlap, summary,
            )
            self._write_gate()

        return summary

    def _write_gate(self):
        from .phase_3_gate import write_gate
        write_gate(self.out_dir)

    # -- writers ----------------------------------------------------------
    def _write_all(self, manifest, master_h1, h4, d1, availability, market_open,
                   missingness, transforms, residuals, stale, outliers, cov, overlap, summary):
        self.out_dir.joinpath("input_manifest.json").write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        master_h1.to_parquet(self.out_dir / "h1_master_panel.parquet")
        h4.to_parquet(self.out_dir / "h4_master_panel.parquet")
        d1.to_parquet(self.out_dir / "d1_master_panel.parquet")
        availability.to_parquet(self.out_dir / "availability_masks.parquet")
        market_open.to_parquet(self.out_dir / "market_open_masks.parquet")
        transforms.to_parquet(self.out_dir / "price_transforms.parquet")

        # Strict common panel = timestamps where ALL symbols have valid data
        # and are market-open. Derived from the master panel, never destroys master.
        strict_mask = availability.all(axis=1) & market_open.all(axis=1)
        strict_common = master_h1[strict_mask.values]

        # Preserve raw OHLC block (drop helper cols)
        ohlc_cols = [c for c in master_h1.columns if not c.startswith("calendar_")]
        strict_common = strict_common[ohlc_cols]
        strict_common.to_parquet(self.out_dir / "h1_strict_common_panel.parquet")

        cov.to_csv(self.out_dir / "coverage_matrix.csv", index=False)

        # cross-rate identity QC
        identity_rows = []
        for (out, num, den), fr in residuals.items():
            fr2 = fr.dropna()
            identity_rows.append({
                "identity": f"{out}~{num}/{den}",
                "output": out, "numerator": num, "denominator": den,
                "observations": int(len(fr2)),
                "mean_residual": round(float(fr2["residual"].mean()), 8),
                "std_residual": round(float(fr2["residual"].std()), 8),
                "max_abs_residual": round(float(fr2["residual"].abs().max()), 8),
                "pct_abs_residual_gt_1e-6": round(
                    100.0 * float((fr2["residual"].abs() > 1e-6).mean()), 4),
            })
        pd.DataFrame(identity_rows).to_csv(self.out_dir / "cross_rate_identity_qc.csv", index=False)

        stale.to_csv(self.out_dir / "staleness_report.csv")
        outliers.to_csv(self.out_dir / "outlier_report.csv")
        self.out_dir.joinpath("common_overlap_report.json").write_text(
            json.dumps(overlap, indent=2, default=str), encoding="utf-8")

        return None


def _coverage_pct_map(cov):
    grp = cov.groupby("symbol")["coverage_pct"].mean()
    return {s: round(float(v), 2) for s, v in grp.items()}


def _largest_unexpected_gap_hours(missingness, market_open):
    """Largest consecutive run of 'unexpected_missing' per symbol."""
    out = {}
    for sym in missingness.columns:
        mk = market_open[sym]
        unexpected = (missingness[sym] == "unexpected_missing") & mk
        # find max run length
        max_run = 0
        cur = 0
        for v in unexpected.values:
            if v:
                cur += 1
                max_run = max(max_run, cur)
            else:
                cur = 0
        out[sym] = int(max_run)
    return out


def _cross_rate_summary(residuals):
    out = {}
    for (o, n, d), fr in residuals.items():
        fr2 = fr.dropna()
        out[f"{o}~{n}/{d}"] = {
            "n": int(len(fr2)),
            "mean_residual": round(float(fr2["residual"].mean()), 8) if len(fr2) else None,
            "std_residual": round(float(fr2["residual"].std()), 8) if len(fr2) else None,
        }
    return out


def main():
    import sys
    base = Path(__file__).resolve().parents[3]
    p = Phase3Panel(base)
    summary = p.run(write=True)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()