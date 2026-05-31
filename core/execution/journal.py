"""
Execution Journal — Phase 0F
Track agent actions, failures, corrections, retries, successful heuristics.

Core principle: Every agent execution leaves a trace.
Raw traces are noise. Compressed journals are intelligence.

Usage:
    from core.execution.journal import ExecutionJournal
    journal = ExecutionJournal(vault_path="/path/to/O2C-VAULT")
    journal.log_step("load_csv", "failed", details="File not found")
    journal.log_step("normalize_schema", "success", details="Schema aligned")
    journal.compress_and_save()  # Distill to markdown + write to vault
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from core.obsidian.vault_writer import VaultWriter, DEFAULT_VAULT_PATH
from core.obsidian.compressor import compress_trace


class ExecutionJournal:
    """Track and compress agent execution traces."""

    def __init__(
        self,
        agent_name: str = "unknown",
        task: str = "",
        vault_path: Optional[str | Path] = None,
    ):
        self.agent_name = agent_name
        self.task = task
        self.vault_path = Path(vault_path) if vault_path else DEFAULT_VAULT_PATH
        self.writer = VaultWriter(vault_path=self.vault_path)
        self.steps: list[dict] = []
        self.start_time = datetime.now(timezone.utc)
        self.end_time: datetime | None = None
        self._successes: list[str] = []
        self._failures: list[str] = []
        self._corrections: list[str] = []

    def log_step(
        self,
        step_name: str,
        result: str,  # "success" or "failed"
        details: str = "",
        duration_ms: float = 0,
    ):
        """Log an execution step."""
        entry = {
            "step": step_name,
            "result": result,
            "details": details,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.steps.append(entry)

        if result == "success":
            self._successes.append(step_name)
        elif result == "failed":
            self._failures.append(step_name)

    def log_correction(self, failed_step: str, correction: str, result: str):
        """Log a correction applied after a failure."""
        self._corrections.append({
            "failed_step": failed_step,
            "correction": correction,
            "result": result,
        })
        self.log_step(f"correction:{failed_step}", "success", details=correction)

    def summarize(self) -> dict:
        """Get a summary of the execution."""
        self.end_time = datetime.now(timezone.utc)
        duration = (self.end_time - self.start_time).total_seconds()

        return {
            "agent": self.agent_name,
            "task": self.task,
            "total_steps": len(self.steps),
            "successes": len(self._successes),
            "failures": len(self._failures),
            "corrections": len(self._corrections),
            "duration_seconds": round(duration, 2),
            "success_rate": round(
                len(self._successes) / max(len(self.steps), 1), 2
            ),
        }

    def to_markdown(self) -> str:
        """Convert journal to compressed markdown."""
        summary = self.summarize()
        timestamp = self.start_time.strftime('%Y-%m-%d %H:%M UTC')

        lines = [
            f"# Agent Execution Report — {self.agent_name}",
            "",
            f"> Task: {self.task} | Date: {timestamp} | Duration: {summary['duration_seconds']}s",
            "",
            "## Summary",
            "",
            f"- **Total Steps:** {summary['total_steps']}",
            f"- **Successes:** {summary['successes']}",
            f"- **Failures:** {summary['failures']}",
            f"- **Corrections:** {summary['corrections']}",
            f"- **Success Rate:** {summary['success_rate']*100:.0f}%",
            "",
        ]

        # Failures section
        if self._failures:
            lines.append("## Failures")
            lines.append("")
            for step in self.steps:
                if step["result"] == "failed":
                    lines.append(f"- **{step['step']}**: {step['details']}")
            lines.append("")

        # Corrections section
        if self._corrections:
            lines.append("## Corrections")
            lines.append("")
            for corr in self._corrections:
                lines.append(f"- **{corr['failed_step']}**: {corr['correction']} → {corr['result']}")
            lines.append("")

        # All steps
        lines.append("## Execution Steps")
        lines.append("")
        lines.append("| Step | Result | Details |")
        lines.append("|------|--------|---------|")
        for step in self.steps:
            result_icon = "✅" if step["result"] == "success" else "❌"
            lines.append(f"| {step['step']} | {result_icon} {step['result']} | {step['details']} |")
        lines.append("")

        # Links
        lines.append("LINKS:")
        lines.append(f"[[{self.agent_name}]]")
        if self._failures:
            lines.append("[[Failures]]")
        if self._corrections:
            lines.append("[[Corrections]]")
        lines.append("")

        return "\n".join(lines)

    def compress_and_save(self) -> Path:
        """Compress journal and write to vault."""
        markdown = self.to_markdown()
        title = f"Execution {self.agent_name} {self.start_time.strftime('%Y%m%d_%H%M')}"
        path = self.writer.write_note(
            category="execution",
            title=title,
            content={
                "cause": f"Agent {self.agent_name} executed task: {self.task}",
                "fix": "See corrections applied" if self._corrections else "No corrections needed",
                "result": f"Success rate: {self.summarize()['success_rate']*100:.0f}%",
                "links": [self.agent_name],
            },
        )
        # Also write the full markdown
        full_path = path.with_name(path.stem + "_full.md")
        full_path.write_text(markdown, encoding="utf-8")
        return path

    def to_json(self) -> str:
        """Serialize journal to JSON."""
        return json.dumps({
            "agent": self.agent_name,
            "task": self.task,
            "steps": self.steps,
            "successes": self._successes,
            "failures": self._failures,
            "corrections": self._corrections,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }, indent=2)
