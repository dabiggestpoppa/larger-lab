"""Schema round-trip — serialized objects validate against their JSON Schemas.

jsonschema is an optional dependency here; if unavailable the schema tests
truthfully skip (mirrors the repo's guarded-test convention) while the pure
engine tests remain dependency-free.
"""
import json
from dataclasses import asdict
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

from engine.evidence import EvidenceRecord
from engine.lifecycle import KnowledgeRecord, LifecycleEdgeTable
from engine.independence import IndependenceRecord
from engine.negative import NegativeKnowledgeRecord
from engine.unresolved import UnresolvedPatternRecord
from engine.epoch import EpochManifest
from engine.evalcontract import PhaseEvaluationContract
from engine.fixtures import StressScenarioSpec
from engine.base import Provenance


def _load(schemas_dir: Path, name: str):
    return json.loads((schemas_dir / name).read_text(encoding="utf-8"))


def test_evidence_roundtrip(schemas_dir):
    ev = EvidenceRecord.make(1, "claim", kind="OBSERVATION",
                             provenance=Provenance(source_kind="OBSERVATION", source_label="s"))
    jsonschema.validate(asdict(ev), _load(schemas_dir, "evidence-record.schema.json"))


def test_knowledge_roundtrip(schemas_dir):
    rec = KnowledgeRecord(record_id="k1", claim="c",
                          provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                          creation_source="t", initial_state="OBSERVED")
    jsonschema.validate(rec.to_dict(), _load(schemas_dir, "knowledge-record.schema.json"))


def test_independence_roundtrip(schemas_dir):
    rec = IndependenceRecord.make(seq=7, raw_reviewers=10, distinct_source_lineages=1,
                                  distinct_model_families=1, distinct_retrieval_bundles=1,
                                  overlaps={"source_overlap": "HIGH", "model_family_overlap": "HIGH",
                                            "retrieval_overlap": "HIGH", "allocator_overlap": "HIGH"})
    jsonschema.validate(asdict(rec), _load(schemas_dir, "independence-record.schema.json"))


def test_negative_knowledge_roundtrip(schemas_dir):
    nk = NegativeKnowledgeRecord.make(8, "claim", "scope", "reason", reopen_conditions=["sensor"])
    jsonschema.validate(asdict(nk), _load(schemas_dir, "negative-knowledge-record.schema.json"))


def test_unresolved_roundtrip(schemas_dir):
    u = UnresolvedPatternRecord.make(9, "observation")
    jsonschema.validate(asdict(u), _load(schemas_dir, "unresolved-record.schema.json"))


def test_epoch_roundtrip(schemas_dir):
    e = EpochManifest.make(10, epoch_id="E17")
    jsonschema.validate(e.to_dict(), _load(schemas_dir, "epoch-manifest.schema.json"))


def test_eval_contract_roundtrip(schemas_dir):
    c = PhaseEvaluationContract.make(11, version_tag="V1")
    jsonschema.validate(asdict(c), _load(schemas_dir, "phase-evaluation-contract.schema.json"))


def test_scenario_spec_roundtrip(schemas_dir):
    s = StressScenarioSpec(scenario_id="x", scenario_version="1.0.0")
    jsonschema.validate(StressScenarioSpec(**s.to_dict()).to_dict(),
                        _load(schemas_dir, "scenario-spec.schema.json"))