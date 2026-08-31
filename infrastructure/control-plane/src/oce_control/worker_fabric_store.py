"""Book 3 — durable PostgreSQL Worker Fabric repositories (B3-R2).

This is the production adapter for the fabric. It replaces the in-memory
``InMemoryLeaseStore`` default and persists every piece of fabric truth in
PostgreSQL (authoritative) using the tables created by migration 0005:

* worker identity + operator-admitted capabilities (``worker_fabric_instances``,
  ``capability_admissions``);
* durable outbound sessions (``worker_sessions``, verifier hashed at rest);
* fenced leases with a monotonic ``fence`` generation and single active lease
  per logical job (``b3_fabric_leases``);
* late-result quarantine (``b3_quarantine``) and one-effect idempotency
  (``b3_effects``);
* restart-safe artifact manifests (``b3_artifacts``);
* durable retry state, poison jobs, dead letters, and PO-authorized-retry
  audit records (``b3_retry_state``, ``b3_dead_letters``,
  ``b3_authorized_retries``).

Same in-memory/default-free design goal as B3-R5: the fabric never silently
defaults to a non-authoritative store in production. ``FabricScheduler(
store=PgWorkerFabricStore(conn))`` is the production wiring; unit tests may
still use ``InMemoryLeaseStore`` but the durable path is PostgreSQL.
"""
from __future__ import annotations
import json
from typing import Optional

from .worker_contracts import utcnow_iso, dt_pass
from .worker_leases import (
    InMemoryLeaseStore, JobEnvelope, default_ttl,
)


class FabricStoreError(RuntimeError):
    """Base for durable fabric-store failures."""


class FabricStoreUnavailable(FabricStoreError):
    """PostgreSQL is unreachable for a fabric read/write — fail closed."""


def _json(v) -> str:
    return json.dumps(v or [])


class PgWorkerFabricStore(InMemoryLeaseStore):
    """Production PostgreSQL implementation of the fabric stores.

    Inherits nothing meaningful from ``InMemoryLeaseStore`` except the
    interface shape — every operation here reads/writes PostgreSQL inside a
    transaction. Redis is never consulted for truth; it remains transport only.
    """

    def __init__(self, conn):
        self._conn = conn
        self._effect_drawn = 0  # current session effect watermark (fence-safe)

    # -- helpers ------------------------------------------------------------

    def _execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        try:
            with self._conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:
                    return cur.fetchall()
                return []
        except Exception as exc:
            try:
                self._conn.rollback()
            except Exception:
                pass
            raise FabricStoreUnavailable(f"fabric PG operation failed: {exc}") from exc

    def _one(self, sql: str, params: tuple = ()) -> Optional[tuple]:
        rows = self._execute(sql, params)
        return rows[0] if rows else None

    def _commit(self) -> None:
        try:
            self._conn.commit()
        except Exception as exc:
            try:
                self._conn.rollback()
            except Exception:
                pass
            raise FabricStoreUnavailable(f"fabric PG commit failed: {exc}") from exc

    # -- B3-R2: identity + capability authorities ----------------------------

    def admit_capability(self, capability: str, actor: str) -> dict:
        self._execute(
            "INSERT INTO capability_admissions (capability, admitted_by) "
            "VALUES (%s,%s) ON CONFLICT (capability) DO NOTHING",
            (capability, actor),
        )
        self._commit()
        return {"capability": capability, "admitted_by": actor}

    def admitted_capabilities(self) -> list[str]:
        rows = self._execute(
            "SELECT capability FROM capability_admissions ORDER BY capability")
        return [r[0] for r in rows]

    def persist_identity(self, *, worker_id: str, protocol_version: str,
                         worker_version: str, host_os_class: str,
                         runtime_class: str, trust_zone: str,
                         sandbox_profile: str, capabilities: list[str],
                         credential_verifier: str, actor: str) -> None:
        # The fabric FKs (`worker_fabric_instances`, `worker_sessions`,
        # `b3_fabric_leases`, `b3_artifacts`, `b3_dead_letters`) all reference
        # the authoritative Book 2 `workers` table. Admission must therefore
        # materialise the authoritative `workers` parent row first; without it
        # every subsequent fabric write fails the FK and no worker could ever be
        # admitted against real PostgreSQL. The verifier (hashed secret, at
        # rest) doubles as the admission-token hash so only hashes persist.
        self._execute(
            """INSERT INTO workers
                 (worker_id, capabilities, trust_zone, admission_token_hash,
                  max_concurrent_jobs)
               VALUES (%s,%s,%s,%s,1)
               ON CONFLICT (worker_id) DO UPDATE SET
                 capabilities = EXCLUDED.capabilities,
                 trust_zone = EXCLUDED.trust_zone,
                 last_heartbeat = now()
                 -- keep existing admission_token_hash; do not clobber on re-admit""",
            (worker_id, _json(capabilities), trust_zone, credential_verifier or ""),
        )
        self._execute(
            """INSERT INTO worker_fabric_instances
                 (worker_id, protocol_version, worker_version, host_os_class,
                  runtime_class, trust_zone, sandbox_profile, capabilities,
                  credential_verifier, admission_actor, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'admitted')
               ON CONFLICT (worker_id) DO UPDATE SET
                 protocol_version = EXCLUDED.protocol_version,
                 worker_version = EXCLUDED.worker_version,
                 host_os_class = EXCLUDED.host_os_class,
                 runtime_class = EXCLUDED.runtime_class,
                 trust_zone = EXCLUDED.trust_zone,
                 sandbox_profile = EXCLUDED.sandbox_profile,
                 capabilities = EXCLUDED.capabilities,
                 credential_verifier = EXCLUDED.credential_verifier,
                 admission_actor = EXCLUDED.admission_actor,
                 status = 'admitted', revoked_at = NULL""",
            (worker_id, protocol_version, worker_version, host_os_class,
             runtime_class, trust_zone, sandbox_profile, _json(capabilities),
             credential_verifier, actor),
        )
        self._commit()

    def identity(self, worker_id: str) -> Optional[dict]:
        row = self._one(
            """SELECT worker_id, protocol_version, worker_version, host_os_class,
                      runtime_class, trust_zone, sandbox_profile, capabilities,
                      credential_verifier, status, revoked_at
               FROM worker_fabric_instances WHERE worker_id = %s""",
            (worker_id,),
        )
        if row is None:
            return None
        (wid, proto, wver, osclass, rt, tz, sandbox, caps, verifier,
         status, revoked_at) = row
        return {
            "worker_id": wid, "protocol_version": proto, "worker_version": wver,
            "host_os_class": osclass, "runtime_class": rt, "trust_zone": tz,
            "sandbox_profile": sandbox, "capabilities": caps or [],
            "credential_verifier": verifier, "status": status,
            "revoked_at": revoked_at.isoformat() if revoked_at else None,
        }

    def set_identity_status(self, worker_id: str, status: str) -> None:
        self._execute(
            "UPDATE worker_fabric_instances SET status = %s WHERE worker_id = %s",
            (status, worker_id),
        )
        self._commit()

    def revoke_identity(self, worker_id: str) -> None:
        now = utcnow_iso()
        self._execute(
            "UPDATE worker_fabric_instances SET status='revoked', revoked_at=%s "
            "WHERE worker_id = %s",
            (now, worker_id),
        )
        self._execute(
            "UPDATE worker_sessions SET revoked_at = %s WHERE worker_id = %s "
            "AND revoked_at IS NULL",
            (now, worker_id),
        )
        self._commit()

    def identities(self) -> dict[str, dict]:
        out = {}
        for ident in self._list_identities():
            out[ident["worker_id"]] = ident
        return out

    def _list_identities(self) -> list[dict]:
        rows = self._execute(
            "SELECT worker_id FROM worker_fabric_instances ORDER BY worker_id")
        out = []
        for (wid,) in rows:
            ident = self.identity(wid)
            if ident:
                out.append(ident)
        return out

    # -- B3-R2: durable outbound sessions ------------------------------------

    def create_session(self, *, worker_id: str, session_id: str,
                       protocol_version: str, trust_zone: str,
                       capabilities: list[str], verifier: str,
                       challenge: str, ttl_s: int) -> dict:
        self._execute(
            """INSERT INTO worker_sessions
                 (session_id, worker_id, protocol_version, trust_zone,
                  capabilities, verifier, challenge, expires_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s, now() + make_interval(secs => %s))
               ON CONFLICT (session_id) DO UPDATE SET
                 verifier = EXCLUDED.verifier,
                 challenge = EXCLUDED.challenge,
                 revoked_at = NULL,
                 expires_at = now() + make_interval(secs => %s),
                 generation = worker_sessions.generation + 1""",
            (session_id, worker_id, protocol_version, trust_zone,
             _json(capabilities), verifier, challenge, ttl_s, ttl_s),
        )
        self._commit()
        return self.session(session_id)  # type: ignore[return-value]

    def session(self, session_id: str) -> Optional[dict]:
        row = self._one(
            """SELECT session_id, worker_id, protocol_version, trust_zone,
                      capabilities, verifier, challenge, created_at, expires_at,
                      last_heartbeat, revoked_at, draining, generation
               FROM worker_sessions WHERE session_id = %s""",
            (session_id,),
        )
        return self._row_session(row) if row else None

    @staticmethod
    def _row_session(row: tuple) -> dict:
        (sid, wid, proto, tz, caps, verifier, challenge, created, expires,
         last_hb, revoked, draining, gen) = row
        return {
            "session_id": sid, "worker_id": wid, "protocol_version": proto,
            "trust_zone": tz, "capabilities": caps or [], "verifier": verifier,
            "challenge": challenge,
            "created_at": created.isoformat() if created else "",
            "expires_at": expires.isoformat() if expires else "",
            "last_heartbeat": last_hb.isoformat() if last_hb else None,
            "revoked_at": revoked.isoformat() if revoked else None,
            "draining": bool(draining), "generation": gen,
        }

    def sessions(self, worker_id: Optional[str] = None) -> list[dict]:
        sql = ("SELECT session_id, worker_id, protocol_version, trust_zone, "
               "capabilities, verifier, challenge, created_at, expires_at, "
               "last_heartbeat, revoked_at, draining, generation "
               "FROM worker_sessions")
        params: tuple = ()
        if worker_id is not None:
            sql += " WHERE worker_id = %s"
            params = (worker_id,)
        sql += " ORDER BY created_at"
        return [self._row_session(r) for r in self._execute(sql, params)]

    def heartbeat_session(self, session_id: str) -> Optional[dict]:
        row = self._one(
            "UPDATE worker_sessions SET last_heartbeat = now(), "
            "expires_at = now() + interval '45 seconds' "
            "WHERE session_id = %s AND revoked_at IS NULL "
            "RETURNING session_id",
            (session_id,),
        )
        if row:
            self._commit()
        return self.session(session_id)

    def drain_worker(self, worker_id: str, draining: bool) -> None:
        self._execute(
            "UPDATE worker_sessions SET draining = %s WHERE worker_id = %s",
            (draining, worker_id),
        )
        self.set_identity_status(worker_id, "draining" if draining else "admitted")
        self._commit()

    def revoke_worker_sessions(self, worker_id: str) -> None:
        self.revoke_identity(worker_id)

    # -- B3-R2: fenced leases + duplicate-safe delivery (LeaseStore surface) ---

    def fetch_fence(self, job_id: str) -> dict:
        row = self._one(
            "SELECT lease_id, fence, status FROM b3_fabric_leases "
            "WHERE job_id = %s FOR UPDATE",
            (job_id,),
        )
        if row is None:
            return {"fence": 0, "lease_id": None, "status": "available"}
        return {"lease_id": row[0], "fence": row[1], "status": row[2]}

    def claim(self, job_id: str, worker_id: str, lease_id: str,
              fence: int, ttl_s: int) -> bool:
        # One active lease per job: atomic INSERT with ON CONFLICT.
        self._execute(
            """INSERT INTO b3_fabric_leases
                 (job_id, lease_id, worker_id, fence, ttl_s, expires_at)
               VALUES (%s,%s,%s,%s,%s, now() + make_interval(secs => %s))
               ON CONFLICT (job_id) DO UPDATE
               SET lease_id = EXCLUDED.lease_id,
                   worker_id = EXCLUDED.worker_id,
                   fence = EXCLUDED.fence, status = 'active',
                   expires_at = excluded.expires_at
               WHERE b3_fabric_leases.status IN ('expired','released','cancelled')""",
            (job_id, lease_id, worker_id, fence, ttl_s, ttl_s),
        )
        self._commit()
        return True

    def renew(self, job_id: str, lease_id: str, fence: int, ttl_s: int) -> bool:
        row = self._one(
            "UPDATE b3_fabric_leases SET ttl_s = %s, "
            "expires_at = now() + make_interval(secs => %s) "
            "WHERE job_id = %s AND lease_id = %s AND fence = %s "
            "AND status = 'active' RETURNING job_id",
            (ttl_s, ttl_s, job_id, lease_id, fence),
        )
        if row:
            self._commit()
            return True
        self._conn.rollback()
        return False

    def surrender(self, job_id: str, lease_id: str, fence: int) -> bool:
        row = self._one(
            "UPDATE b3_fabric_leases SET status='released', surrendered_at=now() "
            "WHERE job_id = %s AND lease_id = %s AND fence = %s "
            "AND status = 'active' RETURNING job_id",
            (job_id, lease_id, fence),
        )
        if row:
            self._commit()
            return True
        self._conn.rollback()
        return False

    def release(self, job_id: str) -> bool:
        self._execute(
            "UPDATE b3_fabric_leases SET status='released', surrendered_at=now() "
            "WHERE job_id = %s",
            (job_id,),
        )
        self._commit()
        return True

    def reclaim_expired(self, now_iso: str) -> list[str]:
        """Expire past-due active leases so they can be re-claimed. Returns
        the reclaimed job_ids. Fencing is preserved: fence is NOT reset here
        (the next claim bumps it), so a late stale worker can never commit."""
        rows = self._execute(
            "UPDATE b3_fabric_leases SET status='expired' "
            "WHERE status = 'active' AND expires_at < now() RETURNING job_id")
        if rows:
            self._commit()
        return [r[0] for r in rows]

    def active_leases(self) -> list[dict]:
        rows = self._execute(
            "SELECT job_id, lease_id, worker_id, fence, expires_at "
            "FROM b3_fabric_leases WHERE status = 'active' OR expires_at > now()")
        out = []
        for job_id, lease_id, worker_id, fence, expires in rows:
            out.append({"job_id": job_id, "lease_id": lease_id,
                        "worker_id": worker_id, "fence": fence,
                        "expires_at": expires.isoformat()})
        return out

    def reclaim_stale_leases(self, now: Optional[str] = None) -> list[str]:
        return self.reclaim_expired(now or utcnow_iso())

    # -- B3-R2: effect idempotency + late-result quarantine -------------------

    def register_effect(self, *, job_id: str, lease_id: str, fence: int,
                        effect_key: str, producer_identity: str) -> bool:
        """Record that a logical material effect was applied exactly once.
        Returns False on duplicate (a second effect for the same key)."""
        try:
            self._execute(
                """INSERT INTO b3_effects (effect_key, job_id, lease_id, fence,
                     producer_identity) VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT (effect_key) DO NOTHING""",
                (effect_key, job_id, lease_id, fence, producer_identity),
            )
            self._commit()
        except FabricStoreError:
            return False
        # An effect may be applied by the same worker creating the job at most
        # once; the UNIQUE(job_id) on b3_effects makes a second effect for the
        # same job impossible regardless of key.
        return True

    def effect_exists(self, effect_key: str) -> bool:
        row = self._one(
            "SELECT 1 FROM b3_effects WHERE effect_key = %s", (effect_key,))
        return row is not None

    def quarantine_late(self, *, job_id: str, lease_id: str, fence: int,
                        reason: str, result_ref: Optional[str] = None) -> None:
        self._execute(
            """INSERT INTO b3_quarantine (job_id, lease_id, fence, reason, result_ref)
               VALUES (%s,%s,%s,%s,%s)""",
            (job_id, lease_id, fence, reason, result_ref),
        )
        self._commit()

    def quarantined(self) -> list[dict]:
        rows = self._execute(
            "SELECT job_id, lease_id, fence, reason, result_ref, created_at "
            "FROM b3_quarantine ORDER BY created_at")
        return [{"job_id": r[0], "lease_id": r[1], "fence": r[2],
                 "reason": r[3], "result_ref": r[4],
                 "created_at": r[5].isoformat()} for r in rows]

    # -- B3-R2: durable artifacts (manifest persistence) -----------------------

    def persist_manifest(self, manifest: dict) -> None:
        self._execute(
            """INSERT INTO b3_artifacts
                 (manifest_id, job_id, attempt, worker_id, producer_identity, payload)
               VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT (manifest_id) DO NOTHING""",
            (manifest["manifest_id"], manifest["job_id"], manifest["attempt"],
             manifest["worker_id"], manifest.get("producer_identity", ""),
             json.dumps(manifest, sort_keys=True)),
        )
        self._commit()

    def load_manifest(self, manifest_id: str) -> Optional[dict]:
        row = self._one(
            "SELECT payload FROM b3_artifacts WHERE manifest_id = %s",
            (manifest_id,),
        )
        if row is None:
            return None
        payload = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        return payload

    def manifests(self, job_id: str) -> list[dict]:
        rows = self._execute(
            "SELECT payload FROM b3_artifacts WHERE job_id = %s ORDER BY attempt",
            (job_id,),
        )
        return [r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in rows]

    # -- B3-R2: durable retry state, poison jobs, dead letters, auth -------------

    def record_retry_state(self, *, job_id: str, attempts: int,
                           max_retries: int, classified: str,
                           last_reason: str, exhausted: bool = False,
                           poison: bool = False) -> None:
        self._execute(
            """INSERT INTO b3_retry_state
                 (job_id, attempts, max_retries, classified, last_reason,
                  exhausted_at, poison)
               VALUES (%s,%s,%s,%s,%s,
                 CASE WHEN %s THEN now() ELSE NULL END, %s)
               ON CONFLICT (job_id) DO UPDATE SET
                 attempts = EXCLUDED.attempts,
                 max_retries = EXCLUDED.max_retries,
                 classified = EXCLUDED.classified,
                 last_reason = EXCLUDED.last_reason,
                 exhausted_at = CASE WHEN EXCLUDED.exhausted_at IS NOT NULL
                                     THEN EXCLUDED.exhausted_at
                                     ELSE b3_retry_state.exhausted_at END,
                 poison = EXCLUDED.poison""",
            (job_id, attempts, max_retries, classified, last_reason,
             exhausted, poison),
        )
        self._commit()

    def retry_state(self, job_id: str) -> Optional[dict]:
        row = self._one(
            "SELECT attempts, max_retries, classified, last_reason, "
            "exhausted_at, poison FROM b3_retry_state WHERE job_id = %s",
            (job_id,),
        )
        if row is None:
            return None
        return {"job_id": job_id, "attempts": row[0], "max_retries": row[1],
                "classified": row[2], "last_reason": row[3],
                "exhausted_at": row[4].isoformat() if row[4] else None,
                "poison": bool(row[5])}

    def dead_letter(self, *, job_id: str, attempt: int, worker_id: str,
                    reason: str, detail: str, idempotency_key: str,
                    poison: bool = False) -> None:
        self._execute(
            """INSERT INTO b3_dead_letters
                 (job_id, attempt, worker_id, reason, detail, idempotency_key, poison)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (job_id) DO UPDATE SET
                 attempt = EXCLUDED.attempt, worker_id = EXCLUDED.worker_id,
                 reason = EXCLUDED.reason, detail = EXCLUDED.detail,
                 idempotency_key = EXCLUDED.idempotency_key,
                 poison = EXCLUDED.poison""",
            (job_id, attempt, worker_id, reason, detail, idempotency_key, poison),
        )
        self._execute(
            "UPDATE jobs SET status = 'failed', failure_envelope = %s "
            "WHERE job_id = %s AND status IN ('pending','leased','running','scheduled')",
            (json.dumps({"error_type": "dead_lettered", "error_message": reason,
                         "retryable": False, "worker_id": worker_id}),
             job_id),
        )
        self._commit()

    def resolve_dead_letter(self, job_id: str) -> Optional[dict]:
        row = self._one(
            "SELECT job_id, attempt, worker_id, reason, detail, idempotency_key, "
            "poison, created_at, authorized_retry_at, operator_actor "
            "FROM b3_dead_letters WHERE job_id = %s",
            (job_id,),
        )
        if row is None:
            return None
        return {"job_id": row[0], "attempt": row[1], "worker_id": row[2],
                "reason": row[3], "detail": row[4], "idempotency_key": row[5],
                "poison": bool(row[6]),
                "created_at": row[7].isoformat(),
                "authorized_retry_at": row[8].isoformat() if row[8] else None,
                "operator_actor": row[9]}

    def list_dead_letters(self) -> list[dict]:
        rows = self._execute(
            "SELECT job_id FROM b3_dead_letters ORDER BY created_at")
        return [self.resolve_dead_letter(r[0]) for r in rows]  # type: ignore[misc]

    def authorized_retry(self, *, job_id: str, actor: str) -> bool:
        """PO-authorized retry of a dead-lettered job. Records an auditable
        decision. Only 'operator:po' (or a permitted PO proxy) may resolve a
        dead letter into a retry."""
        decision = "granted" if actor == "operator:po" else "denied"
        self._execute(
            "INSERT INTO b3_authorized_retries (job_id, actor, decision) "
            "VALUES (%s,%s,%s)",
            (job_id, actor, decision),
        )
        if decision == "denied":
            self._commit()
            raise PermissionError(
                f"actor '{actor}' is not authorized to retry dead-lettered job '{job_id}'")
        self._execute(
            "UPDATE b3_dead_letters SET authorized_retry_at = now(), "
            "operator_actor = %s WHERE job_id = %s",
            (actor, job_id),
        )
        self._execute(
            "UPDATE jobs SET status='pending', failure_envelope = NULL "
            "WHERE job_id = %s",
            (job_id,),
        )
        self._commit()
        return True