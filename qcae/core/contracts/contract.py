"""CapabilityContract — QCAE's normalized, versioned statement of need.

Canon Book I 1.1. A contract is a versioned domain object, not a prompt. It
separates what Quant Lab needs from the implementation form the requester
imagined, and states evidence requirements up front because risk is part of
the need (1.1.10).

Field set follows canon 1.1.4 ("should support at minimum"); fields the
request has not justified remain explicitly unspecified rather than guessed
(1.1.4: "Missing required information must be explicit rather than silently
guessed").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum_tuple
from qcae.core.validation import (
    require_identifier,
    require_no_duplicates,
    require_non_empty_str,
    require_str_list,
)
from qcae.core.vocabulary import AcquisitionForm, EvidenceClass


@dataclass(frozen=True)
class CapabilityContract(SerializableRecord):
    SCHEMA_VERSION = 1

    # -- identity ---------------------------------------------------------
    capability_id: str
    contract_version: int
    request_id: str
    title: str
    problem_statement: str
    intent: str

    # -- functional layers (canon 1.1.3) ----------------------------------
    required_behaviors: Tuple[str, ...]
    optional_behaviors: Tuple[str, ...] = ()
    explicit_non_goals: Tuple[str, ...] = ()
    inputs: Tuple[str, ...] = ()
    outputs: Tuple[str, ...] = ()

    # -- acceptance + evidence (canon 1.1.9, 1.1.10) ----------------------
    acceptance_tests: Tuple[str, ...] = ()
    required_evidence_classes: Tuple[EvidenceClass, ...] = ()

    # -- requirements separation (canon 1.1.7) -----------------------------
    forbidden_conditions: Tuple[str, ...] = ()
    preferred_acquisition_forms: Tuple[AcquisitionForm, ...] = ()
    forbidden_acquisition_forms: Tuple[AcquisitionForm, ...] = ()

    # -- non-functional + constraints (canon 1.1.3 C/D) --------------------
    performance_requirements: Tuple[str, ...] = ()
    precision_requirements: Tuple[str, ...] = ()
    latency_requirements: Tuple[str, ...] = ()
    throughput_requirements: Tuple[str, ...] = ()
    runtime_constraints: Tuple[str, ...] = ()
    platform_constraints: Tuple[str, ...] = ()
    language_constraints: Tuple[str, ...] = ()
    integration_constraints: Tuple[str, ...] = ()
    license_constraints: Tuple[str, ...] = ()
    cost_constraints: Tuple[str, ...] = ()
    maintenance_constraints: Tuple[str, ...] = ()

    # -- security/data posture (canon 1.1.4) --------------------------------
    security_class: str = "unspecified"
    data_classification: str = "unspecified"
    network_policy: str = "unspecified"
    secret_policy: str = "unspecified"

    # -- quant flags (canon 1.1.4; Book III block 7 consumes these) ---------
    quant_domain: bool = False
    cerebus_relevance: bool = False

    # -- provenance ---------------------------------------------------------
    owner: str = ""
    created_at: str = ""
    supersedes_contract: str = ""

    _NESTED_RECORDS = {}
    _COERCIONS = {
        "required_evidence_classes": lambda v: coerce_enum_tuple(v, EvidenceClass),
        "preferred_acquisition_forms": lambda v: coerce_enum_tuple(v, AcquisitionForm),
        "forbidden_acquisition_forms": lambda v: coerce_enum_tuple(v, AcquisitionForm),
    }

    def validate(self) -> None:
        # Identity (canon 1.1.5: capability identity is behavior, not product).
        require_identifier(self.capability_id, "capability_id")
        require_identifier(self.request_id, "request_id")
        require_non_empty_str(self.title, "title")
        require_non_empty_str(self.problem_statement, "problem_statement")
        require_non_empty_str(self.intent, "intent")
        if not isinstance(self.contract_version, int) or isinstance(
            self.contract_version, bool
        ) or self.contract_version < 1:
            raise QcaeValidationError(
                "contract_version must be a positive integer, "
                f"got {self.contract_version!r}"
            )
        if self.supersedes_contract:
            require_identifier(self.supersedes_contract, "supersedes_contract")

        # Behavior must be stated (canon 1.1.2: normalized need, not product).
        if not self.required_behaviors:
            raise QcaeValidationError(
                "required_behaviors must not be empty: a contract without "
                "mandatory behavior cannot be tested"
            )
        require_str_list(self.required_behaviors, "required_behaviors")
        require_str_list(self.optional_behaviors, "optional_behaviors")
        require_str_list(self.explicit_non_goals, "explicit_non_goals")
        require_str_list(self.inputs, "inputs")
        require_str_list(self.outputs, "outputs")
        require_str_list(self.forbidden_conditions, "forbidden_conditions")

        # Observable success before promotion (canon 1.1.9).
        if not self.acceptance_tests:
            raise QcaeValidationError(
                "acceptance_tests must not be empty: observable acceptance "
                "conditions must exist before candidate promotion (canon 1.1.9)"
            )
        require_str_list(self.acceptance_tests, "acceptance_tests")

        # Evidence requirements belong to the contract (canon 1.1.10).
        if not self.required_evidence_classes:
            raise QcaeValidationError(
                "required_evidence_classes must not be empty: risk is part of "
                "the need (canon 1.1.10)"
            )

        # Required / preferred / forbidden separation (canon 1.1.7).
        forbidden_set = set(self.forbidden_conditions)
        overlap = sorted(set(self.required_behaviors) & forbidden_set)
        if overlap:
            raise QcaeValidationError(
                f"behaviors cannot be both required and forbidden: {overlap}"
            )
        optional_overlap = sorted(set(self.required_behaviors) & set(self.optional_behaviors))
        if optional_overlap:
            raise QcaeValidationError(
                f"behaviors cannot be both required and optional: {optional_overlap}"
            )

        # Every declared string-tuple field participates in canonical contract
        # semantics and is shape-validated (P0-A001-04 operator repair).
        for field_name in (
            "performance_requirements",
            "precision_requirements",
            "latency_requirements",
            "throughput_requirements",
            "runtime_constraints",
            "platform_constraints",
            "language_constraints",
            "integration_constraints",
            "license_constraints",
            "cost_constraints",
            "maintenance_constraints",
        ):
            require_str_list(getattr(self, field_name), field_name)

        require_no_duplicates(self.required_behaviors, "required_behaviors")
        require_no_duplicates(self.acceptance_tests, "acceptance_tests")
        require_no_duplicates(self.optional_behaviors, "optional_behaviors")
        require_no_duplicates(self.explicit_non_goals, "explicit_non_goals")
        require_no_duplicates(self.forbidden_conditions, "forbidden_conditions")

        # Evidence classes must be concrete members.
        for evidence in self.required_evidence_classes:
            if not isinstance(evidence, EvidenceClass):
                raise QcaeValidationError(
                    f"required_evidence_classes entries must be EvidenceClass "
                    f"members, got {evidence!r}"
                )
        for forms in (self.preferred_acquisition_forms, self.forbidden_acquisition_forms):
            for form in forms:
                if not isinstance(form, AcquisitionForm):
                    raise QcaeValidationError(
                        f"acquisition form entries must be AcquisitionForm "
                        f"members, got {form!r}"
                    )
        conflicts = sorted(
            set(self.preferred_acquisition_forms) & set(self.forbidden_acquisition_forms)
        )
        if conflicts:
            raise QcaeValidationError(
                f"acquisition forms cannot be both preferred and forbidden: "
                f"{[c.value for c in conflicts]}"
            )

        # Provenance (canon 1.3.16: provenance-linked artifacts).
        require_non_empty_str(self.owner, "owner")
        require_non_empty_str(self.created_at, "created_at")
