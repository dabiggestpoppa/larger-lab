"""Deterministic fixture loading (offline, no network, no paid resources).

All fixtures live in ``model-foundry/fixtures`` as plain JSON so that a reviewer
can read exactly what the substrate was exercised against. Nothing here contacts
a provider, an exchange, or a remote service.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .core import FrozenMap, PolicyBlocked, fingerprint
from .data import ContaminationGraph, ContaminationRelation, RightsDisposition, SourceRecord, SourceRegistry
from .enums import (
    ContaminationType,
    EvaluationTier,
    RightsBasis,
    SourceRole,
    TrustClass,
)
from .evaluation import BenchmarkItem, BenchmarkSpec, EvaluationProtocol, MetricSpec
from .providers import RawProviderObservation
from .refinery import RawItem

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def fixture_path(name: str) -> Path:
    path = FIXTURES_DIR / name
    if not path.exists():
        raise PolicyBlocked("FIXTURE_MISSING", f"fixture {name!r} not found under {FIXTURES_DIR}")
    return path


def load_json(name: str) -> Any:
    return json.loads(fixture_path(name).read_text(encoding="utf-8"))


def load_observations(name: str = "provider_offers.json") -> tuple[RawProviderObservation, ...]:
    payload = load_json(name)
    return tuple(
        RawProviderObservation(
            provider=entry["provider"],
            raw=entry["raw"],
            observed_at_epoch_s=entry["observed_at_epoch_s"],
            freshness_window_s=entry["freshness_window_s"],
        )
        for entry in payload["observations"]
    )


def load_sources(name: str = "sources.json") -> tuple[SourceRecord, ...]:
    payload = load_json(name)
    records = []
    for entry in payload["sources"]:
        rights = RightsDisposition(
            subject=entry["source_id"],
            basis=RightsBasis(entry["rights_basis"]),
            basis_ref=entry["rights_basis_ref"],
            basis_resolved=bool(entry["rights_basis_resolved"]),
            basis_scope=entry.get("rights_basis_scope", ""),
            decided_utc=entry["rights_decided_utc"],
        )
        records.append(
            SourceRecord(
                source_id=entry["source_id"],
                title=entry["title"],
                locator=entry["locator"],
                source_family=entry["source_family"],
                payload_class=entry["payload_class"],
                observed_utc=entry["observed_utc"],
                event_time_start=entry.get("event_time_start"),
                event_time_end=entry.get("event_time_end"),
                known_at_utc=entry.get("known_at_utc"),
                upstream_ancestry=entry["upstream_ancestry"],
                upstream_provenance_known=bool(entry["upstream_provenance_known"]),
                integrity_digest=entry["integrity_digest"],
                record_count=int(entry["record_count"]),
                trust_class=TrustClass(entry["trust_class"]),
                rights=rights,
                role=SourceRole(entry["role"]),
                secret_bearing=bool(entry.get("secret_bearing", False)),
                synthetic=bool(entry.get("synthetic", False)),
                synthetic_of=tuple(entry.get("synthetic_of", ())),
                mirror_of=entry.get("mirror_of"),
                lineage_key=entry.get("lineage_key"),
                contains_prohibited_payload_classes=tuple(
                    entry.get("contains_prohibited_payload_classes", ())
                ),
                doctrine_shape_tokens=tuple(entry.get("doctrine_shape_tokens", ())),
                notes=entry.get("notes", ""),
            )
        )
    return tuple(records)


def build_registry(name: str = "sources.json") -> SourceRegistry:
    registry = SourceRegistry()
    for record in load_sources(name):
        registry.register(record, actor="fixture.loader", reason="deterministic fixture load")
    return registry


def load_contamination(name: str = "contamination.json") -> ContaminationGraph:
    payload = load_json(name)
    relations = tuple(
        ContaminationRelation(
            left=entry["left"],
            right=entry["right"],
            contamination_type=ContaminationType(entry["contamination_type"]),
            evidence_ref=entry["evidence_ref"],
            detected_by=entry["detected_by"],
        )
        for entry in payload["relations"]
    )
    return ContaminationGraph(relations=relations)


def load_items(name: str = "corpus_items.json") -> list[RawItem]:
    payload = load_json(name)
    return [
        RawItem(
            item_id=entry["item_id"],
            source_id=entry["source_id"],
            text=entry["text"],
            event_time_utc=entry["event_time_utc"],
            known_at_utc=entry["known_at_utc"],
            payload_class=entry.get("payload_class", "text"),
            fields=FrozenMap(entry.get("fields", {})),
        )
        for entry in payload["items"]
    ]


def load_benchmark(name: str = "benchmarks.json") -> BenchmarkSpec:
    payload = load_json(name)["benchmark"]
    return BenchmarkSpec(
        benchmark_id=payload["benchmark_id"],
        version=payload["version"],
        task_class=payload["task_class"],
        items=tuple(
            BenchmarkItem(
                item_id=item["item_id"],
                task_class=item["task_class"],
                expected_answer=item["expected_answer"],
                difficulty=item["difficulty"],
                source_id=item.get("source_id"),
            )
            for item in payload["items"]
        ),
        tier=EvaluationTier(payload["tier"]),
        status=payload.get("status", "DRAFT"),
        exposure_count=int(payload.get("exposure_count", 0)),
    )


def load_protocol(name: str = "benchmarks.json") -> EvaluationProtocol:
    payload = load_json(name)["protocol"]
    return EvaluationProtocol(
        protocol_id=payload["protocol_id"],
        version=payload["version"],
        benchmark=load_benchmark(name),
        metrics=tuple(
            MetricSpec(
                name=m["name"],
                description=m["description"],
                direction=m["direction"],
                reported_weight=m.get("reported_weight"),
            )
            for m in payload["metrics"]
        ),
        min_items_for_power=int(payload["min_items_for_power"]),
        required_seeds=int(payload["required_seeds"]),
        baseline_reference=payload["baseline_reference"],
        tolerance=float(payload["tolerance"]),
        decision_rules=tuple(payload["decision_rules"]),
        tier=EvaluationTier(payload["tier"]),
        author=payload["author"],
        framework_lock=payload.get("framework_lock"),
    )


@dataclass(frozen=True)
class FixtureBundle:
    """Everything a cross-block scenario needs, already fingerprinted."""

    observations: tuple[RawProviderObservation, ...]
    sources: tuple[SourceRecord, ...]
    contamination: ContaminationGraph
    items: list[RawItem]
    benchmark: BenchmarkSpec
    protocol: EvaluationProtocol

    def fingerprint(self) -> str:
        return fingerprint(
            {
                "observations": [o.to_dict() for o in self.observations],
                "sources": [s.fingerprint for s in self.sources],
                "contamination": self.contamination.fingerprint,
                "items": [i.to_dict() for i in self.items],
                "benchmark": self.benchmark.fingerprint,
                "protocol": self.protocol.fingerprint,
            }
        )


def load_bundle() -> FixtureBundle:
    return FixtureBundle(
        observations=load_observations(),
        sources=load_sources(),
        contamination=load_contamination(),
        items=load_items(),
        benchmark=load_benchmark(),
        protocol=load_protocol(),
    )


__all__ = [
    "FIXTURES_DIR",
    "FixtureBundle",
    "build_registry",
    "fixture_path",
    "load_benchmark",
    "load_bundle",
    "load_contamination",
    "load_items",
    "load_json",
    "load_observations",
    "load_protocol",
    "load_sources",
]
