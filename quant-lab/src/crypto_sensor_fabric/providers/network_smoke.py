"""Controlled production-adapter network smoke harness (SENSOR-B3-I10).

This is the FIRST authorized live-network checkpoint.  It is neither a
provider-repair, backfill, data-collection, schema-upgrade, history-expansion,
nor a new-provider discovery session.  It tests ONE thing:

    DO THE FOUR FROZEN PRODUCTION ADAPTERS (KRAKEN_FUTURES, GATE_FUTURES,
    OKX_SWAP, DERIBIT) STILL SPEAK TRUTHFULLY TO THEIR PUBLIC SURFACES?

Frozen network-smoke doctrine (Bloc 3):

- OPTIONAL / EXPLICIT / DISABLED BY DEFAULT: network requires the env gate
  ``SENSOR_NETWORK_SMOKE=1``; without it the marked smoke test SKIPs and a
  normal ``pytest`` NEVER touches the network.
- $0 / FREE-ONLY: no credentials, no trading/private endpoints.
- TINY QUERY RANGES: small recent closed windows; tiny page sizes.
- NO UNCONTROLLED DOWNLOAD: response body capped (2 MiB), request cap 20.
- EVIDENCE PRODUCING: immutable, sanitized plan/results artifacts.
- NON-MUTATING TO SCHEMAS: a live observation NEVER rewrites fingerprints,
  fixtures, parsers, or the I09 offline matrix.

Safety policy (enforced BEFORE any request issue, and testable offline):
- HTTPS only; only the four allowlisted production hosts
  (futures.kraken.com, api.gateio.ws, www.okx.com, www.deribit.com);
- GET only; cross-host redirects rejected; TLS verification ON;
- connect/read timeout <= 15 s; sequential only (concurrency 1); retries 0;
- no Authorization / Cookie / X-API-KEY / OK-ACCESS-KEY headers; no API keys.

Live evidence is committed only as a sanitized SUMMARY (no full volatile raw
payloads, no secrets, no cookies, no environment): request fingerprint, raw
content hash, endpoint host/path, HTTP status, result class, row count,
completion/quality flags, schema state, timestamps.  Offline evidence (the I09
matrix) is historical and immutable — I10 writes NEW smoke evidence, never
rewrites NOT_RUN to PASS in the offline inventory.

Every physical request resolves to exactly one result class (the vocabulary
belongs to this smoke evidence layer, not the adapter code):

    LIVE_PASS_NONEMPTY, LIVE_PASS_EMPTY_VALID, LIVE_PASS_PARTIAL_TRUTHFUL,
    ACCESS_BLOCKED, GEO_BLOCKED, RATE_LIMITED, TRANSPORT_FAILURE,
    PROVIDER_ERROR, SCHEMA_ADDITIVE_REVIEW, SCHEMA_BREAKING,
    UNEXPECTED_RESPONSE, INTERNAL_FAILURE

is_complete=False from a frozen LIMITED continuation is NOT a smoke failure
(OKX/Gate/Deribit historical continuation stays LIMITED; EMPTY_VALID and
truthfully-partial are PASS states).  No provider code is modified by this
module; a live defect is RECORDED and returned for operator repair planning.

I10R1 temporal-plausibility doctrine: a 200 with a known JSON shape and a
nonempty batch is NOT semantic correctness.  Non-CURRENT_ONLY historical/event
smoke requests with rows must derive BOTH convenience timestamps, and the
derived timestamps must stay within a broad 365-day envelope around the
requested window (catastrophic unit sanity only — this is NOT
window-completeness validation).  1970 during a 2026 smoke is a broken interpretation and is
classified TEMPORAL_SEMANTIC_REVIEW, never LIVE_PASS.  CURRENT_ONLY books are
exempt from containment (a snapshot may be stamped slightly after the nominal
request end) but a catastrophically wrong supplied timestamp still fails.
"""

from __future__ import annotations

import hashlib
import json
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode, urlparse

from ..contracts.enums import SensorFamily
from .base.enums import FetchPurpose
from .base.errors import (
    AccessClassViolation,
    AcquisitionError,
    AuthenticationRequired,
    CapabilityUnavailable,
    GeoRestricted,
    InvalidInstrument,
    ProviderSemanticError,
    ProviderUnavailable,
    RateLimited,
    SchemaDrift,
)
from .base.models import FetchBatch, FetchRequest
from .base.protocol import dispatch_fetch
from .readiness import DEFAULT_BLOC_03_EVIDENCE_DIR, PRODUCTION_PROVIDER_REGISTRY

# ---------------------------------------------------------------------------
# Opt-in gate + safety constants
# ---------------------------------------------------------------------------

SMOKE_TRIGGER = "SENSOR_NETWORK_SMOKE"

#: The ONLY environment value the smoke reads.  No API keys / secrets.
def network_smoke_enabled() -> bool:
    import os

    return os.environ.get(SMOKE_TRIGGER) == "1"


ALLOWED_HOSTS: frozenset[str] = frozenset(
    {
        "futures.kraken.com",
        "api.gateio.ws",
        "www.okx.com",
        "www.deribit.com",
    }
)

MAX_NETWORK_CALLS = 20
MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2 MiB
DEFAULT_TIMEOUT_S = 15
USER_AGENT = "quant-box-sensor-smoke/1.0"
DEFAULT_PAGE_SIZE_HINT = 25

#: Credential / private headers that must NEVER be sent.
FORBIDDEN_HEADER_KEYS: frozenset[str] = frozenset(
    {
        "authorization",
        "cookie",
        "x-api-key",
        "ok-access-key",
        "proxy-authorization",
    }
)

# ---------------------------------------------------------------------------
# Result vocabulary + exceptions
# ---------------------------------------------------------------------------

LIVE_PASS_NONEMPTY = "LIVE_PASS_NONEMPTY"
LIVE_PASS_EMPTY_VALID = "LIVE_PASS_EMPTY_VALID"
LIVE_PASS_PARTIAL_TRUTHFUL = "LIVE_PASS_PARTIAL_TRUTHFUL"
ACCESS_BLOCKED = "ACCESS_BLOCKED"
GEO_BLOCKED = "GEO_BLOCKED"
RATE_LIMITED = "RATE_LIMITED"
TRANSPORT_FAILURE = "TRANSPORT_FAILURE"
PROVIDER_ERROR = "PROVIDER_ERROR"
SCHEMA_ADDITIVE_REVIEW = "SCHEMA_ADDITIVE_REVIEW"
SCHEMA_BREAKING = "SCHEMA_BREAKING"
TEMPORAL_SEMANTIC_REVIEW = "TEMPORAL_SEMANTIC_REVIEW"
UNEXPECTED_RESPONSE = "UNEXPECTED_RESPONSE"
INTERNAL_FAILURE = "INTERNAL_FAILURE"

PASS_CLASSES = frozenset(
    {LIVE_PASS_NONEMPTY, LIVE_PASS_EMPTY_VALID, LIVE_PASS_PARTIAL_TRUTHFUL}
)
#: Classes that block a full I10 PASS (all non-pass outcomes, incl. additive
#: review which needs HUMAN review before final closure).
BLOCKING_CLASSES: frozenset[str] = frozenset(
    {
        ACCESS_BLOCKED,
        GEO_BLOCKED,
        RATE_LIMITED,
        TRANSPORT_FAILURE,
        PROVIDER_ERROR,
        SCHEMA_ADDITIVE_REVIEW,
        SCHEMA_BREAKING,
        TEMPORAL_SEMANTIC_REVIEW,
        UNEXPECTED_RESPONSE,
        INTERNAL_FAILURE,
    }
)


class SmokeConfigError(Exception):
    """The smoke configuration exceeds the frozen bounds (fail closed)."""


class SmokeSafetyViolation(Exception):
    """A request violated the frozen network-safety policy (rejected)."""


class SmokeTransportFailure(Exception):
    """Transport could not complete the request (no retry, recorded)."""


# ---------------------------------------------------------------------------
# Target derivation (from the canonical matrix + registry, never invented)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SmokeTarget:
    """One PHYSICAL production-symbol request in the frozen run plan."""

    provider_id: str
    sensor_family: SensorFamily
    native_instrument_id: str
    start_time: datetime
    end_time: datetime

    @property
    def logical_key(self) -> tuple[str, SensorFamily]:
        return (self.provider_id, self.sensor_family)


def _window_for(
    provider_id: str, sensor: SensorFamily, anchor: datetime
) -> tuple[datetime, datetime]:
    """Conservative small RECENT closed window (I14 §-time policy).

    INTERVAL/ANALYTICS paths (Kraken basis/book-metric/funding/liquidation/OI/
    positioning; Gate funding/liquidation/OI/positioning; OKX & Deribit
    funding):  end = anchor - 2h, start = end - 24h.

    RAW TRADE (OKX MECHANICAL_TRADE, Deribit MECHANICAL_TRADE):
      end = anchor - 5m, start = end - 10m.

    DERIBIT LIQUIDATION EVENT path:
      end = anchor - 5m, start = end - 60m.

    CURRENT_ONLY BOOK: nominal snapshot window around the anchor (the builder
    stays current-only and ignores historical semantics).
    """
    if sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
        return anchor - timedelta(seconds=1), anchor
    if sensor is SensorFamily.MECHANICAL_TRADE:
        end = anchor - timedelta(minutes=5)
        return end - timedelta(minutes=10), end
    if provider_id == "DERIBIT" and sensor is SensorFamily.MECHANICAL_LIQUIDATION:
        end = anchor - timedelta(minutes=5)
        return end - timedelta(minutes=60), end
    end = anchor - timedelta(hours=2)
    return end - timedelta(hours=24), end


def build_smoke_targets(
    matrix_rows: list[dict[str, str]], anchor: datetime
) -> list[SmokeTarget]:
    """Derive the PHYSICAL request list from the canonical matrix.

    `matrix_rows` are the derived 17 production rows (production_symbol_scope
    pipe-delimited).  For each logical (provider, sensor) path, EVERY
    production symbol becomes one physical request — so Kraken OI (PI_XBTUSD +
    PI_ETHUSD) yields two physical requests.  Stable order: provider_id, then
    sensor_family, then native_instrument_id.
    """
    targets: list[SmokeTarget] = []
    for row in sorted(
        matrix_rows, key=lambda r: (r["provider_id"], r["sensor_family"])
    ):
        provider = row["provider_id"]
        sensor = SensorFamily(row["sensor_family"])
        symbols = [
            s for s in (row.get("production_symbol_scope") or "").split("|") if s
        ]
        for symbol in sorted(set(symbols)):
            start, end = _window_for(provider, sensor, anchor)
            targets.append(
                SmokeTarget(provider, sensor, symbol, start_time=start, end_time=end)
            )
    return targets


# ---------------------------------------------------------------------------
# Live/offline-sharable transport machinery
# ---------------------------------------------------------------------------


def _host_of(url: str) -> str:
    return (urlparse(url).netloc or "").lower().split("@")[-1].split(":")[0]


def assert_safe_https(url: str) -> str:
    """HTTPS-only + host-allowlist enforcement (offline-testable)."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise SmokeSafetyViolation(f"non-HTTPS url rejected: {url!r}")
    host = _host_of(url)
    if host not in ALLOWED_HOSTS:
        raise SmokeSafetyViolation(f"host {host!r} not in allowlist")
    return host


def assert_no_credential_headers(headers: dict[str, str]) -> None:
    """Never send Authorization / Cookie / API-key headers."""
    lowered = {k.lower() for k in headers}
    bad = lowered & FORBIDDEN_HEADER_KEYS
    if bad:
        raise SmokeSafetyViolation(
            f"credential/private header would be sent: {sorted(bad)}"
        )


def cross_host_redirect(old_url: str, new_url: str) -> bool:
    """True if a redirect would move to a different host (must be rejected)."""
    return _host_of(old_url) != _host_of(new_url)


class _SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):  # type: ignore[no-any-unimported]
    """Reject any redirect that crosses to a non-allowlisted / different host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        old = req.full_url or req.get_full_url()
        if cross_host_redirect(old, newurl):
            raise SmokeSafetyViolation(
                f"cross-host redirect rejected: {_host_of(old)!r} -> {_host_of(newurl)!r}"
            )
        assert_safe_https(newurl)
        return super().redirect_request(
            req, fp, code, msg, headers, newurl
        )


def _default_opener() -> Any:
    context = ssl.create_default_context()  # TLS verification ON
    handler = _SameHostRedirectHandler()
    return urllib.request.build_opener(handler, urllib.request.HTTPSHandler(context=context))


def perform_smoke_http(
    method: str,
    url: str,
    params: dict[str, Any],
    *,
    timeout: int = DEFAULT_TIMEOUT_S,
    max_response_bytes: int = MAX_RESPONSE_BYTES,
    opener: Any = _default_opener,
    user_agent: str = USER_AGENT,
) -> tuple[int, Any]:
    """Issue ONE HTTPS GET and return (http_status, parsed_body_or_text).

    Enforces GET-only, HTTPS/host allowlist, no credential headers, timeout,
    and the response-byte cap.  An HTTP error status is returned (status,
    body_text) so the frozen adapter error classifier handles it — it is never
    confused with a successful payload.  A connection-level failure raises
    `SmokeTransportFailure` (no retry in this run).
    """
    if method != "GET":
        raise SmokeSafetyViolation(f"only GET is permitted (requested {method!r})")
    assert_safe_https(url)
    assert_no_credential_headers({"User-Agent": user_agent})
    if timeout <= 0 or timeout > DEFAULT_TIMEOUT_S:
        raise SmokeSafetyViolation(f"timeout {timeout!r} outside <=15s policy")
    if max_response_bytes > MAX_RESPONSE_BYTES:
        raise SmokeSafetyViolation(
            f"response cap {max_response_bytes!r} exceeds 2 MiB policy"
        )

    separator = "&" if "?" in url else "?"
    full_url = f"{url}{separator}{urlencode(params)}"
    request = urllib.request.Request(
        full_url, data=None, method="GET", headers={"User-Agent": user_agent}
    )
    # Accept either an opener INSTANCE (has .open) or a factory to call.
    opener_obj = opener() if callable(opener) and not hasattr(opener, "open") else opener
    try:
        with opener_obj.open(request, timeout=timeout) as response:
            status = int(getattr(response, "status", getattr(response, "code", 200)))
            raw = response.read(max_response_bytes + 1)
            if len(raw) > max_response_bytes:
                raise SmokeTransportFailure(
                    f"response exceeds {max_response_bytes} bytes cap"
                )
            text = raw.decode("utf-8", errors="replace")
            return status, _parse_json(text)
    except (SmokeTransportFailure, SmokeSafetyViolation):
        raise
    except urllib.error.HTTPError as http_err:
        raw = http_err.read(max_response_bytes + 1)
        text = raw.decode("utf-8", errors="replace")
        return int(http_err.code), _parse_json(text)
    except urllib.error.URLError as err:
        raise SmokeTransportFailure(f"URL error: {err}") from err
    except TimeoutError as err:
        raise SmokeTransportFailure(f"timeout: {err}") from err
    except OSError as err:
        raise SmokeTransportFailure(f"OS error: {err}") from err


def _parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        # Preserve the raw text as a sentinel so the failure is classifiable,
        # never silently treated as an empty success or valid JSON.
        return {"_smoke_non_json_body": text}


class LiveSmokeTransport:
    """Generic live JSON transport matching the adapter `(url, params)` contract.

    Compatible with the injected-transport signature sealed for all four
    adapters: ``(url, params) -> (http_status_or_None, parsed_body)``.  Single
    attempt, sequential, no retries, no auth headers.
    """

    def __init__(
        self,
        opener: Any = None,
        *,
        method: str = "GET",
        timeout: int = DEFAULT_TIMEOUT_S,
        max_response_bytes: int = MAX_RESPONSE_BYTES,
    ) -> None:
        self.opener = opener or _default_opener()
        self.method = method
        self.timeout = timeout
        self.max_response_bytes = max_response_bytes
        self.calls: list[str] = []

    def __call__(self, url: str, params: dict[str, Any]) -> tuple[int | None, Any]:
        self.calls.append(url)
        status, body = perform_smoke_http(
            self.method,
            url,
            params,
            timeout=self.timeout,
            max_response_bytes=self.max_response_bytes,
            opener=self.opener,
        )
        return status, body


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def build_adapter(provider_id: str, transport: Callable[..., Any]) -> Any:
    """Instantiate the production adapter for `provider_id` with a transport."""
    if provider_id not in PRODUCTION_PROVIDER_REGISTRY:
        raise SmokeConfigError(f"provider {provider_id!r} not in production registry")
    cls = type(PRODUCTION_PROVIDER_REGISTRY[provider_id]())
    return cls(transport=transport)


def _adapter_version_of(provider_id: str) -> str:
    """Semantic version string of the production adapter (offline, no transport)."""
    factory = PRODUCTION_PROVIDER_REGISTRY.get(provider_id)
    if factory is None:
        raise SmokeConfigError(f"provider {provider_id!r} not in production registry")
    return str(getattr(factory(), "adapter_version", "") or "")


def current_git_head() -> str:
    """Capture the exact HEAD SHA the live run starts from (evidence anchor)."""
    try:
        import subprocess

        repo_root = Path(__file__).resolve().parents[4]
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(repo_root),
            check=False,
        )
        sha = (out.stdout or "").strip()
        return sha if sha else "(unavailable)"
    except Exception:  # noqa: BLE001 - evidence must still be producible offline
        return "(unavailable)"


@dataclass
class PhysicalResult:
    """Sanitized result record for ONE physical smoke request (no raw body)."""

    provider_id: str
    sensor_family: SensorFamily
    native_instrument_id: str
    request_fingerprint: str
    request_start: datetime
    request_end: datetime
    result_class: str
    http_status: int | None
    duration_ms: int
    response_bytes: int
    row_count: int
    is_complete: bool
    quality_flags: list[str]
    schema_state: str
    raw_content_hash: str | None
    actual_first: datetime | None
    actual_last: datetime | None
    error_class: str | None
    error_detail: str | None
    endpoint_host: str | None = None
    endpoint_path: str | None = None
    adapter_version: str | None = None
    evidence_ref_id: str | None = None
    native_first_timestamps: list[int] | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "sensor_family": self.sensor_family.value,
            "native_instrument_id": self.native_instrument_id,
            "request_fingerprint": self.request_fingerprint,
            "request_start": self.request_start.isoformat(),
            "request_end": self.request_end.isoformat(),
            "endpoint_host": self.endpoint_host,
            "endpoint_path": self.endpoint_path,
            "adapter_version": self.adapter_version,
            "evidence_ref_id": self.evidence_ref_id,
            "native_first_timestamps": (
                list(self.native_first_timestamps)
                if self.native_first_timestamps
                else None
            ),
            "result_class": self.result_class,
            "http_status": self.http_status,
            "duration_ms": int(self.duration_ms),
            "response_bytes": int(self.response_bytes),
            "row_count": int(self.row_count),
            "is_complete": bool(self.is_complete),
            "quality_flags": list(self.quality_flags),
            "schema_state": self.schema_state,
            "raw_content_hash": self.raw_content_hash,
            "actual_first_timestamp": self.actual_first.isoformat()
            if self.actual_first
            else None,
            "actual_last_timestamp": self.actual_last.isoformat()
            if self.actual_last
            else None,
            "error_class": self.error_class,
            "error_detail": self.error_detail,
        }


def classify_error(err: BaseException) -> str:
    if isinstance(err, SchemaDrift):
        return SCHEMA_BREAKING
    if isinstance(err, RateLimited):
        return RATE_LIMITED
    if isinstance(err, GeoRestricted):
        return GEO_BLOCKED
    if isinstance(err, AuthenticationRequired):
        return ACCESS_BLOCKED
    if isinstance(err, AccessClassViolation):
        return ACCESS_BLOCKED
    if isinstance(err, ProviderUnavailable):
        return PROVIDER_ERROR
    if isinstance(err, ProviderSemanticError):
        return PROVIDER_ERROR
    if isinstance(err, CapabilityUnavailable):
        return INTERNAL_FAILURE
    if isinstance(err, InvalidInstrument):
        return UNEXPECTED_RESPONSE
    if isinstance(err, SmokeTransportFailure):
        return TRANSPORT_FAILURE
    if isinstance(err, SmokeSafetyViolation):
        return TRANSPORT_FAILURE
    return INTERNAL_FAILURE


def classify_batch(batch: FetchBatch) -> str:
    schema = (batch.raw_payloads[0].schema_state.value if batch.raw_payloads else "none")
    if schema == "ADDITIVE_SCHEMA_CHANGE":
        return SCHEMA_ADDITIVE_REVIEW
    if schema != "KNOWN_SCHEMA":
        return UNEXPECTED_RESPONSE
    if batch.row_count > 0:
        return LIVE_PASS_NONEMPTY
    if "EMPTY_VALID" in {f.value for f in batch.quality_flags}:
        return LIVE_PASS_EMPTY_VALID
    return LIVE_PASS_PARTIAL_TRUTHFUL


def _safe_error_summary(err: AcquisitionError) -> tuple[str, str | None]:
    cls = type(err).__name__
    detail = err.detail
    if detail and len(detail) > 300:
        detail = detail[:300] + "..."
    return cls, detail


# ---------------------------------------------------------------------------
# Temporal-plausibility guard (I10R1 — smoke layer only, never providers)
# ---------------------------------------------------------------------------

#: Broad operational tolerance for the current-runtime smoke.  Historical/event
#: convenience timestamps must not lie more than this far OUTSIDE the requested
#: window — a catastrophic unit-sanity bound, NOT window-completeness
#: validation.  A provider LIMITED page a few days outside the window remains
#: truthfully PARTIAL; 1970 during a 2026 smoke fails review.
TEMPORAL_TOLERANCE_DAYS = 365

#: Native integer timestamp member keys recognized for EVIDENCE sampling only
#: (magnitude/unit adjudication, I10R1 §6/§11/§38).  Never used for
#: classification; provider bodies are heterogeneous so the generic walker
#: intentionally avoids claiming which member is authoritative.
_NATIVE_TIME_KEYS = frozenset({"time", "timestamp"})


def temporal_plausibility_review(
    target: SmokeTarget,
    row_count: int,
    actual_first: datetime | None,
    actual_last: datetime | None,
) -> str | None:
    """Return TEMPORAL_SEMANTIC_REVIEW (smoke-only class) or None.

    - NONEMPTY historical/event batch: BOTH convenience timestamps required.
      A null actual_first OR null actual_last on rows is NOT LIVE_PASS (§16).
    - NONEMPTY batch (incl. books): supplied timestamps must stay inside a
      generous 365-day envelope around the requested window (§17).
    - CURRENT_ONLY books are exempt from the required-non-null rule and
      contains-ment is generous enough to tolerate a snapshot a few seconds
      after the nominal request end (§18).  An empty-valid batch needs no
      fabricated timestamp.
    """
    is_book = target.sensor_family is SensorFamily.MECHANICAL_BOOK_SNAPSHOT
    if row_count > 0 and not is_book:
        if actual_first is None or actual_last is None:
            return TEMPORAL_SEMANTIC_REVIEW
    if row_count > 0:
        low = target.start_time - timedelta(days=TEMPORAL_TOLERANCE_DAYS)
        high = target.end_time + timedelta(days=TEMPORAL_TOLERANCE_DAYS)
        for ts in (actual_first, actual_last):
            if ts is None:
                continue
            if ts < low or ts > high:
                return TEMPORAL_SEMANTIC_REVIEW
    return None


def extract_native_time_samples(body: Any, *, cap: int = 4) -> list[int] | None:
    """Walk a decoded provider payload for native integer timestamp members.

    EVIDENCE ONLY (sanitized): returns the first ``cap`` distinct integer
    values found under keys ``time``/``timestamp`` plus the min and max, so an
    operator can adjudicate unit/magnitude without any full raw body being
    committed.  Strings/floats/bools are ignored — native integers only.
    """
    if not isinstance(body, (dict, list)):
        return None
    found: list[int] = []
    seen: set[int] = set()

    def _add(value: int) -> None:
        if value not in seen:
            seen.add(value)
            found.append(value)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in _NATIVE_TIME_KEYS:
                    if isinstance(value, int) and not isinstance(value, bool):
                        _add(value)
                    elif isinstance(value, list):
                        # Provider time members are sometimes list-typed
                        # (e.g. Kraken analytics `result.timestamp: list[int]`
                        # hour grid) rather than per-row scalars.
                        for item in value:
                            if isinstance(item, int) and not isinstance(item, bool):
                                _add(item)
                    else:
                        walk(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(body)
    if not found:
        return None
    ordered = found[:cap]
    lo, hi = min(found), max(found)
    if lo not in ordered:
        ordered.append(lo)
    if hi not in ordered:
        ordered.append(hi)
    return ordered


def _record_endpoint(
    base: dict[str, Any], transport: Any, calls_before: int
) -> None:
    """Record the endpoint host/path of the transport call this target made.

    The live transport stores the BASE url (no query params) per call, in
    issue order; the call made between `calls_before` and the end belongs to
    THIS target (sequential, one attempt per target).  A pre-transport
    rejection (e.g. safety violation) leaves no call for this target and the
    endpoint stays None — the outcome is recorded as rejected, never
    misattributed to another request.
    """
    calls = getattr(transport, "calls", None)
    if not isinstance(calls, list) or len(calls) <= calls_before:
        return
    url = calls[-1]
    if not isinstance(url, str):
        return
    parsed = urlparse(url)
    base["endpoint_host"] = parsed.netloc or None
    base["endpoint_path"] = parsed.path or None


def smoke_one(
    target: SmokeTarget,
    transport: Callable[..., Any],
    *,
    run_id: str,
    index: int,
    page_size_hint: int = DEFAULT_PAGE_SIZE_HINT,
) -> PhysicalResult:
    """Execute ONE physical request through the real adapter + live transport."""
    began = time.monotonic()
    base: dict[str, Any] = dict(
        provider_id=target.provider_id,
        sensor_family=target.sensor_family,
        native_instrument_id=target.native_instrument_id,
        request_fingerprint="",
        request_start=target.start_time,
        request_end=target.end_time,
        result_class=INTERNAL_FAILURE,
        http_status=None,
        duration_ms=0,
        response_bytes=0,
        row_count=0,
        is_complete=False,
        quality_flags=[],
        schema_state="",
        raw_content_hash=None,
        actual_first=None,
        actual_last=None,
        error_class=None,
        error_detail=None,
        endpoint_host=None,
        endpoint_path=None,
        adapter_version=None,
        evidence_ref_id=None,
    )
    adapter = build_adapter(target.provider_id, transport)
    base["adapter_version"] = str(
        getattr(adapter, "adapter_version", "") or ""
    ) or None
    calls_before = len(getattr(transport, "calls", []))
    request = FetchRequest(
        provider_id=target.provider_id,
        sensor_family=target.sensor_family,
        native_instrument_id=target.native_instrument_id,
        start_time=target.start_time,
        end_time=target.end_time,
        page_size_hint=page_size_hint,
        request_id=f"{run_id}:{index}",
        purpose=FetchPurpose.PROBE,
        adapter_semantic_version="smoke-v1",
    )
    try:
        batch = dispatch_fetch(adapter, request)
    except AcquisitionError as err:
        cls, detail = _safe_error_summary(err)
        base["result_class"] = classify_error(err)
        base["error_class"] = cls
        base["error_detail"] = detail
        base["http_status"] = getattr(err, "http_status", None)
        if getattr(err, "request_fingerprint", None):
            base["request_fingerprint"] = str(err.request_fingerprint)
        env = getattr(err, "raw_payload_envelope", None)
        if env is not None:
            base["raw_content_hash"] = env.content_hash
            base["schema_state"] = env.schema_state.value
        _record_endpoint(base, transport, calls_before)
        base["duration_ms"] = int((time.monotonic() - began) * 1000)
        return PhysicalResult(**base)  # type: ignore[arg-type]
    except (SmokeConfigError, SmokeSafetyViolation) as err:
        base["result_class"] = TRANSPORT_FAILURE
        base["error_class"] = type(err).__name__
        base["error_detail"] = str(err)
        _record_endpoint(base, transport, calls_before)
        base["duration_ms"] = int((time.monotonic() - began) * 1000)
        return PhysicalResult(**base)  # type: ignore[arg-type]
    except Exception as err:  # noqa: BLE001 - classify unexpected as INTERNAL
        base["result_class"] = INTERNAL_FAILURE
        base["error_class"] = type(err).__name__
        base["error_detail"] = str(err)[:300]
        _record_endpoint(base, transport, calls_before)
        base["duration_ms"] = int((time.monotonic() - began) * 1000)
        return PhysicalResult(**base)  # type: ignore[arg-type]

    base["result_class"] = classify_batch(batch)
    base["http_status"] = batch.http_status
    base["request_fingerprint"] = batch.request_fingerprint
    base["row_count"] = batch.row_count
    base["is_complete"] = batch.is_complete
    base["quality_flags"] = [f.value for f in batch.quality_flags]
    base["actual_first"] = batch.actual_first_timestamp
    base["actual_last"] = batch.actual_last_timestamp
    if batch.raw_payloads:
        envelope = batch.raw_payloads[0]
        base["raw_content_hash"] = envelope.content_hash
        base["schema_state"] = envelope.schema_state.value
        base["response_bytes"] = len(
            envelope.raw_body
            if isinstance(envelope.raw_body, bytes)
            else envelope.raw_body.encode()
        )
        if envelope.evidence_ref is not None:
            base["evidence_ref_id"] = envelope.evidence_ref.evidence_id
        try:
            decoded = json.loads(envelope.raw_body)
        except (ValueError, TypeError):
            decoded = None
        base["native_first_timestamps"] = extract_native_time_samples(decoded)

    # Temporal-plausibility guard: a 1970 timestamp (or absent convenience
    # timestamps) on a nonempty historical batch can never count as LIVE_PASS.
    review = temporal_plausibility_review(
        target,
        batch.row_count,
        batch.actual_first_timestamp,
        batch.actual_last_timestamp,
    )
    if review is not None:
        base["result_class"] = review
        base["quality_flags"] = list(base["quality_flags"]) + [
            "temporal_plausibility"
        ]
        base["error_class"] = "TemporalPlausibilityReview"
        base["error_detail"] = (
            "convenience timestamps absent or outside the 365-day smoke "
            "envelope around the requested window"
        )
    _record_endpoint(base, transport, calls_before)
    base["duration_ms"] = int((time.monotonic() - began) * 1000)
    return PhysicalResult(**base)  # type: ignore[arg-type]


@dataclass(frozen=True)
class SmokeManifest:
    run_id: str
    starting_sha: str
    run_anchor_utc: datetime
    logical_path_count: int
    physical_request_count: int
    targets: list[SmokeTarget]
    page_size_hint: int = DEFAULT_PAGE_SIZE_HINT
    purpose: str = FetchPurpose.PROBE.value
    manifest_hash: str = field(init=False, default="")

    def __post_init__(self) -> None:
        payload = self._hash_payload()
        object.__setattr__(
            self,
            "manifest_hash",
            hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode("utf-8")
            ).hexdigest()[:16],
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "starting_sha": self.starting_sha,
            "run_anchor_utc": self.run_anchor_utc.isoformat(),
            "page_size_hint": self.page_size_hint,
            "purpose": self.purpose,
            "requests": self._request_details(),
        }

    def _request_details(self) -> list[dict[str, Any]]:
        return [
            {
                "provider_id": t.provider_id,
                "sensor_family": t.sensor_family.value,
                "native_instrument_id": t.native_instrument_id,
                "start_time": t.start_time.isoformat(),
                "end_time": t.end_time.isoformat(),
                "granularity": None,
                "page_size_hint": self.page_size_hint,
                "purpose": self.purpose,
                "adapter_semantic_version": _adapter_version_of(t.provider_id),
            }
            for t in self.targets
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "starting_sha": self.starting_sha,
            "run_anchor_utc": self.run_anchor_utc.isoformat(),
            "run_timestamp_utc": self.run_anchor_utc.isoformat(),
            "logical_path_count": self.logical_path_count,
            "physical_request_count": self.physical_request_count,
            "manifest_hash": self.manifest_hash,
            "max_permitted_max_calls": MAX_NETWORK_CALLS,
            "page_size_hint": self.page_size_hint,
            "purpose": self.purpose,
            "requests": self._request_details(),
        }


def logical_count(targets: list[SmokeTarget]) -> int:
    return len({t.logical_key for t in targets})


def run_smoke(
    targets: list[SmokeTarget],
    *,
    run_id: str,
    starting_sha: str,
    anchor: datetime,
    transport: LiveSmokeTransport | None = None,
    page_size_hint: int = DEFAULT_PAGE_SIZE_HINT,
) -> tuple[SmokeManifest, list[PhysicalResult]]:
    """Freeze the manifest, then execute EXACTLY that bounded plan (once)."""
    manifest = SmokeManifest(
        run_id=run_id,
        starting_sha=starting_sha,
        run_anchor_utc=anchor,
        logical_path_count=logical_count(targets),
        physical_request_count=len(targets),
        targets=list(targets),
        page_size_hint=page_size_hint,
    )
    if manifest.physical_request_count > MAX_NETWORK_CALLS:
        raise SmokeConfigError(
            f"physical request count {manifest.physical_request_count} exceeds "
            f"frozen cap {MAX_NETWORK_CALLS}; stop before network"
        )
    live = transport or LiveSmokeTransport()
    results = [
        smoke_one(t, live, run_id=run_id, index=i, page_size_hint=page_size_hint)
        for i, t in enumerate(targets)
    ]
    return manifest, results


# ---------------------------------------------------------------------------
# Serialization (sanitized evidence; never the full raw payload)
# ---------------------------------------------------------------------------


def render_results_json(
    manifest: SmokeManifest,
    results: list[PhysicalResult],
    *,
    request_calls: int = 0,
    retries: int = 0,
) -> str:
    class_counts: dict[str, int] = {}

    def _bucket(cls: str) -> None:
        class_counts[cls] = class_counts.get(cls, 0) + 1

    for r in results:
        _bucket(r.result_class)
    return json.dumps(
        {
            "run_id": manifest.run_id,
            "manifest_hash": manifest.manifest_hash,
            "starting_sha": manifest.starting_sha,
            "run_anchor_utc": manifest.run_anchor_utc.isoformat(),
            "run_timestamp_utc": manifest.run_anchor_utc.isoformat(),
            "logical_path_count": manifest.logical_path_count,
            "physical_request_count": manifest.physical_request_count,
            "actual_network_call_count": request_calls,
            "retries": retries,
            "result_class_counts": {k: class_counts[k] for k in sorted(class_counts)},
            "pass_result_count": sum(
                1 for r in results if r.result_class in PASS_CLASSES
            ),
            "blocking_result_count": sum(
                1 for r in results if r.result_class in BLOCKING_CLASSES
            ),
            "physical_results": [r.summary() for r in results],
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def provider_summary(results: list[PhysicalResult]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for r in results:
        d = out.setdefault(r.provider_id, {})
        d.setdefault("pass", 0)
        d.setdefault("total", 0)
        d["total"] += 1
        if r.result_class in PASS_CLASSES:
            d["pass"] += 1
    return {k: out[k] for k in sorted(out)}


def sensor_summary(results: list[PhysicalResult]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for r in results:
        d = out.setdefault(r.sensor_family.value, {})
        d.setdefault("pass", 0)
        d.setdefault("total", 0)
        d["total"] += 1
        if r.result_class in PASS_CLASSES:
            d["pass"] += 1
    return {k: out[k] for k in sorted(out)}


def write_smoke_artifacts(
    manifest: SmokeManifest,
    results: list[PhysicalResult],
    *,
    out_dir: Path | None = None,
    request_calls: int = 0,
    retries: int = 0,
    write_results: bool = True,
) -> dict[str, Path]:
    """Freeze the plan (and optionally the results) into bloc_03 evidence.

    The plan MUST be written BEFORE request #1 so no target is added after
    the network starts.  ``write_results=False`` is used at plan-freeze time
    so an incomplete results file is never mistaken for a finished run.
    """
    out = out_dir or DEFAULT_BLOC_03_EVIDENCE_DIR
    out.mkdir(parents=True, exist_ok=True)
    plan_path = out / "BLOC_03_I10_NETWORK_SMOKE_PLAN.json"
    res_path = out / "BLOC_03_I10_NETWORK_SMOKE_RESULTS.json"
    plan_path.write_text(
        json.dumps(manifest.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    written: dict[str, Path] = {"plan": plan_path}
    if write_results:
        res_path.write_text(
            render_results_json(
                manifest, results, request_calls=request_calls, retries=retries
            ),
            encoding="utf-8",
            newline="\n",
        )
        written["results"] = res_path
    return written