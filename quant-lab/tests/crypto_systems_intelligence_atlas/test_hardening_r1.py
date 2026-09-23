"""Hardening regression tests R1 — Book 1 kernel correctness (2026-09-23).

Each test reproduces an audit finding BEFORE the fix is applied (tests must
fail first). Contract references: plan v0.3 §1A/§1D; INV-1A-9..11, INV-1D-1..5.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from crypto_systems_intelligence_atlas.identity import (
    CanonicalObject,
    DeploymentMarkerKind,
    ObjectType,
    RealizationIdentity,
    RealizationRoute,
    RealizationStatus,
    RepresentationMechanism,
    mint_object_id,
)
from crypto_systems_intelligence_atlas.temporal import (
    OPEN,
    RecordStore,
    TemporalRecord,
    UnknownBound,
    holds_at,
)

from .conftest import NOW, make_token


# ==========================================================================
# R1 — RealizationIdentity.is_live() (Finding A)
# ==========================================================================


class TestRealizationLiveness:
    T0 = datetime(2026, 1, 1, tzinfo=UTC)
    T1 = datetime(2026, 6, 1, tzinfo=UTC)  # closure instant
    T2 = datetime(2026, 12, 1, tzinfo=UTC)

    def _real(
        self,
        status,
        valid_from=datetime(2025, 1, 1, tzinfo=UTC),
        valid_to=OPEN,
        migration_from=None,
    ) -> RealizationIdentity:
        return RealizationIdentity(
            realization_id="csia:stablecoin:x@csia:blockchain:ch:mk",
            canonical_asset_id="csia:stablecoin:x",
            chain_id="csia:blockchain:ch",
            local_asset_identifier="denom",
            representation_mechanism=RepresentationMechanism.IBC,
            valid_from=valid_from,
            valid_to=valid_to,
            status=status,
            migration_from=migration_from,
        )

    def test_1_active_no_valid_to_is_live(self):
        r = self._real(RealizationStatus.ACTIVE)
        assert r.is_live(self.T0) is True
        assert r.is_live(self.T2) is True

    def test_2_active_future_valid_to(self):
        r = self._real(RealizationStatus.ACTIVE, valid_to=self.T1)
        assert r.is_live(self.T0) is True
        assert r.is_live(self.T2) is False

    def test_3_closed_past_valid_to_before_closure_true(self):
        """Finding A: CLOSED + valid_to=T1 must be live at T0 < T1."""
        r = self._real(RealizationStatus.CLOSED, valid_to=self.T1)
        assert r.is_live(self.T0) is True

    def test_4_closed_past_valid_to_after_closure_false(self):
        r = self._real(RealizationStatus.CLOSED, valid_to=self.T1)
        assert r.is_live(self.T2) is False

    def test_5_migrated_with_valid_to(self):
        r = self._real(
            RealizationStatus.MIGRATED,
            valid_to=self.T1,
            migration_from="csia:stablecoin:x@csia:blockchain:ch:old",
        )
        assert r.is_live(self.T0) is True
        assert r.is_live(self.T2) is False

    def test_6_unknown_valid_to_never_certain(self):
        r = self._real(
            RealizationStatus.ACTIVE,
            valid_to=UnknownBound(
                earliest_bound=self.T0,
                latest_bound=self.T2,
            ),
        )
        assert r.is_live(self.T1) is None  # undecidable inside bounds
        assert r.is_live(self.T2) is False  # beyond latest bound: ended

    def test_closed_before_valid_from_not_live(self):
        r = self._real(
            RealizationStatus.CLOSED,
            valid_from=self.T0,
            valid_to=self.T1,
        )
        assert r.is_live(datetime(2024, 1, 1, tzinfo=UTC)) is False


# ==========================================================================
# R2 — holds_at() UNKNOWN semantics (Finding B)
# ==========================================================================


class TestHoldsAtTruthTable:
    """Expected semantics (no fabricated certainty):

    start=KNOWN, end=KNOWN   : normal interval logic
    start=KNOWN, end=OPEN    : True after start
    start=UNKNOWN, end=OPEN  : False before earliest; None in [earliest, latest);
                               True at/after latest (start has begun by then)
    start=UNKNOWN, end=UNKNOWN: False before earliest_start; None where start
                               or end is uncertain; False after latest_end
    start=KNOWN, end=UNKNOWN : False before start; None within end bounds;
                               False after latest_end
    """

    E1 = datetime(2020, 1, 1, tzinfo=UTC)
    E6 = datetime(2020, 6, 1, tzinfo=UTC)

    def test_known_start_open_end(self):
        assert holds_at(self.E1, OPEN, datetime(2021, 1, 1, tzinfo=UTC)) is True
        assert holds_at(self.E1, OPEN, datetime(2019, 1, 1, tzinfo=UTC)) is False

    def test_known_start_known_end(self):
        end = datetime(2021, 1, 1, tzinfo=UTC)
        assert holds_at(self.E1, end, datetime(2020, 6, 1, tzinfo=UTC)) is True
        assert holds_at(self.E1, end, self.E1) is True
        assert holds_at(self.E1, end, end) is False

    def test_unknown_start_open_end_before_earliest_false(self):
        vf = UnknownBound(earliest_bound=self.E1, latest_bound=self.E6)
        assert holds_at(vf, OPEN, datetime(2019, 12, 1, tzinfo=UTC)) is False

    def test_unknown_start_open_end_within_bounds_undecidable(self):
        """Finding B: 2020-03-01 inside [2020-01-01, 2020-06-01) is NOT known
        True — the start may not have occurred yet."""
        vf = UnknownBound(earliest_bound=self.E1, latest_bound=self.E6)
        assert holds_at(vf, OPEN, datetime(2020, 3, 1, tzinfo=UTC)) is None

    def test_unknown_start_open_end_at_or_after_latest_true(self):
        """At/after latest_bound the start has necessarily occurred."""
        vf = UnknownBound(earliest_bound=self.E1, latest_bound=self.E6)
        assert holds_at(vf, OPEN, self.E6) is True
        assert holds_at(vf, OPEN, datetime(2021, 1, 1, tzinfo=UTC)) is True

    def test_unknown_start_known_end(self):
        vf = UnknownBound(earliest_bound=self.E1, latest_bound=self.E6)
        end = datetime(2021, 1, 1, tzinfo=UTC)
        assert holds_at(vf, end, datetime(2019, 12, 1, tzinfo=UTC)) is False
        assert holds_at(vf, end, datetime(2020, 3, 1, tzinfo=UTC)) is None
        assert holds_at(vf, end, self.E6) is True
        assert holds_at(vf, end, end) is False

    def test_unknown_start_unknown_end(self):
        vf = UnknownBound(earliest_bound=self.E1, latest_bound=self.E6)
        vt = UnknownBound(
            earliest_bound=datetime(2022, 1, 1, tzinfo=UTC),
            latest_bound=datetime(2024, 1, 1, tzinfo=UTC),
        )
        assert holds_at(vf, vt, datetime(2019, 12, 1, tzinfo=UTC)) is False
        assert holds_at(vf, vt, datetime(2020, 3, 1, tzinfo=UTC)) is None  # start uncertain
        assert holds_at(vf, vt, datetime(2021, 1, 1, tzinfo=UTC)) is True  # started, not ended
        assert holds_at(vf, vt, datetime(2023, 1, 1, tzinfo=UTC)) is None  # end uncertain
        assert holds_at(vf, vt, datetime(2025, 1, 1, tzinfo=UTC)) is False  # ended by latest

    def test_known_start_unknown_end(self):
        vt = UnknownBound(
            earliest_bound=datetime(2022, 1, 1, tzinfo=UTC),
            latest_bound=datetime(2024, 1, 1, tzinfo=UTC),
        )
        assert holds_at(self.E1, vt, datetime(2019, 1, 1, tzinfo=UTC)) is False
        assert holds_at(self.E1, vt, datetime(2021, 1, 1, tzinfo=UTC)) is True
        assert holds_at(self.E1, vt, datetime(2023, 1, 1, tzinfo=UTC)) is None
        assert holds_at(self.E1, vt, datetime(2025, 1, 1, tzinfo=UTC)) is False

    def test_unknown_start_only_latest_bound(self):
        vf = UnknownBound(latest_bound=self.E6)  # started sometime, by E6 at latest
        assert holds_at(vf, OPEN, datetime(2019, 1, 1, tzinfo=UTC)) is None  # no earliest
        assert holds_at(vf, OPEN, self.E6) is True

    def test_unknown_start_only_earliest_bound(self):
        vf = UnknownBound(earliest_bound=self.E1)  # started E1 or later
        assert holds_at(vf, OPEN, datetime(2019, 1, 1, tzinfo=UTC)) is False
        assert holds_at(vf, OPEN, datetime(2021, 1, 1, tzinfo=UTC)) is None


# ==========================================================================
# R3 — UnknownBound construction invariants
# ==========================================================================


class TestUnknownBoundValidation:
    def test_naive_earliest_rejected(self):
        with pytest.raises(ValueError):
            UnknownBound(earliest_bound=datetime(2020, 1, 1))

    def test_naive_latest_rejected(self):
        with pytest.raises(ValueError):
            UnknownBound(latest_bound=datetime(2020, 1, 1))

    def test_earliest_after_latest_rejected(self):
        with pytest.raises(ValueError):
            UnknownBound(
                earliest_bound=datetime(2021, 1, 1, tzinfo=UTC),
                latest_bound=datetime(2020, 1, 1, tzinfo=UTC),
            )

    def test_equal_bounds_allowed(self):
        ub = UnknownBound(
            earliest_bound=datetime(2020, 1, 1, tzinfo=UTC),
            latest_bound=datetime(2020, 1, 1, tzinfo=UTC),
        )
        assert ub.earliest_bound == ub.latest_bound

    def test_aware_bounds_normalized_to_utc(self):
        # +02:00 timezone normalizes to UTC
        tz_plus2 = timezone(timedelta(hours=2))
        ub = UnknownBound(
            earliest_bound=datetime(2020, 1, 1, 12, 0, tzinfo=tz_plus2),
        )
        assert ub.earliest_bound.utcoffset() == timedelta(0)
        assert ub.earliest_bound.hour == 10

    def test_all_explicit_states_allowed(self):
        # both bounds
        UnknownBound(
            earliest_bound=datetime(2020, 1, 1, tzinfo=UTC),
            latest_bound=datetime(2020, 6, 1, tzinfo=UTC),
        )
        # earliest only
        UnknownBound(earliest_bound=datetime(2020, 1, 1, tzinfo=UTC))
        # latest only
        UnknownBound(latest_bound=datetime(2020, 6, 1, tzinfo=UTC))
        # both absent (fully open uncertainty, still explicit)
        UnknownBound()


# ==========================================================================
# R4 — acyclic insertion enforcement
# ==========================================================================


class TestAcyclicInsertion:
    def _fork_chain(self, registry):
        a = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "bitcoin"))
        b = CanonicalObject(
            object_id=mint_object_id(ObjectType.BLOCKCHAIN, "chain-b"),
            object_type=ObjectType.BLOCKCHAIN,
            canonical_name="Chain B",
            valid_from=NOW,
        )
        c = CanonicalObject(
            object_id=mint_object_id(ObjectType.BLOCKCHAIN, "chain-c"),
            object_type=ObjectType.BLOCKCHAIN,
            canonical_name="Chain C",
            valid_from=NOW,
        )
        registry.mint(b)
        registry.mint(c)
        return a, b, c

    def _fork_edge(self, eid, subj, obj):
        from crypto_systems_intelligence_atlas.relationships import TypedEdge
        from crypto_systems_intelligence_atlas.temporal import ClaimBinding

        return TypedEdge(
            edge_id=eid,
            edge_type=__import__(
                "crypto_systems_intelligence_atlas.relationships", fromlist=["EdgeType"]
            ).EdgeType.FORKED_FROM,
            subject_id=subj,
            object_id=obj,
            claim_binding=ClaimBinding(claim_id=eid, source_id="s"),
            observed_at=NOW,
            valid_from=NOW,
        )

    def test_third_edge_closing_cycle_rejected_atomically(self, registry):
        from crypto_systems_intelligence_atlas.relationships import GraphValidator

        a, b, c = self._fork_chain(registry)
        v = GraphValidator(registry)
        v.add_edge(self._fork_edge("f1", a.object_id, b.object_id))
        v.add_edge(self._fork_edge("f2", b.object_id, c.object_id))
        with pytest.raises(ValueError, match="cycle"):
            v.add_edge(self._fork_edge("f3", c.object_id, a.object_id))
        # rejection atomic: invalid edge absent, prior graph intact
        assert "f3" not in v.edges
        assert set(v.edges) == {"f1", "f2"}

    def test_settles_to_second_insertion_rejected(self, registry):
        from crypto_systems_intelligence_atlas.relationships import (
            EdgeType,
            GraphValidator,
            TypedEdge,
        )
        from crypto_systems_intelligence_atlas.temporal import ClaimBinding

        eth = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
        arb = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "arbitrum"))

        def e(eid, s, o):
            return TypedEdge(
                edge_id=eid,
                edge_type=EdgeType.SETTLES_TO,
                subject_id=s,
                object_id=o,
                claim_binding=ClaimBinding(claim_id=eid, source_id="s"),
                observed_at=NOW,
                valid_from=NOW,
            )

        v = GraphValidator(registry)
        v.add_edge(e("s1", arb.object_id, eth.object_id))
        with pytest.raises(ValueError, match="cycle"):
            v.add_edge(e("s2", eth.object_id, arb.object_id))
        assert "s2" not in v.edges
        assert set(v.edges) == {"s1"}

    def test_diamond_is_not_a_cycle(self, registry):
        from crypto_systems_intelligence_atlas.relationships import GraphValidator

        a, b, c = self._fork_chain(registry)
        d = CanonicalObject(
            object_id=mint_object_id(ObjectType.BLOCKCHAIN, "chain-d"),
            object_type=ObjectType.BLOCKCHAIN,
            canonical_name="Chain D",
            valid_from=NOW,
        )
        registry.mint(d)
        v = GraphValidator(registry)
        v.add_edge(self._fork_edge("f1", b.object_id, a.object_id))
        v.add_edge(self._fork_edge("f2", c.object_id, a.object_id))
        v.add_edge(self._fork_edge("f3", d.object_id, b.object_id))
        v.add_edge(self._fork_edge("f4", d.object_id, c.object_id))
        assert v.validate_acyclic(
            __import__(
                "crypto_systems_intelligence_atlas.relationships", fromlist=["EdgeType"]
            ).EdgeType.FORKED_FROM
        )


# ==========================================================================
# R5 — migration lineage enforcement (kernel-level)
# ==========================================================================


def _real(rid, canonical, chain, lineage_from=None, lineage_to=None, status="ACTIVE"):
    kwargs = {}
    if status in ("CLOSED", "MIGRATED"):
        kwargs["valid_to"] = NOW
    if status == "MIGRATED":
        kwargs["migration_from"] = lineage_from
        kwargs["migration_to"] = lineage_to
    return RealizationIdentity(
        realization_id=rid,
        canonical_asset_id=canonical,
        chain_id=chain,
        local_asset_identifier="denom-" + rid[-4:],
        representation_mechanism=RepresentationMechanism.IBC,
        route=RealizationRoute(path="p-" + rid[-4:], channel_sequence=["channel-1"]),
        valid_from=NOW,
        status=status,
        **kwargs,
    )


class TestMigrationLineageEnforcement:
    def test_self_migration_rejected(self, registry):
        usdc = make_token(registry, "usdc-lin", "USD Coin", otype=ObjectType.STABLECOIN)
        osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
        rid = f"{usdc.object_id}@{osmosis.object_id}:self"
        r = _real(rid, usdc.object_id, osmosis.object_id, lineage_to=rid, status="MIGRATED")
        with pytest.raises(ValueError, match="self-migration"):
            registry.attach_realization(usdc.object_id, r)

    def test_two_node_cycle_rejected(self, registry):
        usdc = make_token(registry, "usdc-cyc2", "USD Coin", otype=ObjectType.STABLECOIN)
        osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
        a = f"{usdc.object_id}@{osmosis.object_id}:a"
        b = f"{usdc.object_id}@{osmosis.object_id}:b"
        ra = _real(a, usdc.object_id, osmosis.object_id, lineage_to=b, status="MIGRATED")
        rb = _real(b, usdc.object_id, osmosis.object_id, lineage_to=a, status="MIGRATED")
        registry.attach_realization(usdc.object_id, ra)
        with pytest.raises(ValueError, match="cycle"):
            registry.attach_realization(usdc.object_id, rb)

    def test_three_node_cycle_rejected(self, registry):
        usdc = make_token(registry, "usdc-cyc3", "USD Coin", otype=ObjectType.STABLECOIN)
        osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
        a = f"{usdc.object_id}@{osmosis.object_id}:a"
        b = f"{usdc.object_id}@{osmosis.object_id}:b"
        c = f"{usdc.object_id}@{osmosis.object_id}:c"
        registry.attach_realization(usdc.object_id, _real(a, usdc.object_id, osmosis.object_id, lineage_to=b, status="MIGRATED"))
        registry.attach_realization(usdc.object_id, _real(b, usdc.object_id, osmosis.object_id, lineage_to=c, status="MIGRATED"))
        with pytest.raises(ValueError, match="cycle"):
            registry.attach_realization(usdc.object_id, _real(c, usdc.object_id, osmosis.object_id, lineage_to=a, status="MIGRATED"))

    def test_valid_chain_accepted(self, registry):
        usdc = make_token(registry, "usdc-chain", "USD Coin", otype=ObjectType.STABLECOIN)
        osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
        a = f"{usdc.object_id}@{osmosis.object_id}:a"
        b = f"{usdc.object_id}@{osmosis.object_id}:b"
        c = f"{usdc.object_id}@{osmosis.object_id}:c"
        registry.attach_realization(usdc.object_id, _real(a, usdc.object_id, osmosis.object_id, lineage_to=b, status="MIGRATED"))
        registry.attach_realization(usdc.object_id, _real(b, usdc.object_id, osmosis.object_id, lineage_to=c, status="MIGRATED"))
        registry.attach_realization(usdc.object_id, _real(c, usdc.object_id, osmosis.object_id, status="ACTIVE"))
        assert len(registry.get(usdc.object_id).realizations) == 3  # history kept

    def test_incoherent_pair_rejected(self, registry):
        """A declares migration_to=B; B declares migration_from=C — incoherent."""
        usdc = make_token(registry, "usdc-incoh", "USD Coin", otype=ObjectType.STABLECOIN)
        osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
        a = f"{usdc.object_id}@{osmosis.object_id}:a"
        b = f"{usdc.object_id}@{osmosis.object_id}:b"
        c = f"{usdc.object_id}@{osmosis.object_id}:c"
        registry.attach_realization(usdc.object_id, _real(a, usdc.object_id, osmosis.object_id, lineage_to=b, status="MIGRATED"))
        with pytest.raises(ValueError, match="coherent"):
            registry.attach_realization(
                usdc.object_id,
                _real(b, usdc.object_id, osmosis.object_id, lineage_from=c, status="MIGRATED"),
            )


# ==========================================================================
# R6 — supersession immutability (INV-1D-1: strict immutability ratified)
# ==========================================================================


class TestSupersessionImmutability:
    def test_supersede_does_not_mutate_old_record(self):
        store = RecordStore()
        r1 = TemporalRecord(observed_at=NOW, valid_from=NOW)
        store.add("r1", r1)
        store.supersede(
            "r1",
            "r2",
            TemporalRecord(
                observed_at=NOW + timedelta(hours=1),
                valid_from=NOW,
                supersedes="r1",
            ),
        )
        # strict immutability (INV-1D-1): the committed record object is
        # untouched — superseded_at lives in store metadata, not on the record
        assert r1.superseded_at is None
        # ...while the store still answers the R5/R7 queries correctly
        assert store.get("r1").superseded_at == NOW + timedelta(hours=1)
        assert [rid for rid, _ in store.current()] == ["r2"]

    def test_as_known_still_uses_supersession_metadata(self):
        store = RecordStore()
        store.add("r1", TemporalRecord(observed_at=NOW, valid_from=NOW))
        store.supersede(
            "r1",
            "r2",
            TemporalRecord(
                observed_at=NOW + timedelta(hours=1),
                valid_from=NOW,
                supersedes="r1",
            ),
        )
        mid = NOW + timedelta(minutes=30)
        assert [rid for rid, _ in store.as_known(mid)] == ["r1"]
        assert [rid for rid, _ in store.as_known(NOW + timedelta(hours=2))] == ["r2"]
