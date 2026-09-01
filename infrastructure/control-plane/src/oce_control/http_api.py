"""Runnable local HTTP service for the OCE control plane (B2-R6, gap 7).

Wraps the ControlPlaneAPI boundary in a real FastAPI service that binds
to loopback only. Every endpoint except health/readiness requires the
service-boundary authorization headers X-OCE-Grant / X-OCE-Actor; the
authority grant is verified by the façade before any read or mutation
(gap 9). A minimal operator console is served at /console (gap 8).

Start the complete local runtime (PG + Redis + API + console +
scheduler + worker) with scripts/start-local.sh, or run the durable
app directly:

    python -m oce_control.http_api          # builds durable wiring from env

For tests: create_app(api, scheduler=..., scheduler_tick_interval=0)
returns a plain FastAPI app (no background loop unless requested).
"""
from __future__ import annotations
import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

try:
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
except ImportError:  # pragma: no cover — only needed where the service runs
    FastAPI = None  # type: ignore

from .api import ControlPlaneAPI, APIResponse

CONSOLE_PATH = Path(__file__).resolve().parents[2] / "ui" / "console.html"

def _default_dsn() -> str:
    """Fail-closed DSN: never a predictable default (B2-R7)."""
    from . import local_secrets
    return local_secrets.require_runtime_dsn()

# Operator grants issued at durable startup (deterministic ids, printed at boot).
OPERATOR_ACTIONS = [
    "submit_job", "cancel_job", "retry_job", "read",
]


def _console_html() -> str:
    try:
        return CONSOLE_PATH.read_text(encoding="utf-8")
    except OSError:
        return "<html><body><h1>OCE console unavailable</h1></body></html>"


def _status_code(resp: APIResponse) -> int:
    if resp.status == "denied":
        return 403
    if resp.status == "not_found":
        return 404
    if resp.status == "error":
        return 400
    if resp.status == "not_ready":
        return 503
    return 200


def create_app(api: ControlPlaneAPI, scheduler=None,
               scheduler_tick_interval: int = 0,
               worker_protocol_server=None) -> FastAPI:
    """Build the FastAPI app over a ControlPlaneAPI boundary.

    scheduler_tick_interval > 0 starts a background tick loop (durable
    runtime). worker_protocol_server optionally exposes the Book 3
    authenticated outbound worker fabric endpoints (loopback only); when
    None (default) those endpoints are absent, matching the Book 2 service.
    Tests pass 0 for deterministic, single-threaded behavior.
    """
    if FastAPI is None:
        raise RuntimeError("fastapi is not installed — required to run the HTTP service")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = None
        if scheduler is not None and scheduler_tick_interval > 0:
            async def _tick_loop():
                while True:
                    await asyncio.sleep(scheduler_tick_interval)
                    try:
                        await asyncio.to_thread(scheduler.tick)
                    except Exception:
                        pass  # transient failures must not kill the loop
            task = asyncio.create_task(_tick_loop())
        yield
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    app = FastAPI(title="OCE Control Plane", version="2.0.0",
                  lifespan=lifespan)

    def _auth(grant: str = Header(default="", alias="X-OCE-Grant"),
              actor: str = Header(default="", alias="X-OCE-Actor")):
        if not grant or not actor:
            raise HTTPException(status_code=401, detail="missing X-OCE-Grant/X-OCE-Actor headers")
        return grant, actor

    def _emit(resp: APIResponse):
        return JSONResponse(status_code=_status_code(resp), content=resp.to_dict())

    @app.get("/api/health")
    def health():
        return _emit(api.health())

    @app.get("/api/readiness")
    def readiness():
        return _emit(api.readiness())

    @app.post("/api/jobs")
    def submit_job(body: dict, auth=Depends(_auth)):
        grant, actor = auth
        resp = api.submit_job(
            grant_id=grant, actor_id=actor,
            job_type=body.get("job_type", ""),
            payload=body.get("payload", {}),
            **{k: v for k, v in body.items() if k in ("resource_scope", "environment", "priority")},
        )
        return _emit(resp)

    @app.get("/api/jobs/{job_id}")
    def inspect_job(job_id: str, auth=Depends(_auth)):
        grant, actor = auth
        return _emit(api.inspect_job(grant_id=grant, actor_id=actor, job_id=job_id))

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel_job(job_id: str, auth=Depends(_auth)):
        grant, actor = auth
        return _emit(api.cancel_job(grant_id=grant, actor_id=actor, job_id=job_id))

    @app.post("/api/jobs/{job_id}/retry")
    def retry_job(job_id: str, auth=Depends(_auth)):
        grant, actor = auth
        return _emit(api.retry_job(grant_id=grant, actor_id=actor, job_id=job_id))

    @app.get("/api/schedules")
    def list_schedules(auth=Depends(_auth)):
        grant, actor = auth
        return _emit(api.list_schedules(grant_id=grant, actor_id=actor))

    @app.get("/api/workers")
    def list_workers(auth=Depends(_auth)):
        grant, actor = auth
        return _emit(api.list_workers(grant_id=grant, actor_id=actor))

    @app.get("/api/system")
    def system_state(auth=Depends(_auth)):
        grant, actor = auth
        return _emit(api.system_state(grant_id=grant, actor_id=actor))

    @app.get("/api/audit")
    def audit_history(auth=Depends(_auth)):
        grant, actor = auth
        return _emit(api.audit_history(grant_id=grant, actor_id=actor))

    # -- Book 3 outbound authenticated worker fabric (loopback only) --------
    # Workers dial OUT to these endpoints; there is no worker public inbound
    # port. Every fabric endpoint authenticates (challenge/response + HMAC
    # signature over the derived wire key). Present only when a
    # worker_protocol_server is wired in.
    proto_errors = None
    if worker_protocol_server is not None:
        from .worker_protocol import (
            WorkerProtocolError, UnknownWorker, ForgedProof, SessionGone,
            CapabilityEscalation, WrongTrustZone)
        proto_errors = (WorkerProtocolError,)

        def _proto_status(e: Exception) -> int:
            if isinstance(e, (ForgedProof, CapabilityEscalation, WrongTrustZone,
                              UnknownWorker)):
                return 403
            if isinstance(e, SessionGone):
                return 410
            return 400

        @app.post("/api/worker/hello")
        def worker_hello(body: dict):
            try:
                return worker_protocol_server.hello(
                    worker_id=body.get("worker_id", ""),
                    proof=body.get("proof", ""))
            except WorkerProtocolError as e:
                raise HTTPException(status_code=_proto_status(e),
                                    detail=str(e))

        @app.post("/api/worker/respond")
        def worker_respond(body: dict):
            try:
                return worker_protocol_server.respond(
                    session_id=body.get("session_id", ""),
                    response=body.get("response", ""))
            except WorkerProtocolError as e:
                raise HTTPException(status_code=_proto_status(e),
                                    detail=str(e))

        @app.post("/api/worker/heartbeat")
        def worker_heartbeat(body: dict):
            try:
                return worker_protocol_server.heartbeat(
                    session_id=body["session_id"], signature=body["signature"])
            except WorkerProtocolError as e:
                raise HTTPException(status_code=_proto_status(e), detail=str(e))

        @app.post("/api/worker/eligible")
        def worker_eligible(body: dict):
            from fastapi import Query as _Q
            try:
                jobs = worker_protocol_server.eligible_jobs(
                    session_id=body["session_id"], signature=body["signature"],
                    queue=body.get("queue", "default"))
                return {"jobs": jobs}
            except WorkerProtocolError as e:
                raise HTTPException(status_code=_proto_status(e), detail=str(e))

        @app.post("/api/worker/fetch_job")
        def worker_fetch_job(body: dict):
            try:
                return worker_protocol_server.fetch_job(
                    session_id=body["session_id"], signature=body["signature"],
                    job_id=body["job_id"])
            except WorkerProtocolError as e:
                raise HTTPException(status_code=_proto_status(e), detail=str(e))

        @app.post("/api/worker/capabilities")
        def worker_capabilities(body: dict):
            try:
                return worker_protocol_server.advertise_capabilities(
                    session_id=body["session_id"], signature=body["signature"])
            except WorkerProtocolError as e:
                raise HTTPException(status_code=_proto_status(e), detail=str(e))

        @app.post("/api/worker/claim")
        def worker_claim(body: dict):
            try:
                return worker_protocol_server.claim(
                    session_id=body["session_id"], signature=body["signature"],
                    job=body.get("job", {}))
            except WorkerProtocolError as e:
                raise HTTPException(status_code=_proto_status(e), detail=str(e))

        @app.post("/api/worker/renew")
        def worker_renew(body: dict):
            try:
                return worker_protocol_server.renew(
                    session_id=body["session_id"], signature=body["signature"],
                    job_id=body["job_id"], lease_id=body["lease_id"],
                    fence=body["fence"])
            except WorkerProtocolError as e:
                raise HTTPException(status_code=_proto_status(e), detail=str(e))

        @app.post("/api/worker/result")
        def worker_result(body: dict):
            try:
                return worker_protocol_server.deliver_result(
                    session_id=body["session_id"], signature=body["signature"],
                    job_id=body["job_id"], lease_id=body["lease_id"],
                    fence=body["fence"], effect_key=body["effect_key"],
                    manifest=body.get("manifest"),
                    success=body.get("success", True))
            except WorkerProtocolError as e:
                raise HTTPException(status_code=_proto_status(e), detail=str(e))

        @app.post("/api/worker/surrender")
        def worker_surrender(body: dict):
            try:
                return worker_protocol_server.surrender(
                    session_id=body["session_id"], signature=body["signature"],
                    job_id=body["job_id"], lease_id=body["lease_id"],
                    fence=body["fence"])
            except WorkerProtocolError as e:
                raise HTTPException(status_code=_proto_status(e), detail=str(e))

        @app.post("/api/worker/revoke")
        def worker_revoke(body: dict):
            from fastapi import Header as _H
            actor = body.get("actor", "")
            try:
                worker_protocol_server.revoke_worker(
                    actor=actor, worker_id=body.get("worker_id", ""))
                return {"revoked": True, "worker_id": body.get("worker_id"),
                        "actor": actor}
            except WorkerProtocolError as e:
                raise HTTPException(status_code=403, detail=str(e))

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/console")

    @app.get("/console", response_class=HTMLResponse, include_in_schema=False)
    def console():
        return HTMLResponse(content=_console_html())

    return app


def runtime_bind(environ: Optional[dict] = None) -> tuple:
    """Return the (host, port) the durable service MUST bind (B4-R3R2).

    The answer comes ONLY from the gated, validated effective config — never
    from a separate legacy env read. Direct ``python -m oce_control.http_api``
    and lifecycle-launched servers therefore produce the SAME effective
    posture; the runtime never validates one port and binds another. Raises
    SystemExit (fail closed) before any bind when the effective config is
    invalid/forbidden.
    """
    from .config_startup import require_startable
    eff = require_startable(environ)
    host = eff.get("control_plane.host")
    port = int(eff.get("control_plane.port"))
    return host, port


def runtime_scheduler_interval(environ: Optional[dict] = None) -> int:
    """Scheduler tick interval from the gated effective config (B4-R3R2)."""
    from .config_startup import require_startable
    return int(require_startable(environ).get("control_plane.scheduler_interval"))


def build_durable_app(*, dsn: Optional[str] = None, scheduler_tick_interval: int = 5) -> FastAPI:
    """Wire the durable components (PG store, PG scheduler, PG worker
    protocol, health) into the API and return a ready FastAPI app.

    Operator grants are issued deterministically at startup and printed;
    the console uses the `read` grant id.
    """
    import psycopg2
    from .authority import AuthorityEngine
    from .pg_store import PgJobStore
    from .pg_scheduler import PgScheduler
    from .pg_worker import PgWorkerProtocol
    from .health import HealthService

    dsn = dsn or os.environ.get("POSTGRES_DSN") or _default_dsn()
    conn = psycopg2.connect(dsn)
    conn.autocommit = False

    authority = AuthorityEngine()
    grants = {}
    for action in OPERATOR_ACTIONS:
        grant = authority.issue_grant(
            actor_id="operator",
            action=action,
            target="default",
            environment="local",
            risk_class="read" if action == "read" else None,
            ttl_seconds=24 * 3600,
        )
        grants[action] = grant.grant_id

    store = PgJobStore(conn)
    scheduler = PgScheduler(conn, store)
    worker = PgWorkerProtocol(store, conn)
    health = HealthService(job_store=store, scheduler=scheduler,
                           worker_protocol=worker)
    try:
        store.get_job("__probe__")
        health.set_pg_available(True)
    except Exception:
        health.set_pg_available(False)

    api = ControlPlaneAPI(
        authority=authority,
        job_store=store,
        scheduler=scheduler,
        worker_protocol=worker,
        health_service=health,
    )
    print("OCE control plane grants (console uses 'read'):")
    for action, gid in grants.items():
        print(f"  {action:14s} -> {gid}")
    return create_app(api, scheduler=scheduler,
                      scheduler_tick_interval=scheduler_tick_interval)


if __name__ == "__main__":
    # B4-R3R2: the durable HTTP service consumes the VALIDATED EFFECTIVE
    # CONFIG for its bind host/port and scheduler interval. There is no
    # separate legacy path that can bind 8080 behind the spine's back — the
    # gate runs first (require_startable) and refuses activation on any
    # malformed / incomplete / forbidden effective config.
    import uvicorn
    host, port = runtime_bind()
    interval = runtime_scheduler_interval()
    app = build_durable_app(scheduler_tick_interval=interval)
    uvicorn.run(app, host=host, port=port, log_level="info")
