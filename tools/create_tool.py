#!/usr/bin/env python3
"""
create_tool.py — GitHub Repo → Agent Tool + Skill Pipeline

Automated pipeline that turns any GitHub repository into:
  1. A cloned repo in C:\\Users\\wifik\\Desktop\\projects\\
  2. A CLI harness (agent-harness/) with Click-based CLI
  3. A SKILL.md in skills/<tool-name>/
  4. Skill distribution to all agent directories
  5. Progress sync + team notification

Usage:
    python tools/create_tool.py <github-url-or-local-path> [options]

Examples:
    python tools/create_tool.py https://github.com/lukilabs/beautiful-mermaid
    python tools/create_tool.py https://github.com/user/repo --name my-tool --dry-run
    python tools/create_tool.py C:\\Users\\wifik\\Desktop\\projects\\some-repo --local
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ─── Constants ───────────────────────────────────────────────────────────────

PROJECTS_DIR = Path(r"C:\Users\wifik\Desktop\projects")
WORKSPACE_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
SKILLS_DIR = WORKSPACE_DIR / "skills"
TOOLS_DIR = WORKSPACE_DIR / "tools"
PROGRESS_DIR = WORKSPACE_DIR / "progress"
TEAM_CHAT = WORKSPACE_DIR / "shared-conversations" / "team-chat.md"
AGENT_TAGS = WORKSPACE_DIR / ".agent-tags.json"
CODEMAP = WORKSPACE_DIR / "CODEMAP.md"

# Agent skill directories for distribution
AGENT_SKILL_DIRS = [
    WORKSPACE_DIR / ".openclaw" / "skills",
    WORKSPACE_DIR / ".hermes" / "skills",
    WORKSPACE_DIR / "agent-lab" / "agents" / "hermes" / "skills",
]

# ─── Utility Functions ───────────────────────────────────────────────────────

def run_cmd(cmd, cwd=None, check=True, capture=True):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, check=check,
            capture_output=capture, text=True
        )
        return result.stdout.strip() if result.stdout else ""
    except subprocess.CalledProcessError as e:
        if check:
            print(f"  [ERROR] Command failed: {cmd}")
            print(f"  {e.stderr[:500] if e.stderr else 'no stderr'}")
        return None


def git_clone(url, dest):
    """Clone a git repo to dest. Returns True on success."""
    print(f"  [GIT] Cloning {url} → {dest}")
    result = run_cmd(f"git clone {url} {dest}", check=False)
    return dest.exists()


def detect_repo_type(repo_path):
    """Analyze repo and classify its type."""
    path = Path(repo_path)
    indicators = {
        "has_setup_py": (path / "setup.py").exists(),
        "has_pyproject": (path / "pyproject.toml").exists(),
        "has_package_json": (path / "package.json").exists(),
        "has_cargo": (path / "Cargo.toml").exists(),
        "has_gemfile": (path / "Gemfile").exists(),
        "has_go_mod": (path / "go.mod").exists(),
        "has_readme": (path / "README.md").exists() or (path / "readme.md").exists(),
        "has_license": any((path / f).exists() for f in ["LICENSE", "LICENSE.md", "LICENSE.txt"]),
        "has_src_dir": (path / "src").is_dir(),
        "has_lib_dir": (path / "lib").is_dir(),
        "has_bin_dir": (path / "bin").is_dir(),
        "has_cli_dir": (path / "cli").is_dir() or (path / "cmd").is_dir(),
        "has_gui_indicators": False,
        "has_web_indicators": False,
        "has_ml_indicators": False,
        "has_docs_only": False,
    }

    # Check for GUI frameworks
    gui_files = ["mainwindow", "app.py", "electron", "qt", "gtk", "wx"]
    for f in gui_files:
        if list(path.glob(f"**/{f}*")):
            indicators["has_gui_indicators"] = True
            break

    # Check for web frameworks
    web_files = ["app.py", "server.py", "express", "flask", "fastapi", "next.config"]
    for f in web_files:
        if list(path.glob(f"**/{f}*")):
            indicators["has_web_indicators"] = True
            break

    # Check for ML/data
    ml_files = ["model", "train", "dataset", "inference", "predict"]
    for f in ml_files:
        if list(path.glob(f"**/{f}*")):
            indicators["has_ml_indicators"] = True
            break

    # Check if docs-only
    code_exts = {".py", ".js", ".ts", ".go", ".rs", ".rb", ".java", ".cpp", ".c"}
    has_code = any(p.suffix in code_exts for p in path.rglob("*") if p.is_file())
    if not has_code and indicators["has_readme"]:
        indicators["has_docs_only"] = True

    # Classify
    if indicators["has_docs_only"]:
        return "docs", indicators
    elif indicators["has_gui_indicators"]:
        return "gui", indicators
    elif indicators["has_web_indicators"]:
        return "web", indicators
    elif indicators["has_ml_indicators"]:
        return "ml", indicators
    elif indicators["has_setup_py"] or indicators["has_pyproject"]:
        # Check if it has CLI entry points
        return "python-lib", indicators
    elif indicators["has_package_json"]:
        return "node-tool", indicators
    elif indicators["has_cargo"]:
        return "rust-tool", indicators
    elif indicators["has_go_mod"]:
        return "go-tool", indicators
    else:
        return "unknown", indicators


def read_readme(repo_path):
    """Read README content for analysis."""
    for name in ["README.md", "readme.md", "README.rst", "README"]:
        p = Path(repo_path) / name
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")[:5000]
    return ""


def extract_description(readme):
    """Extract a one-line description from README."""
    lines = readme.split("\n")
    for line in lines[:20]:
        line = line.strip()
        # Skip title lines (starting with #)
        if line and not line.startswith("#") and len(line) > 10:
            # Clean up markdown
            line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
            line = re.sub(r"[*_`]", "", line)
            if len(line) < 120:
                return line
    return ""


def detect_language(repo_path):
    """Detect primary language from file extensions."""
    ext_counts = {}
    for p in Path(repo_path).rglob("*"):
        if p.is_file() and p.suffix:
            ext_counts[p.suffix] = ext_counts.get(p.suffix, 0) + 1

    lang_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".java": "Java",
        ".cpp": "C++", ".c": "C", ".cs": "C#", ".php": "PHP",
    }

    if not ext_counts:
        return "Unknown"

    top_ext = max(ext_counts, key=ext_counts.get)
    return lang_map.get(top_ext, top_ext.lstrip(".").title())


def get_repo_name(url_or_path):
    """Extract repo name from URL or path."""
    if url_or_path.startswith("http"):
        name = url_or_path.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name
    return Path(url_or_path).name


def kebab_to_snake(name):
    """Convert kebab-case to snake_case."""
    return name.replace("-", "_")


# ─── Phase Functions ─────────────────────────────────────────────────────────

def phase_0_acquire(source, dest_dir):
    """Phase 0: Source Acquisition."""
    print("\n═══ Phase 0: Source Acquisition ═══")
    name = get_repo_name(source)
    dest = dest_dir / name

    if dest.exists():
        print(f"  [SKIP] Already cloned at {dest}")
        # Pull latest
        run_cmd("git pull", cwd=dest, check=False)
        print(f"  [GIT] Pulled latest changes")
    else:
        if source.startswith("http"):
            if not git_clone(source, dest):
                print(f"  [FAIL] Could not clone {source}")
                return None
        else:
            # Local path
            src = Path(source)
            if not src.exists():
                print(f"  [FAIL] Local path does not exist: {source}")
                return None
            print(f"  [LOCAL] Using existing path: {src}")
            return src

    return dest


def phase_1_analyze(repo_path):
    """Phase 1: Codebase Analysis."""
    print("\n═══ Phase 1: Codebase Analysis ═══")

    repo_type, indicators = detect_repo_type(repo_path)
    readme = read_readme(repo_path)
    description = extract_description(readme)
    language = detect_language(repo_path)
    name = get_repo_name(str(repo_path))

    # Count files
    file_count = sum(1 for _ in Path(repo_path).rglob("*") if _.is_file())

    analysis = {
        "name": name,
        "path": str(repo_path),
        "type": repo_type,
        "language": language,
        "description": description,
        "file_count": file_count,
        "indicators": indicators,
        "readme_excerpt": readme[:1000],
    }

    print(f"  Name:        {name}")
    print(f"  Type:        {repo_type}")
    print(f"  Language:    {language}")
    print(f"  Files:       {file_count}")
    print(f"  Description: {description[:80] if description else 'N/A'}")

    return analysis


def phase_2_design(analysis, args):
    """Phase 2: Tool Architecture Design."""
    print("\n═══ Phase 2: Tool Architecture Design ═══")

    name = args.name or analysis["name"]
    repo_type = analysis["type"]

    # Choose integration pattern
    patterns = {
        "docs": "skill-only",
        "gui": "cli-anything-full",
        "web": "api-client-cli",
        "ml": "pipeline-cli",
        "python-lib": "click-wrapper",
        "node-tool": "npx-wrapper",
        "rust-tool": "binary-wrapper",
        "go-tool": "binary-wrapper",
        "unknown": "skill-only",
    }

    pattern = patterns.get(repo_type, "skill-only")

    # Determine install method
    if repo_type == "python-lib":
        install_method = "pip"
    elif repo_type == "node-tool":
        install_method = "npx"
    elif repo_type in ("rust-tool", "go-tool"):
        install_method = "binary"
    else:
        install_method = "direct"

    design = {
        "tool_name": kebab_to_snake(name),
        "display_name": name,
        "integration_pattern": pattern,
        "install_method": install_method,
        "needs_cli": pattern != "skill-only",
        "needs_repl": pattern in ("cli-anything-full", "click-wrapper", "api-client-cli"),
        "category": args.category or "other",
        "focus": args.focus or "",
    }

    print(f"  Tool name:   {design['tool_name']}")
    print(f"  Pattern:     {pattern}")
    print(f"  Install:     {install_method}")
    print(f"  Needs CLI:   {design['needs_cli']}")
    print(f"  Category:    {design['category']}")

    return design


def phase_3_implement(repo_path, analysis, design):
    """Phase 3: Implementation."""
    print("\n═══ Phase 3: Implementation ═══")

    if not design["needs_cli"]:
        print("  [SKIP] Skill-only integration, no CLI needed")
        return None

    tool_name = design["tool_name"]
    pattern = design["integration_pattern"]

    if pattern == "click-wrapper":
        return _build_click_wrapper(repo_path, analysis, design)
    elif pattern == "npx-wrapper":
        return _build_npx_wrapper(repo_path, analysis, design)
    elif pattern == "api-client-cli":
        return _build_api_client(repo_path, analysis, design)
    elif pattern == "pipeline-cli":
        return _build_pipeline_cli(repo_path, analysis, design)
    elif pattern == "cli-anything-full":
        return _build_cli_anything(repo_path, analysis, design)
    else:
        print(f"  [SKIP] Pattern '{pattern}' not yet implemented, generating skill-only")
        return None


def _build_click_wrapper(repo_path, analysis, design):
    """Build a Click CLI wrapper for a Python library."""
    tool_name = design["tool_name"]
    harness_dir = Path(repo_path) / "agent-harness"
    pkg_dir = harness_dir / "cli_anything" / tool_name

    print(f"  [BUILD] Click wrapper → {pkg_dir}")

    # Create directory structure
    for d in ["core", "utils", "tests"]:
        (pkg_dir / d).mkdir(parents=True, exist_ok=True)
        (pkg_dir / d / "__init__.py").touch()

    # Generate core module
    core_init = pkg_dir / "core" / "__init__.py"
    core_init.write_text(textwrap.dedent(f'''\
        """Core modules for {tool_name} CLI."""

        import json
        from pathlib import Path
        from typing import Optional, Any


        class {tool_name.title().replace("_", "")}Session:
            """Session state for {tool_name} operations."""

            def __init__(self, project_path: Optional[str] = None):
                self.project_path = project_path
                self.history = []
                self.state = {{}}

            def to_dict(self) -> dict:
                return {{
                    "project_path": self.project_path,
                    "history_length": len(self.history),
                    "state": self.state,
                }}

            def save(self, path: str) -> None:
                Path(path).write_text(json.dumps(self.to_dict(), indent=2))

            @classmethod
            def load(cls, path: str) -> "{tool_name.title().replace('_', '')}Session":
                data = json.loads(Path(path).read_text())
                session = cls(data.get("project_path"))
                session.state = data.get("state", {{}})
                return session
        '''))

    # Generate CLI module
    cli_file = pkg_dir / "cli.py"
    cli_file.write_text(textwrap.dedent(f'''\
        """CLI for {tool_name}."""

        import json
        import sys
        from typing import Optional

        import click

        from cli_anything.{tool_name}.core import {tool_name.title().replace("_", "")}Session


        @click.group(invoke_without_command=True)
        @click.option("--json", "json_output", is_flag=True, help="Output as JSON")
        @click.option("--project", type=str, default=None, help="Project file path")
        @click.pass_context
        def cli(ctx, json_output, project):
            """{analysis.get("description", tool_name)}"""
            ctx.ensure_object(dict)
            ctx.obj["json"] = json_output
            if project:
                ctx.obj["session"] = {tool_name.title().replace("_", "")}Session.load(project)
            else:
                ctx.obj["session"] = {tool_name.title().replace("_", "")}Session()


        @cli.command()
        @click.pass_context
        def info(ctx):
            """Show session info."""
            session = ctx.obj["session"]
            if ctx.obj.get("json"):
                click.echo(json.dumps(session.to_dict(), indent=2))
            else:
                click.echo(f"Project: {{session.project_path or 'None'}}")
                click.echo(f"History: {{len(session.history)}} commands")


        @cli.command()
        @click.argument("key")
        @click.argument("value")
        @click.pass_context
        def set(ctx, key, value):
            """Set a state value."""
            ctx.obj["session"].state[key] = value
            if ctx.obj.get("json"):
                click.echo(json.dumps({{"ok": True, "key": key, "value": value}}))
            else:
                click.echo(f"Set {{key}} = {{value}}")


        @cli.command()
        @click.pass_context
        def status(ctx):
            """Show status."""
            session = ctx.obj["session"]
            if ctx.obj.get("json"):
                click.echo(json.dumps(session.to_dict(), indent=2))
            else:
                for k, v in session.state.items():
                    click.echo(f"  {{k}}: {{v}}")


        def main():
            cli(obj={{}})


        if __name__ == "__main__":
            main()
        '''))

    # Generate utils
    utils_init = pkg_dir / "utils" / "__init__.py"
    utils_init.write_text(textwrap.dedent(f'''\
        """Utilities for {tool_name} CLI."""

        import json
        from typing import Any


        def format_json(data: Any) -> str:
            return json.dumps(data, indent=2, default=str)


        def format_table(headers: list, rows: list) -> str:
            if not rows:
                return "No data."
            widths = [max(len(str(h)), max(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
            lines = []
            lines.append("  ".join(str(h).ljust(w) for h, w in zip(headers, widths)))
            lines.append("  ".join("-" * w for w in widths))
            for row in rows:
                lines.append("  ".join(str(v).ljust(w) for v, w in zip(row, widths)))
            return "\\n".join(lines)
        '''))

    # Generate setup.py
    setup_py = harness_dir / "setup.py"
    setup_py.write_text(textwrap.dedent(f'''\
        from setuptools import setup, find_namespace_packages

        setup(
            name="cli-anything-{design['tool_name']}",
            version="0.1.0",
            description="{analysis.get('description', design['display_name'])}",
            packages=find_namespace_packages(include=["cli_anything.*"]),
            install_requires=["click>=8.0"],
            entry_points={{
                "console_scripts": [
                    "cli-anything-{design['tool_name']}=cli_anything.{tool_name}.cli:main",
                ],
            }},
            python_requires=">=3.10",
        )
        '''))

    # Generate repl_skin
    repl_skin = pkg_dir / "utils" / "repl_skin.py"
    repl_skin.write_text(textwrap.dedent(f'''\
        """REPL interface for {tool_name}."""

        import sys
        from typing import Optional


        BANNER = \"\"\"
        ╔══════════════════════════════════════════╗
        ║       cli-anything-{design['tool_name']} v0.1.0          ║
        ║  {design['display_name']} CLI for AI Agents       ║
        ╚══════════════════════════════════════════╝
        \"\"\".lstrip()


        def print_banner():
            print(BANNER)


        def print_prompt(session_name: str = "") -> str:
            if session_name:
                return f"{design['tool_name']}[{session_name}]> "
            return f"{design['tool_name']}> "


        def run_repl(cli_func):
            \"\"\"Run interactive REPL.\"\"\"
            print_banner()
            while True:
                try:
                    line = input(print_prompt())
                    if line.strip() in ("exit", "quit", "q"):
                        print("Goodbye! 👋")
                        break
                    if line.strip():
                        cli_func(line)
                except (EOFError, KeyboardInterrupt):
                    print("\\nGoodbye! 👋")
                    break
        '''))

    print(f"  [DONE] Click wrapper created at {harness_dir}")
    return harness_dir


def _build_npx_wrapper(repo_path, analysis, design):
    """Build an npx wrapper for a Node.js tool."""
    tool_name = design["tool_name"]
    wrapper_path = TOOLS_DIR / f"{tool_name}.py"

    print(f"  [BUILD] npx wrapper → {wrapper_path}")

    wrapper_path.write_text(textwrap.dedent(f'''\
        #!/usr/bin/env python3
        \"\"\"Python wrapper for {design['display_name']} (npx-based).\"\"\"

        import argparse
        import subprocess
        import sys
        import json
        from pathlib import Path


        TOOL_NAME = "{design['display_name']}"
        NPX_CMD = "{analysis['name']}"


        def run_npx(args: list, json_output: bool = False) -> str:
            """Run the tool via npx."""
            cmd = ["npx", NPX_CMD] + args
            if json_output:
                cmd.append("--json")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error: {{result.stderr[:500]}}", file=sys.stderr)
                sys.exit(result.returncode)
            return result.stdout


        def main():
            parser = argparse.ArgumentParser(description="{analysis.get('description', tool_name)}")
            parser.add_argument("command", nargs="?", help="Command to run")
            parser.add_argument("args", nargs="*", help="Command arguments")
            parser.add_argument("--json", action="store_true", help="Output as JSON")
            parser.add_argument("--output", "-o", help="Output file path")
            parser.add_argument("--help-tool", action="store_true", help="Show tool's own --help")

            args = parser.parse_args()

            if args.help_tool:
                print(run_npx(["--help"]))
                return

            if args.command:
                cmd_args = [args.command] + (args.args or [])
                output = run_npx(cmd_args, args.json)
            else:
                output = run_npx(["--help"])

            if args.output:
                Path(args.output).write_text(output)
                print(f"Output written to {{args.output}}")
            else:
                print(output)


        if __name__ == "__main__":
            main()
        '''))

    print(f"  [DONE] npx wrapper created at {wrapper_path}")
    return wrapper_path


def _build_api_client(repo_path, analysis, design):
    """Build an API client CLI for web apps."""
    return _build_click_wrapper(repo_path, analysis, design)  # Same pattern for now


def _build_pipeline_cli(repo_path, analysis, design):
    """Build a pipeline CLI for ML/data tools."""
    return _build_click_wrapper(repo_path, analysis, design)  # Same pattern for now


def _build_cli_anything(repo_path, analysis, design):
    """Delegate to CLI-Anything full pipeline."""
    print(f"  [DELEGATE] Full CLI-Anything pipeline for GUI app")
    print(f"  [INFO] Use: /cli-anything {repo_path} (in Claude Code)")
    print(f"  [INFO] Or: python tools/cli_anything.py build {repo_path}")
    return None


def phase_4_generate_skill(repo_path, analysis, design, harness_result):
    """Phase 4: SKILL.md Generation."""
    print("\n═══ Phase 4: SKILL.md Generation ═══")

    tool_name = design["tool_name"]
    display_name = design["display_name"]
    description = analysis.get("description", f"{display_name} agent tool")
    category = design["category"]
    pattern = design["integration_pattern"]
    language = analysis["language"]

    # Build command examples based on pattern
    if pattern == "skill-only":
        cmd_examples = f"""```bash
# Read the skill for detailed usage
cat skills/{tool_name}/SKILL.md
```"""
    elif pattern == "npx-wrapper":
        cmd_examples = f"""```bash
# Use via Python wrapper
python tools/{tool_name}.py --help
python tools/{tool_name}.py <command> [args] --json

# Or directly via npx
npx {analysis['name']} --help
```"""
    else:
        cmd_examples = f"""```bash
# Install the CLI
cd {repo_path}/agent-harness && pip install -e .

# Use from anywhere
cli-anything-{tool_name} --help
cli-anything-{tool_name}           # enters REPL
cli-anything-{tool_name} --json info  # JSON output for agents
```"""

    skill_content = textwrap.dedent(f'''\
        ---
        name: {tool_name}
        description: >
          {description}.
          Auto-generated by create_tool.py from {analysis.get("name", display_name)}.
          Category: {category}. Language: {language}.
        version: 0.1.0
        source: {analysis.get("path", "unknown")}
        ---

        # {display_name} — Agent Tool

        > **Source**: Auto-generated from repository
        > **Language**: {language}
        > **Type**: {pattern}
        > **Category**: {category}

        ## When to Use

        - Tasks related to {display_name}'s functionality
        - When the user asks to use, run, or interact with {display_name}
        - Agent needs to leverage {display_name} capabilities programmatically

        ## Quick Start

        {cmd_examples}

        ## Details

        {description}

        **Repository**: {analysis.get("path", "N/A")}
        **Files**: {analysis.get("file_count", "N/A")}
        **Language**: {language}
        **Integration Pattern**: {pattern}

        ## Agent Integration

        This tool was auto-generated by the create_tool.py pipeline.
        For the full methodology, see `skills/create-tool/SKILL.md`.

        ## Reference Files
        - `skills/{tool_name}/SKILL.md` — This file
        - `tools/{tool_name}.py` — Python wrapper (if applicable)
        - `{repo_path}/agent-harness/` — CLI harness (if built)
    ''')

    # Write to main skills directory
    skill_dir = SKILLS_DIR / tool_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(skill_content)

    print(f"  [DONE] SKILL.md → {skill_file}")
    return skill_file


def phase_5_install_and_register(repo_path, analysis, design, harness_result, skill_file):
    """Phase 5: Installation + Registration."""
    print("\n═══ Phase 5: Installation + Registration ═══")

    tool_name = design["tool_name"]

    # 1. Install Python package if harness exists
    if harness_result and Path(harness_result).exists():
        harness_dir = Path(harness_result)
        if (harness_dir / "setup.py").exists():
            print(f"  [INSTALL] pip install -e {harness_dir}")
            result = run_cmd(f"{sys.executable} -m pip install -e .", cwd=harness_dir, check=False)
            if result is not None:
                print(f"  [DONE] Package installed")
            else:
                print(f"  [WARN] pip install failed, continuing...")

    # 2. Copy skill to all agent directories
    skill_source = SKILLS_DIR / tool_name / "SKILL.md"
    if skill_source.exists():
        for agent_dir in AGENT_SKILL_DIRS:
            agent_skill_dir = agent_dir / tool_name
            agent_skill_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(skill_source, agent_skill_dir / "SKILL.md")
            print(f"  [DISTRIBUTED] → {agent_skill_dir}")

    # 3. Register in .agent-tags.json (if not already)
    if AGENT_TAGS.exists():
        try:
            tags = json.loads(AGENT_TAGS.read_text())
            tools = tags.get("tools", [])
            entry = {
                "name": tool_name,
                "display_name": design["display_name"],
                "category": design["category"],
                "source": str(repo_path),
                "skill": f"skills/{tool_name}/SKILL.md",
                "added": datetime.now(timezone.utc).isoformat(),
            }
            # Check for duplicates
            if not any(t.get("name") == tool_name for t in tools):
                tools.append(entry)
                tags["tools"] = tools
                AGENT_TAGS.write_text(json.dumps(tags, indent=2))
                print(f"  [REGISTERED] in .agent-tags.json")
            else:
                print(f"  [SKIP] Already registered in .agent-tags.json")
        except (json.JSONDecodeError, KeyError):
            print(f"  [WARN] Could not update .agent-tags.json")

    print(f"  [DONE] Installation + registration complete")


def phase_6_sync_and_notify(repo_path, analysis, design, skill_file):
    """Phase 6: Progress Sync + Team Notification."""
    print("\n═══ Phase 6: Progress Sync + Team Notification ═══")

    tool_name = design["tool_name"]
    display_name = design["display_name"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    # 1. Update Polymorph progress
    pm_progress = PROGRESS_DIR / "polymorph-progress.md"
    if pm_progress.exists():
        entry = textwrap.dedent(f'''
            #### 🔴 [PM] {now} — Tool Created: {display_name}
            - **Source**: {repo_path}
            - **Type**: {analysis["type"]} / {analysis["language"]}
            - **Pattern**: {design["integration_pattern"]}
            - **Skill**: `skills/{tool_name}/SKILL.md`
            - **Files**: {analysis["file_count"]}
            - **Pipeline**: create_tool.py (all 6 phases)
        ''')
        content = pm_progress.read_text()
        # Insert after "### Recent Entries"
        if "### Recent Entries" in content:
            content = content.replace(
                "### Recent Entries\n",
                f"### Recent Entries\n{entry}\n"
            )
        else:
            content += f"\n{entry}\n"
        pm_progress.write_text(content)
        print(f"  [UPDATED] polymorph-progress.md")

    # 2. Post to team chat
    if TEAM_CHAT.exists():
        chat_entry = textwrap.dedent(f'''
            ---

            **🔴 [PM] {now}** — New Tool Created: **{display_name}**

            | Field | Value |
            |-------|-------|
            | **Source** | `{repo_path}` |
            | **Type** | {analysis["type"]} / {analysis["language"]} |
            | **Pattern** | {design["integration_pattern"]} |
            | **Skill** | `skills/{tool_name}/SKILL.md` |
            | **Files** | {analysis["file_count"]} |

            All agents can now use this tool. Skill distributed to all agent directories.
        ''')
        chat_content = TEAM_CHAT.read_text()
        chat_content += chat_entry
        TEAM_CHAT.write_text(chat_content)
        print(f"  [POSTED] team-chat.md")

    # 3. Run progress sync
    sync_script = WORKSPACE_DIR / "tools" / "progress-sync.py"
    if sync_script.exists():
        result = run_cmd(
            f"{sys.executable} {sync_script} --agent PM --force",
            cwd=WORKSPACE_DIR, check=False
        )
        if result is not None:
            print(f"  [SYNCED] progress-sync.py")

    # 4. Git commit
    print(f"  [GIT] Committing changes...")
    run_cmd("git add -A", cwd=WORKSPACE_DIR, check=False)
    commit_msg = f"PM: Created tool + skill for {display_name} ({tool_name})"
    result = run_cmd(
        f'git commit -m "{commit_msg}"',
        cwd=WORKSPACE_DIR, check=False
    )
    if result is not None:
        print(f"  [COMMIT] {commit_msg}")
        push_result = run_cmd("git push origin master", cwd=WORKSPACE_DIR, check=False)
        if push_result is not None:
            print(f"  [PUSHED] origin/master")
        else:
            print(f"  [WARN] Push failed (may need auth)")
    else:
        print(f"  [SKIP] Nothing to commit or commit failed")

    print(f"  [DONE] Sync + notification complete")


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def run_pipeline(source, args):
    """Run the full create-tool pipeline."""
    print("=" * 60)
    print(f"  CREATE TOOL PIPELINE")
    print(f"  Source: {source}")
    print(f"  Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Phase 0: Acquire
    if args.local:
        repo_path = Path(source)
        if not repo_path.exists():
            print(f"[FATAL] Local path does not exist: {source}")
            return False
        print(f"\n═══ Phase 0: Source Acquisition (LOCAL) ═══")
        print(f"  Using: {repo_path}")
    else:
        repo_path = phase_0_acquire(source, PROJECTS_DIR)
        if not repo_path:
            return False

    # Phase 1: Analyze
    analysis = phase_1_analyze(repo_path)
    if not analysis:
        return False

    if args.dry_run:
        print("\n[DRY RUN] Analysis complete. Exiting before build.")
        return True

    # Phase 2: Design
    design = phase_2_design(analysis, args)

    # Phase 3: Implement
    harness_result = None
    if not args.install_only:
        harness_result = phase_3_implement(repo_path, analysis, design)

    # Phase 4: Generate SKILL.md
    skill_file = phase_4_generate_skill(repo_path, analysis, design, harness_result)

    # Phase 5: Install + Register
    phase_5_install_and_register(repo_path, analysis, design, harness_result, skill_file)

    # Phase 6: Sync + Notify
    if not args.no_sync:
        phase_6_sync_and_notify(repo_path, analysis, design, skill_file)

    # Summary
    print("\n" + "=" * 60)
    print(f"  ✅ TOOL CREATION COMPLETE")
    print(f"  Name:     {design['tool_name']}")
    print(f"  Display:  {design['display_name']}")
    print(f"  Pattern:  {design['integration_pattern']}")
    print(f"  Skill:    skills/{design['tool_name']}/SKILL.md")
    print(f"  Source:   {repo_path}")
    print("=" * 60)

    return True


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Create Tool — GitHub Repo → Agent Tool + Skill Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python tools/create_tool.py https://github.com/user/repo
              python tools/create_tool.py https://github.com/user/repo --name my-tool
              python tools/create_tool.py https://github.com/user/repo --dry-run
              python tools/create_tool.py C:\\path\\to\\repo --local
        """)
    )

    parser.add_argument("source", help="GitHub URL or local path to repository")
    parser.add_argument("--name", help="Override auto-detected tool name")
    parser.add_argument("--category", choices=[
        "creative", "productivity", "ai", "dev", "science", "gaming", "network", "other"
    ], help="Tool category")
    parser.add_argument("--focus", help="Specific functionality focus")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, don't build")
    parser.add_argument("--install-only", action="store_true", help="Clone + skill, skip CLI build")
    parser.add_argument("--local", action="store_true", help="Build from already-cloned local path")
    parser.add_argument("--no-tests", action="store_true", help="Skip test generation")
    parser.add_argument("--no-sync", action="store_true", help="Skip progress sync and team notification")

    args = parser.parse_args()
    success = run_pipeline(args.source, args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
