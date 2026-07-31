# Pattern Distillation

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #observer

```python
"""Phase 2: Pattern Distillation + Failure Intelligence.

Pattern Distillation:
  - Scans vault for recurring operational patterns
  - Compresses into operational summaries
  - Writes distilled notes back to vault

Failure Intelligence:
  - Every operational failure becomes structured entry: CAUSE / FIX / RESULT / LINKS
  - Indexed for retrieval and cross-referencing
"""
import os
import re
import datetime
from typing import Dict, Any, List
from collections import Counter
from core.observer.vault import Vault


class PatternDistillation:
    def __init__(self, vault: Vault = None):
        self.vault = vault or Vault()

    def distill_patterns(self, min_occurrences: int = 2) -> List[Dict[str, Any]]:
        """Scan vault for recurring patterns (repeated phrases, common structures)."""
        phrase_counter: Counter = Counter()
        file_phrases: Dict[str, List[str]] = {}

        for root, _, files in os.walk(self.vault.path):
            for fn in files:
                if not fn.lower().endswith('.md'):
                    continue
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, self.vault.path)
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        text = f.read()
                except Exception:
                    continue
                # extract 3-4 word phrases
                words = re.findall(r'\w+', text.lower())
                phrases = []
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    if len(phrase) > 10:
                        phrases.append(phrase)
                        phrase_counter[phrase] += 1
                file_phrases[rel] = phrases

        # filter recurring
        recurring = [
            {"phrase": p, "count": c}
            for p, c in phrase_counter.most_common(50)
            if c >= min_occurrences
        ]
        return recurring

    def write_distilled_summary(self, patterns: List[Dict[str, Any]]) -> str:
        """Write a distilled operational summary to the vault."""
        ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        title = f"distilled_patterns_{ts}"
        lines = ["# Distilled Operational Patterns", "", f"**Generated:** {ts}", ""]
        for p in patterns[:30]:
            lines.append(f"- `{p['phrase']}` — occurred {p['count']}x")
        content = "\n".join(lines)
        return self.vault.save_note(title, content)


class FailureIntelligence:
    """Indexes and retrieves structured failure entries from the vault."""

    def __init__(self, vault: Vault = None):
        self.vault = vault or Vault()

    def find_failures(self, keyword: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
        """Search vault for failure entries matching keyword."""
        results = []
        for root, _, files in os.walk(self.vault.path):
            for fn in files:
                if not fn.lower().endswith('.md'):
                    continue
                if 'failure' not in fn.lower():
                    continue
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, self.vault.path)
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        text = f.read()
                except Exception:
                    continue
                if keyword and keyword.lower() not in text.lower():
                    continue
                # extract CAUSE section
                cause = ""
                fix = ""
                result = ""
                in_section = ""
                for line in text.splitlines():
                    if line.strip().upper() == "## CAUSE":
                        in_section = "cause"
                        continue
                    elif line.strip().upper() == "## FIX":
                        in_section = "fix"
                        continue
                    elif line.strip().upper() == "## RESULT":
                        in_section = "result"
                        continue
                    elif line.strip().startswith("## "):
                        in_section = ""
                        continue
                    if in_section == "cause":
                        cause += line + " "
                    elif in_section == "fix":
                        fix += line + " "
                    elif in_section == "result":
                        result += line + " "
                results.append({
                    "path": rel,
                    "cause": cause.strip()[:200],
                    "fix": fix.strip()[:200],
                    "result": result.strip()[:200]
                })
                if len(results) >= max_results:
                    return results
        return results

    def similar_failures(self, description: str) -> List[Dict[str, Any]]:
        """Find failures similar to the given description (keyword overlap)."""
        words = set(re.findall(r'\w+', description.lower()))
        all_failures = self.find_failures(max_results=50)
        scored = []
        for f in all_failures:
            f_words = set(re.findall(r'\w', f.get('cause', '').lower()))
            overlap = len(words & f_words)
            if overlap > 0:
                scored.append((overlap, f))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:10]]


if __name__ == "__main__":
    vault = Vault()
    pd = PatternDistillation(vault)
    patterns = pd.distill_patterns(min_occurrences=2)
    print(f"Found {len(patterns)} recurring patterns")
    if patterns:
        fp = pd.write_distilled_summary(patterns)
        print(f"Wrote distilled summary to {fp}")

    fi = FailureIntelligence(vault)
    failures = fi.find_failures()
    print(f"Indexed {len(failures)} failure entries")

```

LINKS:
[[All Mermaid Graphs]]
[[Module Guide]]
[[Ontology Core Summary]]
[[Test Pattern]]
[[Vault Distillation 20260531 0245]]
[[Citation Workflow]]
[[Description]]
[[Failures]]
[[Patterns]]
[[Server]]
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
