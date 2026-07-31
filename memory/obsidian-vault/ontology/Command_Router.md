# Command Router

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #observer

```python
"""Full command router for Primary Observer Telegram interface.

Implements all 10 slash commands from the Phase 1 plan:
/spawn /report /status /memory /graph /research /sync /task /trace /failure

Phase 3: Wired to real O-2/O-3 spawn engine via AutonomousOrchestrator.
"""
import os
import socket
import datetime
import asyncio
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

        # journaling the command invocation
        self.journal.record_event({"type": "command", "command": cmd, "args": args, "meta": meta or {}})

        if cmd == "status":
            # Phase 3: full runtime state from orchestrator
            return self.orchestrator.format_status()

        if cmd == "spawn":
            target = args[0] if args else "worker"
            user_input = ' '.join(args[1:]) if len(args) > 1 else target
            self.journal.record_event({"type": "spawn", "target": target, "meta": meta or {}})
            # Use real O-3 spawn engine
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
                    f"Output: {result['output'][:200]}"
                )
            except Exception as e:
                # Fallback to stub if spawn engine unavailable
                return f"Spawned (stub): {target} — {e}"

        if cmd == "memory" or cmd == "search":
            if not args:
                return "Usage: /memory <keywords> — searching vault for relevant notes."
            hits = self.vault.search_notes(args)
            if not hits:
                return "No matching notes found."
            return "Found notes:\n" + "\n".join(f"- {h['path']} ({h['snippet']})" for h in hits[:10])

        if cmd == "report":
            # Phase 3: autonomous report from orchestrator
            state = self.orchestrator.get_runtime_state()
            recent = self.journal.recent_events(5)
            lines = [
                "📊 Operational Report",
                f"Active spawns: {state['active_spawns']}",
                f"Tasks: {state['tasks']}",
                f"Queue depth: {state['queue_depth']}",
                "",
                "Recent events:",
            ]
            for e in recent:
                lines.append(f"  [{e.get('timestamp','')}] {e.get('type','')} {e.get('command','')}")
            return "\n".join(lines)

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

        if cmd == "help":
            return (
                "Primary Observer commands:\n"
                "  /status       — check all service ports\n"
                "  /spawn <t>   — spawn agent (stub)\n"
                "  /report       — recent operational summary\n"
                "  /memory <kw> — search vault notes\n"
                "  /graph        — knowledge graph summary\n"
                "  /research <t>— research stub\n"
                "  /sync         — sync vault state\n"
                "  /task <name> — create task\n"
                "  /trace <id>  — trace execution\n"
                "  /failure <d> — log structured failure\n"
                "  /help         — this message"
            )

        return f"Unknown command: {cmd}. Try /help"

    def _cmd_graph(self, args: List[str]) -> str:
        md_count = 0
        link_count = 0
        for root, _, files in os.walk(self.vault.path):
            for fn in files:
                if not fn.lower().endswith('.md'):
                    continue
                md_count += 1
                fp = os.path.join(root, fn)
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        text = f.read()
                    link_count += len([l for l in text.splitlines() if '[[' in l or '](#' in l])
                except Exception:
                    pass
        self.journal.record_event({"type": "graph_summary", "md_files": md_count, "links": link_count})
        return f"Knowledge graph: {md_count} notes, {link_count} internal links (stub)."

    def _cmd_research(self, args: List[str]) -> str:
        topic = ' '.join(args) if args else 'general'
        self.journal.record_event({"type": "research", "topic": topic})
        return f"Research stub: '{topic}' — recorded. (Integrate web search or RAG in production.)"

    def _cmd_sync(self, args: List[str]) -> str:
        total = 0
        for _, _, files in os.walk(self.vault.path):
            total += len([f for f in files if f.lower().endswith('.md')])
        self.journal.record_event({"type": "sync", "total_notes": total})
        return f"Vault sync complete: {total} notes indexed."

    def _cmd_task(self, args: List[str]) -> str:
        if not args:
            # list tasks
            tasks = self.orchestrator.tasks.list_tasks()
            if not tasks:
                return "No tasks. Use /task <name> to create one."
            lines = ["Tasks:"]
            for t in tasks[:10]:
                lines.append(f"  {t.task_id} [{t.status}] {t.name}")
            return "\n".join(lines)
        name = ' '.join(args)
        task = self.orchestrator.tasks.create_task(name, {"source": "telegram"})
        return f"Task created: {task.task_id} — '{name}'"

    def _cmd_trace(self, args: List[str]) -> str:
        trace_id = args[0] if args else 'latest'
        recent = self.journal.recent_events(5)
        self.journal.record_event({"type": "trace", "trace_id": trace_id})
        return f"Trace {trace_id}:\n" + "\n".join(
            f"  [{e.get('timestamp','')}] {e.get('type','')} {e.get('command','')}" for e in recent
        )

    def _cmd_failure(self, args: List[str]) -> str:
        """Log a structured failure entry: CAUSE / FIX / RESULT / LINKS."""
        desc = ' '.join(args) if args else 'unspecified failure'
        entry = {
            "type": "failure",
            "cause": desc,
            "fix": "TBD",
            "result": "TBD",
            "links": []
        }
        self.journal.record_structured_failure(entry)
        return f"Failure logged: {desc}\nStructured entry written to vault."


if __name__ == "__main__":
    cr = CommandRouter()
    print(cr.handle('/status'))
    print('---')
    print(cr.handle('/help'))

```

LINKS:
[[All Mermaid Graphs]]
[[Module Guide]]
[[User]]
[[Journal 20260602T004840Z Command Graph]]
[[Journal 20260602T004840Z Command Help]]
[[Journal 20260602T004840Z Command Status]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T005953Z Command Report]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Command Status]]
[[Journal 20260602T005953Z Command Task]]
[[Ontology Core Summary]]
[[Citation Workflow]]
[[Server]]
[[Usage]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
