"""Lightweight validators for program artifact JSON files.

Hand-rolled (no external schema dependency) but strict: every artifact
schema is validated before it may be committed as a checkpoint artifact.
"""

from __future__ import annotations

import json
from pathlib import Path

from .identity import SPECIES_FULL_IDS, ExperimentID, GenerationID
from .parameters import PARAMETER_CLASSES


def validate_species_register(data: dict) -> list:
    errors = []
    if not isinstance(data, dict):
        return ["SPEC_REGISTER must be a JSON object"]
    species = data.get("species")
    if not isinstance(species, dict):
        return ["SPEC_REGISTER.species must be an object"]
    for sid, entry in species.items():
        if sid not in SPECIES_FULL_IDS:
            errors.append(f"unregistered species {sid!r}")
        if not isinstance(entry, dict):
            errors.append(f"species {sid!r} entry must be an object")
            continue
        if "status" not in entry:
            errors.append(f"species {sid!r} missing 'status'")
    return errors


def validate_experiment_registry(data: dict) -> list:
    errors = []
    if not isinstance(data, dict):
        return ["EXPERIMENT_REGISTRY must be a JSON object"]
    experiments = data.get("experiments", [])
    if not isinstance(experiments, list):
        return ["EXPERIMENT_REGISTRY.experiments must be a list"]
    seen = set()
    for exp in experiments:
        if not isinstance(exp, dict):
            errors.append("experiment entry must be an object")
            continue
        eid = exp.get("experiment_id")
        if eid is None:
            errors.append("experiment entry missing experiment_id")
            continue
        try:
            ExperimentID.parse(eid)
        except ValueError as exc:
            errors.append(f"invalid experiment_id {eid!r}: {exc}")
        if eid in seen:
            errors.append(f"duplicate experiment_id {eid!r}")
        seen.add(eid)
        for gen_field in ("spec_generation", "data_generation", "engine_generation",
                          "cost_generation", "exec_generation"):
            value = exp.get(gen_field)
            if value is None:
                errors.append(f"experiment {eid} missing {gen_field}")
                continue
            try:
                GenerationID.parse(value)
            except ValueError as exc:
                errors.append(f"experiment {eid} invalid {gen_field}: {exc}")
    return errors


def validate_parameter_register(data: dict) -> list:
    errors = []
    if not isinstance(data, dict):
        return ["PARAMETER_REGISTER must be a JSON object"]
    params = data.get("parameters")
    if not isinstance(params, list):
        return ["PARAMETER_REGISTER.parameters must be a list"]
    seen = set()
    for p in params:
        if not isinstance(p, dict):
            errors.append("parameter entry must be an object")
            continue
        pid = p.get("id")
        if pid is None:
            errors.append("parameter entry missing 'id'")
            continue
        if pid in seen:
            errors.append(f"duplicate parameter id {pid!r}")
        seen.add(pid)
        if p.get("parameter_class") not in PARAMETER_CLASSES:
            errors.append(f"parameter {pid} invalid class {p.get('parameter_class')!r}")
        for required in ("name", "value", "source_ref"):
            if required not in p:
                errors.append(f"parameter {pid} missing {required!r}")
    return errors


def validate_formula_register(data: dict) -> list:
    errors = []
    if not isinstance(data, dict):
        return ["FORMULA_REGISTER must be a JSON object"]
    formulas = data.get("formulas")
    if not isinstance(formulas, list):
        return ["FORMULA_REGISTER.formulas must be a list"]
    seen = set()
    for f in formulas:
        if not isinstance(f, dict):
            errors.append("formula entry must be an object")
            continue
        fid = f.get("id")
        if fid is None:
            errors.append("formula entry missing 'id'")
            continue
        if fid in seen:
            errors.append(f"duplicate formula id {fid!r}")
        seen.add(fid)
        # B1 seal: every formula must map to an implementation, a test target
        # and a fail-closed failure behavior.
        for required in ("name", "source_ref", "implementation_status",
                         "implementation_target", "test_target", "failure_behavior"):
            if required not in f:
                errors.append(f"formula {fid} missing {required!r}")
    return errors


def validate_authority_dict(data: dict) -> list:
    from .authority import AUTHORITY_KEYS

    errors = []
    if not isinstance(data, dict):
        return ["AUTHORITY must be a JSON object"]
    for k, v in data.items():
        if k == "extra":
            continue
        if k not in AUTHORITY_KEYS:
            errors.append(f"unknown authority key {k!r}")
        elif not isinstance(v, bool):
            errors.append(f"authority key {k!r} must be boolean")
    return errors


def validate_ledger_json(data: dict) -> list:
    errors = []
    if not isinstance(data, dict):
        return ["DATA_USAGE_LEDGER must be a JSON object"]
    if data.get("immutable") is not True:
        errors.append("DATA_USAGE_LEDGER.immutable must be true")
    entries = data.get("entries")
    if not isinstance(entries, list):
        return ["DATA_USAGE_LEDGER.entries must be a list"]
    for e in entries:
        if e.get("blocked") is True and e.get("authorized") is True:
            errors.append(f"ledger entry {e.get('entry_id')} cannot be both authorized and blocked")
    return errors


def load_json(path: Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_file(path: Path, validator) -> list:
    """Validate one artifact file. Returns list of violations."""
    if not Path(path).exists():
        return [f"artifact missing: {path}"]
    try:
        data = load_json(path)
    except Exception as exc:  # noqa: BLE001 - report any parse failure
        return [f"artifact {path} is not valid JSON: {exc}"]
    return validator(data)
