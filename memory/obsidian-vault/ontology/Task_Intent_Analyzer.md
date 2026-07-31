# Task Intent Analyzer

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #observer

```python
﻿"""
O-1-B5: TaskIntentAnalyzer
===========================
Classifies task domain, complexity, execution requirements,
orchestration needs.

Output: {domain, complexity, requires_spawn, requires_repo_access,
requires_runtime_context, routing_hints}
"""

from __future__ import annotations

import re
from typing import Any


# Task domain classification patterns
# Order matters: more specific domains first
DOMAIN_PATTERNS: dict[str, list[str]] = {
    "repair": [
        r"\b(repair|fix|recover|restore|heal|stabilize)\b",
        r"\b(broken|crash|degrad|failure)\b",
        r"\b(restart|reboot|reset)\b",
        r"\b(fix.*broken|broken.*fix|repair.*system|system.*repair)\b",
    ],
    "debugging": [
        r"\b(debug|trace|log|stack|exception|issue|problem)\b",
        r"\b(why.*not|doesn't work|not working|fails?)\b",
        r"\b(investigate|diagnose|inspect)\b",
    ],
    "coding": [
        r"\b(code|implement|write|build|create|develop|function|class|module|api|endpoint)\b",
        r"\b(bug|patch|refactor|optimize)\b",
        r"\b(test|unittest|pytest|jest)\b",
    ],
    "research": [
        r"\b(research|analyse|investigate|study|explore|survey|review)\b",
        r"\b(what|how|why|when|compare|difference)\b",
        r"\b(documentation|docs|readme)\b",
    ],
    "architecture": [
        r"\b(architecture|design|structure|pattern|system|infrastructure)\b",
        r"\b(plan|blueprint|roadmap|strategy)\b",
        r"\b(microservice|monolith|layer|component|module)\b",
    ],
    "orchestration": [
        r"\b(orchestrate|coordinate|manage|schedule|spawn|delegate)\b",
        r"\b(agent|worker|pipeline|workflow|process)\b",
        r"\b(parallel|concurrent|async|background)\b",
    ],
    "visualization": [
        r"\b(visualize|chart|graph|plot|display|render|dashboard)\b",
        r"\b(ui|interface|component|page|screen|view)\b",
        r"\b(show|display|present)\b",
    ],
    "automation": [
        r"\b(automate|script|cron|schedule|batch|trigger)\b",
        r"\b(deploy|release|publish|push|merge)\b",
        r"\b(ci|cd|pipeline|build)\b",
    ],
    "system_analysis": [
        r"\b(analyz|monitor|metric|performance|load|capacity)\b",
        r"\b(status|health|check|report|summary)\b",
        r"\b(topology|entropy|continuity|field)\b",
    ],
}

# Complexity indicators
COMPLEXITY_INDICATORS = {
    "critical": [
        r"\b(critical|urgent|emergency|production|outage)\b",
        r"\b(multiple|several|many|all|every)\b",
        r"\b(architecture|redesign|rewrite|migrat)\b",
    ],
    "high": [
        r"\b(complex|advanced|comprehensive|full|complete)\b",
        r"\b(integrat|connect|combin|merge)\b",
        r"\b(optimiz|improve|enhance|upgrade)\b",
    ],
    "medium": [
        r"\b(update|modify|change|add|remove|edit)\b",
        r"\b(config|setup|install|create)\b",
    ],
}


class TaskIntentAnalyzer:
    """
    Analyzes user input to determine task intent.
    
    Uses keyword-based classification with confidence scoring.
    """

    def analyze(self, user_input: str) -> dict[str, Any]:
        """
        Analyze user input and return structured intent.
        
        Returns:
            {
                "domain": str,
                "confidence": float,
                "complexity": str,
                "requires_spawn": bool,
                "requires_repo_access": bool,
                "requires_runtime_context": bool,
                "routing_hints": dict,
            }
        """
        text = user_input.lower().strip()

        # Classify domain
        domain, confidence = self._classify_domain(text)

        # Estimate complexity
        complexity = self._estimate_complexity(text)

        # Determine requirements
        requires_spawn = self._requires_spawn(text, domain, complexity)
        requires_repo_access = self._requires_repo_access(text, domain)
        requires_runtime_context = self._requires_runtime_context(text, domain)

        # Build routing hints
        routing_hints = {
            "priority": self._estimate_priority(text),
            "estimated_duration": self._estimate_duration(complexity),
            "suggested_model": self._suggest_model(domain, complexity),
        }

        return {
            "domain": domain,
            "confidence": confidence,
            "complexity": complexity,
            "requires_spawn": requires_spawn,
            "requires_repo_access": requires_repo_access,
            "requires_runtime_context": requires_runtime_context,
            "routing_hints": routing_hints,
        }

    def _classify_domain(self, text: str) -> tuple[str, float]:
        """Classify task domain with confidence score."""
        scores: dict[str, int] = {}
        for domain, patterns in DOMAIN_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                score += len(matches)
            if score > 0:
                scores[domain] = score

        if not scores:
            return "general", 0.3

        best_domain = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = scores[best_domain] / total if total > 0 else 0.0
        return best_domain, min(confidence, 1.0)

    def _estimate_complexity(self, text: str) -> str:
        """Estimate task complexity."""
        for level in ["critical", "high", "medium"]:
            for pattern in COMPLEXITY_INDICATORS[level]:
                if re.search(pattern, text, re.IGNORECASE):
                    return level
        return "low"

    def _requires_spawn(self, text: str, domain: str, complexity: str) -> bool:
        """Determine if task requires spawning an agent."""
        if complexity in ("critical", "high"):
            return True
        if domain in ("orchestration", "automation"):
            return True
        if re.search(r"\b(parallel|concurrent|background|async|multiple)\b", text, re.IGNORECASE):
            return True
        return False

    def _requires_repo_access(self, text: str, domain: str) -> bool:
        """Determine if task requires repository access."""
        if domain in ("coding", "debugging", "repair"):
            return True
        if re.search(r"\b(repo|file|code|project|directory|folder)\b", text, re.IGNORECASE):
            return True
        return False

    def _requires_runtime_context(self, text: str, domain: str) -> bool:
        """Determine if task requires runtime context."""
        if domain in ("system_analysis", "orchestration", "visualization"):
            return True
        if re.search(r"\b(status|health|topology|entropy|runtime|state)\b", text, re.IGNORECASE):
            return True
        return False

    def _estimate_priority(self, text: str) -> str:
        if re.search(r"\b(urgent|asap|critical|emergency|now)\b", text, re.IGNORECASE):
            return "high"
        if re.search(r"\b(soon|today|important)\b", text, re.IGNORECASE):
            return "medium"
        return "normal"

    def _estimate_duration(self, complexity: str) -> str:
        return {
            "low": "< 1min",
            "medium": "1-5min",
            "high": "5-30min",
            "critical": "> 30min",
        }.get(complexity, "unknown")

    def _suggest_model(self, domain: str, complexity: str) -> str:
        if domain == "coding" and complexity in ("high", "critical"):
            return "qwen-coder"
        if domain in ("research", "architecture"):
            return "deepseek"
        if domain in ("system_analysis", "orchestration"):
            return "local"
        return "default"

```

LINKS:
[[All Mermaid Graphs]]
[[Architecture]]
[[Debugging]]
[[Module Guide]]
[[Readme]]
[[User]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Task Update]]
[[Ontology Core Summary]]
[[Task Flow]]
[[Blueprint]]
[[Cal]]
[[Citation Workflow]]
[[Dashboard]]
[[Patterns]]
[[Server]]
[[System]]
[[Workflow]]
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
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
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
