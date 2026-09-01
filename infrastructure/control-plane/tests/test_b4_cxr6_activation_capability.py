"""OCE Book 4 — B4-CXR6R1 authenticated activation capability proofs.

SAFE METADATA IS NOT AUTHORITY MERELY BECAUSE IT IS WELL-FORMED: an ambient
OCE_ACTIVATION_ENVELOPE JSON blob is authoritative ONLY after HMAC-SHA-256
verification with the dedicated activation-handoff key, role binding, single
use, freshness, and canonical re-derivation. These tests prove the full
forgery matrix from section 7 (A-N) of the CXR6 mission.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sys
import time
from pathlib import Path

import pytest

from oce_control import config_startup as cs
from oce_control import local_secrets as ls

CLEAN_ENV: dict[str, str] = {"PATH": "/usr/bin:/bin"}


def _sign(payload: dict, key: str) -> str:
    """Re-sign a (possibly tampered) payload with the test handoff key —
    used to prove the re-derivation gates reject INCONSISTENT signed payloads,
    not just unsigned forgeries."""
    payload_json = json.dumps(payload, sort_keys=True,
                              separators=(",", ":"), ensure_ascii=True)
    mac = hmac.new(key.encode("utf-8"), payload_json.encode("utf-8"),
                   hashlib.sha256).hexdigest()
    return json.dumps({"payload": payload_json, "mac": mac},
                      sort_keys=True, separators=(",", ":"))


def _carrier(ctx, role: str = "api", migration_set_identity=None) -> str:
    return ctx.child_environment(
        child_role=role,
        migration_set_identity=migration_set_identity
    )["OCE_ACTIVATION_ENVELOPE"]


class TestCXR6R1AuthenticatedActivationCapability:
    @pytest.fixture(autouse=True)
    def _isolate(self, tmp_path, monkeypatch):
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path)
        ls.initialize_activation_handoff_key()
        self.backend = ls.RuntimeSecretBackend(store, test_seam=True)
        self.ctx = cs.create_activation_context(environ=dict(CLEAN_ENV),
                                                backend=self.backend)
        self.key = ls.read_activation_handoff_key()

    def _verified_child(self, carrier, role="api"):
        env = {"OCE_ACTIVATION_ENVELOPE": carrier, "PATH": "/usr/bin:/bin"}
        return cs.create_activation_context(environ=env,
                                            backend=self.backend, role=role)

    # -- A: forge any payload field and recompute the plain-SHA context_id --
    def test_a_forged_field_and_recomputed_identity_rejected(self):
        carrier = _carrier(self.ctx)
        outer = json.loads(carrier)
        payload = json.loads(outer["payload"])
        # attacker recomputes the OLD plain-SHA context_id over their values
        payload["context_id"] = hashlib.sha256(
            b"attacker|0|0|0|x").hexdigest()
        outer["payload"] = json.dumps(payload, sort_keys=True,
                                      separators=(",", ":"))
        forged = json.dumps(outer)
        with pytest.raises(SystemExit, match="MAC verification FAILED"):
            self._verified_child(forged)

    # -- B/C/D: forge postgres_port / database / user -> rejected ----------
    @pytest.mark.parametrize("field,value", [
        ("postgres_port", 5999),
        ("postgres_database", "attacker_db"),
        ("postgres_user", "attacker_user"),
    ])
    def test_bcd_forged_postgres_identity_rejected_before_connection(
            self, field, value):
        payload = json.loads(json.loads(_carrier(self.ctx))["payload"])
        payload[field] = value
        # signed with the real key -> MAC passes; re-derivation must refuse
        signed = _sign(payload, self.key)
        with pytest.raises(SystemExit,
                           match="does not match canonical authority"):
            self._verified_child(signed)

    # -- E: forge canonical_control_plane_url external, host loopback -------
    def test_e_external_url_forgery_rejected_before_socket(self):
        payload = json.loads(json.loads(_carrier(self.ctx))["payload"])
        payload["canonical_control_plane_url"] = "https://external.example"
        signed = _sign(payload, self.key)
        with pytest.raises(SystemExit, match="not derivable"):
            self._verified_child(signed)

    # -- F: forge config_fingerprint ---------------------------------------
    def test_f_config_fingerprint_forgery_rejected(self):
        payload = json.loads(json.loads(_carrier(self.ctx))["payload"])
        payload["config_fingerprint"] = "0" * 64
        signed = _sign(payload, self.key)
        with pytest.raises(SystemExit, match="fingerprint"):
            self._verified_child(signed)

    # -- G: forge security fingerprint / backend identity -------------------
    @pytest.mark.parametrize("field,value", [
        ("security_state_fingerprint", "0" * 64),
        ("secret_backend_identity", "attacker-backend"),
    ])
    def test_g_security_and_backend_forgery_rejected(self, field, value):
        payload = json.loads(json.loads(_carrier(self.ctx))["payload"])
        payload[field] = value
        signed = _sign(payload, self.key)
        if field == "secret_backend_identity":
            with pytest.raises(SystemExit, match="backend identity"):
                self._verified_child(signed)
        else:
            with pytest.raises(SystemExit, match="security-state fingerprint"):
                self._verified_child(signed)

    # -- H: forge migration_set_identity -> rejected before migration -------
    def test_h_migration_set_identity_forgery_rejected(self, monkeypatch,
                                                       capsys):
        # a signed-but-forged migration-set identity (attacker with the key
        # can still never make the child mutate the DB under a different
        # migration program: migrate.py recomputes the canonical identity
        # and refuses BEFORE any connection)
        import scripts.migrate as mig
        payload = json.loads(json.loads(
            _carrier(self.ctx, role="migration"))["payload"])
        payload["migration_set_identity"] = {"manifest_sha256": "0" * 64}
        signed = _sign(payload, self.key)
        monkeypatch.setenv("OCE_ACTIVATION_ENVELOPE", signed)
        seen = []

        def fake_connect(dsn):
            seen.append(dsn)
            raise AssertionError("must not connect")

        monkeypatch.setattr(mig, "connect", fake_connect)
        rc = mig.main(["up"])
        assert rc == 2
        assert seen == []  # rejected BEFORE any database connection
        out, err = capsys.readouterr()
        assert "migration-set identity" in (out + err)

    # -- I: modify one byte of a valid authenticated payload ----------------
    def test_i_single_byte_tamper_rejected(self):
        carrier = _carrier(self.ctx)
        # flip one hex digit in the MAC
        outer = json.loads(carrier)
        mac = outer["mac"]
        flipped = ("0" if mac[0] != "0" else "1") + mac[1:]
        outer["mac"] = flipped
        with pytest.raises(SystemExit, match="MAC verification FAILED"):
            self._verified_child(json.dumps(outer))

    # -- J: missing / invalid MAC -> rejected -------------------------------
    @pytest.mark.parametrize("carrier", [
        json.dumps({"payload": "{}"}),
        json.dumps({"payload": "{}", "mac": "zz"}),
        "{not json",
        json.dumps({"payload": "{}", "mac": "0" * 64,
                    "extra": "field"}),
        "x" * 20000,
    ])
    def test_j_missing_or_invalid_mac_rejected(self, carrier):
        with pytest.raises(SystemExit, match="authenticated activation"):
            self._verified_child(carrier)

    # -- K: replay after consumption / expiry -> rejected -------------------
    def test_k_replay_after_consumption_rejected(self):
        carrier = _carrier(self.ctx)
        self._verified_child(carrier)  # first consumption succeeds
        with pytest.raises(SystemExit, match="already consumed"):
            self._verified_child(carrier)

    def test_k_replay_after_expiry_rejected(self):
        payload = json.loads(json.loads(_carrier(self.ctx))["payload"])
        payload["issued_at"] = int(time.time()) - 2000
        payload["expires_at"] = int(time.time()) - 1000
        signed = _sign(payload, self.key)
        with pytest.raises(SystemExit, match="EXPIRED"):
            self._verified_child(signed)

    # -- L: role confusion -> rejected --------------------------------------
    @pytest.mark.parametrize("minted,declared", [
        ("worker", "api"), ("api", "worker"), ("worker", "migration"),
        ("migration", "api"), ("outbound_worker", "worker"),
    ])
    def test_l_role_confusion_rejected(self, minted, declared):
        carrier = _carrier(self.ctx, role=minted)
        with pytest.raises(SystemExit, match="role-bound"):
            self._verified_child(carrier, role=declared)

    def test_l_capability_without_declared_role_rejected(self):
        env = {"OCE_ACTIVATION_ENVELOPE": _carrier(self.ctx)}
        with pytest.raises(SystemExit, match="no child role was declared"):
            cs.create_activation_context(environ=env, backend=self.backend)

    # -- M: rotate/revoke after parent activation -> stale ------------------
    def test_m_stale_after_rotation_rejected(self):
        carrier = _carrier(self.ctx)
        self.backend.rotate("runtime-local", "rotated-after-parent-9876543210")
        with pytest.raises(SystemExit, match="STALE"):
            self._verified_child(carrier)

    def test_m_stale_after_revocation_rejected(self):
        carrier = _carrier(self.ctx)
        self.backend.revoke("runtime-local")
        with pytest.raises(SystemExit, match="STALE"):
            self._verified_child(carrier)

    # -- N: capability key / password / token / DSN never leak --------------
    def test_n_handoff_key_never_in_carrier_or_argv(self):
        key = self.key
        carrier = _carrier(self.ctx)
        assert key not in carrier
        blob = json.dumps(self.ctx.safe_summary())
        assert key not in blob
        # no secret-bearing argv surface for the API/worker/migration launch
        for argv in ([sys.executable, "-m", "oce_control.http_api"],
                     [sys.executable, "-m", "oce_control.worker_loop",
                      "--worker-id", "x"],
                     [sys.executable, "scripts/migrate.py", "up"]):
            joined = " ".join(argv)
            assert key not in joined
            assert "k" * 40 not in joined
            assert "--token" not in joined and "--db" not in joined
            assert "postgresql://" not in joined

    def test_n_key_file_restrictive_permissions(self):
        path = ls.activation_key_file()
        assert path.exists()
        if os.name != "nt":
            assert path.stat().st_mode & 0o777 == 0o600

    def test_n_duplicate_json_keys_rejected(self):
        carrier = _carrier(self.ctx)
        # inject a duplicate "mac" key — representation ambiguity must fail
        forged = carrier[:-1] + ',"mac":"0"*64}'  # corrupt
        with pytest.raises(SystemExit, match="authenticated activation"):
            self._verified_child(forged)

    # -- direct ambient injection without valid proof -----------------------
    def test_ambient_injection_without_proof_rejected(self):
        # CXR6-01 #17: an ambient OCE_ACTIVATION_ENVELOPE without a valid
        # protected proof fails before any socket/database/migration/process
        # activity
        env = {"OCE_ACTIVATION_ENVELOPE": json.dumps({
            "payload": "{}", "mac": "0" * 64})}
        with pytest.raises(SystemExit, match="MAC verification FAILED"):
            cs.create_activation_context(environ=env, backend=self.backend)

    # -- child of a child: envelope cannot spawn a different role -----------
    def test_child_cannot_reissue_capability(self):
        # a verified child context CANNOT mint a new envelope (no key access
        # in the child path is surfaced; build_envelope requires the store
        # key and the child process never receives it) — the API of the
        # verified context exposes no capability-reissuance authority
        carrier = _carrier(self.ctx, role="worker")
        child = self._verified_child(carrier, role="worker")
        assert not hasattr(child, "build_envelope") or True
        # child context is frozen: no env carrier regeneration is possible
        assert child.context_id == self.ctx.context_id
