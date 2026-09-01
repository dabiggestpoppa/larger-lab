"""Offline network-smoke harness tests (SENSOR-B3-I10 — NO network here).

These exercise the harness SAFETY POLICY and target derivation with FAKE
openers/transports only.  They prove the harness is disabled by default, won't
exceed the frozen request cap, derives exactly 17 logical / 18 physical targets
from the canonical matrix, rejects non-HTTPS / non-allowlisted hosts, enforces
GET-only, rejects cross-host redirects and credential headers, enforces the
<=15s timeout and 2 MiB response cap, never retries, never reads a CoinAlyze
key, and that the committed result artifact never contains a raw body.

A normal ``pytest`` run NEVER touches the network (the single LIVE marked test
lives in ``test_network_smoke_live.py`` and skips without the
``SENSOR_NETWORK_SMOKE=1`` env gate).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import Any
from urllib.error import HTTPError, URLError

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.errors import (
    AccessClassViolation,
    AuthenticationRequired,
    GeoRestricted,
    RateLimited,
    SchemaDrift,
)
from crypto_sensor_fabric.providers.network_smoke import (
    ACCESS_BLOCKED,
    GEO_BLOCKED,
    LIVE_PASS_EMPTY_VALID,
    LIVE_PASS_NONEMPTY,
    MAX_NETWORK_CALLS,
    MAX_RESPONSE_BYTES,
    RATE_LIMITED,
    SCHEMA_BREAKING,
    SMOKE_TRIGGER,
    TRANSPORT_FAILURE,
    SmokeConfigError,
    SmokeManifest,
    SmokeSafetyViolation,
    SmokeTransportFailure,
    SmokeTarget,
    assert_no_credential_headers,
    assert_safe_https,
    build_adapter,
    build_smoke_targets,
    classify_error,
    cross_host_redirect,
    network_smoke_enabled,
    perform_smoke_http,
    render_results_json,
    smoke_one,
    write_smoke_artifacts,
)
from crypto_sensor_fabric.providers.readiness import (
    DEFAULT_BLOC_03_EVIDENCE_DIR,
    load_matrix_records,
)

MATRIX_CSV = DEFAULT_BLOC_03_EVIDENCE_DIR / "PRODUCTION_ADAPTER_MATRIX.csv"

ANCHOR = datetime(2026, 8, 31, 12, 0, 0, tzinfo=UTC)


def _matrix_rows() -> list[dict[str, str]]:
    assert MATRIX_CSV.exists(), f"missing {MATRIX_CSV}"
    return load_matrix_records(MATRIX_CSV)


def _targets(anchor: datetime = ANCHOR) -> list[SmokeTarget]:
    return build_smoke_targets(_matrix_rows(), anchor)


class _FakeResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self.code = status
        self._body = body

    def read(self, limit: int = -1) -> bytes:
        return self._body if limit < 0 else self._body[:limit]

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class _FakeOpener:
    """Offline urllib opener stand-in; records every open() call."""

    def __init__(
        self,
        response: _FakeResponse | None = None,
        exc: Exception | None = None,
    ) -> None:
        self.response = response
        self.exc = exc
        self.calls: list[str] = []

    def open(self, request: object, timeout: object = None) -> object:
        self.calls.append(str(getattr(request, "full_url", request)))
        if self.exc is not None:
            raise self.exc
        assert self.response is not None
        return self.response


def _ok_opener(body: bytes = b"{}") -> _FakeOpener:
    return _FakeOpener(_FakeResponse(200, body))


# ---------------------------------------------------------------------------
# Opt-in gate / default off
# ---------------------------------------------------------------------------


class TestOptIn:
    def test_smoke_disabled_without_env_gate(self, monkeypatch) -> None:
        monkeypatch.delenv(SMOKE_TRIGGER, raising=False)
        assert network_smoke_enabled() is False

    def test_smoke_enabled_only_with_explicit_1(self, monkeypatch) -> None:
        monkeypatch.setenv(SMOKE_TRIGGER, "1")
        assert network_smoke_enabled() is True
        monkeypatch.setenv(SMOKE_TRIGGER, "0")
        assert network_smoke_enabled() is False

    def test_trigger_is_only_env_value_read(self, monkeypatch) -> None:
        # A stray exchange/CoinAlyze key must never toggle the smoke gate.
        monkeypatch.setenv("COINALYZE_API_KEY", "super-secret")
        monkeypatch.setenv(SMOKE_TRIGGER, "1")
        assert network_smoke_enabled() is True
        monkeypatch.delenv(SMOKE_TRIGGER, raising=False)
        assert network_smoke_enabled() is False


# ---------------------------------------------------------------------------
# Target derivation + registry bounds
# ---------------------------------------------------------------------------


class TestTargetDerivation:
    def test_excluded_or_fifth_provider_rejected(self) -> None:
        # A callable transport stand-in; never reached because the registry
        # rejects the provider before any request is issued.
        def noop_transport(url: str, params: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            return 200, {}

        with pytest.raises(SmokeConfigError):
            build_adapter("HYPOTHETICAL_FIFTH", noop_transport)
        with pytest.raises(SmokeConfigError):
            build_adapter("BINANCE_USDM", noop_transport)

    def test_exact_17_logical_paths(self) -> None:
        logical = {t.logical_key for t in _targets()}
        assert len(logical) == 17

    def test_exact_18_physical_requests(self) -> None:
        assert len(_targets()) == 18

    def test_every_production_symbol_included(self) -> None:
        targets = _targets()
        kraken_oi = [
            t
            for t in targets
            if t.provider_id == "KRAKEN_FUTURES"
            and t.sensor_family.value == "MECHANICAL_OPEN_INTEREST"
        ]
        # Kraken OI carries BOTH PI_XBTUSD and PI_ETHUSD.
        assert {t.native_instrument_id for t in kraken_oi} == {
            "PI_XBTUSD",
            "PI_ETHUSD",
        }

    def test_request_cap_never_exceeded(self) -> None:
        assert len(_targets()) <= MAX_NETWORK_CALLS

    def test_manifest_deterministic_for_same_anchor(self) -> None:
        a = [(t.provider_id, t.native_instrument_id, t.start_time.isoformat())
             for t in _targets()]
        b = [(t.provider_id, t.native_instrument_id, t.start_time.isoformat())
             for t in _targets()]
        assert a == b


# ---------------------------------------------------------------------------
# Transport safety policy
# ---------------------------------------------------------------------------


class TestTransportSafety:
    def test_https_only_and_host_allowlist(self) -> None:
        assert_safe_https("https://www.okx.com/api/v5/market/books")
        assert_safe_https("https://futures.kraken.com/x")
        assert_safe_https("https://api.gateio.ws/x")
        assert_safe_https("https://www.deribit.com/x")
        with pytest.raises(SmokeSafetyViolation):
            assert_safe_https("http://www.okx.com/api/v5/market/books")
        with pytest.raises(SmokeSafetyViolation):
            assert_safe_https("https://fapi.binance.com/fapi/v1/position")
        with pytest.raises(SmokeSafetyViolation):
            assert_safe_https("https://archive.example.com/file")

    def test_get_only_enforced_before_request(self) -> None:
        opener = _ok_opener()
        with pytest.raises(SmokeSafetyViolation):
            perform_smoke_http(
                "POST",
                "https://www.okx.com/api/v5/market/books",
                {"instId": "BTC-USDT-SWAP"},
                opener=opener,
            )
        assert opener.calls == []  # rejected BEFORE any request

    def test_credential_headers_forbidden(self) -> None:
        assert_no_credential_headers({})
        assert_no_credential_headers({"User-Agent": "x"})
        for key in ("Authorization", "cookie", "X-API-KEY", "OK-ACCESS-KEY"):
            with pytest.raises(SmokeSafetyViolation):
                assert_no_credential_headers({key: "secret"})

    def test_cross_host_redirect_detected(self) -> None:
        assert cross_host_redirect(
            "https://www.okx.com/a", "https://evil.example.com/b"
        )
        assert not cross_host_redirect(
            "https://www.okx.com/a", "https://www.okx.com/b"
        )

    def test_timeout_policy(self) -> None:
        opener = _ok_opener()
        with pytest.raises(SmokeSafetyViolation):
            perform_smoke_http(
                "GET", "https://www.okx.com/x", {}, opener=opener, timeout=20
            )
        with pytest.raises(SmokeSafetyViolation):
            perform_smoke_http(
                "GET", "https://www.okx.com/x", {}, opener=opener, timeout=0
            )

    def test_response_cap_enforced(self) -> None:
        big = _FakeOpener(_FakeResponse(200, b"x" * (MAX_RESPONSE_BYTES + 1)))
        with pytest.raises(SmokeTransportFailure):
            perform_smoke_http("GET", "https://www.okx.com/x", {}, opener=big)

    def test_zero_retries_on_transport_failure(self) -> None:
        opener = _FakeOpener(None, exc=URLError(OSError("refused")))
        with pytest.raises(SmokeTransportFailure):
            perform_smoke_http("GET", "https://www.okx.com/x", {}, opener=opener)
        assert len(opener.calls) == 1  # exactly one attempt, no retry

    def test_json_success_transport_wiring(self) -> None:
        opener = _ok_opener(b'{"ok": true}')
        status, body = perform_smoke_http(
            "GET",
            "https://www.okx.com/api/v5/market/books",
            {"instId": "BTC-USDT-SWAP"},
            opener=opener,
        )
        assert status == 200
        assert body == {"ok": True}
        assert len(opener.calls) == 1

    def test_html_non_json_preserved_not_pretended(self) -> None:
        opener = _FakeOpener(_FakeResponse(200, b"<html>blocked</html>"))
        status, body = perform_smoke_http(
            "GET", "https://www.okx.com/x", {}, opener=opener
        )
        assert status == 200
        # The non-JSON body is preserved (not silently parsed as {} / null).
        assert isinstance(body, dict) and "_smoke_non_json_body" in body

    def test_http_error_status_handed_back_not_raised(self) -> None:
        err = HTTPError(
            "https://futures.kraken.com/history",
            429,
            "Too Many Requests",
            hdrs=None,  # type: ignore[arg-type]
            fp=BytesIO(b'{"error": "rate"}'),
        )
        opener = _FakeOpener(None, exc=err)
        status, body = perform_smoke_http(
            "GET", "https://futures.kraken.com/history", {}, opener=opener
        )
        assert status == 429
        assert body == {"error": "rate"}


# ---------------------------------------------------------------------------
# Result classifier + serializer
# ---------------------------------------------------------------------------


class TestClassifier:
    def test_schema_drift_is_breaking(self) -> None:
        assert (
            classify_error(SchemaDrift("x", SensorFamily.MECHANICAL_FUNDING))
            == SCHEMA_BREAKING
        )

    def test_access_classes(self) -> None:
        assert (
            classify_error(RateLimited("x", SensorFamily.MECHANICAL_FUNDING))
            == RATE_LIMITED
        )
        assert (
            classify_error(GeoRestricted("x", SensorFamily.MECHANICAL_FUNDING))
            == GEO_BLOCKED
        )
        assert (
            classify_error(AuthenticationRequired("x", SensorFamily.MECHANICAL_FUNDING))
            == ACCESS_BLOCKED
        )
        assert (
            classify_error(AccessClassViolation("x", SensorFamily.MECHANICAL_FUNDING))
            == ACCESS_BLOCKED
        )
        assert (
            classify_error(SmokeTransportFailure("boom")) == TRANSPORT_FAILURE
        )

    def test_serializer_never_contains_raw_body(self) -> None:
        from crypto_sensor_fabric.providers.network_smoke import PhysicalResult

        r = PhysicalResult(
            provider_id="OKX_SWAP",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            native_instrument_id="BTC-USDT-SWAP",
            request_fingerprint="fp",
            request_start=ANCHOR,
            request_end=ANCHOR,
            result_class=LIVE_PASS_NONEMPTY,
            http_status=200,
            duration_ms=5,
            response_bytes=10,
            row_count=1,
            is_complete=False,
            quality_flags=[],
            schema_state="KNOWN_SCHEMA",
            raw_content_hash="h",
            actual_first=None,
            actual_last=None,
            error_class=None,
            error_detail=None,
        )
        summary = r.summary()
        assert "raw_body" not in summary
        assert summary["provider_id"] == "OKX_SWAP"

    def test_render_json_is_small_sanitized(self) -> None:
        manifest = SmokeManifest(
            run_id="r1",
            starting_sha="abc",
            run_anchor_utc=ANCHOR,
            logical_path_count=17,
            physical_request_count=len(_targets()),
            targets=_targets(),
        )
        out = render_results_json(manifest, [])
        assert "raw_body" not in out
        assert '"physical_request_count": 18' in out


# ---------------------------------------------------------------------------
# Offline artifacts never touch the I09 immutable matrix
# ---------------------------------------------------------------------------


class TestArtifactBoundary:
    def test_smoke_artifacts_do_not_rewrite_offline_matrix(self, tmp_path) -> None:
        manifest = SmokeManifest(
            run_id="r1",
            starting_sha="abc",
            run_anchor_utc=ANCHOR,
            logical_path_count=17,
            physical_request_count=len(_targets()),
            targets=_targets(),
        )
        out = tmp_path / "smoke"
        written = write_smoke_artifacts(manifest, [], out_dir=out)
        names = {p.name for p in written.values()}
        assert names == {
            "BLOC_03_I10_NETWORK_SMOKE_PLAN.json",
            "BLOC_03_I10_NETWORK_SMOKE_RESULTS.json",
        }
        assert "PRODUCTION_ADAPTER_MATRIX" not in " ".join(names)

    def test_run_smoke_rejects_over_cap_before_network(self) -> None:
        from crypto_sensor_fabric.providers.network_smoke import run_smoke

        targets = _targets() * 2  # 36 > cap of 20
        with pytest.raises(SmokeConfigError):
            run_smoke(
                targets,
                run_id="r1",
                starting_sha="abc",
                anchor=ANCHOR,
            )


# ---------------------------------------------------------------------------
# smoke_one round-trip through a REAL frozen adapter (fake transport only)
# ---------------------------------------------------------------------------

#: Minimal OKX v5 funding body matching the committed 09 schema fingerprint.
_OKX_FUNDING_HAPPY = {
    "code": "0",
    "msg": "",
    "data": [
        {
            "instId": "BTC-USDT-SWAP",
            "fundingRate": "0.000075",
            "realizedRate": "0.000075",
            "fundingTime": "1755000000000",
            "formulaType": "A",
            "instType": "SWAP",
            "method": "ma",
        }
    ],
}

_OKX_FUNDING_EMPTY = {"code": "0", "msg": "", "data": []}


class _FakeSmokeTransport:
    """Fake `(url, params) -> (status, body)` transport — never touches network."""

    def __init__(self, body: dict) -> None:
        self.body = body
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, url: str, params: dict) -> tuple[int | None, dict]:
        self.calls.append((url, params))
        return 200, self.body


class TestSmokeOneOffline:
    def _target(self) -> SmokeTarget:
        end = ANCHOR - timedelta(hours=2)
        return SmokeTarget(
            "OKX_SWAP",
            SensorFamily.MECHANICAL_FUNDING,
            "BTC-USDT-SWAP",
            start_time=end - timedelta(hours=24),
            end_time=end,
        )

    def test_smoke_one_nonempty_result_serializes(self) -> None:
        res = smoke_one(
            self._target(), _FakeSmokeTransport(_OKX_FUNDING_HAPPY), run_id="r1", index=0
        )
        assert res.result_class == LIVE_PASS_NONEMPTY
        assert res.http_status == 200
        assert res.row_count == 1
        assert res.request_fingerprint
        assert res.raw_content_hash
        summary = res.summary()
        assert summary["sensor_family"] == "MECHANICAL_FUNDING"
        assert "raw_body" not in summary

    def test_smoke_one_empty_valid(self) -> None:
        res = smoke_one(
            self._target(), _FakeSmokeTransport(_OKX_FUNDING_EMPTY), run_id="r1", index=0
        )
        assert res.result_class == LIVE_PASS_EMPTY_VALID
        assert res.row_count == 0
        assert res.is_complete is False  # OKX historical continuation LIMITED

    def test_manifest_plan_fields_present(self) -> None:
        manifest = SmokeManifest(
            run_id="r1",
            starting_sha="abc",
            run_anchor_utc=ANCHOR,
            logical_path_count=17,
            physical_request_count=len(_targets()),
            targets=_targets(),
        )
        plan = manifest.as_dict()
        assert plan["run_timestamp_utc"] == ANCHOR.isoformat()
        assert plan["manifest_hash"] == manifest.manifest_hash
        assert plan["logical_path_count"] == 17
        assert plan["physical_request_count"] == 18
        for req in plan["requests"]:
            assert req["page_size_hint"] == 25
            assert req["purpose"] == "PROBE"
            assert req["granularity"] is None
            assert req["adapter_semantic_version"]
        # The hash covers the whole frozen plan (run identity + every target).
        assert plan["manifest_hash"]

    def test_results_json_has_blocking_counts(self) -> None:
        manifest = SmokeManifest(
            run_id="r1",
            starting_sha="abc",
            run_anchor_utc=ANCHOR,
            logical_path_count=1,
            physical_request_count=1,
            targets=[self._target()],
        )
        ok = smoke_one(
            self._target(), _FakeSmokeTransport(_OKX_FUNDING_HAPPY), run_id="r1", index=0
        )
        out = render_results_json(manifest, [ok])
        assert '"blocking_result_count": 0' in out
        assert '"pass_result_count": 1' in out