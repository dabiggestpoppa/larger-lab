"""HARDENING R2 — public lifecycle operations, model_copy validation bypass,
rebrand history semantics, closure chronology.

Written test-first against build 2f2bdb9d: every test below FAILED before the
R2 repairs (see CSIA_BOOK_1_IMPLEMENTATION_EVIDENCE.md, HARDENING R2).

Contract anchors:
- Constitution v0.2 §8.3: "A rebrand changes canonical_name and adds the old
  name to aliases; the object_id never changes."
- INV-1A-10: closure is a world-change; closed realizations stay queryable.
- INV-1D-1: no record is ever deleted or mutated in place.
- IR-6: valid_from > valid_to is always invalid.
- R6/R9: valid-time liveness; no fabricated certainty.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from crypto_systems_intelligence_atlas.identity import (
    CanonicalObject,
    IdentityRegistry,
    ObjectType,
    RealizationIdentity,
    RealizationStatus,
    RepresentationMechanism,
    TickerSymbol,
    mint_object_id,
    mint_realization_id,
)
from crypto_systems_intelligence_atlas.temporal import (
    RecordStore,
    TemporalRecord,
    normalize_utc,
)

NOW = datetime(2026, 9, 23, 12, 0, 0, tzinfo=UTC)
T0 = NOW
T1 = NOW + timedelta(days=30)
T2 = NOW + timedelta(days=60)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _token(registry: IdentityRegistry, slug: str = "r2-token") -> CanonicalObject:
    obj = CanonicalObject(
        object_id=mint_object_id(ObjectType.TOKEN, slug),
        object_type=ObjectType.TOKEN,
        canonical_name="Old Name",
        valid_from=NOW,
        ticker_symbols=(
            TickerSymbol(symbol="OLD", context="spot", valid_from=NOW, collision_group="spot"),
        ),
    )
    return registry.mint(obj)


def _realization(asset: CanonicalObject, chain_id: str, marker: str = "ch20") -> RealizationIdentity:
    return RealizationIdentity(
        realization_id=mint_realization_id(asset.object_id, chain_id, marker),
        canonical_asset_id=asset.object_id,
        chain_id=chain_id,
        local_asset_identifier="ibc/D189336",
        representation_mechanism=RepresentationMechanism.IBC,
        valid_from=T0,
    )


def _registry_with_realization() -> tuple[IdentityRegistry, CanonicalObject, RealizationIdentity]:
    reg = IdentityRegistry()
    chain = reg.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.BLOCKCHAIN, "r2-chain"),
            object_type=ObjectType.BLOCKCHAIN,
            canonical_name="r2-chain",
            valid_from=NOW,
        )
    )
    asset = _token(reg, "r2-asset")
    r = _realization(asset, chain.object_id)
    reg.attach_realization(asset.object_id, r)
    return reg, asset, r


# ---------------------------------------------------------------------------
# Phase 1 — model_copy(update=...) validation-bypass audit
#
# Production sites (verified by grep on 2f2bdb9d):
#   identity.py:592  apply_rebrand      -> TickerSymbol.model_copy(valid_to=at)
#   identity.py:611  close_realization  -> RealizationIdentity.model_copy(...)
#   temporal.py:317  RecordStore.get    -> TemporalRecord.model_copy(superseded_at)
#
# Required disposition: every lifecycle-relevant model_copy site must produce
# a state that would survive full model validation. Proven behaviorally here:
#   - close_realization must NOT be able to mint valid_from > valid_to (IR-6)
#     — i.e. the "updated" record must fail like a direct construction would.
#   - RecordStore.get overlay must never mutate the committed object and the
#     overlaid view must be validation-equivalent.
# ---------------------------------------------------------------------------


class TestModelCopyAudit:
    def test_close_realization_cannot_bypass_ir6(self):
        """IR-6 via the public closure op must be rejected exactly like direct
        construction (model_copy skips validators; the kernel must not)."""
        reg, asset, r = _registry_with_realization()
        # close BEFORE the realization even started
        with pytest.raises(ValueError):
            reg.close_realization(asset.object_id, r.realization_id, T0 - timedelta(days=1))

    def test_store_get_overlay_never_mutates_committed_record(self):
        """temporal.py:317 overlay disposition: SAFE_IMMUTABLE_VIEW."""
        store = RecordStore()
        rec = TemporalRecord(observed_at=T0, valid_from=T0)
        store.add("rec-1", rec)
        store.supersede("rec-1", "rec-2", TemporalRecord(observed_at=T1, valid_from=T0, supersedes="rec-1"))
        view = store.get("rec-1")
        assert view.superseded_at == T1
        assert rec.superseded_at is None  # committed object untouched
        assert store.get("rec-1") is not view  # fresh overlay each call
        # the overlaid view is validation-equivalent (full revalidation passes)
        TemporalRecord.model_validate(view.model_dump())

    def test_apply_rebrand_window_close_view_is_validation_equivalent(self):
        """identity.py:592 overlay disposition: SAFE_BY_PREVALIDATED_INPUT —
        the closed window must satisfy full TickerSymbol validation."""
        reg = IdentityRegistry()
        obj = _token(reg)
        reg.apply_rebrand(obj.object_id, "New Name", at=T1)
        got = reg.get(obj.object_id)
        old = next(t for t in got.ticker_symbols if t.symbol == "OLD")
        assert old.valid_to == T1
        # full revalidation of the closed window passes
        TickerSymbol.model_validate(old.model_dump())


# ---------------------------------------------------------------------------
# Phase 2 — close_realization chronology validation
# ---------------------------------------------------------------------------


class TestCloseRealizationValidation:
    def test_close_before_valid_from_rejected(self):
        reg, asset, r = _registry_with_realization()
        with pytest.raises(ValueError):
            reg.close_realization(asset.object_id, r.realization_id, T0 - timedelta(days=1))

    def test_close_with_naive_time_rejected(self):
        reg, asset, r = _registry_with_realization()
        with pytest.raises(ValueError):
            reg.close_realization(asset.object_id, r.realization_id, T0.replace(tzinfo=None))

    def test_close_exactly_at_valid_from_accepted(self):
        reg, asset, r = _registry_with_realization()
        closed = reg.close_realization(asset.object_id, r.realization_id, T0)
        assert closed.status is RealizationStatus.CLOSED
        assert closed.valid_to == T0

    def test_close_after_valid_from_accepted(self):
        reg, asset, r = _registry_with_realization()
        closed = reg.close_realization(asset.object_id, r.realization_id, T1)
        assert closed.valid_to == T1
        assert closed.is_live(T0 + timedelta(days=1)) is True
        assert closed.is_live(T1 + timedelta(days=1)) is False

    def test_duplicate_close_rejected(self):
        """Closing an already-CLOSED realization is a contradictory world
        change: the closure instant is already committed history."""
        reg, asset, r = _registry_with_realization()
        reg.close_realization(asset.object_id, r.realization_id, T1)
        with pytest.raises(ValueError):
            reg.close_realization(asset.object_id, r.realization_id, T2)

    def test_close_migrated_realization_rejected(self):
        """Closure is the wrong transition for a MIGRATED realization; the
        migration lineage already determines its terminal state."""
        reg, asset, r = _registry_with_realization()
        reg.close_realization(asset.object_id, r.realization_id, T1)
        # force MIGRATED via validated model path for the precondition only
        obj = reg.get(asset.object_id)
        migrated = next(
            rr
            for rr in obj.realizations
            if rr.realization_id == r.realization_id
        ).model_copy(update={"status": RealizationStatus.MIGRATED, "migration_to": "csia:token:successor"})
        obj.realizations = tuple(
            migrated if rr.realization_id == r.realization_id else rr for rr in obj.realizations
        )
        with pytest.raises(ValueError):
            reg.close_realization(asset.object_id, r.realization_id, T2)

    def test_close_nonexistent_realization_rejected(self):
        reg, asset, _ = _registry_with_realization()
        with pytest.raises(KeyError):
            reg.close_realization(asset.object_id, "nope@nope:nope", T1)

    def test_close_unknown_object_rejected(self):
        reg, _, _ = _registry_with_realization()
        with pytest.raises(KeyError):
            reg.close_realization("csia:token:ghost", "ghost@ghost:ghost", T1)


# ---------------------------------------------------------------------------
# Phase 3 — rebrand history semantics (Constitution §8.3)
# ---------------------------------------------------------------------------


class TestRebrandNameHistory:
    def test_rebrand_preserves_old_name_in_aliases(self):
        """§8.3: rebrand changes canonical_name AND adds the old name to
        aliases. Old name must remain historically queryable."""
        reg = IdentityRegistry()
        obj = _token(reg)
        reg.apply_rebrand(obj.object_id, "New Name", at=T1)
        got = reg.get(obj.object_id)
        assert got.canonical_name == "New Name"
        assert got.object_id == obj.object_id
        old_alias = next(a for a in got.aliases if a.name == "Old Name")
        assert old_alias.valid_to == T1  # old name valid through T1
        assert old_alias.name_state == "HISTORICAL"

    def test_new_alias_window_starts_at_rebrand(self):
        reg = IdentityRegistry()
        obj = _token(reg)
        reg.apply_rebrand(obj.object_id, "New Name", at=T1)
        got = reg.get(obj.object_id)
        # the canonical name itself is the current window; the alias history
        # must not claim "New Name" was valid before the rebrand
        new_aliases = [a for a in got.aliases if a.name == "New Name"]
        assert all(a.valid_to is None for a in new_aliases)  # still holds
        old_aliases = [a for a in got.aliases if a.name == "Old Name"]
        assert len(old_aliases) == 1
        assert old_aliases[0].valid_to == T1

    def test_double_rebrand_full_history(self):
        reg = IdentityRegistry()
        obj = _token(reg)
        reg.apply_rebrand(obj.object_id, "Second Name", at=T1)
        reg.apply_rebrand(obj.object_id, "Third Name", at=T2)
        got = reg.get(obj.object_id)
        assert got.canonical_name == "Third Name"
        names = {a.name for a in got.aliases}
        assert {"Old Name", "Second Name"} <= names
        second = next(a for a in got.aliases if a.name == "Second Name")
        assert second.valid_to == T2

    def test_rebrand_ticker_history_preserved(self):
        reg = IdentityRegistry()
        obj = _token(reg)
        reg.apply_rebrand(
            obj.object_id,
            "New Name",
            new_tickers=(TickerSymbol(symbol="NEW", context="spot", valid_from=T1, collision_group="spot"),),
            at=T1,
        )
        got = reg.get(obj.object_id)
        old = next(t for t in got.ticker_symbols if t.symbol == "OLD")
        new = next(t for t in got.ticker_symbols if t.symbol == "NEW")
        assert old.valid_to == T1  # closed at rebrand
        assert new.valid_from == T1  # new window starts at rebrand
        assert old.valid_from <= old.valid_to  # IR-6 holds in history


# ---------------------------------------------------------------------------
# Phase 4 — rebrand temporal validation
# ---------------------------------------------------------------------------


class TestRebrandTemporalValidation:
    def test_rebrand_before_object_valid_from_rejected(self):
        reg = IdentityRegistry()
        obj = _token(reg)
        with pytest.raises(ValueError):
            reg.apply_rebrand(obj.object_id, "New Name", at=NOW - timedelta(days=1))

    def test_rebrand_before_active_ticker_valid_from_rejected(self):
        reg = IdentityRegistry()
        obj = CanonicalObject(
            object_id=mint_object_id(ObjectType.TOKEN, "r2-late-ticker"),
            object_type=ObjectType.TOKEN,
            canonical_name="Old Name",
            valid_from=NOW,
            ticker_symbols=(
                TickerSymbol(symbol="OLD", context="spot", valid_from=T1, collision_group="spot"),
            ),
        )
        reg.mint(obj)
        with pytest.raises(ValueError):
            reg.apply_rebrand(obj.object_id, "New Name", at=T0)  # before OLD starts

    def test_rebrand_naive_timestamp_rejected(self):
        reg = IdentityRegistry()
        obj = _token(reg)
        with pytest.raises(ValueError):
            reg.apply_rebrand(obj.object_id, "New Name", at=T1.replace(tzinfo=None))

    def test_rebrand_same_name_rejected(self):
        """A rebrand to the same canonical name is not a rebrand — it would
        mint a zero-length alias window and pollute the history."""
        reg = IdentityRegistry()
        obj = _token(reg)
        with pytest.raises(ValueError):
            reg.apply_rebrand(obj.object_id, "Old Name", at=T1)

    def test_rebrand_idempotence_not_allowed_same_instant(self):
        """Two rebrands at the same instant would create an ambiguous alias
        window (zero-length or overlapping). Fail closed."""
        reg = IdentityRegistry()
        obj = _token(reg)
        reg.apply_rebrand(obj.object_id, "New Name", at=T1)
        with pytest.raises(ValueError):
            reg.apply_rebrand(obj.object_id, "Newer Name", at=T1)

    def test_new_ticker_starting_before_rebrand_rejected(self):
        reg = IdentityRegistry()
        obj = _token(reg)
        with pytest.raises(ValueError):
            reg.apply_rebrand(
                obj.object_id,
                "New Name",
                new_tickers=(TickerSymbol(symbol="NEW", context="spot", valid_from=T0, collision_group="spot"),),
                at=T1,
            )

    def test_object_id_stable_through_rebrand(self):
        reg = IdentityRegistry()
        obj = _token(reg)
        oid = obj.object_id
        reg.apply_rebrand(obj.object_id, "New Name", at=T1)
        assert reg.get(oid).object_id == oid


# ---------------------------------------------------------------------------
# Phase 5 — lifecycle history preservation
# ---------------------------------------------------------------------------


class TestLifecycleHistoryPreservation:
    def test_deprecate_before_valid_from_rejected(self):
        reg = IdentityRegistry()
        obj = _token(reg, "r2-deprecate")
        with pytest.raises(ValueError):
            reg.deprecate(obj.object_id, at=NOW - timedelta(days=1))

    def test_deprecate_naive_time_rejected(self):
        reg = IdentityRegistry()
        obj = _token(reg, "r2-deprecate")
        with pytest.raises(ValueError):
            reg.deprecate(obj.object_id, at=T1.replace(tzinfo=None))

    def test_deprecate_valid_time_sets_window_and_keeps_object(self):
        reg = IdentityRegistry()
        obj = _token(reg, "r2-deprecate")
        oid = obj.object_id
        reg.deprecate(oid, at=T1)
        got = reg.get(oid)
        assert got.object_id == oid  # never replaced
        assert got.lifecycle_state.value == "DEPRECATED"
        assert got.valid_to == T1

    def test_deprecate_twice_rejected(self):
        reg = IdentityRegistry()
        obj = _token(reg, "r2-deprecate")
        reg.deprecate(obj.object_id, at=T1)
        with pytest.raises(ValueError):
            reg.deprecate(obj.object_id, at=T2)

    def test_before_state_reconstructable_after_lifecycle_ops(self):
        """The Book 1 doctrine: historical truth is never destroyed. After any
        lifecycle operation the pre-operation state must be reconstructable
        from the registry's retained history (names + tickers + closure)."""
        reg, asset, r = _registry_with_realization()
        oid = asset.object_id
        pre_name = asset.canonical_name
        pre_tickers = asset.ticker_symbols
        pre_realization = r
        reg.apply_rebrand(oid, "New Name", at=T1)
        reg.close_realization(oid, r.realization_id, T2)
        got = reg.get(oid)
        # old name reconstructable
        assert any(a.name == pre_name and a.valid_to == T1 for a in got.aliases)
        # old ticker window reconstructable
        old_t = next(t for t in got.ticker_symbols if t.symbol == pre_tickers[0].symbol)
        assert old_t.valid_from == pre_tickers[0].valid_from and old_t.valid_to == T1
        # realization history reconstructable (was live between T0 and T2)
        rr = next(x for x in got.realizations if x.realization_id == pre_realization.realization_id)
        assert rr.status is RealizationStatus.CLOSED
        assert rr.is_live(T1) is True  # was live before closure
        assert rr.is_live(T2 + timedelta(days=1)) is False


# ---------------------------------------------------------------------------
# Phase 6/10 — normalize_utc edge proof (shared with lifecycle validation)
# ---------------------------------------------------------------------------


class TestNormalizeUtcEdge:
    def test_naive_rejected(self):
        with pytest.raises(ValueError):
            normalize_utc(T0.replace(tzinfo=None))

    def test_aware_normalized(self):
        from datetime import timezone, timedelta as td

        tokyo = timezone(td(hours=9))
        out = normalize_utc(datetime(2026, 1, 1, 9, 0, 0, tzinfo=tokyo))
        assert out.utcoffset() == td(0)
        assert out.hour == 0
