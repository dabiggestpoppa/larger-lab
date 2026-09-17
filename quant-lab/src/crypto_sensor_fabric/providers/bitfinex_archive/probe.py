"""Bitfinex community liquidation archive probe (bloc_02/02 §12 / 04 §6, I11R1).

The intended ACTUAL community source is the public GitHub repository
`tradingstrategy-ai/bitfinex-liquidations` — a COMMUNITY REPLICATION source
distributed as a single Git-LFS DuckDB dump (`bitfinex_liquidations.duckdb`),
NOT a daily CSV tree and NOT a Bitfinex first-party archive.

Evidence class stays COMMUNITY_ARCHIVE with a corroboration / replication role:
never EXACT_EQUIVALENT, never first-party venue truth (T2-COV-05 / master §14).

COVERAGE CLAIMS (approx. Aug/Sep 2019 .. ~Jan 2026) and inline market-type
semantics (e.g. `tBTCUSD` spot/margin, `tBTCF0:USTF0` perpetual, liquidation
direction conveyed by amount sign) are COMMUNITY-DOCUMENTED until independently
validated — recorded as observed claims, never upgraded to canonical truth.
The database mixes spot/margin AND perpetual market types, so the source is
never labelled PERPETUAL_LIQUIDATIONS as a whole.

This is capability characterization only: no DuckDB ingestion, no automatic
355 MB download.  Ordinary tests are fully offline and operate on the small Git
LFS pointer text plus README / LICENSE / .gitattributes / repository-metadata
fixtures (the DuckDB fixture is the LFS pointer text, not the binary).

No assumption of a `checksums.txt` exists upstream; integrity evidence is
carried by the Git LFS OID (SHA-256), the upstream commit SHA and the declared
dump size.  Missing a daily date is NOT a Bitfinex-source concept for this
artifact.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from ...contracts.enums import SensorFamily
from ...probes.enums import (
    AccessMode,
    EvidenceSourceClass,
    ProbeFailureClass,
    ResponseStatusClass,
)
from ...probes.models import CapabilityProbeAttempt, CapabilityProbeRequest
from ...probes.payload import fingerprint_payload

PROVIDER_ID = "BITFINEX_COMMUNITY_ARCHIVE"

#: Public GitHub replication repository (the real community source).
REPOSITORY_OWNER = "tradingstrategy-ai"
REPOSITORY_NAME = "bitfinex-liquidations"
REPOSITORY_URL = f"https://github.com/{REPOSITORY_OWNER}/{REPOSITORY_NAME}"
REPOSITORY_API_URL = f"https://api.github.com/repos/{REPOSITORY_OWNER}/{REPOSITORY_NAME}"

#: The single data artifact, stored via Git LFS.  Not a daily file tree.
DUMP_RELATIVE_PATH = "bitfinex_liquidations.duckdb"
DUMP_STORAGE = "GIT_LFS"

LICENSE_FILENAME = "LICENSE"
README_FILENAME = "README.md"
GITATTRIBUTES_FILENAME = ".gitattributes"

#: SOURCE EVIDENCE from the upstream README/pointer at characterization time —
#: recorded as reference, NOT a permanently-frozen future hash.  The live probe
#: (SENSOR-B2-I13) must record whatever commit / LFS OID exists at probe time.
KNOWN_LFS_POINTER_OID = "90b5d550df057fde1b5a66b5ae9b3de256814ce347bdc5ccc05c7bb9f74e2989"
KNOWN_LFS_POINTER_SIZE = 355217408  # bytes

#: Conservative dump coverage claim echoed from upstream documentation.
KNOWN_COVERAGE_CLAIM = "approx. Aug/Sep 2019 .. ~Jan 2026 (per upstream README)"


def parse_lfs_pointer(text: str | None) -> dict[str, Any] | None:
    """Parse a Git LFS pointer and return {version, oid_algorithm, oid_digest, size}.

    Returns None for absent or malformed input (fails closed) — a broken
    pointer must never be treated as a valid source identity.
    """
    if not text:
        return None
    out: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("version "):
            out["version"] = line[len("version "):]
        elif line.startswith("oid sha256:"):
            digest = line[len("oid sha256:"):]
            if len(digest) == 64 and all(c in "0123456789abcdef" for c in digest):
                out["oid_algorithm"] = "sha256"
                out["oid_digest"] = digest
        elif line.startswith("size "):
            try:
                out["size"] = int(line[len("size "):])
            except ValueError:
                return None
    # require the three identity-bearing lines to be present consistently
    if not (
        out.get("version")
        and out.get("oid_algorithm") == "sha256"
        and out.get("oid_digest")
        and "size" in out
    ):
        return None
    return out


class BitfinexArchiveCapabilityProbe:
    """Bitfinex community GitHub/LFS DuckDB source characterization (offline)."""

    provider_id = PROVIDER_ID
    evidence_class = EvidenceSourceClass.COMMUNITY_ARCHIVE
    access_mode = AccessMode.COMMUNITY_ARCHIVE
    probe_version = "bitfinex-archive-v2"

    # ------------------------------------------------------------------
    # deterministic source URLs
    # ------------------------------------------------------------------

    def repository_url(self) -> str:
        return REPOSITORY_URL

    def repository_api_url(self) -> str:
        return REPOSITORY_API_URL

    def readme_url(self) -> str:
        return f"{REPOSITORY_URL}/blob/HEAD/{README_FILENAME}"

    def license_url(self) -> str:
        return f"{REPOSITORY_URL}/blob/HEAD/{LICENSE_FILENAME}"

    def gitattributes_url(self) -> str:
        return f"{REPOSITORY_URL}/blob/HEAD/{GITATTRIBUTES_FILENAME}"

    def dump_relative_path(self) -> str:
        return DUMP_RELATIVE_PATH

    def dump_storage(self) -> str:
        return DUMP_STORAGE

    def dump_pointer_url(self) -> str:
        # The DuckDB file is the LFS-tracked artifact; this is its raw URL.
        return f"https://raw.githubusercontent.com/{REPOSITORY_OWNER}/{REPOSITORY_NAME}/HEAD/{DUMP_RELATIVE_PATH}"

    def lfs_pointer_blob_url(self) -> str:
        return f"{REPOSITORY_URL}/blob/HEAD/{DUMP_RELATIVE_PATH}"

    # ------------------------------------------------------------------
    # source revision / reproducibility
    # ------------------------------------------------------------------

    def source_revision(
        self, *, upstream_commit: str | None = None, lfs_pointer_text: str | None = None
    ) -> dict[str, Any]:
        """Identity tuple for one source revision (commit SHA + LFS OID + size).

        Later Bloc 4/5 revision lineage keys off this: a new commit or a changed
        LFS OID is a NEW source revision and must never overwrite prior evidence.
        """
        ptr = parse_lfs_pointer(lfs_pointer_text)
        oid = ptr["oid_digest"] if ptr else None
        size = ptr["size"] if ptr else None
        return {
            "upstream_commit": upstream_commit,
            "lfs_oid": oid,
            "lfs_declared_size": size,
            "source_revision_id": oid or upstream_commit,
        }

    def lfs_oid_changed(
        self,
        lfs_pointer_text: str | None,
        known_oid: str = KNOWN_LFS_POINTER_OID,
    ) -> bool:
        """True when the observed LFS OID differs from a known/prior revision."""
        ptr = parse_lfs_pointer(lfs_pointer_text)
        if not ptr:
            return False
        return ptr["oid_digest"] != known_oid

    # ------------------------------------------------------------------
    # license / methodology classification
    # ------------------------------------------------------------------

    def classify_license(self, license_text: str | None) -> str:
        """SPDX-style license classification from a LICENSE sample."""
        if license_text is None:
            return "MISSING"
        upper = license_text.upper()
        if "MIT" in upper and "PERMISSION IS HEREBY GRANTED" in upper:
            return "MIT"
        if "MIT LICENSE" in upper:
            return "MIT"
        if "APACHE LICENSE" in upper:
            return "Apache-2.0"
        if "GNU GENERAL PUBLIC LICENSE" in upper and "VERSION 3" in upper:
            return "GPL-3.0-only"
        if "CREATIVE COMMONS" in upper:
            return "CC-BY-* (check)"
        return "UNRECOGNIZED"

    # ------------------------------------------------------------------
    # repository / dump characterization
    # ------------------------------------------------------------------

    def characterize_repository(
        self,
        request: CapabilityProbeRequest,
        *,
        repo_status: int = 200,
        repo_present: bool = True,
        license_text: str | None = None,
        readme_text: str | None = None,
        gitattributes_text: str | None = None,
        lfs_pointer_text: str | None = None,
        upstream_commit: str | None = None,
        license_status_override: str | None = None,
    ) -> CapabilityProbeAttempt:
        """Characterize the community repository + dump pointer.

        Source integrity evidence is the Git LFS OID / upstream commit / declared
        size — there is NO upstream `checksums.txt` (no fabrication here).  The
        355 MB DuckDB artifact is NOT downloaded to establish capability.
        """
        license_status = license_status_override or (
            self.classify_license(license_text) if license_text is not None else "unverified"
        )
        readme_status = "present" if readme_text else ("unverified" if readme_text is None else "missing")
        ptr = parse_lfs_pointer(lfs_pointer_text)
        if lfs_pointer_text is None:
            lfs_status = "absent"
        elif ptr is None:
            lfs_status = "malformed"
        else:
            lfs_status = "present"

        common: dict[str, Any] = {
            "probe_id": f"{PROVIDER_ID.lower()}_repo_characterization",
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
            "http_status_or_file_status": repo_status,
            "request_fingerprint": self.repository_url(),
            "payload_schema_fingerprint": fingerprint_payload(
                {
                    "dump_storage": DUMP_STORAGE,
                    "market_types": "spot/margin + perpetual (explicit)",
                    "coverage_claim": KNOWN_COVERAGE_CLAIM,
                }
            ),
            "payload_hash_sample": (ptr["oid_digest"][:100] if ptr else None),
            "native_timestamp_fields": ["timestamp"],
            "native_units_summary": {
                "market_types": "spot/margin + perpetual (explicit; never whole-db PERPETUAL_LIQUIDATIONS)",
                "direction_semantics": "liquidation direction via amount sign (community-documented)",
                "semantics_status": "COMMUNITY_DOCUMENTED",
            },
            "era_hint": request.era_hint,
            "probe_version": self.probe_version,
            "rate_limit_metadata": {
                "evidence_class": self.evidence_class.value,
                "source": f"{REPOSITORY_OWNER}/{REPOSITORY_NAME}",
                "repository_url": REPOSITORY_URL,
                "repository_api_url": REPOSITORY_API_URL,
                "dump_storage": DUMP_STORAGE,
                "dump_path": DUMP_RELATIVE_PATH,
                "repo_status_code": repo_status,
                "repo_present": repo_present,
                "license_status": license_status,
                "license_class": self.classify_license(license_text),
                "readme_methodology_status": readme_status,
                "gitattributes_present": bool(gitattributes_text),
                "lfs_status": lfs_status,
                "lfs_oid": (ptr["oid_digest"] if ptr else None),
                "lfs_declared_size": (ptr["size"] if ptr else None),
                "upstream_commit": upstream_commit,
                "coverage_claim": KNOWN_COVERAGE_CLAIM,
                "different_from_known_oid": (
                    self.lfs_oid_changed(lfs_pointer_text) if lfs_pointer_text else None
                ),
                "dump_acquired": False,
                "dump_downloaded": False,
            },
        }

        # failure classification (reused controlled vocabulary)
        if not repo_present or repo_status == 404:
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": ProbeFailureClass.F_ARCHIVE_NOT_FOUND,
                    "error_detail_redacted": "community repository not found",
                }
            )
        if repo_status >= 500:
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": ProbeFailureClass.F_SERVER_5XX,
                    "error_detail_redacted": "repository metadata service error",
                }
            )
        if lfs_status == "absent":
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": ProbeFailureClass.F_ARCHIVE_NOT_FOUND,
                    "error_detail_redacted": "dump artifact absent (no Git LFS pointer for the DuckDB)",
                }
            )
        if lfs_status == "malformed":
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": ProbeFailureClass.F_PAYLOAD_CORRUPT,
                    "error_detail_redacted": "malformed Git LFS pointer",
                }
            )
        if license_status in ("MISSING", "UNRECOGNIZED") or license_status == "missing":
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": ProbeFailureClass.F_REQUIRED_ARTIFACT_MISSING,
                    "error_detail_redacted": "free-only governance requires an explicit license",
                }
            )
        if readme_status == "missing":
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": ProbeFailureClass.F_REQUIRED_ARTIFACT_MISSING,
                    "error_detail_redacted": "readme methodology missing — generation/coverage claims unresolved",
                }
            )
        return CapabilityProbeAttempt.model_validate(
            {
                **common,
                "response_status_class": ResponseStatusClass.VERIFIED_SAMPLE,
                "error_class": None,
            }
        )


def sample_timestamp_bounds(
    sample_rows: Mapping[str, Any] | list[Any],
) -> tuple[datetime | None, datetime | None]:
    """Return (None, None).  The DuckDB dump is not row-inspected in Bloc 2."""
    return None, None