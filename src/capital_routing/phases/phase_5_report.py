"""
Generate PHASE_5_EVENT_REPORT.md from the Phase 5 artifacts.
CR-P5-ROUTING-EVENT-ENGINE-01
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def generate_phase5_report(phase5_dir: Path) -> Path:
    ev = pd.read_parquet(phase5_dir / "routing_events.parquet") if (
        phase5_dir / "routing_events.parquet").exists() else pd.DataFrame()
    counts = pd.read_csv(phase5_dir / "event_counts.csv") if (
        phase5_dir / "event_counts.csv").exists() else pd.DataFrame()
    sample = pd.read_csv(phase5_dir / "event_sample_size_report.csv") if (
        phase5_dir / "event_sample_size_report.csv").exists() else pd.DataFrame()
    thresh = json.loads((phase5_dir / "threshold_manifest.json").read_text(encoding="utf-8"))

    lines = []
    lines.append("# Phase 5 — Routing Event Engine")
    lines.append("")
    lines.append("**Task:** CR-P5-ROUTING-EVENT-ENGINE-01")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total event episodes: **{len(ev)}**")
    if len(counts):
        for _, r in counts.iterrows():
            if r["dimension"] == "event_family":
                lines.append(f"- {r['value']}: {r['count']}")
    lines.append("")
    lines.append("## Sample-Size Classifications")
    lines.append("")
    if len(sample):
        lines.append("| Family | Count | Classification |")
        lines.append("|--------|-------|----------------|")
        for _, r in sample.iterrows():
            lines.append(f"| {r['family']} | {r['count']} | {r['classification']} |")
    lines.append("")
    lines.append("## Threshold Manifest")
    lines.append("")
    lines.append(f"- Method: {thresh['statistical_method']}")
    lines.append(f"- Origin factor p95 threshold: {thresh['origin_factor_p95_threshold']:.6g}")
    lines.append(f"- Residual p95 threshold: {thresh['residual_p95_threshold']:.6g}")
    lines.append(f"- Network RMSE p95: {thresh['network_rmse_p95']:.6g}")
    lines.append(f"- Hysteresis entry/reset: {thresh['hysteresis']}")
    lines.append("")
    lines.append("## Severity Distribution")
    lines.append("")
    sd = pd.read_csv(phase5_dir / "event_severity_distribution.csv") if (
        phase5_dir / "event_severity_distribution.csv").exists() else pd.DataFrame()
    if len(sd):
        lines.append(sd.to_markdown(index=False))
    lines.append("")

    report = "\n".join(lines)
    out_file = phase5_dir / "PHASE_5_EVENT_REPORT.md"
    out_file.write_text(report, encoding="utf-8")
    return out_file