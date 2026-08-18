"""PFT-B0 program constitution tests.

Covers experiment identity, generation fingerprints, parameter
classification, protected-partition authority, immutable run handling,
and the decision schema (build prompt section 7.8).
"""

import json

import pytest

from strategy_foundry.pft.governance import (
    decisions,
    generations,
    identity,
    ledger,
    parameters,
    partitions,
    schemas,
)
from strategy_foundry.pft.governance.identity import (
    ExperimentFingerprint,
    ExperimentID,
    GenerationID,
    InvalidExperimentID,
)
from strategy_foundry.pft.governance.parameters import (
    ForbiddenParameterUse,
    Parameter,
    ParameterRegistryError,
)
from strategy_foundry.pft.program_registry import (
    SPECIES_REGISTER,
    build_parameter_register,
    formula_register_dict,
    species_register_dict,
)

# ---------------------------------------------------------------------------
# 7.8.1 experiment ID validation
# ---------------------------------------------------------------------------


class TestExperimentID:
    def test_valid_parse_roundtrip(self):
        eid = ExperimentID.parse("PFT-A1-K1-RAW-001")
        assert str(eid) == "PFT-A1-K1-RAW-001"
        assert eid.species == "A1"
        assert eid.full_species_name == "A1-DEEPERS"
        assert eid.scope == "K1"
        assert eid.experiment_class == "RAW"
        assert eid.sequence == 1

    @pytest.mark.parametrize(
        "bad",
        [
            "PFT-A1-K1-RAW-01",      # sequence must be 3 digits
            "PFT-A1-K1-RAW-0001",    # sequence too long
            "PFT-X2-K1-RAW-001",     # unknown species
            "PFT-A1-K1-HOPE-001",    # unknown class
            "pft-a1-k1-raw-001",     # lowercase
            "A1-K1-RAW-001",         # missing program
            "PFT-A1-K1-RAW",         # missing sequence
            "PFT-A1-K1-RAW-abc",     # non-numeric sequence
        ],
    )
    def test_invalid_ids_rejected(self, bad):
        with pytest.raises(InvalidExperimentID):
            ExperimentID.parse(bad)

    def test_scope_validation(self):
        with pytest.raises(InvalidExperimentID):
            ExperimentID(species="A1-DEEPERS", scope="k1", experiment_class="RAW", sequence=1)
        with pytest.raises(InvalidExperimentID):
            ExperimentID(species="A1-DEEPERS", scope="K-1", experiment_class="RAW", sequence=1)

    def test_sequence_range(self):
        with pytest.raises(InvalidExperimentID):
            ExperimentID(species="A1-DEEPERS", scope="K1", experiment_class="RAW", sequence=1000)


# ---------------------------------------------------------------------------
# 7.8.2 generation fingerprint determinism
# ---------------------------------------------------------------------------


class TestFingerprint:
    def _fp(self, **over):
        base = dict(
            spec_gen="PFT-SPEC-GEN-001",
            data_gen="PFT-DATA-GEN-001",
            engine_gen="PFT-ENGINE-GEN-001",
            cost_gen="PFT-COST-GEN-001",
            exec_gen="PFT-EXEC-GEN-001",
            code_sha="a" * 40,
            seed=42,
        )
        base.update(over)
        return ExperimentFingerprint(**base)

    def test_same_inputs_same_fingerprint(self):
        assert self._fp().fingerprint_hex() == self._fp().fingerprint_hex()

    def test_any_generation_change_changes_fingerprint(self):
        base = self._fp()
        for field, value in [
            ("spec_gen", "PFT-SPEC-GEN-002"),
            ("data_gen", "PFT-DATA-GEN-002"),
            ("engine_gen", "PFT-ENGINE-GEN-002"),
            ("cost_gen", "PFT-COST-GEN-002"),
            ("exec_gen", "PFT-EXEC-GEN-002"),
            ("code_sha", "b" * 40),
            ("seed", 43),
        ]:
            assert self._fp(**{field: value}).fingerprint_hex() != base.fingerprint_hex()

    def test_malformed_generation_rejected(self):
        with pytest.raises(identity.InvalidGenerationID):
            self._fp(spec_gen="PFT-SPEC-GEN-xx")

    def test_reproducibility_check(self):
        self._fp().assert_reproducible(self._fp())

    def test_reproducibility_mismatch_raises(self):
        with pytest.raises(identity.FingerprintMismatchError):
            self._fp().assert_reproducible(self._fp(seed=7))

    def test_generation_id_parse_increment(self):
        gen = GenerationID.parse("PFT-ENGINE-GEN-007")
        assert str(gen.increment()) == "PFT-ENGINE-GEN-008"
        with pytest.raises(identity.InvalidGenerationID):
            GenerationID.parse("PFT-ENGINE-GEN-7")
        with pytest.raises(identity.InvalidGenerationID):
            GenerationID.parse("PFT-ALPHA-GEN-001")


# ---------------------------------------------------------------------------
# 7.8.3 parameter classification validation
# ---------------------------------------------------------------------------


class TestParameterClassification:
    def test_all_classes_parse(self):
        for cls in sorted(parameters.PARAMETER_CLASSES):
            p = Parameter(id=f"T.{cls}", name="x", value=1, parameter_class=cls, source_ref="test")
            assert p.parameter_class == cls

    def test_invalid_class_rejected(self):
        with pytest.raises(ParameterRegistryError):
            Parameter(id="T.1", name="x", value=1, parameter_class="HOPE", source_ref="test")

    def test_forbidden_optimization_blocked_in_raw(self):
        p = Parameter(
            id="T.FB", name="x", value=1.5,
            parameter_class="FORBIDDEN_OPTIMIZATION", source_ref="test",
        )
        with pytest.raises(ForbiddenParameterUse):
            p.assert_usable_in_raw()

    def test_twin_parameter_blocked_in_raw(self):
        p = Parameter(
            id="T.TW", name="x", value=2.0,
            parameter_class="TWIN_PARAMETER", source_ref="test",
        )
        with pytest.raises(ForbiddenParameterUse):
            p.assert_usable_in_raw()

    def test_author_constant_is_frozen(self):
        p = Parameter(
            id="T.AC", name="x", value=1.57,
            parameter_class="AUTHOR_CONSTANT", source_ref="test",
        )
        with pytest.raises(ForbiddenParameterUse):
            p.assert_frozen()

    def test_register_duplicates_rejected(self):
        reg = parameters.ParameterRegister()
        reg.add(Parameter(id="T.D", name="x", value=1, parameter_class="AUTHOR_CONSTANT", source_ref="t"))
        with pytest.raises(ParameterRegistryError):
            reg.add(Parameter(id="T.D", name="x", value=2, parameter_class="AUTHOR_CONSTANT", source_ref="t"))

    def test_register_completeness_check(self):
        reg = parameters.ParameterRegister()
        reg.add(Parameter(id="T.A", name="x", value=1, parameter_class="AUTHOR_CONSTANT", source_ref="t"))
        with pytest.raises(ParameterRegistryError):
            reg.assert_complete_for_raw({"T.A", "T.MISSING"})

    def test_frozen_author_constants_registered(self):
        """Every A1 author constant transcribed in the registry is frozen and RAW-usable."""
        reg = build_parameter_register()
        for p in reg.by_class("AUTHOR_CONSTANT"):
            p.assert_usable_in_raw()  # must not raise
            with pytest.raises(ForbiddenParameterUse):
                p.assert_frozen()


# ---------------------------------------------------------------------------
# 7.8.4 protected-partition authority checks
# ---------------------------------------------------------------------------


class TestPartitionAuthority:
    def test_development_open(self):
        guard = partitions.PartitionGuard()
        guard.guard("DEVELOPMENT")  # must not raise

    def test_metadata_only_open(self):
        partitions.PartitionGuard().guard("METADATA_ONLY")

    def test_confirmation_blocked_by_default(self):
        with pytest.raises(partitions.ProtectedPartitionError):
            partitions.PartitionGuard().guard("CONFIRMATION")

    def test_holdout_blocked_by_default(self):
        with pytest.raises(partitions.ProtectedPartitionError):
            partitions.PartitionGuard().guard("HOLDOUT")

    def test_unknown_partition_fails_closed(self):
        with pytest.raises(partitions.ProtectedPartitionError):
            partitions.PartitionGuard().guard("ALPHA")

    def test_explicit_authorization_opens(self):
        guard = partitions.PartitionGuard(confirmation_authorized=True, holdout_authorized=True)
        guard.guard("CONFIRMATION")
        guard.guard("HOLDOUT")

    def test_ledger_records_blocked_access(self, tmp_path):
        log_path = tmp_path / "ledger.jsonl"
        log = ledger.DataUsageLedger(log_path)
        with pytest.raises(partitions.ProtectedPartitionError):
            log.record(
                dataset_id="D1", path="x.csv", purpose="should be blocked",
                experiment_id="PFT-A1-K1-RAW-001", partition_class="HOLDOUT",
            )
        entries = log.entries()
        assert len(entries) == 1
        assert entries[0]["blocked"] is True
        assert entries[0]["authorized"] is False
        assert entries[0]["partition_class"] == "HOLDOUT"

    def test_ledger_allows_development(self, tmp_path):
        log = ledger.DataUsageLedger(tmp_path / "ledger.jsonl")
        entry = log.record(
            dataset_id="D1", path="x.csv", purpose="audit",
            experiment_id="PFT-A1-K1-RAW-001", partition_class="DEVELOPMENT",
        )
        assert entry["authorized"] is True
        assert log.entries()[0]["entry_id"] == entry["entry_id"]


# ---------------------------------------------------------------------------
# 7.8.5 immutable completed-run handling
# ---------------------------------------------------------------------------


class TestImmutableRuns:
    def _fp(self):
        return ExperimentFingerprint(
            spec_gen="PFT-SPEC-GEN-001", data_gen="PFT-DATA-GEN-001",
            engine_gen="PFT-ENGINE-GEN-001", cost_gen="PFT-COST-GEN-001",
            exec_gen="PFT-EXEC-GEN-001", code_sha="c" * 40,
        )

    def test_completed_run_cannot_be_edited(self, tmp_path):
        reg = generations.RunRegistry(tmp_path / "runs.jsonl")
        rec = reg.register("PFT-A1-K1-RAW-001", self._fp())
        assert rec.status == "COMPLETED"
        # attempt to mutate via with_status must produce a NEW record, never edit
        edited = rec.with_status("COMPLETED", reason="sneaky edit")
        assert edited is not rec
        assert reg.get(rec.run_id).status == "COMPLETED"
        assert reg.get(rec.run_id).reason == ""

    def test_invalidation_preserves_history(self, tmp_path):
        reg = generations.RunRegistry(tmp_path / "runs.jsonl")
        rec = reg.register("PFT-A1-K1-RAW-001", self._fp())
        updated = reg.invalidate(rec.run_id, reason="bug found", defect_class="INDEXING")
        assert updated.status == "INVALIDATED"
        assert reg.get(rec.run_id).status == "INVALIDATED"
        # invalidating twice must fail
        with pytest.raises(generations.RunRegistryError):
            reg.invalidate(rec.run_id, reason="again")

    def test_supersede_creates_new_generation(self, tmp_path):
        reg = generations.RunRegistry(tmp_path / "runs.jsonl")
        rec = reg.register("PFT-A1-FULL-RAW-001", self._fp())
        new_fp = ExperimentFingerprint(
            spec_gen="PFT-SPEC-GEN-002", data_gen="PFT-DATA-GEN-001",
            engine_gen="PFT-ENGINE-GEN-001", cost_gen="PFT-COST-GEN-001",
            exec_gen="PFT-EXEC-GEN-001", code_sha="c" * 40,
        )
        replacement = reg.supersede(rec.run_id, new_fp, reason="spec repaired")
        assert replacement.status == "COMPLETED"
        assert replacement.parent_run_id == rec.run_id
        assert reg.get(rec.run_id).status == "INVALIDATED"


# ---------------------------------------------------------------------------
# 7.8.6 decision-schema validation
# ---------------------------------------------------------------------------


class TestDecisionSchema:
    def _valid_decision(self):
        d = decisions.DecisionRecord(
            checkpoint_id="PFT-B0-PROGRAM-CONSTITUTION",
            program_id="PFT",
            branch="agent/deepers-strategy-foundry",
            base_sha="9f61288679eea56a298e08f718c314f2ca509bc5",
            commit_sha="225393631406200909cda8106f09edb2e456fee1",
        )
        return d

    def test_valid_decision_passes_validation(self):
        d = self._valid_decision()
        assert decisions.validate_decision_dict(d.to_dict()) == []

    def test_derived_status_pass(self):
        d = self._valid_decision()
        d.data_truth_pass = True
        d.math_conformance_pass = True
        d.causality_pass = True
        d.status = d.derive_status()
        assert d.status == "PASS"
        assert d.next_checkpoint_authorized is False
        assert d.human_review_required is True

    def test_derived_status_fail_on_gate(self):
        d = self._valid_decision()
        d.data_truth_pass = True
        d.math_conformance_pass = False
        d.causality_pass = True
        assert d.derive_status() == "FAIL"

    def test_derived_status_blocked(self):
        d = self._valid_decision()
        d.data_truth_pass = True
        d.math_conformance_pass = True
        d.causality_pass = True
        d.blockers = ["missing Brent reference data"]
        assert d.derive_status() == "BLOCKED"

    def test_missing_required_field_rejected(self):
        data = self._valid_decision().to_dict()
        del data["checkpoint_id"]
        assert "missing required field 'checkpoint_id'" in decisions.validate_decision_dict(data)

    def test_non_boolean_field_rejected(self):
        data = self._valid_decision().to_dict()
        data["economic_pnl_computed"] = "no"
        assert decisions.validate_decision_dict(data) != []

    def test_invalid_status_rejected(self):
        data = self._valid_decision().to_dict()
        data["status"] = "GOLD"
        assert decisions.validate_decision_dict(data) != []


# ---------------------------------------------------------------------------
# B0 PASS gate prerequisites: species + register schema
# ---------------------------------------------------------------------------


class TestProgramRegistry:
    def test_species_registered(self):
        reg = species_register_dict()
        assert schemas.validate_species_register(reg) == []
        assert set(SPECIES_REGISTER) == {"A0-GENESIS", "A1-DEEPERS", "Q0-TRANSMISSION", "X1-SYNTHESIS"}

    def test_a1_frozen_and_x1_not_authorized(self):
        assert SPECIES_REGISTER["A1-DEEPERS"]["status"] == "FROZEN_PRIMARY_RAW_SPEC"
        assert SPECIES_REGISTER["X1-SYNTHESIS"]["status"] == "NOT_AUTHORIZED"

    def test_formula_register_schema(self):
        reg = formula_register_dict()
        assert schemas.validate_formula_register(reg) == []
        ids = [f["id"] for f in reg["formulas"]]
        assert len(ids) == len(set(ids)) == 19

    def test_parameter_register_schema(self):
        reg = build_parameter_register()
        data = reg.to_register()
        assert schemas.validate_parameter_register(data) == []

    def test_parameter_register_json_roundtrip(self):
        data = build_parameter_register().to_register()
        # must serialize cleanly to JSON (values JSON-compatible)
        json.dumps(data)
