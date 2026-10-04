"""SENSOR-B4-I16R2 — source-unit claim truth tests (RED at I16R2A).

I16R2A lands these tests RED: the I16R1 contract accepts and persists

    SourceUnitEvidence(field_name="quantity_unit",
                       native_unit_lexeme="SOL",
                       state=VERIFIED_NATIVE)

without proving anything about the committed projection evidence, so the
operator finding reproduces exactly (I16R2 §2/§3, recorded in
``BLOC_04_I16R2_REAL_UNIT_PROJECTION_AUDIT.json``):

    RED-1  declared SOL / rows BTC      -> COMMIT_SUCCEEDED,
                                          handoff exposed VERIFIED_NATIVE/SOL
    RED-2  mixed rows SOL + BTC         -> COMMIT_SUCCEEDED,
                                          static claim silently collapsed

I16R2B makes these GREEN by binding static claims to committed row evidence
at the T0B commit boundary:

  * §4/§9/§14 — VERIFIED_NATIVE means ONLY: the declared provider-native
    lexeme is proven invariant across the committed projection evidence;
    mismatch / mixed distinct lexemes / an all-null column are typed
    refusals BEFORE any durable projection publication.
  * §10 — null/optional law: nulls are absence of a value, not disagreement;
    zero non-null values cannot vacuously verify a static claim.
  * §15 — bounded distinct-state scanning (0 / 1 / >1), never all values.
  * §17 — typed ``ProjectionUnitEvidenceConflict`` with safe metadata only.
  * §18 — UNIT_UNVERIFIED never auto-promotes from row bytes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pyarrow as pa
import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

from crypto_sensor_fabric.storage import (  # noqa: E402
    ProjectionUnitEvidenceConflict,
    SourceUnitState,
)

CURRENT_HEAD = "e8d1384d98771c39cb119e2cae0ff93296be02ec"

_support = load_sibling("i16r1_contract_support", "test_i16r1_unit_contract")
Lake = _support.Lake
KNOWN = _support.KNOWN  # quantity_unit VERIFIED_NATIVE "SOL"
UNKNOWN = _support.UNKNOWN  # quantity_unit UNIT_UNVERIFIED

NULLABLE_UNIT_SCHEMA = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.float64(), nullable=False),
        pa.field("quantity_unit", pa.string(), nullable=True),
    ]
)

SOL_ROW = {"price": 1.0, "qty": 1.0, "quantity_unit": "SOL"}
BTC_ROW = {"price": 1.0, "qty": 1.0, "quantity_unit": "BTC"}


def _stack(tmp_path: Path, *, schema_id: str, declarations, schema=None):
    lake = Lake(tmp_path / "lake")
    _support._register_definition(
        lake, schema_id=schema_id, declarations=declarations, schema=schema
    )
    return lake


def _seed(lake) -> str:
    sha = lake.seed_blob(
        b'{"rows":[{"price":1.0,"qty":1.0,"quantity_unit":"SOL"}],'
        b'"ts":1700000000}'
    )
    lake.seed_acquisition(sha, "acq-r2")
    return sha


def _commit(lake, sha: str, rows, *, projection_id: str = "proj-r1"):
    result = lake.projection_service.commit_projection(
        rows=rows,
        schema_definition=lake.schema_definition,
        projection_id=projection_id,
        source_blob_sha256=[sha],
        acquisition_ids=["acq-r2"],
        provider="kraken",
        venue="futures",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="BTC-USDT",
        native_granularity="1m",
        parser_version="1.0.0",
        partition_key="kraken/futures/BTC-USDT/2026-01-15",
        logical_year=2026,
        logical_month=1,
        logical_day=15,
        lineage_manifest_id=f"lm-{projection_id}",
    )
    lake.commit_manifest(
        "pm-r1", blob_refs=[sha], projection_refs=[projection_id]
    )
    return result


def _read_back(lake, projection_id: str = "proj-r1") -> list:
    import pyarrow.parquet as pq

    artifact = lake.artifacts.get_strict(projection_id)
    table = pq.read_table(str(lake.t0b / artifact.projection_uri))
    return table.column("quantity_unit").to_pylist()


# ---------------------------------------------------------------------------
# §4/§9/§14 — static claim must be proven by committed row evidence
# ---------------------------------------------------------------------------


class TestStaticClaimCommitProof:
    def test_static_mismatch_is_refused_before_durable_commit(
        self, tmp_path: Path
    ) -> None:
        """RED-1: declared SOL but every committed row says BTC."""
        lake = _stack(
            tmp_path, schema_id="i16r2.claim.mismatch", declarations=[KNOWN]
        )
        sha = _seed(lake)
        with pytest.raises(ProjectionUnitEvidenceConflict) as excinfo:
            _commit(lake, sha, [BTC_ROW])
        conflict = excinfo.value
        assert conflict.field_path == ("quantity_unit",)
        assert conflict.declared_state == SourceUnitState.VERIFIED_NATIVE.value
        assert conflict.declared_lexeme == "SOL"
        assert conflict.conflict_class == "MISMATCH"
        assert conflict.rows_inspected == 1
        assert conflict.null_count == 0
        # No durable projection may exist after the refusal (§9).
        assert lake.artifacts.list_ids() == []
        assert lake.contexts.list_ids() == []

    def test_mixed_row_units_are_refused_for_static_claim(
        self, tmp_path: Path
    ) -> None:
        """RED-2: SOL + BTC in one batch under a static declaration."""
        lake = _stack(
            tmp_path, schema_id="i16r2.claim.mixed", declarations=[KNOWN]
        )
        sha = _seed(lake)
        with pytest.raises(ProjectionUnitEvidenceConflict) as excinfo:
            _commit(lake, sha, [SOL_ROW, BTC_ROW])
        conflict = excinfo.value
        assert conflict.conflict_class == "MIXED"
        assert conflict.distinct_lexeme_count == 2
        assert conflict.rows_inspected == 2
        assert lake.artifacts.list_ids() == []

    def test_all_null_is_not_vacuously_verified(self, tmp_path: Path) -> None:
        """§10: zero non-null values cannot prove a static lexeme."""
        lake = _stack(
            tmp_path,
            schema_id="i16r2.claim.allnull",
            declarations=[KNOWN],
            schema=NULLABLE_UNIT_SCHEMA,
        )
        sha = _seed(lake)
        with pytest.raises(ProjectionUnitEvidenceConflict) as excinfo:
            _commit(
                lake,
                sha,
                [{"price": 1.0, "qty": 1.0, "quantity_unit": None}],
            )
        conflict = excinfo.value
        assert conflict.conflict_class == "ALL_NULL"
        assert conflict.null_count == 1
        assert conflict.distinct_lexeme_count == 0
        assert lake.artifacts.list_ids() == []

    def test_partial_null_with_matching_values_is_accepted(
        self, tmp_path: Path
    ) -> None:
        """§10: null is absence of a value, not a different unit."""
        lake = _stack(
            tmp_path,
            schema_id="i16r2.claim.partialnull",
            declarations=[KNOWN],
            schema=NULLABLE_UNIT_SCHEMA,
        )
        sha = _seed(lake)
        _commit(
            lake,
            sha,
            [
                {"price": 1.0, "qty": 1.0, "quantity_unit": None},
                SOL_ROW,
            ],
        )
        assert _read_back(lake) == [None, "SOL"]

    def test_partial_null_with_conflicting_value_is_refused(
        self, tmp_path: Path
    ) -> None:
        lake = _stack(
            tmp_path,
            schema_id="i16r2.claim.partialconflict",
            declarations=[KNOWN],
            schema=NULLABLE_UNIT_SCHEMA,
        )
        sha = _seed(lake)
        with pytest.raises(ProjectionUnitEvidenceConflict) as excinfo:
            _commit(
                lake,
                sha,
                [
                    {"price": 1.0, "qty": 1.0, "quantity_unit": None},
                    BTC_ROW,
                ],
            )
        assert excinfo.value.conflict_class == "MISMATCH"
        assert lake.artifacts.list_ids() == []

    def test_matching_rows_bind_declaration_to_committed_evidence(
        self, tmp_path: Path
    ) -> None:
        """The claim is provable from durable schema + durable rows."""
        lake = _stack(
            tmp_path, schema_id="i16r2.claim.match", declarations=[KNOWN]
        )
        sha = _seed(lake)
        _commit(lake, sha, [SOL_ROW, SOL_ROW])
        committed = _read_back(lake)
        assert committed == ["SOL", "SOL"]
        registered = lake.schemas.resolve_by_id("i16r2.claim.match", "1.0.0")
        declared = registered.source_unit_evidence[0]
        assert declared.state == SourceUnitState.VERIFIED_NATIVE
        assert all(value == declared.native_unit_lexeme for value in committed)

    def test_refusal_happens_after_schema_binding_and_before_publication(
        self, tmp_path: Path
    ) -> None:
        """The refusal is a write-boundary law, not a caller convenience."""
        lake = _stack(
            tmp_path, schema_id="i16r2.claim.boundary", declarations=[KNOWN]
        )
        sha = _seed(lake)
        with pytest.raises(ProjectionUnitEvidenceConflict):
            _commit(lake, sha, [BTC_ROW])
        # No staged file survives and no committed object exists anywhere.
        assert lake.artifacts.list_ids() == []
        staging = lake.t0b / "_staging"
        assert not staging.exists() or list(staging.iterdir()) == []


# ---------------------------------------------------------------------------
# §18 — UNIT_UNVERIFIED must never auto-promote from row bytes
# ---------------------------------------------------------------------------


class TestUnknownPreservation:
    def test_unverified_never_promotes_even_when_rows_carry_a_lexeme(
        self, tmp_path: Path
    ) -> None:
        lake = _stack(
            tmp_path, schema_id="i16r2.claim.unknown", declarations=[UNKNOWN]
        )
        sha = _seed(lake)
        _commit(lake, sha, [{"price": 1.0, "qty": 1.0, "quantity_unit": "SOL"}])
        assert _read_back(lake) == ["SOL"]
        batch = _support._handoff_batch(lake, sha, registry=lake.schemas)
        assert len(batch.source_unit_evidence) == 1
        evidence = batch.source_unit_evidence[0]
        assert evidence.state == SourceUnitState.UNIT_UNVERIFIED
        assert evidence.native_unit_lexeme is None

    def test_unverified_accepts_row_varying_bytes_without_a_claim(
        self, tmp_path: Path
    ) -> None:
        lake = _stack(
            tmp_path, schema_id="i16r2.claim.unknownvary", declarations=[UNKNOWN]
        )
        sha = _seed(lake)
        _commit(lake, sha, [SOL_ROW, BTC_ROW])
        batch = _support._handoff_batch(lake, sha, registry=lake.schemas)
        assert batch.source_unit_evidence[0].state == SourceUnitState.UNIT_UNVERIFIED
        assert batch.source_unit_evidence[0].native_unit_lexeme is None
