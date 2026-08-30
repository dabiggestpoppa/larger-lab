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

CONSOLE_PATH = Path(__file__).resolve().parent.parent / "ui" / "console.html"

DEFAULT_DSN = "postgresql://oce_control_admin:test-secret-b2-pg-001@127.0.0.1:5433/oce_control"

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
               scheduler_tick_interval: int = 0) -> FastAPI:
    """Build the FastAPI app over a ControlPlaneAPI boundary.

    scheduler_tick_interval > 0 starts a background tick loop (durable
    runtime). Tests pass 0 for deterministic, single-threaded behavior.
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

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/console")

    @app.get("/console", response_class=HTMLResponse, include_in_schema=False)
    def console():
        return HTMLResponse(content=_console_html())

    return app


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

    dsn = dsn or os.environ.get("POSTGRES_DSN", DEFAULT_DSN)
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
    import uvicorn
    interval = int(os.environ.get("OCE_SCHEDULER_INTERVAL", "5"))
    app = build_durable_app(scheduler_tick_interval=interval)
    uvicorn.run(app, host="127.0.0.1",
                port=int(os.environ.get("OCE_API_PORT", "8080")),
                log_level="info")
