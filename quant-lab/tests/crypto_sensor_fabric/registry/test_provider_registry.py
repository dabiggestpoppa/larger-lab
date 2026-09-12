"""Provider-registry tests (B1-T30 .. B1-T33) and free-only registry
integration (B1-T20 .. T24 at the config level)."""

from __future__ import annotations

import pytest
import yaml
from crypto_sensor_fabric._paths import CONFIG_DIR
from crypto_sensor_fabric.contracts.access import FreeOnlyPolicy
from crypto_sensor_fabric.contracts.enums import AccessClass, EvidenceClass
from crypto_sensor_fabric.registry.provider_registry import (
    CAPABILITY_KEYS,
    PROVIDER_IDS,
    ProviderEntry,
    ProviderRegistry,
    eligible_required_providers,
    is_required_runtime_allowed,
    load_provider_registry,
    validate_required_runtime,
)
from crypto_sensor_fabric.registry.sensor_priority import (
    CRITICAL_SENSOR_STATES,
    critical_states_with_redundancy_intent,
    load_sensor_priority,
)
from pydantic import ValidationError

DEFAULT_REGISTRY = load_provider_registry()
DEFAULT_PRIORITY = load_sensor_priority()


# ---------------------------------------------------------------------------
# B1-T30 — every provider has an evidence class
# ---------------------------------------------------------------------------


def test_t30_every_provider_has_evidence_class():
    assert set(DEFAULT_REGISTRY.providers) == set(PROVIDER_IDS)
    for provider, entry in DEFAULT_REGISTRY.providers.items():
        assert isinstance(entry.evidence_class, EvidenceClass), provider


def test_t30_missing_evidence_class_fails():
    with pytest.raises(ValidationError):
        ProviderEntry.model_validate(
            {"status": "CANDIDATE", "access": {"access_class": "UNVERIFIED"}}
        )


def test_t30_community_archive_evidence_distinct():
    assert (
        DEFAULT_REGISTRY.providers["BITFINEX_COMMUNITY_ARCHIVE"].evidence_class
        is EvidenceClass.COMMUNITY_ARCHIVE
    )
    assert (
        DEFAULT_REGISTRY.providers["COINALYZE"].evidence_class
        is EvidenceClass.THIRD_PARTY_AGGREGATOR
    )
    # A community archive is never first-party exchange truth (F10)
    assert (
        DEFAULT_REGISTRY.providers["BITFINEX_COMMUNITY_ARCHIVE"].evidence_class
        is not EvidenceClass.FIRST_PARTY_EXCHANGE
    )


# ---------------------------------------------------------------------------
# B1-T31 — capabilities default unverified
# ---------------------------------------------------------------------------


def test_t31_capabilities_default_unverified():
    for provider, entry in DEFAULT_REGISTRY.providers.items():
        for capability in entry.capabilities.values():
            assert capability.verified is False, provider


def test_t31_claimed_but_unverified_is_legal():
    # Bloc 1: planning claims may be true, historical verification stays false
    kraken = DEFAULT_REGISTRY.providers["KRAKEN_FUTURES"]
    assert kraken.capabilities["liquidations"].claimed is True
    assert kraken.capabilities["liquidations"].verified is False


def test_t31_no_provider_marked_verified():
    for entry in DEFAULT_REGISTRY.providers.values():
        assert all(not cap.verified for cap in entry.capabilities.values())


def test_t31_verified_without_claimed_fails():
    with pytest.raises(ValidationError):
        ProviderEntry.model_validate(
            {
                "evidence_class": "FIRST_PARTY_EXCHANGE",
                "capabilities": {"funding": {"claimed": False, "verified": True}},
            }
        )


def test_t31_unknown_capability_key_fails():
    with pytest.raises(ValidationError, match="capability keys"):
        ProviderEntry.model_validate(
            {
                "evidence_class": "FIRST_PARTY_EXCHANGE",
                "capabilities": {"fancy_new_sensor": {"claimed": True}},
            }
        )


# ---------------------------------------------------------------------------
# B1-T32 — critical sensor redundancy intent
# ---------------------------------------------------------------------------


def test_t32_critical_sensors_have_planned_redundancy():
    assert set(DEFAULT_PRIORITY.critical) == set(CRITICAL_SENSOR_STATES)
    satisfied = critical_states_with_redundancy_intent(DEFAULT_PRIORITY)
    assert set(satisfied) == set(CRITICAL_SENSOR_STATES), (
        "every critical sensor state must list at least two preferred sources "
        "where the planning registry identifies plausible providers"
    )


def test_t32_priority_entries_declare_min_sources():
    for name, entry in DEFAULT_PRIORITY.critical.items():
        assert entry.min_preferred_sources >= 2, name
        assert len(entry.source_priority) >= 2, name


# ---------------------------------------------------------------------------
# B1-T33 — ordering is config, not hard-coded logic
# ---------------------------------------------------------------------------


def test_t33_priority_ordering_comes_from_config():
    raw = yaml.safe_load(
        (CONFIG_DIR / "sensor_priority.yaml").read_text(encoding="utf-8")
    )
    for name, entry in DEFAULT_PRIORITY.critical.items():
        assert entry.source_priority == raw["critical"][name]["source_priority"]


def test_t33_no_hardcoded_ordering_in_module():
    # The module exposes no ordering constant and embeds no provider ids;
    # ordering lives in the registry config.
    import inspect

    import crypto_sensor_fabric.registry.sensor_priority as module

    assert not hasattr(module, "ORDERING")
    source = inspect.getsource(module)
    for provider in PROVIDER_IDS:
        assert provider not in source, f"provider {provider} hard-coded in module source"


# ---------------------------------------------------------------------------
# Free-only required-runtime integration (T20..T24 at config level)
# ---------------------------------------------------------------------------


def test_default_registry_has_no_required_providers():
    # Correct Bloc 1 state: nothing may be required until Bloc 2 verifies it.
    assert eligible_required_providers(DEFAULT_REGISTRY) == []


@pytest.mark.parametrize(
    "access_class",
    [AccessClass.PAID_EXCLUDED, AccessClass.FREE_REFERENCE_ONLY, AccessClass.UNVERIFIED],
)
def test_t20_t22_required_runtime_rejects_non_automated(access_class: AccessClass):
    registry = ProviderRegistry.model_validate(
        {
            "providers": {
                "X": {
                    "evidence_class": "FIRST_PARTY_EXCHANGE",
                    "access": {
                        "access_class": access_class,
                        "cost_usd_required": 0,
                        "payment_method_required": False,
                        "staking_required": False,
                        "transaction_required": False,
                    },
                }
            }
        }
    )
    violations = validate_required_runtime(registry, ["X"])
    assert violations, f"required runtime must reject {access_class.value}"
    assert not is_required_runtime_allowed(registry, "X")


@pytest.mark.parametrize(
    "overrides",
    [
        {"cost_usd_required": 25},
        {"payment_method_required": True},
        {"staking_required": True},
        {"transaction_required": True},
    ],
)
def test_t23_required_runtime_rejects_cost_violations(overrides: dict):
    policy_kwargs = {"access_class": AccessClass.FREE_AUTOMATED, **overrides}
    registry = ProviderRegistry.model_validate(
        {
            "providers": {
                "X": {
                    "evidence_class": "FIRST_PARTY_EXCHANGE",
                    "access": policy_kwargs,
                }
            }
        }
    )
    assert validate_required_runtime(registry, ["X"])


def test_t24_free_api_key_required_runtime_allowed():
    policy = FreeOnlyPolicy.model_validate(
        {
            "access_class": AccessClass.FREE_AUTOMATED,
            "api_key_required": True,
            "cost_usd_required": 0,
            "payment_method_required": False,
            "staking_required": False,
            "transaction_required": False,
        }
    )
    registry = ProviderRegistry.model_validate(
        {"providers": {"X": {"evidence_class": "FIRST_PARTY_EXCHANGE", "access": policy}}}
    )
    assert validate_required_runtime(registry, ["X"]) == []
    assert is_required_runtime_allowed(registry, "X")


def test_unknown_required_provider_reported():
    violations = validate_required_runtime(DEFAULT_REGISTRY, ["NOT_A_PROVIDER"])
    assert any("unknown provider" in v for v in violations)


def test_capability_keys_are_controlled():
    assert CAPABILITY_KEYS == (
        "liquidations",
        "open_interest",
        "funding",
        "order_flow",
        "order_book",
        "positioning",
        "basis",
    )


# ---------------------------------------------------------------------------
# SENSOR-B1-R02 — positioning + basis capability vocabulary
# ---------------------------------------------------------------------------


def test_r02_positioning_capability_accepted():
    entry = DEFAULT_REGISTRY.providers["GATE_FUTURES"]
    assert entry.capabilities["positioning"].claimed is True
    assert entry.capabilities["positioning"].verified is False


@pytest.mark.parametrize(
    "provider, capability",
    [
        ("GATE_FUTURES", "positioning"),
        ("COINALYZE", "positioning"),
        ("KRAKEN_FUTURES", "basis"),
    ],
)
def test_r02_planned_capabilities_claimed_but_unverified(provider: str, capability: str):
    entry = DEFAULT_REGISTRY.providers[provider]
    assert capability in entry.capabilities
    assert entry.capabilities[capability].claimed is True
    assert entry.capabilities[capability].verified is False


def test_r02_unknown_capability_keys_still_fail():
    with pytest.raises(ValidationError, match="capability keys"):
        ProviderEntry.model_validate(
            {
                "evidence_class": "FIRST_PARTY_EXCHANGE",
                "capabilities": {"liquidations": {"claimed": True}, "hack": {"claimed": True}},
            }
        )


def test_r02_every_sensor_family_representable_without_vocabulary_extension():
    """Bloc 2 can represent every planned sensor capability using the
    foundational capability vocabulary (repair SENSOR-B1-R02)."""
    from crypto_sensor_fabric.contracts.enums import SensorFamily
    from crypto_sensor_fabric.registry.provider_registry import (
        SENSOR_FAMILY_CAPABILITY,
    )

    assert set(SENSOR_FAMILY_CAPABILITY) == {m.value for m in SensorFamily}
    assert set(SENSOR_FAMILY_CAPABILITY.values()) <= set(CAPABILITY_KEYS)


def test_r02_no_provider_marks_positioning_or_basis_verified():
    for entry in DEFAULT_REGISTRY.providers.values():
        for capability in entry.capabilities.values():
            assert capability.verified is False
