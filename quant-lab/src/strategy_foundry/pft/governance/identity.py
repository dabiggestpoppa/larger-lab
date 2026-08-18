"""Experiment identity and reproducibility fingerprints.

An experiment identity binds spec, data, engine, cost, execution,
code commit and seed. Same fingerprint => reproducible rerun.
Changed fingerprint => new experiment generation.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Optional

PROGRAM_ID = "PFT"
PROGRAM_VERSION = "1.0"

# Short species tokens used inside experiment ids, e.g. PFT-A1-K1-RAW-001.
SPECIES_IDS = {"A0", "A1", "Q0", "X1"}

# Full registered species names (as used by SPEC_REGISTER.json).
SPECIES_FULL_IDS = {
    "A0-GENESIS",
    "A1-DEEPERS",
    "Q0-TRANSMISSION",
    "X1-SYNTHESIS",
}

SPECIES_SHORT_TO_FULL = {
    "A0": "A0-GENESIS",
    "A1": "A1-DEEPERS",
    "Q0": "Q0-TRANSMISSION",
    "X1": "X1-SYNTHESIS",
}

# Evidence classes per PFT constitution.
EXPERIMENT_CLASSES = {
    "RAW",      # literal submitted strategy/model
    "TWIN",     # preregistered mathematically consistent alternative
    "ABLATION", # component removed or isolated
    "FIXTURE",  # deterministic mathematical reference fixture
}

_EXPERIMENT_ID_RE = re.compile(
    r"^(?P<program>[A-Z0-9]+)-(?P<species>A0|A1|Q0|X1)-"
    r"(?P<scope>[A-Z0-9]+)-(?P<class>[A-Z]+)-(?P<seq>[0-9]{3})$"
)


class InvalidExperimentID(ValueError):
    pass


@dataclass(frozen=True)
class ExperimentID:
    """Immutable experiment identifier, e.g. PFT-A1-K1-RAW-001."""

    species: str
    scope: str
    experiment_class: str
    sequence: int
    program: str = PROGRAM_ID

    def __post_init__(self) -> None:
        if self.program != PROGRAM_ID:
            raise InvalidExperimentID(f"program must be {PROGRAM_ID!r}, got {self.program!r}")
        if self.species not in SPECIES_IDS:
            raise InvalidExperimentID(
                f"unknown species {self.species!r}; allowed: {sorted(SPECIES_IDS)}"
            )
        if not re.fullmatch(r"[A-Z0-9]+", self.scope):
            raise InvalidExperimentID(f"scope must be uppercase alnum, got {self.scope!r}")
        if self.experiment_class not in EXPERIMENT_CLASSES:
            raise InvalidExperimentID(
                f"unknown class {self.experiment_class!r}; allowed: {sorted(EXPERIMENT_CLASSES)}"
            )
        if not 0 <= self.sequence <= 999:
            raise InvalidExperimentID(f"sequence must be 0..999, got {self.sequence}")

    @property
    def full_species_name(self) -> str:
        return SPECIES_SHORT_TO_FULL[self.species]

    def __str__(self) -> str:
        return f"{self.program}-{self.species}-{self.scope}-{self.experiment_class}-{self.sequence:03d}"

    @classmethod
    def parse(cls, value: str) -> "ExperimentID":
        m = _EXPERIMENT_ID_RE.fullmatch(value)
        if not m:
            raise InvalidExperimentID(
                f"invalid experiment id {value!r}; expected "
                f"{PROGRAM_ID}-<SPECIES>-<SCOPE>-<CLASS>-<NNN>"
            )
        return cls(
            program=m.group("program"),
            species=m.group("species"),
            scope=m.group("scope"),
            experiment_class=m.group("class"),
            sequence=int(m.group("seq")),
        )


# Generation kinds per program constitution 7.2.
GEN_KINDS = ("SPEC", "DATA", "ENGINE", "COST", "EXEC")

_GEN_ID_RE = re.compile(
    r"^(?P<program>[A-Z0-9]+)-(?P<kind>[A-Z]+)-GEN-(?P<seq>[0-9]{3})$"
)


class InvalidGenerationID(ValueError):
    pass


@dataclass(frozen=True)
class GenerationID:
    """e.g. PFT-ENGINE-GEN-001."""

    kind: str
    sequence: int
    program: str = PROGRAM_ID

    def __post_init__(self) -> None:
        if self.program != PROGRAM_ID:
            raise InvalidGenerationID(f"program must be {PROGRAM_ID!r}")
        if self.kind not in GEN_KINDS:
            raise InvalidGenerationID(f"kind must be one of {GEN_KINDS}, got {self.kind!r}")
        if not 0 <= self.sequence <= 9999:
            raise InvalidGenerationID(f"sequence out of range: {self.sequence}")

    def __str__(self) -> str:
        return f"{self.program}-{self.kind}-GEN-{self.sequence:03d}"

    def increment(self) -> "GenerationID":
        return GenerationID(kind=self.kind, sequence=self.sequence + 1)

    @classmethod
    def parse(cls, value: str) -> "GenerationID":
        m = _GEN_ID_RE.fullmatch(value)
        if not m:
            raise InvalidGenerationID(
                f"invalid generation id {value!r}; expected {PROGRAM_ID}-<KIND>-GEN-<NNN>"
            )
        return cls(program=m.group("program"), kind=m.group("kind"), sequence=int(m.group("seq")))


@dataclass(frozen=True)
class ExperimentFingerprint:
    """Reproducibility fingerprint over all experiment generations."""

    spec_gen: str
    data_gen: str
    engine_gen: str
    cost_gen: str
    exec_gen: str
    code_sha: str
    seed: Optional[int] = None
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("spec_gen", "data_gen", "engine_gen", "cost_gen", "exec_gen"):
            GenerationID.parse(getattr(self, name))  # raises if malformed
        if self.seed is not None and not isinstance(self.seed, int):
            raise TypeError("seed must be an int or None")

    def _canonical_json(self) -> str:
        payload = {
            "spec_gen": self.spec_gen,
            "data_gen": self.data_gen,
            "engine_gen": self.engine_gen,
            "cost_gen": self.cost_gen,
            "exec_gen": self.exec_gen,
            "code_sha": self.code_sha,
            "seed": self.seed,
            "extra": dict(sorted(self.extra.items())),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def fingerprint_hex(self) -> str:
        return hashlib.sha256(self._canonical_json().encode("utf-8")).hexdigest()

    def assert_reproducible(self, other: "ExperimentFingerprint") -> None:
        if self.fingerprint_hex() != other.fingerprint_hex():
            raise FingerprintMismatchError(
                f"fingerprint mismatch: {self.fingerprint_hex()[:12]} != "
                f"{other.fingerprint_hex()[:12]}"
            )


class FingerprintMismatchError(RuntimeError):
    pass
