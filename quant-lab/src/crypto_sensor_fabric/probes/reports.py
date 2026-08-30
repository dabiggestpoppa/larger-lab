"""Report-and-gap-matrix generator (SENSOR-B2-I12).

Deterministic, offline generation of the frozen evidence packet from probe
evidence and capability claims.  Outputs align with
`bloc_02/05_PROBE_OUTPUT_TEMPLATES.md`:

```text
01_PROBE_RUN_MANIFEST.md
02_PROVIDER_COVERAGE_MATRIX.csv
03_SENSOR_GAP_MATRIX.csv
04_PROVIDER_ROLE_RECOMMENDATIONS.md
05_BLOCKING_CONTRADICTIONS.csv
06_FREE_ONLY_AUDIT.csv
07_PIT_READINESS_MATRIX.csv
08_HISTORY_BOUNDARIES.csv
09_SCHEMA_FINGERPRINTS.jsonl
10_CAPABILITY_CLAIMS.jsonl
11_FAILURES.jsonl
```

`12_BLOC_02_IMPLEMENTATION_DECISION.md` (the final provider-role promotion
packet) is deliberately OUT OF SCOPE here and reserved for SENSOR-B2-I14.

Reports distinguish `claimed` vs `fixture-characterized` vs `live-verified` vs
`historically-verified` vs `blocked` vs `unattempted` — an unprobed claim is
never promoted.  This module performs no I/O except the explicit `write_reports`
surface, which only touches the provided output directory.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..contracts.enums import SensorFamily
from .enums import (
    PITReadiness,
    RedundancyClass,
    ResponseStatusClass,
)
from .models import (
    CapabilityClaim,
    CapabilityProbeAttempt,
    DocumentationRuntimeContradiction,
    FailureRecord,
    ProbeRunResult,
    ProviderSensorCoverage,
    SensorRedundancySummary,
)

FABRIC_VERSION = "sensor-fabric-v1"
PROBE_VERSION = "sensor-probe-v1"

#: Stable output filenames of the evidence packet (12 is reserved for I14).
REPORT_FILENAMES: tuple[str, ...] = (
    "01_PROBE_RUN_MANIFEST.md",
    "02_PROVIDER_COVERAGE_MATRIX.csv",
    "03_SENSOR_GAP_MATRIX.csv",
    "04_PROVIDER_ROLE_RECOMMENDATIONS.md",
    "05_BLOCKING_CONTRADICTIONS.csv",
    "06_FREE_ONLY_AUDIT.csv",
    "07_PIT_READINESS_MATRIX.csv",
    "08_HISTORY_BOUNDARIES.csv",
    "09_SCHEMA_FINGERPRINTS.jsonl",
    "10_CAPABILITY_CLAIMS.jsonl",
    "11_FAILURES.jsonl",
)

#: Coverage matrix era columns (template §3).
COVERAGE_ERA_COLUMNS: tuple[str, ...] = ("2021", "2022", "2024", "2026", "recent_status")


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return ""
    ts = value
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.isoformat().replace("+00:00", "Z")


def _to_csv(header: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Serialize rows deterministically (LF line endings, utf-8)."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(list(header))
    for row in rows:
        writer.writerow(
            ["" if v is None else (v.value if isinstance(v, Enum) else str(v)) for v in row]
        )
    return buf.getvalue()


def _jsonl(records: Sequence[Mapping[str, Any]]) -> str:
    """Serialize records deterministically as JSON-lines."""
    lines: list[str] = []
    for record in records:
        lines.append(json.dumps(_jsonable(dict(record)), sort_keys=True, default=_json_default))
    return "\n".join(lines) + ("\n" if lines else "")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return _fmt_dt(value)
    if isinstance(value, Mapping):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _json_default(value: Any) -> Any:
    return _jsonable(value)


# ---------------------------------------------------------------------------
# 01_PROBE_RUN_MANIFEST.md
# ---------------------------------------------------------------------------


def probe_run_manifest(
    run: ProbeRunResult | None,
    *,
    attempts: Sequence[CapabilityProbeAttempt],
    provider_ids: Sequence[str],
    claims: Sequence[CapabilityClaim],
    coverages: Sequence[ProviderSensorCoverage],
) -> str:
    """Human-readable run manifest with a claimed-vs-verified ledger."""
    verified_count = sum(
        1 for a in attempts if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    )
    failed_count = sum(
        1 for a in attempts if a.response_status_class is ResponseStatusClass.FAILED
    )
    lines: list[str] = [
        "# Probe Run Manifest",
        "",
        f"- fabric_version: `{FABRIC_VERSION}`",
        f"- probe_version: `{run.probe_version if run else PROBE_VERSION}`",
        f"- probe_run_id: `{run.probe_run_id if run else 'unassigned'}`",
        f"- run_status: `{run.run_status.value if run else 'PLANNED_ONLY'}`",
        "",
        "## Status vocabulary (claimed / fixture / live / historical / blocked / unattempted)",
        "",
        "Every scope below carries one of:",
        "",
        "- `CLAIMED`       — documentation claim only (E0), no observation yet",
        "- `FIXTURE`       — characterized on synthetic offline fixtures",
        "- `LIVE_VERIFIED` — verified on a live free endpoint (E2, SENSOR-B2-I13)",
        "- `HISTORICAL`    — verified at a historical checkpoint (E3/E4/E5)",
        "- `BLOCKED`       — access/payment/geo/auth/unsupported with recorded evidence",
        "- `UNATTEMPTED`   — not yet probed (never equated to unsupported)",
        "",
        "Claims are promoted across a category ONLY when supporting observation exists.",
        "",
        "## Attempt ledger",
        "",
        f"- attempts recorded: {len(attempts)}",
        f"- verified samples: {verified_count}",
        f"- failed samples: {failed_count}",
        f"- coverage scopes synthesized: {len(coverages)}",
        f"- capability claims: {len(claims)}",
        "",
        "## Providers characterized",
        "",
        "| provider_id | sensors claimed | scope evidence |",
        "|---|---|---|",
    ]
    for pid in sorted(set(provider_ids)):
        scopes = [c for c in coverages if c.provider_id == pid]
        sensors = sorted({c.sensor_family.value for c in scopes}) or ["(none)"]
        claims_n = sum(1 for cl in claims if cl.provider_id == pid)
        lines.append(
            f"| {pid} | {len(scopes)} coverage scope(s): {', '.join(sensors)} | "
            f"{claims_n} claim(s) |"
        )
    lines += ["", "## Evidence trust boundaries", "", "This manifest is live-agnostic until SENSOR-B2-I13."]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 02_PROVIDER_COVERAGE_MATRIX.csv
# ---------------------------------------------------------------------------


def provider_coverage_csv(coverages: Sequence[ProviderSensorCoverage]) -> str:
    header = [
        "provider_id",
        "sensor_family",
        "venue_market",
        "instrument_scope",
        "access_mode",
        *COVERAGE_ERA_COLUMNS,
        "earliest_verified_history",
        "latest_verified_history",
        "granularity_scope",
        "PIT_readiness",
        "unit_clarity",
        "pagination_quality",
        "schema_stability",
        "semantic_equivalence_class",
        "evidence_level",
        "provider_role",
        "capability_score",
        "promotion_eligible",
        "blocking_reason",
    ]
    rows: list[list[Any]] = []
    for c in sorted(coverages, key=lambda x: (x.provider_id, x.sensor_family.value)):
        era_row: list[Any] = []
        for col in COVERAGE_ERA_COLUMNS:
            era_name = "recent" if col == "recent_status" else col
            status = c.era_status.get(era_name) if col != "recent_status" else c.era_status.get("RECENT_CONTROL")
            era_row.append(status.value if status else "UNATTEMPTED")
        rows.append(
            [
                c.provider_id,
                c.sensor_family.value,
                c.venue_market,
                "|".join(c.instrument_scope) or "",
                c.access_mode.value,
                *era_row,
                _fmt_dt(c.earliest_verified_history),
                _fmt_dt(c.latest_verified_history),
                "|".join(g.value for g in sorted(c.granularity_scope, key=lambda g: g.value)),
                c.PIT_readiness.value,
                c.unit_clarity,
                c.pagination_quality,
                c.schema_stability,
                c.semantic_equivalence_class.value if c.semantic_equivalence_class else "",
                c.evidence_level.value,
                c.provider_role.value,
                c.capability_score,
                "TRUE" if c.promotion_eligible else "FALSE",
                c.blocking_reason or "",
            ]
        )
    return _to_csv(header, rows)


# ---------------------------------------------------------------------------
# 03_SENSOR_GAP_MATRIX.csv
# ---------------------------------------------------------------------------


def sensor_gap_csv(
    redundancies: Sequence[SensorRedundancySummary],
    expected_sensors: Sequence[SensorFamily],
) -> str:
    header = [
        "sensor_family",
        "verified_provider_count",
        "verified_venues",
        "redundancy_class",
        "first_party_count",
        "aggregator_count",
        "community_count",
        "PIT_ready_provider_count",
        "gap_status",
        "notes",
    ]
    by_sensor = {r.sensor_family: r for r in redundancies}
    rows: list[list[Any]] = []
    for sensor in sorted(set(expected_sensors), key=lambda s: s.value):
        r = by_sensor.get(sensor)
        rows.append(
            [
                sensor.value,
                r.verified_provider_count if r else 0,
                "|".join(r.verified_venues) if r else "",
                r.redundancy_class.value if r else RedundancyClass.R0_NONE.value,
                r.first_party_count if r else 0,
                r.aggregator_count if r else 0,
                r.community_count if r else 0,
                r.PIT_ready_provider_count if r else 0,
                r.gap_status if r else "UNVERIFIED",
                r.notes or "unprobed" if r else "no verified source yet — unattempted, not unsupported",
            ]
        )
    return _to_csv(header, rows)


# ---------------------------------------------------------------------------
# 04_PROVIDER_ROLE_RECOMMENDATIONS.md
# ---------------------------------------------------------------------------


def role_recommendations_markdown(coverages: Sequence[ProviderSensorCoverage]) -> str:
    lines = [
        "# Provider Role Recommendations",
        "",
        "Provisional, evidence-based.  Final roles are frozen at SENSOR-B2-I14.",
        "",
        "| provider_id | sensor_family | access_mode | evidence_level | PIT | provider_role | promotion_eligible |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in sorted(coverages, key=lambda x: (x.provider_id, x.sensor_family.value)):
        lines.append(
            f"| {c.provider_id} | {c.sensor_family.value} | {c.access_mode.value} | "
            f"{c.evidence_level.value} | {c.PIT_readiness.value} | {c.provider_role.value} | "
            f"{'TRUE' if c.promotion_eligible else 'FALSE'} |"
        )
    lines += [
        "",
        "A row is a promotion CANDIDATE only when `promotion_eligible = TRUE`;",
        "that gate is fail-closed (paid access, unusable timestamps or",
        "non-comparable semantics can never promote — see `scoring.py`).",
        "No row authored here implies a Bloc 3 production adapter.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 05_BLOCKING_CONTRADICTIONS.csv
# ---------------------------------------------------------------------------


def blocking_contradictions_csv(
    contradictions: Sequence[DocumentationRuntimeContradiction],
) -> str:
    header = [
        "contradiction_id",
        "provider_id",
        "sensor_family",
        "documentation_claim",
        "documentation_source_ref",
        "runtime_observation",
        "runtime_evidence_ids",
        "severity",
        "resolution_status",
        "notes",
    ]
    rows = [
        [
            c.contradiction_id,
            c.provider_id,
            c.sensor_family.value,
            c.documentation_claim,
            c.documentation_source_ref or "",
            c.runtime_observation,
            "|".join(c.runtime_evidence_ids),
            c.severity.value,
            c.resolution_status.value,
            c.notes or "",
        ]
        for c in contradictions
    ]
    return _to_csv(header, rows)


# ---------------------------------------------------------------------------
# 06_FREE_ONLY_AUDIT.csv
# ---------------------------------------------------------------------------


FREE_ONLY_AUDIT_HEADER: tuple[str, ...] = (
    "provider_id",
    "sensor_family",
    "access_mode",
    "api_key_required",
    "account_required",
    "payment_method_required",
    "paid_subscription_required",
    "staking_required",
    "transaction_required",
    "free_quota",
    "access_class",
    "eligible_required_runtime",
    "evidence_refs",
)


def free_only_audit_csv(rows: Sequence[Mapping[str, Any]]) -> str:
    """Serialize a free-only audit table (template §9).

    `payment_method_required`, `paid_subscription_required`, `staking_required`
    and `transaction_required` must be `false` for any eligible required runtime.
    """
    out: list[list[Any]] = []
    for row in rows:
        out.append([row.get(k, "") for k in FREE_ONLY_AUDIT_HEADER])
    return _to_csv(FREE_ONLY_AUDIT_HEADER, out)


# ---------------------------------------------------------------------------
# 07_PIT_READINESS_MATRIX.csv
# ---------------------------------------------------------------------------


def pit_readiness_csv(coverages: Sequence[ProviderSensorCoverage]) -> str:
    header = [
        "provider_id",
        "sensor_family",
        "effective_timestamp_understood",
        "observation_timestamp_understood",
        "publication_delay_understood",
        "forward_info_required",
        "PIT_readiness",
        "methodology_required",
        "blocking_reason",
    ]
    rows = [
        [
            c.provider_id,
            c.sensor_family.value,
            "YES" if c.PIT_readiness is PITReadiness.PIT_READY else "NO",
            "YES" if c.PIT_readiness is PITReadiness.PIT_READY else "NO",
            "UNKNOWN",
            "YES" if c.PIT_readiness in (PITReadiness.PIT_READY_WITH_METHOD_VERSION,) else "NO",
            c.PIT_readiness.value,
            "YES" if c.PIT_readiness is PITReadiness.PIT_READY_WITH_METHOD_VERSION else "NO",
            c.blocking_reason or "",
        ]
        for c in coverages
    ]
    return _to_csv(header, rows)


# ---------------------------------------------------------------------------
# 08_HISTORY_BOUNDARIES.csv
# ---------------------------------------------------------------------------


def history_boundaries_csv(claims: Sequence[CapabilityClaim]) -> str:
    header = [
        "provider_id",
        "sensor_family",
        "instrument",
        "granularity",
        "earliest_claimed",
        "earliest_verified",
        "boundary_confidence",
        "latest_verified",
        "probe_method",
        "evidence_ids",
    ]
    rows: list[list[Any]] = []
    for cl in claims:
        instrument = "|".join(cl.instrument_scope) or ""
        granularity = "|".join(g.value for g in cl.granularity_scope) or ""
        probe_method = (
            "archive" if "ARCHIVE" in cl.access_mode.value else "runtime"
        )
        rows.append(
            [
                cl.provider_id,
                cl.sensor_family.value,
                instrument,
                granularity,
                _fmt_dt(cl.earliest_claimed_history),
                _fmt_dt(cl.earliest_verified_history),
                cl.history_boundary_confidence.value,
                _fmt_dt(cl.latest_verified_history),
                probe_method,
                "|".join(cl.evidence_ids),
            ]
        )
    return _to_csv(header, rows)


# ---------------------------------------------------------------------------
# 09_SCHEMA_FINGERPRINTS.jsonl
# ---------------------------------------------------------------------------


def schema_fingerprints_jsonl(attempts: Sequence[CapabilityProbeAttempt]) -> str:
    records = [
        {
            "provider_id": a.provider_id,
            "sensor_family": a.sensor_family.value,
            "evidence_id": a.probe_id,
            "schema_fingerprint": a.payload_schema_fingerprint,
            "fields": a.native_timestamp_fields or [],
            "sample_period": (
                f"{_fmt_dt(a.first_timestamp_returned)}/{_fmt_dt(a.last_timestamp_returned)}"
            ),
        }
        for a in attempts
        if a.payload_schema_fingerprint or a.native_timestamp_fields
    ]
    return _jsonl(records)


# ---------------------------------------------------------------------------
# 10_CAPABILITY_CLAIMS.jsonl
# ---------------------------------------------------------------------------


def capability_claims_jsonl(claims: Sequence[CapabilityClaim]) -> str:
    # plain dump() keeps datetime/enum objects so _jsonable renders Z-datetimes
    return _jsonl([cl.model_dump() for cl in claims])


# ---------------------------------------------------------------------------
# 11_FAILURES.jsonl
# ---------------------------------------------------------------------------


def failures_jsonl(failures: Sequence[FailureRecord]) -> str:
    return _jsonl([f.model_dump() for f in failures])


# ---------------------------------------------------------------------------
# write_reports — the only surfacing entry point with I/O
# ---------------------------------------------------------------------------


def write_reports(
    *,
    output_dir: str,
    run: ProbeRunResult | None = None,
    attempts: Sequence[CapabilityProbeAttempt] = (),
    claims: Sequence[CapabilityClaim] = (),
    coverages: Sequence[ProviderSensorCoverage] = (),
    redundancies: Sequence[SensorRedundancySummary] = (),
    contradictions: Sequence[DocumentationRuntimeContradiction] = (),
    free_only_audit: Sequence[Mapping[str, Any]] = (),
    failures: Sequence[FailureRecord] = (),
    provider_ids: Sequence[str] = (),
    expected_sensors: Sequence[SensorFamily] = (),
) -> list[str]:
    """Write the frozen evidence packet into `output_dir`; returns file paths."""
    from pathlib import Path

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    races = {
        "01_PROBE_RUN_MANIFEST.md": probe_run_manifest(
            run,
            attempts=attempts,
            provider_ids=provider_ids or sorted({a.provider_id for a in attempts}),
            claims=claims,
            coverages=coverages,
        ),
        "02_PROVIDER_COVERAGE_MATRIX.csv": provider_coverage_csv(coverages),
        "03_SENSOR_GAP_MATRIX.csv": sensor_gap_csv(redundancies, expected_sensors),
        "04_PROVIDER_ROLE_RECOMMENDATIONS.md": role_recommendations_markdown(coverages),
        "05_BLOCKING_CONTRADICTIONS.csv": blocking_contradictions_csv(contradictions),
        "06_FREE_ONLY_AUDIT.csv": free_only_audit_csv(free_only_audit),
        "07_PIT_READINESS_MATRIX.csv": pit_readiness_csv(coverages),
        "08_HISTORY_BOUNDARIES.csv": history_boundaries_csv(claims),
        "09_SCHEMA_FINGERPRINTS.jsonl": schema_fingerprints_jsonl(attempts),
        "10_CAPABILITY_CLAIMS.jsonl": capability_claims_jsonl(claims),
        "11_FAILURES.jsonl": failures_jsonl(failures),
    }
    written: list[str] = []
    for name, content in races.items():
        path = directory / name
        path.write_text(content, encoding="utf-8", newline="\n")
        written.append(str(path))
    return written