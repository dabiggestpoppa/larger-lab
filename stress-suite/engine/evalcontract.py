"""PhaseEvaluationContract (G1 §8; CON-03 / AMB-05) — HARDENED (G1R-02).

A versioned contract capturing A-010 evidence-channel thresholds, hysteresis,
and admissible phase transitions, with a freeze flag.

CRITICAL INVARIANTS (G1R-02):
  1. Once frozen, the COMPLETE semantic evaluation snapshot is immutable —
     direct nested mutation (channel_rules["x"]["threshold"]=...) FAILS (raises)
     rather than silently mutating.
  2. next_version() deep-copies every nested structure: no shared mutable
     aliases between a version and its predecessor/descendant.
  3. A frozen predecessor's fingerprint is byte-stable even after a descendant
     version is mutated.
  4. Each version carries its own identity + version lineage (supersedes).

Implementation: while UNFROZEN the contract holds plain mutable dicts so editors
behave normally; freeze() swaps them for immutable MappingProxyType/tuple views
(the mutation-attack vector), caches a plain snapshot, and fixes the fingerprint.
visibility_policy (PUBLIC / ROLE_RESTRICTED / SEALED_TEST_PARAMETER) is preserved
so CON-03 stays measurable.
"""
from __future__ import annotations

import copy
from dataclasses import asdict  # noqa: F401 (kept for parity)
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import EVALUATION_CONTRACT_VERSION, EvidenceChannel, deterministic_hex

VISIBILITY_POLICIES = ("PUBLIC", "ROLE_RESTRICTED", "SEALED_TEST_PARAMETER")


class FreezeViolation(ValueError):
    pass


class FrozenContractError(ValueError):
    pass


class PhaseEvaluationContract:
    def __init__(
        self,
        contract_id: str,
        schema_version: str = "1.0.0",
        version_tag: str = "V1",
        channel_rules: Optional[Dict[str, Dict[str, str]]] = None,
        hysteresis_rules: Optional[Dict[str, str]] = None,
        admissible_phase_transitions: Optional[Sequence[Tuple[str, str]]] = None,
        created_at_seq: int = 0,
        authority_basis: str = "",
        freeze_status: str = "UNFROZEN",
        supersedes: Optional[str] = None,
    ):
        self.contract_id = contract_id
        self.schema_version = schema_version
        self.version_tag = version_tag
        self._channel_rules = _plain_dict(channel_rules or {})
        self._hysteresis_rules = _plain_dict(hysteresis_rules or {})
        self._admissible_phase_transitions = [tuple(p) for p in (admissible_phase_transitions or [])]
        self.created_at_seq = created_at_seq
        self.authority_basis = authority_basis
        self.freeze_status = freeze_status
        self.supersedes = supersedes
        self._snapshot_plain: Optional[dict] = None
        self._fingerprint_value: Optional[str] = None
        if freeze_status == "FROZEN":
            self.freeze()

    # ------------------------------------------------------------------ #
    # read accessors — live/frozen appropriate
    # ------------------------------------------------------------------ #
    @property
    def channel_rules(self):
        # frozen -> immutable proxy (mutation raises); unfrozen -> live mutable dict
        return self._channel_rules

    @property
    def hysteresis_rules(self):
        return self._hysteresis_rules

    @property
    def admissible_phase_transitions(self):
        return self._admissible_phase_transitions

    # ------------------------------------------------------------------ #
    @classmethod
    def make(cls, seq, version_tag="V1", visibility_policy="PUBLIC", channels=None,
             channel_rules=None, hysteresis_rules=None, admissible_phase_transitions=None,
             authority_basis="OPP", created_at_seq=None):
        if channel_rules is None:
            channel_rules = {}
            for ch in (channels or tuple(c.value for c in EvidenceChannel)):
                channel_rules[ch] = {
                    "threshold": "MEDIUM",
                    "visibility_policy": visibility_policy,
                    "note": "",
                }
        return cls(
            contract_id=deterministic_hex("eval_contract", seq, version_tag),
            version_tag=version_tag,
            channel_rules=channel_rules,
            hysteresis_rules=dict(hysteresis_rules or {}),
            admissible_phase_transitions=list(admissible_phase_transitions or []),
            created_at_seq=created_at_seq or seq,
            authority_basis=authority_basis,
        )

    # ------------------------------------------------------------------ #
    # freeze
    # ------------------------------------------------------------------ #
    def freeze(self) -> None:
        self._snapshot_plain = _plain_normalize(dict(self._channel_rules))
        self._channel_rules = _deep_freeze_dict(self._channel_rules)
        self._hysteresis_rules = MappingProxyType(dict(self._hysteresis_rules))
        self._admissible_phase_transitions = tuple(tuple(p) for p in self._admissible_phase_transitions)
        self._fingerprint_value = deterministic_hex("snapshot", self._canonical())
        self.freeze_status = "FROZEN"

    def is_frozen(self) -> bool:
        return self.freeze_status == "FROZEN"

    def _require_mutable_store(self):
        return not self.is_frozen()

    # ------------------------------------------------------------------ #
    # version lineage
    # ------------------------------------------------------------------ #
    def next_version(self, seq: int) -> "PhaseEvaluationContract":
        """A NEW future contract, deep-copied from the CURRENT semantic values
        (plain normalized, so no frozen aliases leak). Fresh identity + lineage."""
        return PhaseEvaluationContract(
            contract_id=deterministic_hex("eval_contract", seq, f"{self.version_tag}-next"),
            version_tag=f"{self.version_tag}-n{seq}",
            channel_rules=_plain_normalize(self._channel_rules),
            hysteresis_rules=_plain_normalize(self._hysteresis_rules),
            admissible_phase_transitions=[tuple(p) for p in self._admissible_phase_transitions],
            authority_basis=self.authority_basis,
            freeze_status="UNFROZEN",
            supersedes=self.contract_id,
        )

    def mutate(self, changes: Dict[str, Any]) -> "PhaseEvaluationContract":
        if self.is_frozen():
            raise FreezeViolation(
                "frozen evaluation contract may not change mid-window; "
                "open a separate future contract instead"
            )
        next_ = copy.deepcopy(_plain_normalize(self._channel_rules))
        copy_obj = PhaseEvaluationContract(
            contract_id=self.contract_id, schema_version=self.schema_version,
            version_tag=self.version_tag,
            channel_rules=next_,
            hysteresis_rules=_plain_normalize(self._hysteresis_rules),
            admissible_phase_transitions=[tuple(p) for p in self._admissible_phase_transitions],
            created_at_seq=self.created_at_seq, authority_basis=self.authority_basis,
            freeze_status=self.freeze_status, supersedes=self.supersedes,
        )
        for key, val in changes.items():
            if key == "channel_rules":
                copy_obj._channel_rules = _plain_dict(val)
            elif key == "hysteresis_rules":
                copy_obj._hysteresis_rules = _plain_dict(val)
            elif key == "admissible_phase_transitions":
                copy_obj._admissible_phase_transitions = [tuple(p) for p in val]
            elif hasattr(copy_obj, key):
                setattr(copy_obj, key, val)
        return copy_obj

    # ------------------------------------------------------------------ #
    def _canonical(self) -> str:
        return deterministic_hex(
            "eval", self.contract_id, self.version_tag, self.created_at_seq,
            self.authority_basis,
            _plain_normalize(self._channel_rules),
            _plain_normalize(self._hysteresis_rules),
            [tuple(p) for p in self._admissible_phase_transitions],
        )

    def fingerprint(self) -> str:
        if self._fingerprint_value is not None:
            return self._fingerprint_value
        return deterministic_hex("eval_fp", self._canonical())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "version_tag": self.version_tag,
            "channel_rules": _plain_normalize(self._channel_rules),
            "hysteresis_rules": _plain_normalize(self._hysteresis_rules),
            "admissible_phase_transitions": [tuple(p) for p in self._admissible_phase_transitions],
            "created_at_seq": self.created_at_seq,
            "authority_basis": self.authority_basis,
            "freeze_status": self.freeze_status,
            "supersedes": self.supersedes,
        }


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

_TRUE_DICT = (dict, MappingProxyType, Mapping)


def _plain_dict(value):
    """Normalize any mapping (incl MappingProxyType) to a plain *mutable* dict of
    plain values — safe to deep-copy / pickle."""
    return _plain_normalize(value)


def _plain_normalize(value):
    if isinstance(value, Mapping):
        return {k: _plain_normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_normalize(v) for v in value]
    return value


def _deep_freeze_dict(d):
    """Immutable proxy of a nested dict: outer + inner MappingProxy so any write
    at any depth raises TypeError."""
    frozen = {}
    for k, v in d.items():
        frozen[k] = MappingProxyType(dict(v)) if isinstance(v, dict) else v
    return MappingProxyType(frozen)