#!/usr/bin/env python3
"""
TB-R6.3 — WEEKLY SIGNAL-COMPLETENESS AUDITOR · CLI
===================================================

Independent end-of-week verification sidecar answering:

    "Given the COMPLETE M5 market record for this week, what signals should
     the canonical TB engine have generated, and did the live runtime
     account for every one?"

Usage:
    python tb_weekly_audit.py --week latest
    python tb_weekly_audit.py --week YYYY-MM-DD     # any day -> its ISO week
    python tb_weekly_audit.py --month YYYY-MM        # weekly audits + rollup

Options:
    --data-dir PATH   repo CSV cache (default quant-lab/data)
    --live-db PATH    runtime event ledger (default quant-lab/state/tb_control.db)
    --runtime-db PATH runtime status DB (default quant-lab/state/tb_runtime.db)
    --out-dir PATH    artifact root (default quant-lab/tb_audits)
    --no-mt5          never attempt a read-only MT5 pull
    --mt5-parity      use read-only MT5 pull for disputed-signal parity

AUTHORITY: READ ONLY · DIAGNOSTIC ONLY · NO EXECUTION · NO CAPITAL ·
NO STRATEGY-MODIFICATION. This tool never writes to the runtime DBs, never
sends broker orders, and never alters strategy parameters.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

# repo layout: quant-lab/audit/tb_weekly_audit.py
QUANT_LAB = Path(__file__).resolve().parent.parent
for _p in (str(QUANT_LAB), str(QUANT_LAB / "audit")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tb_audit_core import (  # noqa: E402
    CONTROL_STRATEGY_ID,
    PRIMARY_STRATEGY_ID,
    STRATEGY_IDS,
    OutcomeClass,
    ParityStatus,
)
from tb_audit_data import (  # noqa: E402
    DataCompletenessError,
    MarketDataLoader,
    load_full_history,
)
from tb_audit_live import (  # noqa: E402
    BarsParityProvider,
    EventMatcher,
    LiveLedgerReader,
    LiveRuntimeReader,
    Mt5ParityProvider,
    NullParityProvider,
    build_parity_map,
)
from tb_audit_replay import (  # noqa: E402
    TBWeeklyReplayEngine,
    replay_historical,
)
from tb_audit_report import AuditReportWriter  # noqa: E402
from tb_audit_stats import Cadence, ActivityClassification  # noqa: E402

DEFAULT_DATA_DIR = QUANT_LAB / "data"
DEFAULT_LIVE_DB = QUANT_LAB / "state" / "tb_control.db"
DEFAULT_RUNTIME_DB = QUANT_LAB / "state" / "tb_runtime.db"
DEFAULT_OUT_DIR = QUANT_LAB / "tb_audits"


# ─── engineering completeness ────────────────────────────────────────────
def engineering_completeness(summaries: dict, data_valid: bool,
                             data_reasons: List[str]) -> str:
    if not data_valid:
        return "BLOCKED_DATA_DIVERGENCE"
    missed = sum(s.missed for s in summaries.values())
    rt_only = sum(s.runtime_only for s in summaries.values())
    divergence = sum(s.data_divergence for s in summaries.values())
    if divergence > 0:
        return "BLOCKED_DATA_DIVERGENCE"
    if missed > 0:
        return "FAIL_MISSED_SIGNAL"
    if rt_only > 0:
        return "FAIL_RUNTIME_ONLY_SIGNAL"
    return "PASS"


# ─── one-week audit ──────────────────────────────────────────────────────
def run_week_audit(
    week_start: datetime,
    data_dir: Path = DEFAULT_DATA_DIR,
    live_db: Path = DEFAULT_LIVE_DB,
    runtime_db: Path = DEFAULT_RUNTIME_DB,
    out_dir: Path = DEFAULT_OUT_DIR,
    use_mt5: bool = True,
    mt5_parity: bool = False,
    parity_override=None,          # test seam
    dev_entries_override=None,     # test seam: {strategy: [datetimes]}
) -> dict:
    """Full weekly audit. Returns the structured report dict."""
    loader = MarketDataLoader(data_dir)
    ws = week_start - timedelta(days=week_start.weekday())
    ws = ws.replace(hour=0, minute=0, second=0, microsecond=0)
    we = ws + timedelta(days=7)

    # 1) raw data + completeness gates (fail closed)
    try:
        dw = loader.load_week(ws, use_mt5=use_mt5)
        data_valid = True
        data_reasons: List[str] = []
    except DataCompletenessError as e:
        dw = None
        data_valid = False
        data_reasons = [str(e)]

    report: dict = {
        "auditor": "TB-R6.3-WEEKLY-SIGNAL-COMPLETENESS-AUDITOR",
        "run_id": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "week_start": ws.strftime("%Y-%m-%d"),
        "week_end": we.strftime("%Y-%m-%d"),
        "iso_week": f"{ws.isocalendar()[0]}-W{ws.isocalendar()[1]:02d}",
        "data_valid": data_valid,
        "data_reasons": data_reasons,
        "data_source": _data_source_desc(loader, dw),
        "summaries": {},
        "expected_events": [],
        "match_records": [],
        "parity_rows": [],
        "activity": {},
        "engineering": "BLOCKED_DATA_DIVERGENCE",
        "data_parity": "FAIL",
        "runtime_context": {},
    }

    if not data_valid:
        report["engineering"] = "BLOCKED_DATA_DIVERGENCE"
        report["activity"] = _insufficient_activity()
        return report

    # 2) independent canonical replay (both strategies)
    replays = {}
    for cfg_name in ("primary", "control"):
        from engines.tb_forward_config import (  # noqa: PLC0415
            PRIMARY_CONFIG, CONTROL_CONFIG)
        cfg = PRIMARY_CONFIG if cfg_name == "primary" else CONTROL_CONFIG
        replays[cfg.strategy_id] = TBWeeklyReplayEngine(model_config=cfg) \
            .replay(dw)
    expected = []
    for r in replays.values():
        expected.extend(r.expected_events)
    expected.sort(key=lambda e: (e.bar_key, e.strategy_id,
                                 e.decision_type.value))

    # 3) live runtime artifacts (READ ONLY)
    live = LiveLedgerReader(live_db).read_events(
        since_ts=(ws - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S"))
    live_window = [ev for ev in live
                   if ws.strftime("%Y-%m-%d") <= ev.ts_utc[:10] <
                   we.strftime("%Y-%m-%d")]

    # 4) parity provider
    if parity_override is not None:
        parity = parity_override
    elif mt5_parity:
        audit_map = build_parity_map(dw)
        disputed = {e.bar_key for e in expected
                    if e.decision_type.value == "ENTRY"}
        parity = Mt5ParityProvider(audit_map, disputed, ws)
    else:
        parity = NullParityProvider()

    # 5) matching -> outcome classes
    matcher = EventMatcher(parity)
    records, summaries, _ = matcher.match(expected, live_window)

    # 6) historical cadence + rolling activity
    audit_entries = {
        s: [datetime.fromisoformat(e.timestamp_utc)
            for e in replays[s].expected_events
            if e.decision_type.value == "ENTRY"]
        for s in STRATEGY_IDS}
    if dev_entries_override is not None:
        dev_entries = dev_entries_override
    else:
        dev_entries = _dev_entries(data_dir)
    cadence = Cadence(dev_entries)
    activity = cadence.context(audit_entries, ws)

    # 7) assemble report
    report["summaries"] = {s: summaries[s].to_dict() for s in STRATEGY_IDS}
    report["expected_events"] = [e.to_row() for e in expected]
    report["match_records"] = [r.to_row() for r in records]
    report["parity_rows"] = getattr(parity, "divergences", [])
    report["activity"] = activity
    report["engineering"] = engineering_completeness(
        summaries, data_valid, data_reasons)
    report["data_parity"] = _data_parity_label(report)
    report["runtime_context"] = LiveRuntimeReader(runtime_db).context()

    # 8) artifacts
    writer = AuditReportWriter(_week_dir(out_dir, ws))
    writer.write_json("TB_WEEKLY_AUDIT.json", report)
    writer.write_md(report)
    writer.write_expected(expected)
    writer.write_match(records)
    writer.write_parity(report["parity_rows"])
    writer.write_activity(activity)
    for s in STRATEGY_IDS:
        writer.append_history({
            "run_id": writer.run_id,
            "week_start": report["week_start"],
            "iso_week": report["iso_week"],
            "strategy": s,
            **report["summaries"][s],
            "engineering": report["engineering"],
            "data_parity": report["data_parity"],
        })
    return report


def _data_source_desc(loader: MarketDataLoader, dw) -> str:
    if dw is None:
        r = loader.available_range()
        return f"cache range {r[0]}..{r[1]}" if r else "no data"
    srcs = sorted({b.source for b in dw.per_symbol["GBPAUD"]})
    return f"raw completed M5 bars ({','.join(srcs)}), " \
           f"warmup={dw.warmup_bars} window={dw.window_bars}"


@lru_cache(maxsize=4)
def _dev_entries(data_dir: Path) -> Dict[str, List[datetime]]:
    """Frozen dev-window entry times per strategy (independent replay).

    Cached per data_dir so a multi-week/month run replays the historical
    dev window exactly once.
    """
    hist = load_full_history(data_dir)
    res = replay_historical(hist)
    return {
        s: [datetime.fromisoformat(e.timestamp_utc)
            for e in res[s].expected_events
            if e.decision_type.value == "ENTRY"]
        for s in STRATEGY_IDS}


def _week_dir(out_dir: Path, ws: datetime) -> Path:
    iso = ws.isocalendar()
    return out_dir / f"{iso.year}-W{iso.week:02d}"


def _data_parity_label(report: dict) -> str:
    if not report["data_valid"]:
        return "FAIL"
    if report["parity_rows"]:
        return "FAIL"
    if any(r["outcome"] == "DATA_DIVERGENCE"
           for r in report["match_records"]):
        return "UNKNOWN"
    return "PASS"


def _insufficient_activity() -> dict:
    return {
        s: {"current_week": None, "current_week_class":
            ActivityClassification.INSUFFICIENT,
            "trailing_4_week": None,
            "trailing_4_week_class": ActivityClassification.INSUFFICIENT,
            "trailing_8_week": None,
            "trailing_8_week_class": ActivityClassification.INSUFFICIENT,
            "trailing_12_week": None,
            "trailing_12_week_class": ActivityClassification.INSUFFICIENT}
        for s in STRATEGY_IDS}


# ─── month rollup ────────────────────────────────────────────────────────
def run_month_audit(month: str, **kw) -> dict:
    """Run each ISO week intersecting the month; aggregate the rollup."""
    y, m = (int(p) for p in month.split("-"))
    first = datetime(y, m, 1)
    # ISO weeks whose Monday falls within the month (full weeks only)
    ws = first + timedelta(days=(7 - first.weekday()) % 7)
    weeks = []
    while ws.month == m:
        weeks.append(ws)
        ws += timedelta(days=7)
    week_reports = [run_week_audit(w, **kw) for w in weeks]

    rollup = {
        "auditor": "TB-R6.3-WEEKLY-SIGNAL-COMPLETENESS-AUDITOR",
        "month": f"{y:04d}-{m:02d}",
        "weeks": [r["iso_week"] for r in week_reports],
        "strategies": {},
    }
    for s in STRATEGY_IDS:
        expected = sum(r["summaries"][s]["expected_signals"]
                       for r in week_reports if r["data_valid"])
        recognized = expected - sum(
            r["summaries"][s]["missed"] for r in week_reports
            if r["data_valid"])
        executed = sum(r["summaries"][s]["taken"] for r in week_reports
                       if r["data_valid"])
        blocked = sum(r["summaries"][s]["valid_blocks"]
                      for r in week_reports if r["data_valid"])
        missed = sum(r["summaries"][s]["missed"] for r in week_reports
                     if r["data_valid"])
        runtime_only = sum(r["summaries"][s]["runtime_only"]
                           for r in week_reports if r["data_valid"])
        divergence = sum(r["summaries"][s]["data_divergence"]
                         for r in week_reports if r["data_valid"])
        rollup["strategies"][s] = {
            "expected_signals": expected,
            "recognized": recognized,
            "executed": executed,
            "blocked": blocked,
            "missed": missed,
            "runtime_only_signals": runtime_only,
            "data_divergence_count": divergence,
            "signal_recognition_rate":
                round(recognized / expected, 6) if expected else 1.0,
        }
    out_dir = Path(kw.get("out_dir", DEFAULT_OUT_DIR)) / f"{y:04d}-{m:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "TB_MONTHLY_AUDIT.json").write_text(
        json.dumps(rollup, indent=2), encoding="utf-8")
    lines = [f"# TB MONTHLY AUDIT  {y:04d}-{m:02d}",
             f"Weeks: {', '.join(rollup['weeks'])}", ""]
    for s, d in rollup["strategies"].items():
        lines.append(f"## {s}")
        for k, v in d.items():
            lines.append(f"{k}: {v}")
        lines.append("")
    (out_dir / "TB_MONTHLY_AUDIT.md").write_text("\n".join(lines),
                                                 encoding="utf-8")
    return rollup


# ─── CLI ─────────────────────────────────────────────────────────────────
def resolve_week(arg: str) -> datetime:
    if arg == "latest":
        # most recent COMPLETE trading week: Monday of (today - 7d window)
        now = datetime.now(timezone.utc)
        # last Monday strictly before today
        today = now.date()
        last_mon = today - timedelta(days=today.weekday())
        return datetime(last_mon.year, last_mon.month, last_mon.day)
    return datetime.fromisoformat(arg)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--week", help="latest | YYYY-MM-DD")
    g.add_argument("--month", help="YYYY-MM")
    ap.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    ap.add_argument("--live-db", default=str(DEFAULT_LIVE_DB))
    ap.add_argument("--runtime-db", default=str(DEFAULT_RUNTIME_DB))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--no-mt5", action="store_true",
                    help="never attempt read-only MT5 data pull")
    ap.add_argument("--mt5-parity", action="store_true",
                    help="read-only MT5 parity for disputed signals")
    args = ap.parse_args(argv)

    kw = dict(data_dir=Path(args.data_dir), live_db=Path(args.live_db),
              runtime_db=Path(args.runtime_db), out_dir=Path(args.out_dir),
              use_mt5=not args.no_mt5, mt5_parity=args.mt5_parity)
    if args.week:
        rep = run_week_audit(resolve_week(args.week), **kw)
        print(json.dumps({"week": rep["iso_week"],
                          "data_valid": rep["data_valid"],
                          "engineering": rep["engineering"],
                          "data_parity": rep["data_parity"],
                          "summaries": rep["summaries"]}, indent=2,
                         default=str))
        print(f"artifacts: {_week_dir(Path(args.out_dir), resolve_week(args.week))}")
    else:
        roll = run_month_audit(args.month, **kw)
        print(json.dumps(roll, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
