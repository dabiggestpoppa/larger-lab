# TB Deployment Profiles

| Profile        | Status       | Notes |
|----------------|--------------|-------|
| `local_windows` | **implemented** | This machine, MT5 terminal + python + Task Scheduler logon task |
| `windows_vps`   | template only | Same code; supervisor/worker/dashboard run on a Windows VPS with MT5 |

Set `TB_DEPLOYMENT_PROFILE` (default `local_windows`). The worker logs the
active profile at startup; nothing else branches on it yet.

## local_windows (implemented)

- Runtime: `quant-lab/runtime/` — supervisor owns the worker lifecycle.
- Auto-start: Task Scheduler logon task `TB-Runtime-Supervisor` (current user,
  limited privilege) → `python -u tb_supervisor.py`.
- Dashboard: `http://127.0.0.1:8765` (localhost only, read-only).
- Control: `tbctl status|start|stop|restart`.
- Durable state: `quant-lab/state/tb_runtime.db` (SQLite/WAL), PID files,
  desired-state flag.
- Logs: `quant-lab/logs/tb_runtime.log`, `tb_supervisor.log`,
  `tb_dashboard.log` (rotating 5 MB × 5).

## windows_vps (template — NOT authorized to deploy)

Same runtime layout on a Windows VPS with an MT5 terminal:

- `TB_DEPLOYMENT_PROFILE=windows_vps`
- Auto-start: the same Task Scheduler mechanism (VPS has interactive login).
- MT5 must be running with the approved demo account logged in.
- Remote dashboard is NOT authorized; keep the dashboard on loopback and use
  an SSH tunnel if remote visibility is ever needed.

No remote deployment, no Railway dependency: execution always stays local to
the machine running MT5.
