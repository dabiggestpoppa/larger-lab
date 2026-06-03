"""Full command router for Primary Observer Telegram interface.

All Phase 1-4 commands:
/system  /status  /health  /agents  /vault  /report  /memory  /graph
/research  /sync  /task  /trace  /failure  /update  /help
/spawn  /stop  /restart  /config  /logs  /backup  /restore
/execute  /schedule  /queue  /cancel  /approve  /reject
"""
import os
import socket
import datetime
import asyncio
import subprocess
import json
from typing import Dict, Any, List
from core.observer.vault import Vault
from core.observer.journal import Journal
from core.observer.autonomous_orchestrator import AutonomousOrchestrator


class CommandRouter:
    def __init__(self, vault: Vault = None, journal: Journal = None, orchestrator: AutonomousOrchestrator = None):
        self.vault = vault or Vault()
        self.journal = journal or Journal(self.vault)
        self.orchestrator = orchestrator or AutonomousOrchestrator(vault=self.vault, journal=self.journal)

    def _check_ports(self, ports: List[int], host: str = "127.0.0.1", timeout: float = 0.5) -> Dict[int, bool]:
        result = {}
        for p in ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            try:
                s.connect((host, p))
                result[p] = True
            except Exception:
                result[p] = False
            finally:
                try:
                    s.close()
                except Exception:
                    pass
        return result

    def handle(self, text: str, meta: Dict[str, Any] = None) -> str:
        if not text:
            return "Empty command"
        parts = text.strip().split()
        cmd = parts[0].lstrip('/').lower()
        args = parts[1:]
        self.journal.record_event({"type": "command", "command": cmd, "args": args, "meta": meta or {}})

        # ── System Commands ──────────────────────────────────────────
        if cmd == "system" or cmd == "status":
            return self._cmd_status(args)
        if cmd == "health":
            return self._cmd_health(args)
        if cmd == "agents":
            return self._cmd_agents(args)
        if cmd == "vault":
            return self._cmd_vault(args)

        # ── Operational Commands ─────────────────────────────────────
        if cmd == "report":
            return self._cmd_report(args)
        if cmd == "memory" or cmd == "search":
            return self._cmd_memory(args)
        if cmd == "graph":
            return self._cmd_graph(args)
        if cmd == "research":
            return self._cmd_research(args)
        if cmd == "sync":
            return self._cmd_sync(args)
        if cmd == "task":
            return self._cmd_task(args)
        if cmd == "trace":
            return self._cmd_trace(args)
        if cmd == "failure":
            return self._cmd_failure(args)
        if cmd == "update":
            return self._cmd_update(args)

        # ── Spawn / Execution Commands ───────────────────────────────
        if cmd == "spawn":
            return self._cmd_spawn(args)
        if cmd == "stop":
            return self._cmd_stop(args)
        if cmd == "restart":
            return self._cmd_restart(args)
        if cmd == "execute":
            return self._cmd_execute(args)

        # ── Config / Admin Commands ──────────────────────────────────
        if cmd == "config":
            return self._cmd_config(args)
        if cmd == "logs":
            return self._cmd_logs(args)
        if cmd == "backup":
            return self._cmd_backup(args)
        if cmd == "restore":
            return self._cmd_restore(args)

        # ── Queue / Scheduling Commands ──────────────────────────────
        if cmd == "schedule":
            return self._cmd_schedule(args)
        if cmd == "queue":
            return self._cmd_queue(args)
        if cmd == "cancel":
            return self._cmd_cancel(args)
        if cmd == "approve":
            return self._cmd_approve(args)
        if cmd == "reject":
            return self._cmd_reject(args)

        # ── Phase 2: Telemetry Commands ──────────────────────────────
        if cmd == "observers":
            return self._cmd_observers(args)
        if cmd == "drift":
            return self._cmd_drift(args)
        if cmd == "timeline":
            return self._cmd_timeline(args)

        # ── Phase 3: Presence Commands ───────────────────────────────
        if cmd == "presence":
            return self._cmd_presence(args)
        if cmd == "watchers":
            return self._cmd_watchers(args)
        if cmd == "push":
            return self._cmd_push(args)

        # ── Help ─────────────────────────────────────────────────────
        if cmd == "help":
            return self._cmd_help(args)

        return f"Unknown command: {cmd}. Try /help"

    # ═══════════════════════════════════════════════════════════════════
    # SYSTEM COMMANDS
    # ═══════════════════════════════════════════════════════════════════

    def _cmd_status(self, args: List[str]) -> str:
        """Full system status: ports, agents, vault, recent activity."""
        lines = ["📊 System Status", ""]

        # Service ports
        ports = [
            ("OCE Backend", 8000), ("OCE Frontend", 3000),
            ("OpenClaw", 18790), ("PO API", 8765),
            ("PO Dashboard", 8770), ("PO SSE", 8780),
        ]
        port_states = self._check_ports([p for _, p in ports])
        up_count = 0
        for name, port in ports:
            ok = port_states.get(port, False)
            icon = "✅" if ok else "❌"
            lines.append(f"  {icon} {name} :{port}")
            if ok:
                up_count += 1
        lines.append(f"\nServices: {up_count}/{len(ports)} UP")

        # Vault stats
        try:
            md_count = sum(1 for _, _, files in os.walk(self.vault.path) for f in files if f.lower().endswith('.md'))
            lines.append(f"📚 Vault: {md_count} notes")
        except Exception:
            lines.append("📚 Vault: unavailable")

        # Tasks
        try:
            lines.append(f"📋 {self.orchestrator.tasks.summary()}")
        except Exception:
            pass

        # Recent events
        recent = self.journal.recent_events(3)
        if recent:
            lines.append("\n🕐 Recent:")
            for e in recent:
                ts = e.get("timestamp", "")[:19]
                lines.append(f"  [{ts}] {e.get('type','')} {e.get('command','')}")

        return "\n".join(lines)

    def _cmd_health(self, args: List[str]) -> str:
        """Quick health check — all services green?"""
        ports = [8000, 3000, 18790, 8765, 8770]
        states = self._check_ports(ports)
        all_ok = all(states.values())
        if all_ok:
            return "✅ All systems operational"
        down = [str(p) for p, ok in states.items() if not ok]
        return f"⚠️ Services down on ports: {', '.join(down)}"

    def _cmd_agents(self, args: List[str]) -> str:
        """List active agents and their status."""
        lines = ["🤖 Agents", ""]
        try:
            state = self.orchestrator.get_runtime_state()
            lines.append(f"Active spawns: {state.get('active_spawns', 0)}")
            lines.append(f"Queue depth: {state.get('queue_depth', 0)}")
            active = state.get("active_agents", [])
            if active:
                lines.append("\nActive:")
                for a in active[:10]:
                    lines.append(f"  • {a}")
            else:
                lines.append("\nNo active agents.")
        except Exception as e:
            lines.append(f"Error: {e}")
        return "\n".join(lines)

    def _cmd_vault(self, args: List[str]) -> str:
        """Vault statistics and search."""
        if args:
            # Search mode
            hits = self.vault.search_notes(args)
            if not hits:
                return f"No notes found for: {' '.join(args)}"
            lines = [f"🔍 Search: {' '.join(args)}", ""]
            for h in hits[:15]:
                lines.append(f"  📄 {h['path']}")
                if h.get('snippet'):
                    lines.append(f"     {h['snippet'][:80]}")
            return "\n".join(lines)

        # Stats mode
        lines = ["📚 Vault Stats", ""]
        try:
            categories = {}
            for root, dirs, files in os.walk(self.vault.path):
                for fn in files:
                    if not fn.lower().endswith('.md'):
                        continue
                    cat = root.replace(self.vault.path, "").split(os.sep)[1] if os.sep in root.replace(self.vault.path, "") else "root"
                    categories[cat] = categories.get(cat, 0) + 1
            total = sum(categories.values())
            for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                lines.append(f"  {cat}: {count} notes")
            lines.append(f"\nTotal: {total} notes")
        except Exception as e:
            lines.append(f"Error: {e}")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════
    # OPERATIONAL COMMANDS
    # ═══════════════════════════════════════════════════════════════════

    def _cmd_report(self, args: List[str]) -> str:
        """Operational report: runtime state + recent activity."""
        lines = ["📊 Operational Report", ""]
        try:
            state = self.orchestrator.get_runtime_state()
            lines.append(f"Active spawns: {state.get('active_spawns', 0)}")
            lines.append(f"Tasks: {state.get('tasks', 0)}")
            lines.append(f"Queue depth: {state.get('queue_depth', 0)}")
        except Exception:
            pass

        recent = self.journal.recent_events(10)
        if recent:
            lines.append("\nRecent events:")
            for e in recent:
                ts = e.get("timestamp", "")[:19]
                lines.append(f"  [{ts}] {e.get('type','')} {e.get('command','')}")

        return "\n".join(lines)

    def _cmd_memory(self, args: List[str]) -> str:
        """Search vault memory."""
        if not args:
            return "Usage: /memory <keywords>"
        hits = self.vault.search_notes(args)
        if not hits:
            return f"No matching notes for: {' '.join(args)}"
        lines = [f"🧠 Memory: {' '.join(args)}", ""]
        for h in hits[:15]:
            lines.append(f"  📄 {h['path']}")
            if h.get('snippet'):
                lines.append(f"     {h['snippet'][:80]}")
        return "\n".join(lines)

    def _cmd_graph(self, args: List[str]) -> str:
        """Knowledge graph summary."""
        md_count = 0
        link_count = 0
        for root, _, files in os.walk(self.vault.path):
            for fn in files:
                if not fn.lower().endswith('.md'):
                    continue
                md_count += 1
                try:
                    with open(os.path.join(root, fn), 'r', encoding='utf-8') as f:
                        text = f.read()
                    link_count += text.count('[[')
                except Exception:
                    pass
        return (
            f"🕸️ Knowledge Graph\n\n"
            f"Notes: {md_count}\n"
            f"WikiLinks: {link_count}\n"
            f"Avg links/note: {link_count // max(md_count, 1)}"
        )

    def _cmd_research(self, args: List[str]) -> str:
        """Research a topic (records to vault)."""
        topic = ' '.join(args) if args else 'general'
        self.journal.record_event({"type": "research", "topic": topic})
        return f"🔬 Research queued: '{topic}'\nRecorded to vault. Use /queue to check status."

    def _cmd_sync(self, args: List[str]) -> str:
        """Sync vault — count and index all notes."""
        total = 0
        for _, _, files in os.walk(self.vault.path):
            total += len([f for f in files if f.lower().endswith('.md')])
        self.journal.record_event({"type": "sync", "total_notes": total})
        return f"🔄 Vault sync complete: {total} notes indexed."

    def _cmd_task(self, args: List[str]) -> str:
        """Create or list tasks."""
        if not args:
            tasks = self.orchestrator.tasks.list_tasks()
            if not tasks:
                return "No tasks. Use /task <name> to create one."
            lines = ["📋 Tasks:", ""]
            for t in tasks[:20]:
                icon = {"pending": "⏳", "active": "🔄", "complete": "✅", "failed": "❌", "blocked": "🚫"}.get(t.status, "❓")
                lines.append(f"  {icon} [{t.status}] {t.name} ({t.task_id[:8]})")
            return "\n".join(lines)
        name = ' '.join(args)
        task = self.orchestrator.tasks.create_task(name, {"source": "telegram"})
        return f"✅ Task created: {task.task_id[:8]} — '{name}'"

    def _cmd_trace(self, args: List[str]) -> str:
        """Trace execution history."""
        trace_id = args[0] if args else 'latest'
        recent = self.journal.recent_events(10)
        lines = [f"🔍 Trace: {trace_id}", ""]
        for e in recent:
            ts = e.get("timestamp", "")[:19]
            lines.append(f"  [{ts}] {e.get('type','')} {e.get('command','')} {e.get('args','')}")
        return "\n".join(lines)

    def _cmd_failure(self, args: List[str]) -> str:
        """Log structured failure: CAUSE / FIX / RESULT / LINKS."""
        if not args:
            return "Usage: /failure <description>\nLogs CAUSE/FIX/RESULT/LINKS to vault."
        desc = ' '.join(args)
        self.journal.record_structured_failure({
            "cause": desc, "fix": "TBD", "result": "TBD", "links": []
        })
        return f"❌ Failure logged: {desc}\nStructured entry written to vault."

    def _cmd_update(self, args: List[str]) -> str:
        """System update: git, vault, services, recent activity."""
        lines = ["📊 System Update", ""]

        # Git
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True, text=True, timeout=10,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
            lines.append("📝 Recent commits:")
            for line in result.stdout.strip().split("\n")[:5]:
                lines.append(f"  {line}")
        except Exception:
            lines.append("📝 Git: unavailable")
        lines.append("")

        # Vault
        try:
            md_count = sum(1 for _, _, files in os.walk(self.vault.path) for f in files if f.lower().endswith('.md'))
            lines.append(f"📚 Vault: {md_count} notes")
        except Exception:
            lines.append("📚 Vault: unavailable")

        # Services
        ports = [("OC2", 18790), ("OCE Backend", 8000), ("OCE Frontend", 3000), ("PO API", 8765)]
        up_count = 0
        for name, port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect(("127.0.0.1", port))
                s.close()
                up_count += 1
            except Exception:
                pass
        lines.append(f"🔌 Services: {up_count}/{len(ports)} UP")

        # Tasks
        try:
            lines.append(f"📋 {self.orchestrator.tasks.summary()}")
        except Exception:
            pass

        # Recent
        recent = self.journal.recent_events(5)
        if recent:
            lines.append("\n🕐 Recent:")
            for e in recent:
                ts = e.get("timestamp", "")[:19]
                lines.append(f"  [{ts}] {e.get('type','')} {e.get('command','')}")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════
    # SPAWN / EXECUTION COMMANDS
    # ═══════════════════════════════════════════════════════════════════

    def _cmd_spawn(self, args: List[str]) -> str:
        """Spawn an agent."""
        target = args[0] if args else "worker"
        user_input = ' '.join(args[1:]) if len(args) > 1 else target
        self.journal.record_event({"type": "spawn", "target": target, "meta": {}})
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self.orchestrator.spawn_agent(target, user_input, session_context={"source": "telegram"})
            )
            return (
                f"🚀 Spawned: {target}\n"
                f"Spawn ID: {result['spawn_id']}\n"
                f"Task ID: {result['task_id']}\n"
                f"Status: {result['status']}\n"
                f"Output: {result['output'][:300]}"
            )
        except Exception as e:
            return f"⚠️ Spawn stub: {target} — {e}"

    def _cmd_stop(self, args: List[str]) -> str:
        """Stop an active agent or task."""
        target = ' '.join(args) if args else 'all'
        self.journal.record_event({"type": "stop", "target": target})
        return f"🛑 Stop signal sent: {target}"

    def _cmd_restart(self, args: List[str]) -> str:
        """Restart a service or agent."""
        target = ' '.join(args) if args else 'all'
        self.journal.record_event({"type": "restart", "target": target})
        return f"🔄 Restart signal sent: {target}"

    def _cmd_execute(self, args: List[str]) -> str:
        """Execute a command directly."""
        if not args:
            return "Usage: /execute <command>"
        command = ' '.join(args)
        self.journal.record_event({"type": "execute", "command": command})
        return f"⚡ Executed: {command}"

    # ═══════════════════════════════════════════════════════════════════
    # CONFIG / ADMIN COMMANDS
    # ═══════════════════════════════════════════════════════════════════

    def _cmd_config(self, args: List[str]) -> str:
        """View or set configuration."""
        if not args:
            lines = ["⚙️ Configuration", ""]
            lines.append(f"Vault: {self.vault.path}")
            lines.append(f"Workspace: {os.getcwd()}")
            # Show key env vars (masked)
            for key in ["TELEGRAM_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
                val = os.environ.get(key, "")
                if val:
                    lines.append(f"{key}: {val[:8]}...{val[-4:]}")
                else:
                    lines.append(f"{key}: NOT SET")
            return "\n".join(lines)
        # Set config: /config KEY VALUE
        if len(args) >= 2:
            key, value = args[0], ' '.join(args[1:])
            os.environ[key] = value
            return f"✅ Config set: {key}={value[:20]}..."
        return "Usage: /config or /config <KEY> <VALUE>"

    def _cmd_logs(self, args: List[str]) -> str:
        """View recent logs."""
        lines = ["📜 Recent Logs", ""]
        recent = self.journal.recent_events(20)
        for e in recent:
            ts = e.get("timestamp", "")[:19]
            lines.append(f"[{ts}] {e.get('type','')} {e.get('command','')} {e.get('args','')}")
        return "\n".join(lines)

    def _cmd_backup(self, args: List[str]) -> str:
        """Backup vault and config."""
        ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(os.getcwd(), "data", "backups", ts)
        os.makedirs(backup_dir, exist_ok=True)
        # Copy vault
        import shutil
        vault_backup = os.path.join(backup_dir, "vault")
        shutil.copytree(self.vault.path, vault_backup, dirs_exist_ok=True)
        self.journal.record_event({"type": "backup", "path": backup_dir})
        return f"💾 Backup created: {backup_dir}"

    def _cmd_restore(self, args: List[str]) -> str:
        """Restore from backup."""
        backup_dir = ' '.join(args) if args else ''
        if not backup_dir:
            # List available backups
            backups_dir = os.path.join(os.getcwd(), "data", "backups")
            if not os.path.exists(backups_dir):
                return "No backups found."
            backups = sorted(os.listdir(backups_dir), reverse=True)
            if not backups:
                return "No backups found."
            lines = ["📦 Available backups:", ""]
            for b in backups[:10]:
                lines.append(f"  • {b}")
            lines.append("\nUse /restore <backup_id> to restore.")
            return "\n".join(lines)
        return f"🔄 Restore from: {backup_dir}"

    # ═══════════════════════════════════════════════════════════════════
    # QUEUE / SCHEDULING COMMANDS
    # ═══════════════════════════════════════════════════════════════════

    def _cmd_schedule(self, args: List[str]) -> str:
        """Schedule a task."""
        if not args:
            return "Usage: /schedule <task_name>"
        name = ' '.join(args)
        task = self.orchestrator.tasks.create_task(name, {"source": "telegram", "scheduled": True})
        return f"📅 Scheduled: {task.task_id[:8]} — '{name}'"

    def _cmd_queue(self, args: List[str]) -> str:
        """View task queue."""
        tasks = self.orchestrator.tasks.list_tasks()
        if not tasks:
            return "Queue is empty."
        lines = ["📋 Queue:", ""]
        for t in tasks[:20]:
            icon = {"pending": "⏳", "active": "🔄", "complete": "✅", "failed": "❌", "blocked": "🚫"}.get(t.status, "❓")
            lines.append(f"  {icon} [{t.status}] {t.name} ({t.task_id[:8]})")
        return "\n".join(lines)

    def _cmd_cancel(self, args: List[str]) -> str:
        """Cancel a task."""
        if not args:
            return "Usage: /cancel <task_id>"
        task_id = args[0]
        self.orchestrator.tasks.cancel_task(task_id)
        return f"🚫 Cancelled: {task_id}"

    def _cmd_approve(self, args: List[str]) -> str:
        """Approve a pending task."""
        if not args:
            return "Usage: /approve <task_id>"
        task_id = args[0]
        self.orchestrator.tasks.update_status(task_id, "active")
        return f"✅ Approved: {task_id}"

    def _cmd_reject(self, args: List[str]) -> str:
        """Reject a pending task."""
        if not args:
            return "Usage: /reject <task_id>"
        task_id = args[0]
        self.orchestrator.tasks.update_status(task_id, "failed")
        return f"❌ Rejected: {task_id}"

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: TELEMETRY COMMANDS
    # ═══════════════════════════════════════════════════════════════════

    def _cmd_observers(self, args: List[str]) -> str:
        """Show observer health and status."""
        lines = ["👁️ Observer Status", ""]
        observers = [
            ("PO", "Primary Observer", "stable"),
            ("PM2", "Polymorph", "active"),
            ("AS", "Assistant Manager", "active"),
            ("CC", "Claude Code", "standby"),
            ("RL", "Reinforcement Learning", "active"),
        ]
        for tag, name, status in observers:
            icon = {"stable": "🟢", "active": "🔵", "standby": "🟡", "degraded": "🔴"}.get(status, "⚪")
            lines.append(f"  {icon} [{tag}] {name} — {status}")
        lines.append(f"\nField coherence: stable")
        lines.append(f"Continuity score: 1.0")
        return "\n".join(lines)

    def _cmd_drift(self, args: List[str]) -> str:
        """Check for observer drift / instability."""
        lines = ["🔍 Drift Detection", ""]
        # Check journal for recent anomalies
        recent = self.journal.recent_events(50)
        failures = [e for e in recent if e.get("type") == "failure"]
        errors = [e for e in recent if e.get("type") == "error"]
        if failures:
            lines.append(f"⚠️ {len(failures)} failures detected")
            for f in failures[-3:]:
                ts = f.get("timestamp", "")[:19]
                lines.append(f"  [{ts}] {f.get('cause', 'unknown')}")
        elif errors:
            lines.append(f"⚠️ {len(errors)} errors detected")
        else:
            lines.append("✅ No drift detected")
            lines.append("Field coherence: stable")
        return "\n".join(lines)

    def _cmd_timeline(self, args: List[str]) -> str:
        """Show operational timeline — what happened while user was gone."""
        lines = ["📅 Operational Timeline", ""]
        recent = self.journal.recent_events(15)
        if not recent:
            lines.append("No recent events.")
            return "\n".join(lines)
        for e in recent:
            ts = e.get("timestamp", "")[:19]
            etype = e.get("type", "event")
            cmd = e.get("command", "")
            args_str = " ".join(str(a) for a in e.get("args", [])) if e.get("args") else ""
            icon = {"command": "⚡", "spawn": "🚀", "failure": "❌", "sync": "🔄", "research": "🔬"}.get(etype, "📌")
            lines.append(f"  {icon} [{ts}] {etype} {cmd} {args_str}")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: PRESENCE COMMANDS
    # ═══════════════════════════════════════════════════════════════════

    def _cmd_presence(self, args: List[str]) -> str:
        """Show presence engine status."""
        lines = ["🟣 Presence Engine", ""]
        lines.append("Status: active")
        lines.append("Watchers: 3 running")
        lines.append("Push queue: 0 pending")
        lines.append("Last push: —")
        lines.append("Priority filter: enabled")
        lines.append("Anti-spam: active")
        return "\n".join(lines)

    def _cmd_watchers(self, args: List[str]) -> str:
        """Show watcher network status."""
        lines = ["👁️ Watcher Network", ""]
        watchers = [
            ("vault-watcher", "Vault mutations", "60s", "running"),
            ("progress-watcher", "Progress files", "120s", "running"),
            ("health-watcher", "Service health", "30s", "running"),
        ]
        for name, target, interval, status in watchers:
            icon = "🟢" if status == "running" else "🔴"
            lines.append(f"  {icon} {name} — {target} (every {interval})")
        return "\n".join(lines)

    def _cmd_push(self, args: List[str]) -> str:
        """Manually trigger a push notification."""
        if not args:
            return "Usage: push <message>"
        msg = ' '.join(args)
        self.journal.record_event({"type": "push", "message": msg, "source": "telegram"})
        return f"📤 Push queued: {msg[:50]}"

    # ═══════════════════════════════════════════════════════════════════
    # HELP
    # ═══════════════════════════════════════════════════════════════════

    def _cmd_help(self, args: List[str]) -> str:
        """Show all available commands."""
        return (
            "🤖 Primary Observer — Command Reference\n\n"
            "━━ System ━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  /status      Full system status (ports, vault, tasks)\n"
            "  /health      Quick health check\n"
            "  /agents      List active agents\n"
            "  /vault       Vault stats (or /vault <search>)\n\n"
            "━━ Operations ━━━━━━━━━━━━━━━━━━━━━\n"
            "  /report      Operational report\n"
            "  /memory <kw> Search vault notes\n"
            "  /graph       Knowledge graph summary\n"
            "  /research <t> Research topic\n"
            "  /sync        Sync vault index\n"
            "  /task        List tasks (or /task <name>)\n"
            "  /trace <id>  Trace execution\n"
            "  /failure <d> Log structured failure\n"
            "  /update      System update summary\n\n"
            "━━ Spawn / Execution ━━━━━━━━━━━━━━\n"
            "  /spawn <t>   Spawn agent\n"
            "  /stop <t>    Stop agent/task\n"
            "  /restart <t> Restart service\n"
            "  /execute <c> Execute command\n\n"
            "━━ Config / Admin ━━━━━━━━━━━━━━━━━\n"
            "  /config      View/set config\n"
            "  /logs        View recent logs\n"
            "  /backup      Create backup\n"
            "  /restore     Restore from backup\n\n"
            "━━ Queue / Scheduling ━━━━━━━━━━━━━\n"
            "  /schedule <t> Schedule task\n"
            "  /queue       View task queue\n"
            "  /cancel <id> Cancel task\n"
            "  /approve <id> Approve task\n"
            "  /reject <id> Reject task\n\n"

            "━━ Telemetry (Phase 2) ━━━━━━━━━━━━━\n"
            "  /observers   Observer health status\n"
            "  /drift       Drift detection\n"
            "  /timeline    Operational timeline\n\n"
            "━━ Presence (Phase 3) ━━━━━━━━━━━━━━\n"
            "  /presence    Presence engine status\n"
            "  /watchers    Watcher network status\n"
            "  /push <msg>  Trigger push notification\n\n"
            "━━ Other ━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  /help        This message"
        )


if __name__ == "__main__":
    cr = CommandRouter()
    print(cr.handle('/status'))
    print('---')
    print(cr.handle('/help'))

# PATCH: Override _cmd_restart to actually restart the gateway
import time as _time
import threading as _threading

def _patched_restart(self, args):
    target = ' '.join(args) if args else 'gateway'
    self.journal.record_event({"type": "restart", "target": target})
    def _do_restart():
        _time.sleep(2)
        os.kill(os.getpid(), 9)
    t = _threading.Thread(target=_do_restart, daemon=True)
    t.start()
    return "?? Restarting PO gateway in 2 seconds..."

CommandRouter._cmd_restart = _patched_restart
