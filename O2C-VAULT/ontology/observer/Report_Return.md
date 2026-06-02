# Report Return

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #observer

```python
"""Report Return System — agent output → Telegram.

Collects agent execution results, compresses them, and formats
for Telegram delivery. Also writes compressed reports into the vault.
"""
import datetime
from typing import Dict, Any, List, Optional
from core.observer.vault import Vault
from core.observer.journal import Journal


class ReportReturnSystem:
    def __init__(self, vault: Vault = None, journal: Journal = None):
        self.vault = vault or Vault()
        self.journal = journal or Journal(self.vault)
        self._reports: List[Dict[str, Any]] = []

    def submit_report(self, agent: str, task: str, output: str, meta: Dict[str, Any] = None) -> str:
        """Submit an agent report. Returns a compressed Telegram-ready summary."""
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        # compress: truncate long outputs
        compressed = output[:500] + ("..." if len(output) > 500 else "")
        report = {
            "timestamp": ts,
            "agent": agent,
            "task": task,
            "output": compressed,
            "full_length": len(output),
            "meta": meta or {}
        }
        self._reports.append(report)

        # persist to vault
        title = f"report_{agent}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        content = (
            f"# Report: {agent} — {task}\n\n"
            f"**Timestamp:** {ts}\n\n"
            f"## Output\n{compressed}\n\n"
            f"## Meta\n{meta or {}}\n"
        )
        self.vault.save_note(title, content)
        self.journal.record_event({"type": "report", "agent": agent, "task": task})

        return self._format_for_telegram(report)

    def _format_for_telegram(self, report: Dict[str, Any]) -> str:
        return (
            f"📋 Report from {report['agent']}\n"
            f"Task: {report['task']}\n"
            f"Time: {report['timestamp']}\n"
            f"---\n"
            f"{report['output']}"
        )

    def recent_reports(self, n: int = 10) -> List[Dict[str, Any]]:
        return list(self._reports[-n:])[::-1]


if __name__ == "__main__":
    rrs = ReportReturnSystem()
    print(rrs.submit_report("AS", "workspace review", "All 7 services online. Vault synced. 71 notes indexed."))

```

LINKS:
[[All Mermaid Graphs]]
[[Cleanup Report]]
[[Module Guide]]
[[Cc Phase 01 Build Certification Report]]
[[Journal 20260602T004841Z Report]]
[[Journal 20260602T004841Z Report Oc2 20260602004841]]
[[Journal 20260602T005953Z Command Report]]
[[Ontology Core Summary]]
[[Self Heal Report]]
[[Bug Report]]
[[Citation Workflow]]
[[Dogfood Report Template]]
[[Server]]
[[System]]
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
[[Command Router]]
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
