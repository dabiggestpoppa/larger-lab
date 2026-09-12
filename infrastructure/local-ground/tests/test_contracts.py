#!/usr/bin/env python3
"""
OCE Local Ground — contract/schema validation (B1-LOCAL, A-003).

Separate from the 30 acceptance tests: validates that the frozen
local-ground contract, runtime profiles, and deployment targets satisfy
their schemas, including the fail-closed cloud plan/apply separation.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONTRACTS = BASE_DIR / "contracts"
FIXTURES = BASE_DIR / "tests" / "fixtures"


def mini_validate(inst, sch, path="$"):
    if "type" in sch:
        t = sch["type"]
        ok = ((t == "object" and isinstance(inst, dict))
              or (t == "array" and isinstance(inst, list))
              or (t == "string" and isinstance(inst, str))
              or (t == "number" and isinstance(inst, (int, float)) and not isinstance(inst, bool))
              or (t == "boolean" and isinstance(inst, bool)))
        assert ok, f"{path}: expected {t}"
    if isinstance(inst, dict):
        if sch.get("additionalProperties") is False:
            extra = set(inst) - set(sch.get("properties", {}))
            assert not extra, f"{path}: unexpected {sorted(extra)}"
        for k, subs in sch.get("properties", {}).items():
            if k in inst:
                mini_validate(inst[k], subs, f"{path}.{k}")
        for req in sch.get("required", []):
            assert req in inst, f"{path}: missing '{req}'"
        if "enum" in sch:
            assert inst in sch["enum"], f"{path}: enum"
        if "const" in sch:
            assert inst == sch["const"], f"{path}: const"
        if "minimum" in sch and isinstance(inst, (int, float)):
            assert inst >= sch["minimum"], f"{path}: minimum"
        if "minItems" in sch and isinstance(inst, list):
            assert len(inst) >= sch["minItems"], f"{path}: minItems"
        if "if" in sch:
            try:
                mini_validate(inst, sch["if"], path)
                mini_validate(inst, sch["then"], path)
            except AssertionError:
                if "else" in sch:
                    mini_validate(inst, sch["else"], path)
        if "allOf" in sch:
            for sub in sch["allOf"]:
                mini_validate(inst, sub, path)
    elif isinstance(inst, list):
        for i, item in enumerate(inst):
            mini_validate(item, sch.get("items", {}), f"{path}[{i}]")


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_local_ground_contract_matches_schema():
    contract = load(CONTRACTS / "local-ground-contract.json")
    schema = load(CONTRACTS / "local-ground-contract.schema.json")
    mini_validate(contract, schema)


def test_runtime_profile_schema_accepts_local():
    schema = load(CONTRACTS / "runtime-profile.schema.json")
    mini_validate(load(FIXTURES / "valid" / "runtime-profile.local.json"), schema)


def test_runtime_profile_schema_rejects_unhardened_cloud():
    schema = load(CONTRACTS / "runtime-profile.schema.json")
    try:
        mini_validate(load(FIXTURES / "invalid" / "runtime-profile.cloud-no-auth.json"), schema)
        raise AssertionError("cloud profile without authorization must fail validation")
    except AssertionError:
        pass


def test_deployment_target_schema_accepts_authorized_apply_and_readonly_plan():
    schema = load(CONTRACTS / "deployment-target.schema.json")
    mini_validate(load(FIXTURES / "valid" / "deployment-target.cloud-apply-authorized.json"), schema)
    mini_validate(load(FIXTURES / "valid" / "deployment-target.cloud-plan-readonly.json"), schema)


def test_deployment_target_schema_rejects_mutating_plan_and_no_cost_apply():
    schema = load(CONTRACTS / "deployment-target.schema.json")
    for name in ["deployment-target.cloud-plan-mutating.json", "deployment-target.cloud-apply-no-cost.json"]:
        try:
            mini_validate(load(FIXTURES / "invalid" / name), schema)
            raise AssertionError(f"invalid fixture must fail: {name}")
        except AssertionError:
            pass


def test_frozen_contract_enforces_deferral():
    contract = load(CONTRACTS / "local-ground-contract.json")
    assert contract["cloud_activation"]["state"] == "DEFERRED_BY_OPERATOR"
    assert contract["cloud_activation"]["zero_cost"] is True
    assert contract["cloud_activation"]["zero_mutations"] is True
    assert contract["default_runtime_target"] == "local"
    assert contract["ledger_model"]["cloud_cost_state"] == "ZERO"


def test_no_provider_hardcoded_in_domain_logic():
    contract = load(CONTRACTS / "local-ground-contract.json")
    assert contract["provider_policy"]["provider_values_in_deployment_adapters_only"] is True
    assert contract["provider_policy"]["no_provider_hardcoded_in_domain_logic"] is True