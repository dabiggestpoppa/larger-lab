#!/usr/bin/env python3
"""
CODEMAP Auto-Updater
=====================
Scans the workspace and generates/updates Mermaid diagrams in CODEMAP.md.
Run this whenever the architecture changes significantly.

Usage:
  python tools/codemap-updater.py          # Update all diagrams
  python tools/codemap-updater.py --check  # Check what would change (dry run)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent
CODEMAP_FILE = LAB_ROOT / "CODEMAP.md"
AGENT_TAGS_FILE = LAB_ROOT / ".agent-tags.json"


def load_agent_tags() -> dict:
    """Load agent tag registry."""
    if AGENT_TAGS_FILE.exists():
        with open(AGENT_TAGS_FILE) as f:
            return json.load(f)
    return {"agents": {}}


def scan_workspace_structure() -> dict:
    """Scan workspace for key directories and files."""
    structure = {
        "agents": [],
        "tools": [],
        "strategies": [],
        "progress_files": [],
        "memory_files": [],
        "key_files": [],
    }

    # Scan top-level for agent-related dirs
    for item in sorted(LAB_ROOT.iterdir()):
        if item.is_dir() and not item.name.startswith(".") and item.name not in [
            "__pycache__", "node_modules", ".venv", ".git", "htmlcov"
        ]:
            if item.name in ["progress", "tools", "nautilus", "strategies", "srrs_opc"]:
                structure["agents"].append(item.name)

    # Scan tools/
    tools_dir = LAB_ROOT / "tools"
    if tools_dir.exists():
        for f in sorted(tools_dir.glob("*.py")):
            structure["tools"].append(f.name)

    # Scan progress/
    progress_dir = LAB_ROOT / "progress"
    if progress_dir.exists():
        for f in sorted(progress_dir.glob("*.md")):
            structure["progress_files"].append(f.name)

    # Scan strategies/
    strategies_dir = LAB_ROOT / "strategies"
    if strategies_dir.exists():
        for f in sorted(strategies_dir.glob("*.py")):
            structure["strategies"].append(f.name)

    # Scan srrs_opc/
    srrs_dir = LAB_ROOT / "srrs_opc"
    if srrs_dir.exists():
        for f in sorted(srrs_dir.glob("*.py")):
            structure["agents"].append(f"srrs_opc/{f.name}")

    # Key root files
    for fname in ["CODEMAP.md", "WORKFLOW_PROTOCOL.md", "SYSTEM_ARCHITECTURE.md",
                  "PROJECT_PROGRESS_CLEAN.md", "TASK_BRIEF_TEMPLATE.json",
                  ".agent-tags.json", ".progress-sync-counters.json"]:
        if (LAB_ROOT / fname).exists():
            structure["key_files"].append(fname)

    return structure


def generate_system_overview_diagram(structure: dict) -> str:
    """Generate the system overview Mermaid diagram."""
    return """```mermaid
graph TB
    subgraph "Human Interface"
        H[Human / Board] --> CC[Claude Code<br/>🔵 Overseer]
        H --> OC[OpenClaw<br/>🟣 Analysis]
        H --> HR[Hermes<br/>🟢 Execution]
    end

    subgraph "Progress & Memory Layer"
        PP[progress/<br/>sub-progress files] --> SYNC[progress-sync.py<br/>v2]
        SYNC --> PM[Persistent Memory<br/>.openclaw/MEMORY.md<br/>.hermes/MEMORY.md]
        SYNC --> WM[Working Memory<br/>progress/*-memory.md]
        SYNC --> CM[CODEMAP.md<br/>Auto-updated]
    end

    subgraph "SRRA-OPH Phase 1"
        CL[CollarLayer] --> PP1[PlannerPatch]
        CL --> EP[ExecutionPatch]
        CL --> MP[MemoryPatch]
        CL --> RP[RepairPatch]
        CL --> AB[AgentBridge]
    end

    subgraph "Trading Engine"
        NT[Nautilus Trader<br/>Backtest Engine]
        STR[strategies/<br/>p90, symmetry, ema]
        DATA[data/<br/>CSV → Parquet]
    end

    subgraph "Tools"
        TU[tools/<br/>codemap-updater<br/>progress-sync<br/>task-runner]
    end

    CC --> PP
    OC --> PP
    HR --> PP
    CC --> TU
    HR --> NT
    AB --> OC
    AB --> HR
    DATA --> NT
    STR --> NT
```"""


def generate_agent_workflow_diagram() -> str:
    """Generate the agent workflow Mermaid diagram."""
    return """```mermaid
flowchart TD
    H[Human gives direction] --> CC[Claude Code<br/>Overseer]

    CC --> |Task Brief| OC[OpenClaw<br/>Analysis & Planning]
    OC --> |Execution Plan| HR[Hermes<br/>Execution]

    HR --> |Backtest| NT[Nautilus Trader]
    NT --> |Results| HR

    HR --> |Progress Update| PP[progress/hermes-progress.md]
    OC --> |Progress Update| PP2[progress/openclaw-progress.md]
    CC --> |Progress Update| PP3[progress/claude-code-progress.md]

    PP --> SYNC[progress-sync.py]
    PP2 --> SYNC
    PP3 --> SYNC

    SYNC --> |Every 3 updates| PPC[PROJECT_PROGRESS_CLEAN.md]
    SYNC --> |Working Memory| WM[progress/*-memory.md]
    SYNC --> |Append Summary| PM[.openclaw/MEMORY.md<br/>.hermes/MEMORY.md]
    SYNC --> |Global State| RM[/memories/repo/workspace-state.md]

    HR --> |Complete| REVIEW{Overseer Review}
    REVIEW --> |Approve| NEXT[Next Phase]
    REVIEW --> |Fix| HR
    NEXT --> |New Task| OC
```"""


def generate_data_flow_diagram() -> str:
    """Generate the data pipeline Mermaid diagram."""
    return """```mermaid
flowchart LR
    subgraph "Input"
        CSV[Downloads/*.csv<br/>29 files M1/M5 2022-2026]
    end

    subgraph "Processing"
        PREP[nautilus/step1_prep_data.py<br/>CSV → Parquet]
        VALID[Data Validation<br/>Schema Check]
    end

    subgraph "Execution"
        NT[Nautilus Trader<br/>Backtest Engine]
        SWEEP[Parameter Sweep<br/>Grid/Random Search]
    end

    subgraph "Output"
        REPORTS[nautilus/reports/<br/>Performance Metrics]
        PROGRESS[progress/<br/>Agent sub-progress files]
        MEMORY[Working Memory<br/>Auto-synced]
    end

    CSV --> PREP --> VALID --> NT --> SWEEP --> REPORTS
    REPORTS --> PROGRESS --> MEMORY
```"""


def generate_srra_architecture_diagram() -> str:
    """Generate the SRRA-OPH architecture Mermaid diagram."""
    return """```mermaid
graph LR
    subgraph "Collar Protocol"
        C1[CollarState<br/>JSON Contract]
    end

    subgraph "Observer Patches"
        PP[PlannerPatch<br/>Bounded Horizon: 10]
        EP[ExecutionPatch<br/>Bounded Actions: 100]
        MP[MemoryPatch<br/>Bounded History: 50]
        RP[RepairPatch<br/>Bounded Log: 100]
    end

    subgraph "Repair Loops"
        SC[Self Check]
        RE[Reconciliation]
        COMP[State Compression]
    end

    PP --> C1
    EP --> C1
    MP --> C1
    RP --> C1

    C1 --> PP
    C1 --> EP
    C1 --> MP
    C1 --> RP

    PP --> SC
    EP --> SC
    MP --> SC
    RP --> SC

    SC -->|Inconsistent| RE
    RE --> COMP
    COMP -->|Stabilized| C1

    style PP fill:#3498db,color:#fff
    style EP fill:#2ecc71,color:#fff
    style MP fill:#9b59b6,color:#fff
    style RP fill:#e74c3c,color:#fff
    style C1 fill:#f39c12,color:#fff
```"""


def generate_file_structure_diagram(structure: dict) -> str:
    """Generate the file structure Mermaid diagram."""
    tools_list = "\n".join(f"        T --> {t.replace('.py', '')}[{t}]" for t in structure["tools"][:8])
    progress_list = "\n".join(f"        P --> {p.replace('.md', '')}[{p}]" for p in structure["progress_files"][:6])

    return f"""```mermaid
graph TD
    ROOT[larger-lab/]

    ROOT --> AGT[agents/]
    ROOT --> NAUT[nautilus/]
    ROOT --> SRRS[srrs_opc/]
    ROOT --> PROG[progress/]
    ROOT --> TOOLS[tools/]
    ROOT --> STRAT[strategies/]

    subgraph "Tools"
        T[tools/]
{tools_list}
    end

    subgraph "Progress"
        P[progress/]
{progress_list}
    end

    ROOT --> DOCS[Documentation]
    DOCS --> CODEMAP[CODEMAP.md]
    DOCS --> WORKFLOW[WORKFLOW_PROTOCOL.md]
    DOCS --> ARCH[SYSTEM_ARCHITECTURE.md]
    DOCS --> PROJ[PROJECT_PROGRESS_CLEAN.md]
```"""


def update_codemap(dry_run: bool = False):
    """Update CODEMAP.md with current diagrams."""
    structure = scan_workspace_structure()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    diagrams = {
        "System Overview": generate_system_overview_diagram(structure),
        "Agent Workflow": generate_agent_workflow_diagram(),
        "Data Pipeline": generate_data_flow_diagram(),
        "SRRA-OPH Architecture": generate_srra_architecture_diagram(),
        "File Structure": generate_file_structure_diagram(structure),
    }

    if CODEMAP_FILE.exists():
        with open(CODEMAP_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "# CODEMAP - System Architecture\n\n"

    # Update each diagram section
    for title, diagram in diagrams.items():
        # Look for the section header and replace until next section or end
        pattern = rf"### {re.escape(title)}.*?(?=\n### |\Z)"
        replacement = f"### {title}\n\n{diagram}\n"

        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, replacement.strip() + "\n", content, flags=re.DOTALL)
        else:
            # Append new section
            content = content.rstrip() + "\n\n" + replacement

    # Update timestamp
    timestamp_pattern = r"> \*\*Last Updated:\*\* .*"
    if re.search(timestamp_pattern, content):
        content = re.sub(timestamp_pattern, f"> **Last Updated:** {now}", content)
    else:
        content = f"> **Last Updated:** {now}\n\n" + content

    if dry_run:
        print("🔍 Dry run — would update the following sections:")
        for title in diagrams:
            print(f"  ✓ {title}")
        return

    with open(CODEMAP_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ CODEMAP.md updated at {now}")
    print(f"   Sections updated: {', '.join(diagrams.keys())}")


def main():
    parser = argparse.ArgumentParser(description="CODEMAP Auto-Updater")
    parser.add_argument("--check", action="store_true", help="Dry run — show what would change")
    args = parser.parse_args()

    update_codemap(dry_run=args.check)


if __name__ == "__main__":
    main()
