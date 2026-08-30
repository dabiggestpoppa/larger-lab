"""Schema validation for OCE Control Plane contracts.

Lightweight JSON Schema validator matching the pattern from B1's test_contracts.py.
No external dependencies — validates type, required, enum, const, pattern,
additionalProperties, minimum, minItems, and if/then/else.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any


def mini_validate(inst: Any, sch: dict, path: str = "$") -> list[str]:
    """Validate instance against schema. Returns list of error strings (empty if valid)."""
    errors: list[str] = []

    if "type" in sch:
        t = sch["type"]
        ok = ((t == "object" and isinstance(inst, dict))
              or (t == "array" and isinstance(inst, list))
              or (t == "string" and isinstance(inst, str))
              or (t == "number" and isinstance(inst, (int, float)) and not isinstance(inst, bool))
              or (t == "boolean" and isinstance(inst, bool))
              or (t == "integer" and isinstance(inst, int) and not isinstance(inst, bool)))
        if not ok:
            return [f"{path}: expected {t}, got {type(inst).__name__}"]

    if isinstance(inst, dict):
        if sch.get("additionalProperties") is False:
            extra = set(inst) - set(sch.get("properties", {}))
            if extra:
                errors.append(f"{path}: unexpected properties {sorted(extra)}")

        for req in sch.get("required", []):
            if req not in inst:
                errors.append(f"{path}: missing required '{req}'")

        if "enum" in sch and inst not in sch["enum"]:
            errors.append(f"{path}: value '{inst}' not in enum {sch['enum']}")

        if "const" in sch and inst != sch["const"]:
            errors.append(f"{path}: expected const {sch['const']!r}, got {inst!r}")

        for k, subs in sch.get("properties", {}).items():
            if k in inst:
                errors.extend(mini_validate(inst[k], subs, f"{path}.{k}"))

        if "if" in sch:
            if_errors = mini_validate(inst, sch["if"], path)
            if not if_errors:
                errors.extend(mini_validate(inst, sch.get("then", {}), path))
            elif "else" in sch:
                errors.extend(mini_validate(inst, sch["else"], path))

        if "allOf" in sch:
            for sub in sch["allOf"]:
                errors.extend(mini_validate(inst, sub, path))

    elif isinstance(inst, list):
        if "minItems" in sch and len(inst) < sch["minItems"]:
            errors.append(f"{path}: minItems {sch['minItems']}, got {len(inst)}")
        if "items" in sch:
            for i, item in enumerate(inst):
                errors.extend(mini_validate(item, sch["items"], f"{path}[{i}]"))

    if isinstance(inst, str):
        if "pattern" in sch and not re.match(sch["pattern"], inst):
            errors.append(f"{path}: string '{inst}' does not match pattern {sch['pattern']}")
        if "minLength" in sch and len(inst) < sch["minLength"]:
            errors.append(f"{path}: minLength {sch['minLength']}, got {len(inst)}")
        if "enum" in sch and inst not in sch["enum"]:
            errors.append(f"{path}: value '{inst}' not in enum {sch['enum']}")
        if "const" in sch and inst != sch["const"]:
            errors.append(f"{path}: expected const {sch['const']!r}, got {inst!r}")

    if isinstance(inst, (int, float)) and not isinstance(inst, bool):
        if "minimum" in sch and inst < sch["minimum"]:
            errors.append(f"{path}: minimum {sch['minimum']}, got {inst}")
        if "maximum" in sch and inst > sch["maximum"]:
            errors.append(f"{path}: maximum {sch['maximum']}, got {inst}")

    return errors


def validate(instance: Any, schema: dict) -> tuple[bool, list[str]]:
    """Validate and return (ok, errors)."""
    errors = mini_validate(instance, schema)
    return (len(errors) == 0, errors)


def load_schema(schema_path: str | Path) -> dict:
    """Load a JSON schema from file."""
    return json.loads(Path(schema_path).read_text(encoding="utf-8"))


def validate_file(instance_path: str | Path, schema_path: str | Path) -> tuple[bool, list[str]]:
    """Validate a JSON file against a schema file."""
    instance = json.loads(Path(instance_path).read_text(encoding="utf-8"))
    schema = load_schema(schema_path)
    return validate(instance, schema)
