"""P2-C04 — local identity, policy, authority qualification (directive §10-12)."""

from __future__ import annotations

import pytest

from qcae.core.decisions.authority import (
    AuthorityOutcome,
    AuthorityRequest,
    PolicyAction,
)
from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.authority import (
    LocalAuthorityProvider,
    policy_outcome_to_authority_outcome,
)
from qcae.infrastructure.persistence.sqlite_policy_log import (
    GOVERNANCE_DDL,
    SqlitePolicyDecisionLog,
)
from qcae.governance.standalone.identity import (
    IdentityKind,
    LocalIdentity,
    LocalIdentityProvider,
)
from qcae.governance.standalone.policy import (
    LocalPolicyEngine,
    PolicyDecisionType,
    PolicyEffect,
    PolicyRequest,
    PolicyRule,
    PolicySet,
)


def _policy_set(*extra_rules):
    rules = [
        PolicyRule(
            rule_id="allow-worker-discover",
            effect=PolicyEffect.ALLOW,
            action=PolicyAction.MAY_DISCOVER.value,
            principal_match="id-worker-*",
            reason="discovery worker may query configured providers",
        ),
        PolicyRule(
            rule_id="approval-for-sandbox-exec",
            effect=PolicyEffect.REQUIRE_APPROVAL,
            action=PolicyAction.MAY_EXECUTE_IN_SANDBOX.value,
            principal_match="id-worker-*",
            reason="sandbox execution requires operator approval",
        ),
        PolicyRule(
            rule_id="constrained-persist",
            effect=PolicyEffect.ALLOW_WITH_CONSTRAINTS,
            action=PolicyAction.MAY_PERSIST_REGISTRY_RECORD.value,
            principal_match="id-worker-*",
            constraints=("scope:candidate-metadata-only",),
            reason="persist only candidate metadata",
        ),
        PolicyRule(
            rule_id="deny-secrets",
            effect=PolicyEffect.DENY,
            action="may_access_production_credentials",
            reason="production credentials outside local authority",
        ),
    ]
    return PolicySet(
        policy_id="pol-standalone", policy_version="1.0.0",
        rules=tuple(rules) + tuple(extra_rules),
    )


def _engine(*first_rules):
    # first_rules precede the generic wildcards so first-match ordering is
    # under test control.
    return LocalPolicyEngine(PolicySet(
        policy_id="pol-standalone", policy_version="1.0.0",
        rules=tuple(first_rules) + _policy_set().rules,
    ))


def _request(action="may_discover", principal="id-worker-1", resource="cap-0001", **over):
    base = dict(action=action, principal=principal, resource=resource)
    base.update(over)
    return PolicyRequest(**base)


def _provider(conn):
    conn.executescript(GOVERNANCE_DDL)
    return LocalAuthorityProvider(
        _engine(), SqlitePolicyDecisionLog(conn),
        clock=lambda: "2026-09-13T00:00:00Z",
    )


class TestPolicyEngine:
    def test_allow(self):
        d = _engine().evaluate(_request(), decision_id="d1", created_at="t")
        assert d.decision is PolicyDecisionType.ALLOW
        assert d.rule_ref == "allow-worker-discover"

    def test_deny(self):
        d = _engine().evaluate(
            _request(action="may_access_production_credentials"),
            decision_id="d2", created_at="t",
        )
        assert d.decision is PolicyDecisionType.DENY

    def test_require_approval(self):
        d = _engine().evaluate(
            _request(action="may_execute_in_sandbox"),
            decision_id="d3", created_at="t",
        )
        assert d.decision is PolicyDecisionType.REQUIRE_APPROVAL

    def test_allow_with_constraints(self):
        d = _engine().evaluate(
            _request(action="may_persist_registry_record"),
            decision_id="d4", created_at="t",
        )
        assert d.decision is PolicyDecisionType.ALLOW_WITH_CONSTRAINTS
        assert d.constraints == ("scope:candidate-metadata-only",)

    def test_unknown_action_fails_closed(self):
        d = _engine().evaluate(
            _request(action="may_do_anything_i_want"),
            decision_id="d5", created_at="t",
        )
        assert d.decision is PolicyDecisionType.DENY
        assert d.rule_ref == "NO_MATCH"

    def test_wrong_principal_fails_closed(self):
        d = _engine().evaluate(
            _request(principal="id-attacker"),
            decision_id="d6", created_at="t",
        )
        assert d.decision is PolicyDecisionType.DENY
        assert d.rule_ref == "NO_MATCH"

    def test_decision_is_structured_and_complete(self):
        d = _engine().evaluate(_request(), decision_id="d7", created_at="t0")
        d.validate()
        assert d.policy_version == "1.0.0"
        assert d.principal and d.action and d.resource and d.reason

    def test_policy_round_trip(self):
        ps = _policy_set()
        restored = PolicySet.from_dict(ps.to_dict())
        assert restored == ps

    def test_policy_rejects_duplicate_rule_ids(self):
        with pytest.raises(QcaeValidationError, match="duplicate"):
            PolicySet(
                policy_id="p", policy_version="1",
                rules=(
                    PolicyRule(rule_id="r1", effect=PolicyEffect.DENY, action="a"),
                    PolicyRule(rule_id="r1", effect=PolicyEffect.DENY, action="b"),
                ),
            ).validate()

    def test_first_match_wins(self):
        engine = _engine(
            PolicyRule(
                rule_id="deny-specific-worker",
                effect=PolicyEffect.DENY,
                action=PolicyAction.MAY_DISCOVER.value,
                principal_match="id-worker-rogue",
                reason="rogue worker denied",
            )
        )
        d = engine.evaluate(
            _request(principal="id-worker-rogue"), decision_id="d8", created_at="t"
        )
        assert d.decision is PolicyDecisionType.DENY
        assert d.rule_ref == "deny-specific-worker"

    def test_engine_has_no_mutation_api(self):
        assert not hasattr(_engine(), "add_rule")
        assert not hasattr(_engine(), "modify_rule")
        assert not hasattr(_engine(), "remove_rule")


class TestAuthorityMapping:
    def test_mapping_table(self):
        from qcae.governance.standalone.policy import PolicyDecision

        def _dec(dt):
            return PolicyDecision(
                decision_id="x", decision=dt, principal="p", action="a",
                resource="r", policy_id="pol", policy_version="1",
                rule_ref="r1", reason="m",
            )

        assert policy_outcome_to_authority_outcome(
            _dec(PolicyDecisionType.ALLOW)
        ) is AuthorityOutcome.GRANT
        assert policy_outcome_to_authority_outcome(
            _dec(PolicyDecisionType.ALLOW_WITH_CONSTRAINTS)
        ) is AuthorityOutcome.GRANT
        assert policy_outcome_to_authority_outcome(
            _dec(PolicyDecisionType.REQUIRE_APPROVAL)
        ) is AuthorityOutcome.REQUEST_MORE_EVIDENCE
        assert policy_outcome_to_authority_outcome(
            _dec(PolicyDecisionType.DENY)
        ) is AuthorityOutcome.DENY

    def test_local_provider_implements_p0_protocol(self):
        from qcae.core.decisions.authority import AuthorityProvider
        from qcae.infrastructure.persistence.store_factory import open_metadata_db

        conn = open_metadata_db(":memory:")
        provider = _provider(conn)
        assert isinstance(provider, AuthorityProvider)

    def test_end_to_end_decision(self):
        from qcae.infrastructure.persistence.store_factory import open_metadata_db

        conn = open_metadata_db(":memory:")
        provider = _provider(conn)
        request = AuthorityRequest(
            request_id="req-00000001",
            action=PolicyAction.MAY_DISCOVER,
            subject_id="cap-0001",
            justification="find prior art",
            requested_by="id-worker-1",
        )
        decision = provider.decide(request)
        assert decision.outcome is AuthorityOutcome.GRANT
        assert decision.request_ref == "req-00000001"

        # Durable + retrievable.
        assert provider.logged_decisions_for("req-00000001")

        # Duplicate request rejected (append-oriented).
        with pytest.raises(QcaeValidationError, match="already exists"):
            provider.decide(request)

    def test_denied_action_is_denied_end_to_end(self):
        from qcae.infrastructure.persistence.store_factory import open_metadata_db

        conn = open_metadata_db(":memory:")
        provider = _provider(conn)
        request = AuthorityRequest(
            request_id="req-00000002",
            action=PolicyAction.MAY_EXECUTE_IN_SANDBOX,
            subject_id="cand-1",
            justification="run tests",
            requested_by="id-worker-1",
        )
        assert provider.decide(request).outcome is AuthorityOutcome.REQUEST_MORE_EVIDENCE


class TestIdentity:
    def test_operator_runtime_worker_registered(self):
        provider = LocalIdentityProvider()
        provider.register(LocalIdentity(identity_id="id-operator-1", kind=IdentityKind.OPERATOR))
        provider.register(LocalIdentity(identity_id="id-worker-1", kind=IdentityKind.WORKER))
        assert provider.get("id-runtime-local").kind is IdentityKind.RUNTIME
        assert provider.require("id-operator-1").kind is IdentityKind.OPERATOR

    def test_unknown_identity_fails_closed(self):
        provider = LocalIdentityProvider()
        with pytest.raises(QcaeValidationError, match="unknown identity"):
            provider.require("id-ghost")

    def test_current_identity_stable(self):
        provider = LocalIdentityProvider()
        provider.register(LocalIdentity(identity_id="id-worker-2", kind=IdentityKind.WORKER))
        provider.set_current("id-worker-2")
        assert provider.current_identity() == "id-worker-2"

    def test_duplicate_identity_rejected(self):
        provider = LocalIdentityProvider()
        provider.register(LocalIdentity(identity_id="id-op", kind=IdentityKind.OPERATOR))
        with pytest.raises(QcaeValidationError, match="already registered"):
            provider.register(LocalIdentity(identity_id="id-op", kind=IdentityKind.OPERATOR))

    def test_identity_round_trip(self):
        i = LocalIdentity(identity_id="id-1", kind=IdentityKind.WORKER, display_name="w")
        assert LocalIdentity.from_dict(i.to_dict()) == i
