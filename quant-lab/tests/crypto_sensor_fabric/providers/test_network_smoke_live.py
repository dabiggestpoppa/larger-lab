"""SENSOR-B3-I10 — single LIVE production-adapter network smoke test.

This is the FIRST authorized live-network checkpoint.  It is disabled by
default: without ``SENSOR_NETWORK_SMOKE=1`` the marked test SKIPs and a normal
``pytest`` run NEVER touches the network.

With the gate (``SENSOR_NETWORK_SMOKE=1 pytest -m sensor_network_smoke``) it:

1. freezes the run plan from the canonical production matrix (17 logical /
   18 physical targets) into BLOC_03_I10_NETWORK_SMOKE_PLAN.json BEFORE any
   request;
2. executes every bounded target EXACTLY once, sequentially, through the real
   frozen production adapters + the guarded live transport (HTTPS-only,
   allowlisted hosts, GET-only, <=15s timeout, 2 MiB cap, zero retries, no
   credentials);
3. records ALL outcomes into BLOC_03_I10_NETWORK_SMOKE_RESULTS.json FIRST;
4. asserts overall pass only after every result is recorded.

Any single target that fails does NOT abort the run — the remaining bounded
targets are still executed so the operator gets a complete provider map; the
test fails/holds at the very END if any BLOCKING outcome was recorded.  No
provider code is modified here; a live defect is recorded for operator repair.

LIMITED completion (OKX/Gate/Deribit) and EMPTY_VALID are PASS states, never
failures.  This test never writes the immutable offline I09 matrix.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.providers.network_smoke import (
    BLOCKING_CLASSES,
    LiveSmokeTransport,
    MAX_NETWORK_CALLS,
    SmokeManifest,
    build_smoke_targets,
    current_git_head,
    logical_count,
    network_smoke_enabled,
    run_smoke,
    write_smoke_artifacts,
    provider_summary,
    sensor_summary,
)
from crypto_sensor_fabric.providers.readiness import (
    DEFAULT_BLOC_03_EVIDENCE_DIR,
    load_matrix_records,
)

MATRIX_CSV = DEFAULT_BLOC_03_EVIDENCE_DIR / "PRODUCTION_ADAPTER_MATRIX.csv"


@pytest.mark.sensor_network_smoke
def test_live_production_network_smoke() -> None:
    if not network_smoke_enabled():
        pytest.skip("SENSOR_NETWORK_SMOKE not set; live network smoke disabled")

    records = load_matrix_records(MATRIX_CSV)
    anchor = datetime.now(UTC)
    targets = build_smoke_targets(records, anchor)
    assert len(targets) <= MAX_NETWORK_CALLS

    run_id = "i10-live"
    starting_sha = current_git_head()
    assert starting_sha and starting_sha != "(unavailable)"
    manifest = SmokeManifest(
        run_id=run_id,
        starting_sha=starting_sha,
        run_anchor_utc=anchor,
        logical_path_count=logical_count(targets),
        physical_request_count=len(targets),
        targets=targets,
    )
    # Freeze the plan BEFORE request #1 (results are written only after ALL
    # bounded targets complete).
    write_smoke_artifacts(
        manifest, [], out_dir=DEFAULT_BLOC_03_EVIDENCE_DIR, write_results=False
    )

    transport = LiveSmokeTransport()
    run_manifest, results = run_smoke(
        targets,
        run_id=run_id,
        starting_sha=starting_sha,
        anchor=anchor,
        transport=transport,
    )
    assert run_manifest.manifest_hash == manifest.manifest_hash
    request_calls = len(transport.calls)
    retries = 0  # zero retries by frozen doctrine

    # Record ALL results BEFORE any pass/fail assertion.
    write_smoke_artifacts(
        run_manifest,
        results,
        out_dir=DEFAULT_BLOC_03_EVIDENCE_DIR,
        request_calls=request_calls,
        retries=retries,
    )
    assert request_calls == len(targets)  # exactly one attempt per target
    assert request_calls <= MAX_NETWORK_CALLS
    assert run_manifest.logical_path_count == 17
    assert run_manifest.physical_request_count == 18

    blocking = [r for r in results if r.result_class in BLOCKING_CLASSES]
    if blocking:
        summary = "\n".join(
            f"  {r.provider_id}/{r.sensor_family.value}/{r.native_instrument_id}: "
            f"{r.result_class} ({r.error_class})"
            for r in blocking
        )
        pytest.fail(
            "I10 live smoke recorded BLOCK/HOLD outcome(s); all results written "
            "to BLOC_03_I10_NETWORK_SMOKE_RESULTS.json before this assertion.\n"
            f"providers={provider_summary(results)}\n"
            f"sensors={sensor_summary(results)}\nblocking:\n{summary}"
        )