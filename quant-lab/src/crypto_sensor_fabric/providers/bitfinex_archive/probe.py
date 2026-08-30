"""Bitfinex community liquidation archive probe (bloc_02/02 §12 / 04 §6).

Minimal characterization module — NOT a production adapter.  This candidate is
an independent historical liquidation REPLICATION source with evidence class
COMMUNITY_ARCHIVE: it is never EXACT_EQUIVALENT to first-party interval
liquidation totals (T2-COV-05 / master §14); expected role is corroboration /
replication (§12 promotion expectations).

Characterization covers the archive as a data source (probe priorities
§12.1-12.8):

- repository/archive availability (verified only at the live probe),
- license presence and SPDX classification,
- published dump hash/checksum manifest,
- liquidation side / size / instrument semantics from a file sample,
- spot/margin/perpetual semantics inspection (community dumps often mix
  spot-margin liquidations),
- duplicates/revisions detection and rebuild-reproducibility notes.

The archive base URL is UNVERIFIED by default; the live probe (SENSOR-B2-I13)
records the actual reachable root before any promotion decision.  All
characterization logic is offline.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ...contracts.enums import SensorFamily
from ...probes.enums import (
    AccessMode,
    EvidenceSourceClass,
    ProbeFailureClass,
    ResponseStatusClass,
)
from ...probes.models import CapabilityProbeAttempt, CapabilityProbeRequest
from ...probes.payload import fingerprint_payload, first_last_timestamps

PROVIDER_ID = "BITFINEX_COMMUNITY_ARCHIVE"

#: Default archive root — deliberately UNVERIFIED; the live probe records the
#: actually reachable community archive before any promotion decision.
DEFAULT_ARCHIVE_BASE = "https://example.invalid/bitfinex-community-liquidation-archive"

#: Per-day liquidation dump file naming ({date} = YYYY-MM-DD).
DAILY_FILE_TEMPLATE = "{base}/liquidations/{date}.csv"
CHECKSUMS_FILE = "checksums.txt"
LICENSE_FILE = "LICENSE"
METHODOLOGY_FILE = "README.md"

#: Columns the community dumps are known to carry (characterization level).
EXPECTED_LIQUIDATION_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "symbol",
    "side",
    "amount",
    "price",
)


class BitfinexArchiveCapabilityProbe:
    """Bitfinex community liquidation archive characterization (offline)."""

    provider_id = PROVIDER_ID
    evidence_class = EvidenceSourceClass.COMMUNITY_ARCHIVE
    access_mode = AccessMode.COMMUNITY_ARCHIVE
    probe_version = "bitfinex-archive-v1"

    def __init__(self, archive_base_url: str | None = None) -> None:
        self.archive_base_url = archive_base_url or DEFAULT_ARCHIVE_BASE

    # ------------------------------------------------------------------
    # deterministic archive URLs
    # ------------------------------------------------------------------

    def daily_file_url(self, date: str) -> str:
        return DAILY_FILE_TEMPLATE.format(base=self.archive_base_url, date=date)

    def checksums_url(self) -> str:
        return f"{self.archive_base_url}/{CHECKSUMS_FILE}"

    def license_url(self) -> str:
        return f"{self.archive_base_url}/{LICENSE_FILE}"

    def methodology_url(self) -> str:
        return f"{self.archive_base_url}/{METHODOLOGY_FILE}"

    # ------------------------------------------------------------------
    # schema / semantics inspection
    # ------------------------------------------------------------------

    def inspect_liquidation_schema(
        self, sample_rows: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Inspect observed liquidation columns and semantics (§12.5-12.6)."""
        if not sample_rows:
            return {"observed_columns": "", "semantics": "EMPTY_SAMPLE"}
        columns: list[str] = []
        for row in sample_rows:
            for key in row:
                if key not in columns:
                    columns.append(key)
        has_side = "side" in columns
        has_amount = "amount" in columns
        has_pair = "symbol" in columns or "pair" in columns
        notes: list[str] = []
        if not has_side:
            notes.append("no side column — liquidation direction unresolved")
        if not has_amount:
            notes.append("no amount column — size semantics unresolved")
        if not has_pair:
            notes.append("no instrument column — symbol attribution unresolved")
        # community dumps commonly mix spot-margin liquidations with derivatives
        notes.append(
            "spot/margin/perpetual semantics must be inspected per dump; "
            "never assume perpetual-only"
        )
        return {
            "observed_columns": ",".join(columns),
            "semantics": "; ".join(notes),
            "duplicates_revisions": "detect at full-file ingest (row-level ids/pairs)",
            "rebuild_reproducibility": "depends on documented generation methodology",
        }

    def _schema_fingerprint(self, sample_rows: list[dict[str, Any]]) -> str | None:
        if not sample_rows:
            return None
        return fingerprint_payload(sample_rows)

    # ------------------------------------------------------------------
    # archive file characterization
    # ------------------------------------------------------------------

    def characterize_daily_file(
        self,
        request: CapabilityProbeRequest,
        *,
        date: str,
        file_status: int,
        checksum_status: str = "unverified",
        license_status: str = "unverified",
        methodology_status: str = "unverified",
        checksum_line: str | None = None,
        sample_rows: list[dict[str, Any]] | None = None,
    ) -> CapabilityProbeAttempt:
        """Characterize one daily liquidation dump + archive metadata.

        `checksum_status` / `license_status` / `methodology_status` are one of
        "verified" | "missing" | "unverified".  A 404 file is an archive hole
        (F_ARCHIVE_NOT_FOUND) — never a zero.
        """
        sample_rows = sample_rows or []
        first_ts, last_ts = first_last_timestamps(sample_rows)
        common: dict[str, Any] = {
            "probe_id": f"{PROVIDER_ID.lower()}_archive_{date}",
            "probe_run_id": request.probe_run_id,
            "provider_id": PROVIDER_ID,
            "sensor_family": SensorFamily.MECHANICAL_LIQUIDATION,
            "venue_market": "BITFINEX",
            "instrument_native": request.instrument_native,
            "canonical_asset_hint": request.canonical_asset_hint,
            "requested_start": request.requested_start,
            "requested_end": request.requested_end,
            "requested_granularity": request.requested_granularity,
            "access_mode": self.access_mode,
            "query_mode": request.query_mode,
            "http_status_or_file_status": file_status,
            "request_fingerprint": self.daily_file_url(date),
            "payload_schema_fingerprint": self._schema_fingerprint(sample_rows),
            "payload_hash_sample": (checksum_line or "")[:100] or None,
            "native_timestamp_fields": (
                ["timestamp"] if any("timestamp" in row for row in sample_rows) else []
            ),
            "native_units_summary": self.inspect_liquidation_schema(sample_rows),
            "era_hint": request.era_hint,
            "probe_version": self.probe_version,
            "rate_limit_metadata": {
                "evidence_class": self.evidence_class.value,
                "archive_base_url_status": (
                    "UNVERIFIED"
                    if "example.invalid" in self.archive_base_url
                    else "configured"
                ),
                "license_status": license_status,
                "checksum_status": checksum_status,
                "methodology_status": methodology_status,
            },
        }
        if file_status == 200:
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.VERIFIED_SAMPLE,
                    "rows_returned": len(sample_rows),
                    "first_timestamp_returned": first_ts,
                    "last_timestamp_returned": last_ts,
                }
            )
        failure = ProbeFailureClass.F_ARCHIVE_NOT_FOUND if file_status == 404 else ProbeFailureClass.F_UNKNOWN
        if file_status >= 500:
            failure = ProbeFailureClass.F_SERVER_5XX
        elif file_status == 429:
            failure = ProbeFailureClass.F_ACCESS_RATE_LIMIT
        elif file_status in (401, 403):
            failure = ProbeFailureClass.F_ACCESS_AUTH
        return CapabilityProbeAttempt.model_validate(
            {
                **common,
                "response_status_class": ResponseStatusClass.FAILED,
                "error_class": failure,
                "error_detail_redacted": (
                    f"archive file missing: liquidations/{date}.csv"
                    if file_status == 404
                    else None
                ),
            }
        )

    # ------------------------------------------------------------------
    # license / checksum classification helpers
    # ------------------------------------------------------------------

    def classify_license(self, license_text: str) -> str:
        """SPDX-style license classification from a license file sample."""
        upper = license_text.upper()
        if "MIT" in upper and "PERMISSION IS HEREBY GRANTED" in upper:
            return "MIT"
        if "APACHE LICENSE" in upper:
            return "Apache-2.0"
        if "GNU GENERAL PUBLIC LICENSE" in upper and "VERSION 3" in upper:
            return "GPL-3.0-only"
        if "CREATIVE COMMONS" in upper:
            return "CC-BY-* (check)"
        return "UNRECOGNIZED"

    def parse_checksums(self, checksum_text: str) -> list[dict[str, str]]:
        """Parse a sha256 manifest (lines: '<hash>  <filename>')."""
        entries: list[dict[str, str]] = []
        for line in checksum_text.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                entries.append({"hash": parts[0], "file": parts[-1]})
        return entries


def sample_timestamp_bounds(
    sample_rows: list[dict[str, Any]],
) -> tuple[datetime | None, datetime | None]:
    """(first, last) parsed timestamps across sample rows (ms or seconds)."""
    return first_last_timestamps(sample_rows)
