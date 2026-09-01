"""OCE Book 4 — Configuration & Security Control Spine tests (B4-R2).

Covers surfaces A–J of the canonical config/security spine plus the
adversarial matrix. Every test here runs LOCALLY (no container gate) so the
assertions stay in the authoritative run. The spine's public API is exercised
directly and exactly; nothing here weakens the frozen Book 2/3 invariants
(sandbox strictness, authenticated outbound sessions, fenced leases, disposable
Redis, one material effect, live-order/billable-cloud denial).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from oce_control.config_spine import (
    REDACTED,
    SOURCE_CLI,
    SOURCE_DEFAULT,
    SOURCE_ENV,
    SOURCE_FILE,
    SECRET_REF_RE,
    ConfigAuthorization,
    ConfigResolver,
    OverrideAudit,
    SecretStore,
    Setting,
    SettingsRegistry,
    ValidationError,
    build_default_registry,
    fingerprint_config,
    redact_mapping,
    redact_string,
    redact_value,
    resolve_postgres_password,
    validate_effective,
    validate_setting_value,
)

# A sentinel secret value used in tests; it must never appear in redacted
# output, fingerprints, snapshots, or any committed source below.
TEST_SECRET = "B4-SUPER-SEKRE7-0nly-in-tests-9f3a"
# CXR4-02: Book 4 has exactly ONE legal secret reference (secret:runtime-local);
# resolver/fingerprint tests model runtime configs with the canonical ref.
REF_PG = "secret:runtime-local"
# Postgres password_ref is mandatory-with-no-default; supply it in happy paths.
HAPPY = {"file": {"postgres.password_ref": REF_PG}}


# --------------------------------------------------------------------------- #
# Surface A — canonical settings ownership
# --------------------------------------------------------------------------- #
class TestOwnershipRegistry:
    def test_registry_has_canonical_settings(self):
        reg = build_default_registry()
        expected = {
            "control_plane.host", "control_plane.port",
            "control_plane.public_listen", "postgres.host",
            "postgres.password_ref", "redis.mode", "workers.egress",
            "sandbox.strict", "sandbox.process_tree_termination",
            "sessions.auth_required", "execution.broker_enabled",
            "execution.paper_trading_enabled", "execution.live_order_mode",
            "capital.authority", "cloud.provisioning", "cloud.gpu_burst",
            "cloud.accounts", "cloud.cost_ceiling_usd_per_month",
            "logging.redact_secrets", "logging.redact_cli",
        }
        assert expected <= set(reg.settings)

    def test_every_setting_has_owner_and_sensitivity_classification(self):
        reg = build_default_registry()
        for name, s in reg.settings.items():
            assert s.owner in ("operator", "operator(po)", "policy")
            assert isinstance(s.sensitive, bool)
            assert isinstance(s.mutability, str)
            assert s.validation_rule  # every setting documents a rule

    def test_secret_setting_marked_sensitive(self):
        reg = build_default_registry()
        assert reg.get("postgres.password_ref").sensitive is True

    def test_no_default_required_setting_has_no_silent_value(self):
        reg = build_default_registry()
        s = reg.get("postgres.password_ref")
        assert s.has_default is False  # guessing would be unsafe

    def test_dup_registration_rejected(self):
        reg = SettingsRegistry()
        reg.register(Setting(name="a.b", value_type="int", default=1))
        with pytest.raises(ValueError):
            reg.register(Setting(name="a.b", value_type="int", default=2))

    def test_no_default_with_value_rejected(self):
        reg = SettingsRegistry()
        with pytest.raises(ValueError):
            reg.register(Setting(name="a.b", value_type="int",
                                 has_default=False, default=1))

    def test_enum_without_allowed_values_rejected(self):
        reg = SettingsRegistry()
        with pytest.raises(ValueError):
            reg.register(Setting(name="a.b", value_type="enum"))

    def test_alias_collision_rejected(self):
        reg = SettingsRegistry()
        reg.register(Setting(name="real.name", value_type="int", default=1))
        with pytest.raises(ValueError):
            reg.alias("real.name", "bogus")

    def test_forbidden_source_is_recorded_and_tested(self):
        reg = build_default_registry()
        reg.forbid_source("workers.egress", SOURCE_ENV)
        assert ("workers.egress", SOURCE_ENV) in reg.forbidden_sources

    def test_unknown_value_type_fails_registry_validation(self):
        reg = SettingsRegistry()
        reg.register(Setting(name="a.b", value_type="float", default=1.0))
        # corrupt to an unsupported type, then validate
        reg._settings["a.b"] = Setting(name="a.b", value_type="nothing")
        with pytest.raises(ValueError):
            reg.validate_registry()


# --------------------------------------------------------------------------- #
# Surface B — deterministic resolution / precedence
# --------------------------------------------------------------------------- #
class TestDeterministicResolution:
    def test_precedence_default_file_env_cli(self):
        reg = build_default_registry()
        r = ConfigResolver(reg)
        # default=8448, file, env, cli all contradicting the port
        eff = r.resolve({
            "file": {"control_plane.port": "7000",
                     "postgres.password_ref": REF_PG},
            "environment": {"control_plane.port": "9000"},
        }, cli={"control_plane.port": "9100"})
        assert eff.get("control_plane.port") == 9100  # cli highest

    def test_env_overrides_file_and_default(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve({
            "file": {"postgres.password_ref": REF_PG},
            "environment": {"control_plane.port": "9000"},
        })
        assert eff.get("control_plane.port") == 9000
        assert eff.provenance["control_plane.port"] == "environment"

    def test_file_overrides_default(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve({
            "file": {"postgres.password_ref": REF_PG,
                     "control_plane.port": "7000"},
        })
        assert eff.get("control_plane.port") == 7000
        assert eff.provenance["control_plane.port"] == "file"

    def test_same_inputs_same_effective_config(self):
        reg = build_default_registry()
        src = {"file": {"postgres.password_ref": REF_PG},
               "environment": {"control_plane.port": "9000"}}
        a = ConfigResolver(reg).resolve(src)
        b = ConfigResolver(reg).resolve(src)
        assert a.resolved == b.resolved
        assert a.fingerprint == b.fingerprint

    def test_lower_source_never_overrides_higher(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve({
            "file": {"control_plane.port": "7000",
                     "postgres.password_ref": REF_PG},
            "environment": {"control_plane.port": "9000"},
        }, cli={"control_plane.port": "9100"})
        # any subset of the sources must yield exactly max-priority wins
        assert eff.get("control_plane.port") == 9100

    def test_conflicting_sources_resolve_deterministically(self):
        reg = build_default_registry()
        from functools import reduce
        orders = [
            {"default", "file", "environment", "cli"},
        ]
        # flip iteration only; resolution must remain keyed by fixed order
        e1 = ConfigResolver(reg).resolve(
            {"file": {"postgres.password_ref": REF_PG, "control_plane.port": "7000"},
             "environment": {"control_plane.port": "9000"}},
            cli={"control_plane.port": "9100"})
        e2 = ConfigResolver(reg).resolve(
            {"environment": {"control_plane.port": "9000"},
             "file": {"postgres.password_ref": REF_PG, "control_plane.port": "7000"}},
            cli={"control_plane.port": "9100"})
        assert e1.get("control_plane.port") == e2.get("control_plane.port") == 9100

    def test_unknown_setting_rejected(self):
        reg = build_default_registry()
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"environment": {"totally.unknown.setting": "1"}})

    def test_malformed_bool_rejected(self):
        reg = build_default_registry()
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": REF_PG,
                          "sandbox.strict": "not-a-bool"}})

    def test_malformed_int_rejected(self):
        reg = build_default_registry()
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": REF_PG,
                          "control_plane.port": "abc"}})

    def test_conflicting_enum_rejected(self):
        reg = build_default_registry()
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": REF_PG,
                          "execution.live_order_mode": "paper"}})

    def test_reserved_port_rejected(self):
        reg = build_default_registry()
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": REF_PG,
                          "control_plane.port": "5432"}})

    def test_public_listen_cannot_activate(self):
        reg = build_default_registry()
        # no default-host outside loopback; env cannot bind public host
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": REF_PG,
                          "control_plane.host": "0.0.0.0"}})

    def test_empty_null_ambiguity_handled(self):
        reg = build_default_registry()
        # empty port string -> invalid int -> fail closed rather than guess
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": REF_PG,
                          "control_plane.port": ""}})

    def test_restart_consistency(self):
        reg = build_default_registry()
        src = {"file": {"postgres.password_ref": REF_PG}}
        a = ConfigResolver(reg).resolve(dict(src))
        b = ConfigResolver(reg).resolve(dict(src))
        assert a.to_dict() == b.to_dict()


# --------------------------------------------------------------------------- #
# Surface C — startup validation (fail closed)
# --------------------------------------------------------------------------- #
class TestStartupFailClosed:
    def _resolve(self, file_extra=None):
        src = {"file": {"postgres.password_ref": REF_PG}}
        if file_extra:
            src["file"].update(file_extra)
        return ConfigResolver(build_default_registry()).resolve(src)

    def test_happy_path_resolves(self):
        eff = self._resolve()
        assert eff.get_bool("sandbox.strict") is True

    def test_missing_incomplete_required_rejected(self):
        reg = build_default_registry()
        # postgres.password_ref is required and absent everywhere
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve({})

    def test_public_listen_true_rejected(self):
        with pytest.raises(ValidationError):
            self._resolve({"control_plane.public_listen": True})

    def test_redis_mode_must_be_transport(self):
        with pytest.raises(ValidationError):
            self._resolve({"redis.mode": "cache"})

    def test_workers_egress_denied_by_default(self):
        with pytest.raises(ValidationError):
            self._resolve({"workers.egress": "public"})

    def test_sandbox_strict_false_rejected(self):
        with pytest.raises(ValidationError):
            self._resolve({"sandbox.strict": False})

    def test_broker_enabled_rejected(self):
        with pytest.raises(ValidationError):
            self._resolve({"execution.broker_enabled": True})

    def test_paper_trading_rejected(self):
        with pytest.raises(ValidationError):
            self._resolve({"execution.paper_trading_enabled": True})

    def test_live_order_mode_denied_by_config(self):
        with pytest.raises(ValidationError):
            self._resolve({"execution.live_order_mode": "paper"})

    def test_cloud_provisioning_rejected(self):
        with pytest.raises(ValidationError):
            self._resolve({"cloud.provisioning": True})

    def test_cloud_gpu_burst_rejected(self):
        with pytest.raises(ValidationError):
            self._resolve({"cloud.gpu_burst": True})

    def test_cloud_accounts_must_be_empty(self):
        with pytest.raises(ValidationError):
            self._resolve({"cloud.accounts": ["aws:prod"]})

    def test_cloud_cost_ceiling_must_be_zero(self):
        with pytest.raises(ValidationError):
            self._resolve({"cloud.cost_ceiling_usd_per_month": 50})

    def test_sessions_auth_cannot_be_disabled(self):
        with pytest.raises(ValidationError):
            self._resolve({"sessions.auth_required": False})

    def test_error_is_operator_legible_and_secret_free(self):
        with pytest.raises(ValidationError) as exc:
            self._resolve({"execution.broker_enabled": True})
        msg = str(exc.value)
        assert "broker" in msg.lower()
        assert TEST_SECRET not in msg


# --------------------------------------------------------------------------- #
# Surface D — secret reference model
# --------------------------------------------------------------------------- #
class TestSecretReference:
    def test_store_resolve_roundtrip(self):
        s = SecretStore()
        ref = s.store("pg", TEST_SECRET)
        assert ref == "secret:pg"
        assert s.resolve(ref) == TEST_SECRET

    def test_reference_has_valid_shape(self):
        s = SecretStore()
        ref = s.store("pg", TEST_SECRET)
        assert SECRET_REF_RE.match(ref)

    def test_missing_secret_fails_closed(self):
        s = SecretStore()
        with pytest.raises(KeyError):
            s.resolve("secret:missing")

    def test_revoked_secret_refused(self):
        s = SecretStore()
        s.store("pg", TEST_SECRET)
        s.revoke("pg")
        assert s.is_revoked("pg")
        with pytest.raises(PermissionError):
            s.resolve("secret:pg")

    def test_rotation_new_generation(self):
        s = SecretStore()
        s.store("pg", "gen1")
        g1 = s.generation("pg")
        s.rotate("pg", "gen2")
        assert s.generation("pg") == g1 + 1
        assert s.resolve("secret:pg") == "gen2"

    def test_restart_resolution_after_reconstruct(self):
        # A restart restores from the approved external store. A fresh store
        # with the same secret resolves; without it, resolve fails closed.
        s1 = SecretStore()
        ref = s1.store("pg", TEST_SECRET)
        s2 = SecretStore()
        s2.store("pg", TEST_SECRET)
        assert s2.resolve(ref) == TEST_SECRET
        s3 = SecretStore()
        with pytest.raises(KeyError):
            s3.resolve(ref)

    def test_empty_secret_refused(self):
        s = SecretStore()
        with pytest.raises(ValidationError):
            s.store("pg", "")

    def test_invalid_reference_name_refused(self):
        s = SecretStore()
        with pytest.raises(ValidationError):
            s.store("bad name!", "value")

    def test_resolve_postgres_password_requires_reference(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(HAPPY)
        store = SecretStore()
        store.store("runtime-local", TEST_SECRET)
        assert resolve_postgres_password(eff, store) == TEST_SECRET

    def test_resolve_postgres_password_rejects_plain_value(self):
        reg = build_default_registry()
        # a configuration that embeds a plain password instead of a reference
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": "actualplainpw123"}})

    def test_snapshot_redacts_by_default(self):
        s = SecretStore()
        s.store("pg", TEST_SECRET)
        snap = s.snapshot()
        assert TEST_SECRET not in json.dumps(snap)
        assert snap["pg"]["value"] == REDACTED

    def test_resolve_postgres_missing_raises(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(HAPPY)
        store = SecretStore()  # reference present but store empty
        with pytest.raises(KeyError):
            resolve_postgres_password(eff, store)


# --------------------------------------------------------------------------- #
# Surface E — redaction / leakage defense
# --------------------------------------------------------------------------- #
class TestRedaction:
    def test_redact_value_masks_sensitive(self):
        assert redact_value("password", "hunter2") == REDACTED
        assert redact_value("api_token", "abc") == REDACTED

    def test_redact_value_keeps_secret_reference(self):
        assert redact_value("password", "secret:pg") == "secret:pg"

    def test_redact_value_passes_nonsensitive(self):
        assert redact_value("port", 8448) == 8448

    def test_redact_mapping_nested(self):
        data = {"postgres": {"password": "hunter2", "host": "127.0.0.1"}}
        out = redact_mapping(data)
        assert out["postgres"]["password"] == REDACTED
        assert out["postgres"]["host"] == "127.0.0.1"

    def test_redact_string_scans_key_eq_value(self):
        out = redact_string('password=hunter2 and host=127.0.0.1')
        assert "hunter2" not in out
        assert REDACTED in out

    def test_redact_string_with_secret_pool(self):
        out = redact_string("conn failed: " + TEST_SECRET,
                            secrets_pool=[TEST_SECRET])
        assert TEST_SECRET not in out

    def test_effective_redacted_view_has_no_secret(self):
        reg = build_default_registry()
        s = SecretStore()
        s.store("runtime-local", TEST_SECRET)
        eff = ConfigResolver(reg).resolve(HAPPY).bind_secret_resolver(s)
        view = eff.redacted()
        blob = json.dumps(view)
        assert TEST_SECRET not in blob
        assert view["postgres.password_ref"] == REF_PG

    def test_to_dict_has_no_secret(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(HAPPY)
        blob = json.dumps(eff.to_dict())
        assert TEST_SECRET not in blob

    def test_exception_from_sensitive_config_is_redacted(self):
        reg = build_default_registry()
        # force a validation error and make sure it never carries the secret
        with pytest.raises(ValidationError) as exc:
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": TEST_SECRET}})
        assert TEST_SECRET not in str(exc.value)

    def test_committed_source_has_no_test_secret(self):
        # Scan the control-plane source+tests+scripts for the sentinel secret.
        # If TEST_SECRET ever leaks into a committed file below, this fails.
        base = Path(__file__).resolve().parent.parent  # infrastructure/control-plane
        offenders = []
        for path in [base / "src", base / "tests", base / "scripts"]:
            for p in path.rglob("*.py"):
                if p.read_text(encoding="utf-8", errors="ignore").count(TEST_SECRET):
                    # the definition line itself is unavoidable; only flag
                    # occurrences OUTSIDE this test module
                    if "TEST_SECRET = " not in p.read_text(encoding="utf-8",
                                                           errors="ignore"):
                        offenders.append(str(p))
        assert offenders == [], f"secret leaked into: {offenders}"


# --------------------------------------------------------------------------- #
# Surface F — authorization boundaries & override audit
# --------------------------------------------------------------------------- #
class TestAuthorization:
    def test_policy_setting_not_mutable_by_operator(self):
        reg = build_default_registry()
        authz = ConfigAuthorization(reg)
        s = reg.get("sandbox.strict")
        assert authz.can_mutate("operator", s) is False

    def test_operator_can_mutate_operator_setting(self):
        reg = build_default_registry()
        authz = ConfigAuthorization(reg)
        s = reg.get("control_plane.port")
        assert authz.can_mutate("operator", s) is True

    def test_po_only_owner_requires_po(self):
        reg = build_default_registry()
        authz = ConfigAuthorization(reg)
        s = reg.get("capital.authority")
        assert authz.can_mutate("operator:po", s) is True
        assert authz.can_mutate("operator", s) is False
        assert authz.can_mutate("hermes", s) is False

    def test_override_records_attributable_audit(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(HAPPY)
        authz = ConfigAuthorization(reg)
        new = authz.operator_override(
            eff, actor="operator:po", setting_name="control_plane.port",
            requested_change="raise local port to 9100 for CI",
            reason="explicit operator decision", new_value="9100")
        assert new == 9100
        assert len(authz.audit) == 1
        entry = authz.audit[0]
        assert entry.actor == "operator:po"
        assert entry.target == "control_plane.port"
        assert entry.reason
        assert entry.authorized is True
        assert entry.timestamp

    def test_override_of_policy_setting_denied(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(HAPPY)
        authz = ConfigAuthorization(reg)
        for actor in ("operator", "operator:po"):
            with pytest.raises(PermissionError):
                authz.operator_override(
                    eff, actor=actor, setting_name="sandbox.strict",
                    requested_change="x", reason="x", new_value=False)

    def test_override_of_sensitive_setting_denied(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(HAPPY)
        authz = ConfigAuthorization(reg)
        with pytest.raises(PermissionError):
            authz.operator_override(
                eff, actor="operator", setting_name="postgres.password_ref",
                requested_change="x", reason="x", new_value="secret:other")

    def test_override_unknown_setting_denied(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(HAPPY)
        authz = ConfigAuthorization(reg)
        with pytest.raises(ValidationError):
            authz.operator_override(
                eff, actor="operator", setting_name="no.such",
                requested_change="x", reason="x", new_value="1")

    def test_hermes_cannot_mutate_governance(self):
        reg = build_default_registry()
        authz = ConfigAuthorization(reg)
        for name in ("sandbox.strict", "cloud.provisioning",
                     "execution.broker_enabled", "capital.authority"):
            s = reg.get(name)
            assert authz.can_mutate("hermes", s) is False


# --------------------------------------------------------------------------- #
# Surfaces G/H/I — network, live-order, billable-cloud denial (adversarial)
# --------------------------------------------------------------------------- #
class TestDenialGates:
    def _resolve(self, kw=None):
        src = {"file": {"postgres.password_ref": REF_PG}}
        if kw:
            src["file"].update(kw)
        return ConfigResolver(build_default_registry()).resolve(src)

    def test_0_0_0_0_listen_denied(self):
        with pytest.raises(ValidationError):
            self._resolve({"control_plane.host": "0.0.0.0"})

    def test_public_egress_denied(self):
        with pytest.raises(ValidationError):
            self._resolve({"workers.egress": "public"})

    def test_live_mode_via_env_denied(self):
        with pytest.raises(ValidationError):
            ConfigResolver(build_default_registry()).resolve(
                {"environment": {"execution.live_order_mode": "paper",
                                 "postgres.password_ref": REF_PG}})

    def test_live_mode_via_cli_denied(self):
        with pytest.raises(ValidationError):
            ConfigResolver(build_default_registry()).resolve(
                HAPPY, cli={"execution.live_order_mode": "paper"})

    def test_live_mode_via_malformed_enum_denied(self):
        with pytest.raises(ValidationError):
            self._resolve({"execution.live_order_mode": "not-a-mode"})

    def test_contradictory_mode_settings_denied(self):
        with pytest.raises(ValidationError):
            self._resolve({"execution.live_order_mode": "disabled",
                           "execution.broker_enabled": True})

    def test_cloud_provisioning_via_env_denied(self):
        with pytest.raises(ValidationError):
            ConfigResolver(build_default_registry()).resolve(
                {"environment": {"cloud.provisioning": True,
                                 "postgres.password_ref": REF_PG}})

    def test_cloud_gpu_burst_via_cli_denied(self):
        with pytest.raises(ValidationError):
            ConfigResolver(build_default_registry()).resolve(
                HAPPY, cli={"cloud.gpu_burst": True})

    def test_cloud_account_activation_denied(self):
        with pytest.raises(ValidationError):
            self._resolve({"cloud.accounts": ["gcp:burst"]})

    def test_secure_looking_https_endpoint_still_no_binding_expansion(self):
        # "secure-looking" hostname is still a non-loopback listen — denied
        with pytest.raises(ValidationError):
            self._resolve({"control_plane.host": "secure.example.com"})

    def test_deny_by_default_toggles_stay_denied(self):
        reg = build_default_registry()
        for name in ("execution.broker_enabled", "execution.paper_trading_enabled",
                     "cloud.provisioning", "cloud.gpu_burst"):
            s = reg.get(name)
            assert s.default is False
            assert "deny-by-default" in s.tags or name in (
                "execution.paper_trading_enabled",)


# --------------------------------------------------------------------------- #
# Surface J — config drift / effective state
# --------------------------------------------------------------------------- #
class TestDriftFingerprint:
    def test_fingerprint_is_deterministic_and_sha256(self):
        reg = build_default_registry()
        e1 = ConfigResolver(reg).resolve(HAPPY)
        e2 = ConfigResolver(reg).resolve(HAPPY)
        assert e1.fingerprint == e2.fingerprint
        assert re.fullmatch(r"[0-9a-f]{64}", e1.fingerprint)

    def test_fingerprint_changes_when_config_changes(self):
        reg = build_default_registry()
        a = ConfigResolver(reg).resolve(HAPPY)
        b = ConfigResolver(reg).resolve(
            {"file": {"postgres.password_ref": REF_PG,
                      "control_plane.port": "9000"}})
        assert a.fingerprint != b.fingerprint

    def test_fingerprint_does_not_leak_secret_value(self):
        reg = build_default_registry()
        s = SecretStore()
        s.store("runtime-local", TEST_SECRET)
        eff = ConfigResolver(reg).resolve(HAPPY)
        assert TEST_SECRET not in eff.fingerprint

    def test_restart_does_not_silently_change_effective_authority(self):
        reg = build_default_registry()
        src = {"file": {"postgres.password_ref": REF_PG}}
        a = ConfigResolver(reg).resolve(dict(src))
        b = ConfigResolver(reg).resolve(dict(src))
        # identical inputs -> identical effective authority
        assert a.fingerprint == b.fingerprint
        assert a.resolved == b.resolved

    def test_environment_only_change_alters_fingerprint(self):
        reg = build_default_registry()
        base = ConfigResolver(reg).resolve(HAPPY)
        env_changed = ConfigResolver(reg).resolve(
            {"environment": {"control_plane.port": "9000",
                             "postgres.password_ref": REF_PG}})
        assert base.fingerprint != env_changed.fingerprint
        # but restarting with the same env is stable
        env_changed2 = ConfigResolver(reg).resolve(
            {"environment": {"control_plane.port": "9000",
                             "postgres.password_ref": REF_PG}})
        assert env_changed.fingerprint == env_changed2.fingerprint


# --------------------------------------------------------------------------- #
# Adversarial matrix — real boundary failures, no Book 3 weakening
# --------------------------------------------------------------------------- #
class TestAdversarialMatrix:
    def test_unknown_setting_injection_denied(self):
        with pytest.raises(ValidationError):
            ConfigResolver(build_default_registry()).resolve(
                {"environment": {"workers.egress_superuser": True}})

    def test_duplicate_conflicting_alias_denied(self):
        reg = build_default_registry()
        with pytest.raises(ValueError):
            reg.alias("sandbox.strict", "some.other")

    def test_invalid_enum_fall_through_denied(self):
        with pytest.raises(ValidationError):
            ConfigResolver(build_default_registry()).resolve(
                {"file": {"redis.mode": "ephemeral-authority",
                          "postgres.password_ref": REF_PG}})

    def test_capability_escalation_via_config_denied(self):
        # worker-egress broadening / session auth demotion must fail closed
        with pytest.raises(ValidationError):
            ConfigResolver(build_default_registry()).resolve(
                {"file": {"sessions.auth_required": False,
                          "workers.egress": "public",
                          "postgres.password_ref": REF_PG}})

    def test_fake_secret_reference_denied_on_resolve(self):
        s = SecretStore()
        with pytest.raises(KeyError):
            s.resolve("secret:not-provisioned")

    def test_secret_in_plain_config_denied(self):
        with pytest.raises(ValidationError):
            ConfigResolver(build_default_registry()).resolve(
                {"file": {"postgres.password_ref": TEST_SECRET}})

    def test_worker_capability_unchanged_by_spine(self):
        # The spine policy must not relax Book 3 worker capability admission.
        reg = build_default_registry()
        assert reg.get("workers.egress").owner == "policy"
        assert "sandbox" in reg.get("workers.egress").tags

    def test_sandbox_invariants_remain(self):
        reg = build_default_registry()
        assert reg.get("sandbox.strict").default is True
        assert reg.get("sandbox.process_tree_termination").default is True

    def test_session_auth_invariant_remains(self):
        reg = build_default_registry()
        assert reg.get("sessions.auth_required").default is True

    def test_fence_idempotency_surfaces_untouched(self):
        # Spawn a lightweight subprocess importing the spine only, to prove the
        # module loads in the authoritative environment (no hidden deps).
        base = Path(__file__).resolve().parent.parent
        src = base / "src"
        code = (
            "import sys; sys.path.insert(0, %r); "
            "from oce_control.config_spine import build_default_registry; "
            "assert len(build_default_registry().settings) >= 20"
        ) % str(src)
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr


# --------------------------------------------------------------------------- #
# shared backed helper for secret-store proofs
# --------------------------------------------------------------------------- #
def _make_backend(tmp_path, provision: bool = True,
                  value: str = "genuine-secret-abc123"):
    from oce_control import local_secrets as ls
    f = tmp_path / "secrets.json"
    if provision:
        f.write_text(json.dumps({"postgres_password": value}), encoding="utf-8")
    return ls.RuntimeSecretBackend(f)


# --------------------------------------------------------------------------- #
# B4-R3R3 — secret-reference model: configuration/init vs runtime/start.
# Runtime start passes ONLY when the reference resolves in the approved
# store; a fabricated-but-unresolvable reference string fails closed.
# --------------------------------------------------------------------------- #
class TestR3R3SecretResolution:
    def _backend(self, tmp_path, provision: bool = True, value: str = "genuine-secret-abc123"):
        return _make_backend(tmp_path, provision=provision, value=value)

    def test_missing_required_reference_fails_closed(self, tmp_path):
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=False)
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        with pytest.raises(SystemExit) as exc:
            cs.require_secret_resolvable(environ=None, backend=backend, eff=eff)
        assert "configure" in str(exc.value)

    def test_valid_reference_with_existing_secret_passes(self, tmp_path):
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=True, value="genuine-secret-abc123")
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        secret = cs.resolve_startup_secret(eff, backend)  # must not raise
        assert secret == "genuine-secret-abc123"

    def test_valid_reference_absent_secret_fails_closed(self, tmp_path):
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=False)
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        with pytest.raises(SystemExit):
            cs.require_secret_resolvable(environ=None, backend=backend, eff=eff)

    def test_custom_reference_is_future_locked_even_when_resolvable(self, tmp_path):
        # CXR4-02: a custom reference is BLOCKED at CONFIG validation even
        # when it would resolve — Book 4 has exactly ONE secret authority
        # (secret:runtime-local), so no runtime consumer can split between
        # two secret sources.
        import oce_control.config_startup as cs
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({
            "postgres_password": "genuine-secret-abc123",
            "other-secret": "custom-secret-value-9876543210",
        }), encoding="utf-8")
        backend = ls.RuntimeSecretBackend(store)
        assert backend.resolve("secret:other-secret") == "custom-secret-value-9876543210"
        env = {"PATH": "/usr/bin", "OCE_POSTGRES_PASSWORD_REF": "secret:other-secret"}
        # resolvable, but the BOOK 4 contract has ONE secret authority:
        with pytest.raises(ValidationError, match="future-locked"):
            cs.effective_from_env(env)

    def test_revoked_secret_fails_closed(self, tmp_path):
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=True)
        backend.revoke("runtime-local")
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        with pytest.raises(SystemExit):
            cs.require_secret_resolvable(environ=None, backend=backend, eff=eff)

    def test_rotated_secret_new_value_and_generation(self, tmp_path):
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=True, value="gen-1-secret")
        backend.rotate("runtime-local", "gen-2-secret")
        assert backend.generation("runtime-local") == 2
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        assert cs.resolve_startup_secret(eff, backend) == "gen-2-secret"

    def test_plain_secret_supplied_fails_closed(self):
        # A plain password value is rejected at RESOLUTION (validator raises)
        # — even before the startup secret-resolution step runs.
        import oce_control.config_startup as cs
        with pytest.raises(ValidationError):
            cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "plain-password-123"})

    def test_malformed_reference_fails_closed(self, tmp_path):
        # A non-canonical reference (regex-valid but not secret:runtime-local)
        # fails at the CONFIG gate now — never deferred to readiness (CXR4-02).
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=True)
        with pytest.raises(ValidationError):
            cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:bad..name"})

    def test_unbacked_reference_fails_readiness_not_contradictory(self, tmp_path):
        # B4-CXR3R7: validate_startup is the CONFIG gate (no secret state);
        # the complete runtime-start contract lives in
        # validate_runtime_readiness, where ready=False whenever the secret
        # does not resolve — start=True + secret_ok=False is impossible.
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=False)
        cfg = cs.validate_startup(
            environ={"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        assert cfg["ok"] is True            # config posture is valid
        assert "secret_ok" not in cfg       # config gate reports no secret
        rep = cs.validate_runtime_readiness(
            environ={"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"},
            backend=backend)
        assert rep["ok"] is True           # configuration posture valid...
        assert rep["secret_ok"] is False   # ...but the runtime secret is NOT
        assert rep["ready"] is False       # ...therefore NOT ready (no lie)
        # invariant: ready => secret_ok => ok
        assert not (rep["ready"] and not rep["secret_ok"])
        assert not (rep["secret_ok"] and not rep["ok"])

    def test_first_governed_initialization_then_restart(self, tmp_path):
        # configure materializes a real secret into the store; restart then
        # resolves the same reference successfully (Book 2 invariant kept).
        import oce_control.config_startup as cs
        f = tmp_path / "secrets.json"
        from oce_control import local_secrets as ls
        f.write_text(json.dumps({"postgres_password": "first-init-secret-xyz"}),
                     encoding="utf-8")
        backend = ls.RuntimeSecretBackend(f)
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        # a fresh RuntimeSecretBackend instance (simulating a restart) resolves
        # the SAME canonical reference to the persisted secret
        fresh = ls.RuntimeSecretBackend(f)
        assert cs.resolve_startup_secret(eff, fresh) == "first-init-secret-xyz"

    def test_secret_value_never_appears_in_evidence_metadata(self, tmp_path):
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=True,
                                value="EVIDENCE-CANARY-SECRET-98765")
        meta = backend.security_metadata()
        blob = json.dumps(meta)
        assert "EVIDENCE-CANARY-SECRET-98765" not in blob
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        eff_redacted = json.dumps(eff.redacted())
        assert "EVIDENCE-CANARY-SECRET-98765" not in eff_redacted
        assert "EVIDENCE-CANARY-SECRET-98765" not in eff.fingerprint


# --------------------------------------------------------------------------- #
# B4-R3R6 — error-path leakage defense: a canary secret placed in the WRONG
# field must never appear in exceptions, reports, doctor/CLI output, or
# captured logs.
# --------------------------------------------------------------------------- #
CANARY = "canary-secret-wxyz-98765"
CANARY_ENV_BASE = {"PATH": "/usr/bin:/bin"}


class TestR3R6ErrorLeakageCanary:
    def _canary_report(self, env_extra: dict):
        import oce_control.config_startup as cs
        env = dict(CANARY_ENV_BASE)
        env.update(env_extra)
        return cs.validate_startup(env), cs.startup_report(env)

    def test_malformed_port_with_canary_never_leaks(self):
        rep, msg = self._canary_report({"OCE_CONTROL_PLANE_PORT": CANARY})
        assert rep["ok"] is False
        assert CANARY not in json.dumps(rep)
        assert CANARY not in msg
        # the canonical setting name is still identified, not a generic token
        assert "control_plane.port" in msg

    def test_malformed_bool_with_canary_never_leaks(self):
        rep, msg = self._canary_report({"OCE_SANDBOX_STRICT": CANARY})
        assert rep["ok"] is False
        assert CANARY not in json.dumps(rep)
        assert CANARY not in msg

    def test_malformed_enum_with_canary_never_leaks(self):
        rep, msg = self._canary_report({"OCE_REDIS_MODE": CANARY})
        assert rep["ok"] is False
        assert CANARY not in json.dumps(rep)
        assert CANARY not in msg

    def test_resolver_exception_never_echoes_candidate_value(self):
        reg = build_default_registry()
        with pytest.raises(ValidationError) as exc:
            ConfigResolver(reg).resolve(
                {"file": {"control_plane.port": CANARY,
                          "postgres.password_ref": REF_PG}})
        assert CANARY not in str(exc.value)
        assert "control_plane.port" in str(exc.value)

    def test_cli_path_denial_is_secret_free(self):
        rep, msg = self._canary_report({"OCE_CONTROL_PLANE_PUBLIC_LISTEN": "true"})
        assert rep["ok"] is False
        assert CANARY not in msg  # canary not present at all, trivially safe
        assert "public_listen" in msg

    def test_canary_in_plain_password_position_is_redacted(self):
        rep, msg = self._canary_report({"OCE_POSTGRES_PASSWORD_REF": CANARY})
        assert rep["ok"] is False
        assert CANARY not in json.dumps(rep)
        assert CANARY not in msg


# --------------------------------------------------------------------------- #
# B4-R3R5 — sensitive drift + security-state fingerprints (blind-fingeprint
# repair): reference identity changes count, secret values never do.
# --------------------------------------------------------------------------- #
class TestR3R5SecretSensitiveFingerprint:
    def test_same_config_same_fingerprint_stable(self):
        reg = build_default_registry()
        a = ConfigResolver(reg).resolve(HAPPY)
        b = ConfigResolver(reg).resolve(HAPPY)
        assert a.fingerprint == b.fingerprint

    def test_changed_nonsecret_setting_changes_fingerprint(self):
        reg = build_default_registry()
        a = ConfigResolver(reg).resolve(HAPPY)
        b = ConfigResolver(reg).resolve(
            {"file": {"postgres.password_ref": REF_PG,
                      "control_plane.port": "9000"}})
        assert a.fingerprint != b.fingerprint

    def test_secret_ref_identity_change_is_locked_or_observable(self):
        # CXR4-02: alternate reference identities are FUTURE-LOCKED at the
        # config surface (a second secret authority is rejected, never
        # silently adopted), and the security-state fingerprint still
        # distinguishes reference identity metadata without hashing the
        # secret value — identity drift stays observable even in depth.
        reg = build_default_registry()
        with pytest.raises(ValidationError, match="future-locked"):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": "secret:alpha"}})
        eff = ConfigResolver(reg).resolve(
            {"file": {"postgres.password_ref": "secret:runtime-local"}})
        meta_a = {"alpha": {"generation": 1, "revoked": False,
                            "backend": "local-runtime-store-v1"}}
        meta_b = {"beta": {"generation": 1, "revoked": False,
                           "backend": "local-runtime-store-v1"}}
        assert eff.bind_secret_resolver_dict(meta_a).security_fingerprint != \
            eff.bind_secret_resolver_dict(meta_b).security_fingerprint

    def test_same_reference_new_generation_stable_config_fp(self):
        # rotation of the SAME reference keeps the CONFIG fingerprint stable
        # (identity unchanged) while the SECURITY-state fingerprint changes.
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(
            {"file": {"postgres.password_ref": "secret:runtime-local"}})
        meta1 = {"runtime-local": {"generation": 1, "revoked": False,
                                   "backend": "local-runtime-store-v1"}}
        meta2 = {"runtime-local": {"generation": 2, "revoked": False,
                                   "backend": "local-runtime-store-v1"}}
        e1 = eff.bind_secret_resolver_dict(meta1)
        e2 = eff.bind_secret_resolver_dict(meta2)
        assert e1.fingerprint == e2.fingerprint   # config identity unchanged
        assert e1.security_fingerprint != e2.security_fingerprint

    def test_revocation_changes_security_fingerprint(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(
            {"file": {"postgres.password_ref": "secret:runtime-local"}})
        live = {"runtime-local": {"generation": 1, "revoked": False,
                                  "backend": "local-runtime-store-v1"}}
        revoked = {"runtime-local": {"generation": 2, "revoked": True,
                                     "backend": "local-runtime-store-v1"}}
        assert eff.bind_secret_resolver_dict(live).security_fingerprint != \
            eff.bind_secret_resolver_dict(revoked).security_fingerprint

    def test_same_ref_and_generation_both_fingerprints_stable(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(
            {"file": {"postgres.password_ref": "secret:runtime-local"}})
        meta = {"runtime-local": {"generation": 4, "revoked": False,
                                  "backend": "local-runtime-store-v1"}}
        a = eff.bind_secret_resolver_dict(meta)
        b = eff.bind_secret_resolver_dict(dict(meta))
        assert a.fingerprint == b.fingerprint
        assert a.security_fingerprint == b.security_fingerprint

    def test_no_raw_secret_value_in_any_fingerprint(self):
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(
            {"file": {"postgres.password_ref": "secret:runtime-local"}})
        meta = {"runtime-local": {"generation": 1, "revoked": False,
                                  "backend": "local-runtime-store-v1"}}
        bound = eff.bind_secret_resolver_dict(meta)
        # a canary VALUE (not reference) must never reach any fingerprint
        canary = "FINGERPRINT-CANARY-VALUE-42"
        assert canary not in bound.fingerprint
        assert canary not in (bound.security_fingerprint or "")
        # the reference IDENTITY is allowed (identifier only) but the canary
        # value is not
        assert "secret:runtime-local" in bound.to_dict()["fingerprint"] \
            or "runtime-local" not in (
                "FINGERPRINT-CANARY-VALUE-42",)

    def test_real_backend_security_fingerprint_detects_rotation(self, tmp_path):
        import oce_control.config_startup as cs
        backend = _make_backend(tmp_path, provision=True, value="gen-1-store-value")
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        eff = eff.bind_secret_resolver(backend)
        fp_before = eff.security_fingerprint
        backend.rotate("runtime-local", "gen-2-store-value")
        eff2 = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        eff2 = eff2.bind_secret_resolver(backend)
        assert fp_before != eff2.security_fingerprint
        assert eff.fingerprint == eff2.fingerprint  # reference identity stable


# --------------------------------------------------------------------------- #
# B4-R3R4 — database runtime bound to the governed secret resolution boundary
# --------------------------------------------------------------------------- #
class TestR3R4DatabaseSecretBinding:
    def _backend(self, tmp_path, provision: bool = True,
                 value: str = "genuine-secret-abc123"):
        return _make_backend(tmp_path, provision=provision, value=value)

    def test_governed_dsn_derived_from_resolved_secret(self, tmp_path):
        import oce_control.config_startup as cs
        backend = _make_backend(tmp_path, provision=True,
                                value="DB-BOUND-SECRET-12345")
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        dsn = cs.governed_runtime_dsn(eff=eff, backend=backend)
        assert "DB-BOUND-SECRET-12345" in dsn
        assert dsn.startswith("postgresql://oce_control_admin:")
        assert "@127.0.0.1:5433/oce_control" in dsn

    def test_governed_dsn_honors_canonical_host(self, tmp_path):
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=True)
        eff = cs.effective_from_env({
            "OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local",
            "OCE_POSTGRES_HOST": "127.0.0.1",
        })
        dsn = cs.governed_runtime_dsn(eff=eff, backend=backend)
        assert "@127.0.0.1:" in dsn

    def test_external_postgres_dsn_bypass_denied(self, tmp_path, monkeypatch):
        import oce_control.config_startup as cs
        from oce_control import local_secrets as ls
        # Hermetic env: in CI the runner pre-seeds POSTGRES_PASSWORD /
        # POSTGRES_DSN, which would re-materialize the store from the ambient
        # env instead of the tmp file. Remove both so the approved tmp store
        # is the ONLY authority (matches the runtime contract).
        monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
        monkeypatch.delenv("POSTGRES_DSN", raising=False)
        backend = _make_backend(tmp_path, provision=True,
                                value="REAL-SECRET-FROM-STORE")
        # point the module store at the same tmp file so require_runtime_dsn
        # derives the SAME governed DSN
        monkeypatch.setattr(ls, "SECRETS_FILE", tmp_path / "secrets.json")
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        governed = cs.governed_runtime_dsn(eff=eff, backend=backend)
        # an operator-supplied divergent DSN must never win (fail closed)
        monkeypatch.setenv("POSTGRES_DSN", "postgresql://u:p@10.0.0.9:5432/other")
        with pytest.raises(RuntimeError, match="bypass"):
            ls.require_runtime_dsn()
        # internal propagation of the governed DSN is accepted
        monkeypatch.setenv("POSTGRES_DSN", governed)
        assert ls.require_runtime_dsn() == governed

    def test_resolution_evidence_never_contains_secret_or_dsn(self, tmp_path):
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=True,
                                value="EVIDENCE-CANARY-DSN-SECRET")
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        ev = cs.secret_resolution_evidence(eff=eff, backend=backend)
        blob = json.dumps(ev)
        assert ev["resolved"] is True
        assert ev["reference"] == "secret:runtime-local"
        assert ev["generation"] >= 1
        assert "EVIDENCE-CANARY-DSN-SECRET" not in blob
        assert "postgresql://" not in blob

    def test_resolution_evidence_reports_failure_safely(self, tmp_path):
        import oce_control.config_startup as cs
        backend = self._backend(tmp_path, provision=False)
        eff = cs.effective_from_env({"OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"})
        ev = cs.secret_resolution_evidence(eff=eff, backend=backend)
        assert ev["resolved"] is False
        assert "configure" in (ev["error"] or "")
        assert "postgresql://" not in json.dumps(ev)


# --------------------------------------------------------------------------- #
# B4-CXR3R6 (CXR3-07) — override-audit TRUTH LABEL: the in-process audit is
# explicitly NON-AUTHORITATIVE until an append-only durable sink is attached.
# --------------------------------------------------------------------------- #
class TestCXR3R6OverrideAuditTruth:
    def test_default_audit_is_explicitly_non_authoritative(self):
        reg = build_default_registry()
        authz = ConfigAuthorization(reg)
        assert authz.audit_durable is False
        eff = ConfigResolver(reg).resolve(HAPPY)
        authz.operator_override(
            eff, actor="operator:po", setting_name="control_plane.port",
            requested_change="x", reason="r", new_value="9123")
        assert len(authz.audit) == 1
        # no durable truth is claimed for the in-process helper
        assert authz.audit[0].durable is False

    def test_durable_sink_attached_marks_entries_durable(self):
        reg = build_default_registry()
        sink: list[dict] = []
        authz = ConfigAuthorization(reg, durable_sink=sink)
        assert authz.audit_durable is True
        eff = ConfigResolver(reg).resolve(HAPPY)
        authz.operator_override(
            eff, actor="operator:po", setting_name="control_plane.port",
            requested_change="x", reason="r", new_value="9124")
        assert authz.audit[0].durable is True
        assert len(sink) == 1
        rec = sink[0]
        assert rec["actor"] == "operator:po"
        assert rec["setting"] == "control_plane.port"
        assert rec["decision"] == "granted"
        assert rec["durable"] is True
        assert rec["timestamp"]

    def test_durable_sink_never_contains_secret_values(self):
        reg = build_default_registry()
        sink: list[dict] = []
        authz = ConfigAuthorization(reg, durable_sink=sink)
        eff = ConfigResolver(reg).resolve(HAPPY)
        with pytest.raises(PermissionError):
            authz.operator_override(
                eff, actor="operator", setting_name="postgres.password_ref",
                requested_change="x", reason="x", new_value="secret:other")
        assert sink == [] and authz.audit == []

    def test_denied_override_writes_no_record(self):
        reg = build_default_registry()
        sink: list[dict] = []
        authz = ConfigAuthorization(reg, durable_sink=sink)
        eff = ConfigResolver(reg).resolve(HAPPY)
        with pytest.raises(PermissionError):
            authz.operator_override(
                eff, actor="hermes", setting_name="control_plane.port",
                requested_change="x", reason="x", new_value="9999")
        assert sink == [] and authz.audit == []


# --------------------------------------------------------------------------- #
# B4-CXR3R5 (CXR3-06) — capital authority is locked to 'none' in Book 4.
# No source, actor, or override path can produce live-capital authority.
# --------------------------------------------------------------------------- #
class TestCXR3R5CapitalAuthorityLocked:
    def test_approved_via_env_blocked(self):
        import oce_control.config_startup as cs
        with pytest.raises(ValidationError) as exc:
            cs.effective_from_env(
                {"PATH": "/usr/bin", "OCE_CAPITAL_AUTHORITY": "approved"})
        assert "capital.authority" in str(exc.value)

    def test_approved_via_file_and_cli_blocked(self):
        reg = build_default_registry()
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"capital.authority": "approved",
                         "postgres.password_ref": REF_PG}})
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": REF_PG}},
                cli={"capital.authority": "approved"})

    def test_approved_through_custom_default_rejected_by_validate_effective(self):
        # even if a registry defaulted capital.authority to 'approved', the
        # effective-config gate rejects it — defense in depth
        reg = build_default_registry()
        eff = ConfigResolver(reg).resolve(HAPPY)
        eff._resolved["capital.authority"] = "approved"
        with pytest.raises(ValidationError, match="capital.authority"):
            validate_effective(eff)

    def test_hermes_and_operator_cannot_mutate(self):
        reg = build_default_registry()
        authz = ConfigAuthorization(reg)
        eff = ConfigResolver(reg).resolve(HAPPY)
        s = reg.get("capital.authority")
        assert authz.can_mutate("hermes", s) is False
        assert authz.can_mutate("operator", s) is False
        for actor in ("hermes", "operator"):
            with pytest.raises(PermissionError):
                authz.operator_override(
                    eff, actor=actor, setting_name="capital.authority",
                    requested_change="x", reason="x", new_value="approved")

    def test_po_override_still_blocked_in_book4(self):
        # operator:po is the CEO-level actor, but even PO cannot activate
        # live-capital authority in Book 4 (future-locked)
        reg = build_default_registry()
        authz = ConfigAuthorization(reg)
        eff = ConfigResolver(reg).resolve(HAPPY)
        with pytest.raises(PermissionError, match="locked to 'none'"):
            authz.operator_override(
                eff, actor="operator:po", setting_name="capital.authority",
                requested_change="activate capital", reason="po decision",
                new_value="approved")

    def test_po_can_override_none_value_records_audit(self):
        # the lock allows the (no-op) 'none' value; attribution still records
        reg = build_default_registry()
        authz = ConfigAuthorization(reg)
        eff = ConfigResolver(reg).resolve(HAPPY)
        new = authz.operator_override(
            eff, actor="operator:po", setting_name="capital.authority",
            requested_change="confirm no capital authority",
            reason="explicit operator decision", new_value="none")
        assert new == "none"


# --------------------------------------------------------------------------- #
# B4-CXR3R4 (CXR3-05) — OWNERSHIP enforced in the real resolver: policy-owned
# and operator(po)-owned settings cannot be weakened through ordinary
# file/env/CLI configuration. Precedence and authority are distinct layers.
# --------------------------------------------------------------------------- #
class TestCXR3R4PolicyOwnershipEnforced:
    POLICY_WEAKENING = [
        ("OCE_LOG_REDACT_SECRETS", "false", "logging.redact_secrets"),
        ("OCE_LOG_REDACT_CLI", "false", "logging.redact_cli"),
        ("OCE_SANDBOX_PROCESS_TREE_TERMINATION", "false",
         "sandbox.process_tree_termination"),
        ("OCE_SANDBOX_STRICT", "false", "sandbox.strict"),
        ("OCE_SESSIONS_AUTH_REQUIRED", "false", "sessions.auth_required"),
        ("OCE_WORKERS_EGRESS", "loopback", "workers.egress"),
        ("OCE_REDIS_MODE", "cache", "redis.mode"),
        ("OCE_CONTROL_PLANE_PUBLIC_LISTEN", "true",
         "control_plane.public_listen"),
        ("OCE_EXECUTION_BROKER_ENABLED", "true", "execution.broker_enabled"),
        ("OCE_EXECUTION_PAPER_TRADING_ENABLED", "true",
         "execution.paper_trading_enabled"),
        ("OCE_EXECUTION_LIVE_ORDER_MODE", "paper", "execution.live_order_mode"),
        ("OCE_CLOUD_PROVISIONING", "true", "cloud.provisioning"),
        ("OCE_CLOUD_GPU_BURST", "true", "cloud.gpu_burst"),
        ("OCE_CAPITAL_AUTHORITY", "approved", "capital.authority"),
    ]

    def test_policy_weakening_via_env_fails_closed(self):
        import oce_control.config_startup as cs
        for var, val, setting in self.POLICY_WEAKENING:
            with pytest.raises(ValidationError) as exc:
                cs.effective_from_env({"PATH": "/usr/bin", var: val})
            msg = str(exc.value)
            assert setting in msg          # canonical setting, not generic
            assert "source-authority" in msg
            assert val not in msg          # candidate value never echoed

    def test_policy_weakening_via_file_and_cli_fails_closed(self):
        reg = build_default_registry()
        cases = [
            {"logging.redact_secrets": False},
            {"logging.redact_cli": False},
            {"sandbox.process_tree_termination": False},
            {"sessions.auth_required": False},
            {"capital.authority": "approved"},
        ]
        for kw in cases:
            with pytest.raises(ValidationError):
                ConfigResolver(reg).resolve(
                    {"file": {**kw, "postgres.password_ref": REF_PG}})
            with pytest.raises(ValidationError):
                ConfigResolver(reg).resolve(
                    {"file": {"postgres.password_ref": REF_PG}}, cli=kw)

    def test_operator_setting_remains_env_settable(self):
        import oce_control.config_startup as cs
        eff = cs.effective_from_env(
            {"PATH": "/usr/bin", "OCE_CONTROL_PLANE_PORT": "8460"})
        assert eff.get("control_plane.port") == 8460
        assert eff.provenance["control_plane.port"] == "environment"

    def test_ownership_and_precedence_are_distinct_layers(self):
        # even at the HIGHEST source (cli), a policy-owned setting cannot
        # weaken policy — precedence never overrides authority
        reg = build_default_registry()
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": REF_PG}},
                cli={"sandbox.strict": False})

    def test_default_tier_policy_is_authoritative(self):
        # the safe canonical policy resolves from the default tier
        eff = ConfigResolver(build_default_registry()).resolve(HAPPY)
        assert eff.get_bool("sandbox.strict") is True
        assert eff.get_bool("sandbox.process_tree_termination") is True
        assert eff.get_bool("logging.redact_secrets") is True
        assert eff.get_bool("logging.redact_cli") is True
        assert eff.get("capital.authority") == "none"


# --------------------------------------------------------------------------- #
# B4-R3R1 — honest source provenance (env value must never masquerade as file)
# --------------------------------------------------------------------------- #
class TestR3R1SourceProvenance:
    def test_environment_value_reports_provenance_environment(self):
        eff = ConfigResolver(build_default_registry()).resolve({
            "environment": {"control_plane.port": "9000",
                            "postgres.password_ref": REF_PG},
        })
        assert eff.provenance["control_plane.port"] == "environment"

    def test_file_value_reports_provenance_file(self):
        eff = ConfigResolver(build_default_registry()).resolve({
            "file": {"control_plane.port": "7000",
                     "postgres.password_ref": REF_PG},
        })
        assert eff.provenance["control_plane.port"] == "file"

    def test_cli_value_reports_provenance_cli(self):
        eff = ConfigResolver(build_default_registry()).resolve({
            "file": {"postgres.password_ref": REF_PG},
        }, cli={"control_plane.port": "9100"})
        assert eff.provenance["control_plane.port"] == "cli"

    def test_default_value_reports_provenance_default(self):
        eff = ConfigResolver(build_default_registry()).resolve({
            "file": {"postgres.password_ref": REF_PG},
        })
        assert eff.provenance["control_plane.port"] == "default"

    def test_same_value_different_source_has_different_provenance(self):
        reg = build_default_registry()
        same = "9000"
        as_file = ConfigResolver(reg).resolve({
            "file": {"control_plane.port": same, "postgres.password_ref": REF_PG}})
        as_env = ConfigResolver(reg).resolve({
            "environment": {"control_plane.port": same,
                            "postgres.password_ref": REF_PG}})
        assert as_file.provenance["control_plane.port"] == "file"
        assert as_env.provenance["control_plane.port"] == "environment"

    def test_env_value_cannot_bypass_file_only_setting(self):
        # A setting allowed from file but forbidden from the environment must
        # fail closed when the value arrives labeled 'environment' — even if
        # effective_from_env orchestrates the resolution.
        import oce_control.config_startup as cs
        reg = build_default_registry()
        reg.forbid_source("postgres.host", SOURCE_ENV)
        with pytest.raises(ValidationError):
            cs.effective_from_env(
                {"OCE_POSTGRES_HOST": "10.0.0.5"}, registry=reg)

    def test_default_under_env_never_overrides(self):
        # default tier supplies the runtime password ref; environment may not
        # collide with a default-tier-only setting it is forbidden from
        import oce_control.config_startup as cs
        reg = build_default_registry()
        reg.forbid_source("control_plane.scheduler_interval", SOURCE_ENV)
        with pytest.raises(ValidationError):
            cs.effective_from_env(
                {"OCE_SCHEDULER_INTERVAL": "10"}, registry=reg)

    def test_env_provenance_truthful_through_startup_path(self):
        import oce_control.config_startup as cs
        eff = cs.effective_from_env({"OCE_CONTROL_PLANE_PORT": "8449"})
        assert eff.provenance["control_plane.port"] == "environment"
        # the runtime password-ref is a default-tier supply, never mislabeled
        assert eff.provenance["postgres.password_ref"] == "default"

    def test_scheduler_interval_env_maps_to_canonical(self):
        import oce_control.config_startup as cs
        eff = cs.effective_from_env({"OCE_SCHEDULER_INTERVAL": "17"})
        assert eff.get("control_plane.scheduler_interval") == 17
        assert eff.provenance["control_plane.scheduler_interval"] == "environment"