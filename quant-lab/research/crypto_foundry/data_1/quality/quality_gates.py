"""
Crypto Foundry DATA-1 Quality Gates

17 preregistered quality gates. No gate can silently downgrade failure to warning
unless preregistered. Every gate returns PASS/BLOCKED/FAIL with evidence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

GATE_VERSION = "1.0.0"


@dataclass
class GateResult:
    gate_id: str
    gate_name: str
    status: str  # PASS, FAIL, BLOCKED, NOT_APPLICABLE
    evidence: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    affected_rows: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _gate(cls):
    """Decorator that auto-appends GateResult to self.results."""
    import functools

    @functools.wraps(cls)
    def wrapper(self, *args, **kwargs):
        result = cls(self, *args, **kwargs)
        self.results.append(result)
        return result

    return wrapper


class QualityGates:
    """Run all 17 preregistered quality gates on normalized data."""

    def __init__(self):
        self.results: List[GateResult] = []

    def reset(self):
        self.results = []

    # ── Q1: Duplicates ──────────────────────────────────────────────
    @_gate
    def q1_duplicates(self, records: List[Dict], key_fields: List[str]) -> GateResult:
        seen: Set[str] = set()
        dup_count = 0
        dup_indices: List[int] = []
        for i, r in enumerate(records):
            key = tuple(str(r.get(f, "")) for f in key_fields)
            key_str = "|".join(key)
            if key_str in seen:
                dup_count += 1
                dup_indices.append(i)
            seen.add(key_str)
        status = "PASS" if dup_count == 0 else "FAIL"
        return GateResult(
            gate_id="Q1", gate_name="duplicates", status=status,
            evidence=f"{dup_count} duplicate records found out of {len(records)}",
            details={"duplicate_count": dup_count, "sample_indices": dup_indices[:10]},
            affected_rows=dup_count,
        )

    # ── Q2: Monotonic Timestamps ────────────────────────────────────
    @_gate
    def q2_monotonic_timestamps(self, records: List[Dict], ts_field: str = "event_time_utc") -> GateResult:
        non_mono = 0
        for i in range(1, len(records)):
            prev = records[i - 1].get(ts_field)
            curr = records[i].get(ts_field)
            if prev is not None and curr is not None:
                if _ts_to_float(curr) < _ts_to_float(prev):
                    non_mono += 1
        status = "PASS" if non_mono == 0 else "FAIL"
        return GateResult(
            gate_id="Q2", gate_name="monotonic_timestamps", status=status,
            evidence=f"{non_mono} non-monotonic timestamp transitions",
            details={"non_monotonic_count": non_mono}, affected_rows=non_mono,
        )

    # ── Q3: Invalid/Nonpositive Price ──────────────────────────────
    @_gate
    def q3_invalid_price(self, records: List[Dict], price_field: str = "price") -> GateResult:
        bad = 0
        for r in records:
            p = r.get(price_field)
            if p is not None:
                if not isinstance(p, (int, float)) or p <= 0:
                    bad += 1
        status = "PASS" if bad == 0 else "FAIL"
        return GateResult(
            gate_id="Q3", gate_name="invalid_price", status=status,
            evidence=f"{bad} records with invalid/nonpositive price",
            details={"invalid_price_count": bad}, affected_rows=bad,
        )

    # ── Q4: Invalid/Nonpositive Size ───────────────────────────────
    @_gate
    def q4_invalid_size(self, records: List[Dict], size_field: str = "size") -> GateResult:
        bad = 0
        for r in records:
            s = r.get(size_field)
            if s is not None:
                if not isinstance(s, (int, float)) or s <= 0:
                    bad += 1
        status = "PASS" if bad == 0 else "FAIL"
        return GateResult(
            gate_id="Q4", gate_name="invalid_size", status=status,
            evidence=f"{bad} records with invalid/nonpositive size",
            details={"invalid_size_count": bad}, affected_rows=bad,
        )

    # ── Q5: Missing Intervals ──────────────────────────────────────
    @_gate
    def q5_missing_intervals(
        self, records: List[Dict], ts_field: str, expected_interval_sec: int,
        tolerance_sec: int = None,
    ) -> GateResult:
        if tolerance_sec is None:
            tolerance_sec = expected_interval_sec * 1.5
        timestamps = sorted(
            [r[ts_field] for r in records if r.get(ts_field) is not None], key=_ts_to_float,
        )
        gaps = 0
        gap_details: List[Dict] = []
        for i in range(1, len(timestamps)):
            diff = _ts_to_float(timestamps[i]) - _ts_to_float(timestamps[i - 1])
            if diff > tolerance_sec:
                gaps += 1
                if len(gap_details) < 5:
                    gap_details.append({"from": str(timestamps[i - 1]), "to": str(timestamps[i]), "gap_seconds": round(diff)})
        status = "PASS" if gaps == 0 else "FAIL"
        return GateResult(
            gate_id="Q5", gate_name="missing_intervals", status=status,
            evidence=f"{gaps} interval gaps detected (expected every {expected_interval_sec}s)",
            details={"gap_count": gaps, "sample_gaps": gap_details}, affected_rows=gaps,
        )

    # ── Q6: Crossed/Invalid Books ──────────────────────────────────
    @_gate
    def q6_crossed_books(self, records: List[Dict]) -> GateResult:
        crossed = 0
        for r in records:
            bids = r.get("bids", [])
            asks = r.get("asks", [])
            if bids and asks:
                best_bid = max(float(b[0]) for b in bids) if bids else 0
                best_ask = min(float(a[0]) for a in asks) if asks else float("inf")
                if best_bid >= best_ask:
                    crossed += 1
        status = "PASS" if crossed == 0 else "FAIL"
        return GateResult(
            gate_id="Q6", gate_name="crossed_invalid_books", status=status,
            evidence=f"{crossed} crossed book snapshots",
            details={"crossed_count": crossed}, affected_rows=crossed,
        )

    # ── Q7: Mark/Index Sanity ──────────────────────────────────────
    @_gate
    def q7_mark_index_sanity(
        self, records: List[Dict], mark_field: str = "mark_price",
        index_field: str = "index_price", max_bps: float = 500.0,
    ) -> GateResult:
        bad = 0
        for r in records:
            mark = r.get(mark_field)
            index = r.get(index_field)
            if mark is not None and index is not None and index > 0:
                bps = abs(mark - index) / index * 10000
                if bps > max_bps:
                    bad += 1
        status = "PASS" if bad == 0 else "FAIL"
        return GateResult(
            gate_id="Q7", gate_name="mark_index_sanity", status=status,
            evidence=f"{bad} records with mark/index divergence > {max_bps} bps",
            details={"excessive_divergence_count": bad, "max_bps_threshold": max_bps}, affected_rows=bad,
        )

    # ── Q8: Funding Timestamp Sanity ───────────────────────────────
    @_gate
    def q8_funding_timestamp_sanity(
        self, records: List[Dict], funding_ts_field: str = "funding_time_utc",
        event_ts_field: str = "event_time_utc",
    ) -> GateResult:
        bad = 0
        for r in records:
            ft = r.get(funding_ts_field)
            et = r.get(event_ts_field)
            if ft is not None and et is not None:
                if abs(_ts_to_float(ft) - _ts_to_float(et)) > 86400:
                    bad += 1
        status = "PASS" if bad == 0 else "FAIL"
        return GateResult(
            gate_id="Q8", gate_name="funding_timestamp_sanity", status=status,
            evidence=f"{bad} funding timestamps > 24h from event time",
            details={"bad_funding_ts_count": bad}, affected_rows=bad,
        )

    # ── Q9: Nonnegative OI ─────────────────────────────────────────
    @_gate
    def q9_nonnegative_oi(self, records: List[Dict], oi_field: str = "open_interest") -> GateResult:
        bad = sum(1 for r in records if (oi := r.get(oi_field)) is not None and isinstance(oi, (int, float)) and oi < 0)
        status = "PASS" if bad == 0 else "FAIL"
        return GateResult(
            gate_id="Q9", gate_name="nonnegative_oi", status=status,
            evidence=f"{bad} records with negative OI", details={"negative_oi_count": bad}, affected_rows=bad,
        )

    # ── Q10: AMM Token Order ───────────────────────────────────────
    @_gate
    def q10_amm_token_order(self, records: List[Dict], token0: str, token1: str) -> GateResult:
        if int(token0, 16) > int(token1, 16):
            return GateResult(
                gate_id="Q10", gate_name="amm_token_order", status="FAIL",
                evidence=f"token0 ({token0}) > token1 ({token1}) — violates address ordering",
                details={"token0": token0, "token1": token1},
            )
        return GateResult(gate_id="Q10", gate_name="amm_token_order", status="PASS", evidence="Token ordering is valid")

    # ── Q11: Pool Identity ─────────────────────────────────────────
    @_gate
    def q11_pool_identity(self, records: List[Dict], expected_pool: str, pool_field: str = "pool_address") -> GateResult:
        wrong = sum(1 for r in records if (pa := r.get(pool_field, "").lower()) and pa != expected_pool.lower())
        status = "PASS" if wrong == 0 else "FAIL"
        return GateResult(
            gate_id="Q11", gate_name="pool_identity", status=status,
            evidence=f"{wrong} records with wrong pool address",
            details={"expected": expected_pool, "wrong_count": wrong}, affected_rows=wrong,
        )

    # ── Q12: Unique Block/Tx/Log Keys ──────────────────────────────
    @_gate
    def q12_unique_block_tx_log(self, records: List[Dict]) -> GateResult:
        seen: Set[str] = set()
        dupes = 0
        for r in records:
            key = f"{r.get('block_number', '')}|{r.get('tx_hash', '')}|{r.get('log_index', '')}"
            if key in seen:
                dupes += 1
            seen.add(key)
        status = "PASS" if dupes == 0 else "FAIL"
        return GateResult(
            gate_id="Q12", gate_name="unique_block_tx_log_keys", status=status,
            evidence=f"{dupes} duplicate block/tx/log keys",
            details={"duplicate_keys": dupes}, affected_rows=dupes,
        )

    # ── Q13: Replay Determinism ────────────────────────────────────
    @_gate
    def q13_replay_determinism(self, records_batch_1: List[Dict], records_batch_2: List[Dict]) -> GateResult:
        if len(records_batch_1) != len(records_batch_2):
            return GateResult(
                gate_id="Q13", gate_name="replay_determinism", status="FAIL",
                evidence=f"Batch sizes differ: {len(records_batch_1)} vs {len(records_batch_2)}",
            )
        diffs = sum(
            1 for a, b in zip(records_batch_1, records_batch_2)
            if json.dumps(a, sort_keys=True, default=str) != json.dumps(b, sort_keys=True, default=str)
        )
        status = "PASS" if diffs == 0 else "FAIL"
        return GateResult(
            gate_id="Q13", gate_name="replay_determinism", status=status,
            evidence=f"{diffs} records differ between replay batches",
            details={"diff_count": diffs}, affected_rows=diffs,
        )

    # ── Q14: Normalized-from-Raw Determinism ────────────────────────
    @_gate
    def q14_normalized_from_raw_determinism(self, raw_data: Any, normalize_fn, run_count: int = 2) -> GateResult:
        results = [json.dumps(normalize_fn(raw_data), sort_keys=True, default=str) for _ in range(run_count)]
        all_same = len(set(results)) == 1
        status = "PASS" if all_same else "FAIL"
        return GateResult(
            gate_id="Q14", gate_name="normalized_from_raw_determinism", status=status,
            evidence=f"Normalization produced {len(set(results))} distinct outputs from {run_count} runs",
            details={"unique_outputs": len(set(results))},
        )

    # ── Q15: Future-Independent Normalization ───────────────────────
    @_gate
    def q15_future_independent(self, records: List[Dict], normalize_fn, cutoff_index: int) -> GateResult:
        before = records[:cutoff_index]
        full = records
        norm_before = json.dumps(normalize_fn(before), sort_keys=True, default=str)
        norm_full_prefix = json.dumps(normalize_fn(full)[:cutoff_index], sort_keys=True, default=str)
        match = norm_before == norm_full_prefix
        status = "PASS" if match else "FAIL"
        return GateResult(
            gate_id="Q15", gate_name="future_independent_normalization", status=status,
            evidence="Prefix normalization matches" if match else "Prefix changed with future records added",
            details={"match": match},
        )

    # ── Q16: Schema Validation ──────────────────────────────────────
    @_gate
    def q16_schema_validation(self, schema_summary: Dict[str, Any]) -> GateResult:
        total = schema_summary.get("total", 0)
        passed = schema_summary.get("passed", 0)
        failed = schema_summary.get("failed", 0)
        status = "PASS" if failed == 0 else "FAIL"
        return GateResult(
            gate_id="Q16", gate_name="schema_validation", status=status,
            evidence=f"{passed}/{total} records passed schema validation",
            details=schema_summary, affected_rows=failed,
        )

    # ── Q17: Source Outage Classification ───────────────────────────
    @_gate
    def q17_source_outage(self, expected_count: int, actual_count: int, source_name: str = "") -> GateResult:
        if expected_count == 0:
            return GateResult(gate_id="Q17", gate_name="source_outage_classification", status="NOT_APPLICABLE", evidence="No expected count specified")
        ratio = actual_count / expected_count
        if ratio < 0.1:
            status = "BLOCKED"
        elif ratio < 0.5:
            status = "FAIL"
        else:
            status = "PASS"
        evidence = f"Source '{source_name}' returned {actual_count}/{expected_count} records ({ratio:.1%})"
        return GateResult(
            gate_id="Q17", gate_name="source_outage_classification", status=status,
            evidence=evidence, details={"expected": expected_count, "actual": actual_count, "ratio": ratio},
            affected_rows=max(0, expected_count - actual_count),
        )

    def run_all_applicable(self, records: List[Dict], schema_name: str, **kwargs) -> List[GateResult]:
        """Run applicable gates based on record type."""
        self.reset()
        key_fields = kwargs.get("key_fields", ["event_time_utc", "source", "market_id"])
        self.q1_duplicates(records, key_fields)
        self.q2_monotonic_timestamps(records)
        if schema_name in ("PERP_TRADE", "PERP_LIQUIDATION", "SPOT_BAR_REFERENCE"):
            self.q3_invalid_price(records)
        if schema_name in ("PERP_TRADE", "PERP_LIQUIDATION"):
            self.q4_invalid_size(records)
        if schema_name == "PERP_BOOK_SNAPSHOT" and records:
            self.q6_crossed_books(records)
        if schema_name == "PERP_MARK_INDEX":
            self.q7_mark_index_sanity(records)
        if schema_name == "PERP_FUNDING":
            self.q8_funding_timestamp_sanity(records)
        if schema_name == "PERP_OPEN_INTEREST":
            self.q9_nonnegative_oi(records)
        if schema_name in ("AMM_SWAP", "AMM_LIQUIDITY_EVENT", "AMM_POOL_STATE") and records:
            self.q12_unique_block_tx_log(records)
        return self.results

    def summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        blocked = sum(1 for r in self.results if r.status == "BLOCKED")
        na = sum(1 for r in self.results if r.status == "NOT_APPLICABLE")
        return {
            "total_gates": total, "passed": passed, "failed": failed,
            "blocked": blocked, "not_applicable": na,
            "gates": [r.to_dict() for r in self.results],
        }


def _ts_to_float(ts) -> float:
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return 0.0
    if isinstance(ts, datetime):
        return ts.timestamp()
    return 0.0
