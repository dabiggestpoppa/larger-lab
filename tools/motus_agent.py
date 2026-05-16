#!/usr/bin/env python3
"""
motus_agent.py — Motus Agent Builder & Server Wrapper

Wrapper around the Motus framework for building, serving, and deploying agents.

Usage:
    python tools/motus_agent.py build <name>           # Create a new agent template
    python tools/motus_agent.py serve <module>:<agent>  # Serve agent locally
    python tools/motus_agent.py chat <url> <message>    # Chat with agent
    python tools/motus_agent.py deploy <name> <agent>   # Deploy to cloud
    python tools/motus_agent.py list                     # List available agents
    python tools/motus_agent.py example <name>           # Create example agent
"""

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
MOTUS_DIR = Path(r"C:\Users\wifik\Desktop\projects\motus")
AGENTS_DIR = WORKSPACE / "agents"


def cmd_build(args):
    """Build a new Motus agent template."""
    name = args.name
    agent_dir = AGENTS_DIR / name
    agent_dir.mkdir(parents=True, exist_ok=True)

    # Create agent.py
    agent_file = agent_dir / "agent.py"
    agent_file.write_text(f'''#!/usr/bin/env python3
"""Motus agent: {name}"""

from motus.agent import ReActAgent
from motus.models import AnthropicChatClient, ChatMessage
from motus.tools import tool

# Define your tools here
@tool
async def example_tool(query: str) -> str:
    """An example tool."""
    return f"Result for: {{query}}"

# Create the agent
agent = ReActAgent(
    client=AnthropicChatClient(),
    model_name="claude-haiku-4-5",
    system_prompt="You are {name}, a specialized agent.",
    tools=[example_tool],
)

# For serving: motus serve start {name}.agent:agent
# For console:
async def main():
    messages = []
    while True:
        user_input = input("User: ")
        if user_input.lower() in {{"exit", "quit"}}:
            break
        response, messages = await agent.run_turn(
            ChatMessage.user_message(content=user_input), messages
        )
        print(f"Agent: {{response.content}}")

if __name__ == "__main__":
    asyncio.run(main())
''')

    # Create __init__.py
    (agent_dir / "__init__.py").write_text(f"from .agent import agent\n")

    # Create requirements.txt
    (agent_dir / "requirements.txt").write_text("lithosai-motus\n")

    print(f"[OK] Agent created at {agent_dir}")
    print(f"  Serve: motus serve start {name}.agent:agent")
    print(f"  Edit:  {agent_file}")


def cmd_serve(args):
    """Serve an agent locally."""
    target = args.target
    port = args.port
    print(f"[SERVE] Starting {target} on port {port}")
    subprocess.run(["motus", "serve", "start", target, "--port", str(port)])


def cmd_chat(args):
    """Chat with an agent."""
    url = args.url
    message = args.message
    print(f"[CHAT] {url}")
    subprocess.run(["motus", "serve", "chat", url, message])


def cmd_deploy(args):
    """Deploy an agent to Motus Cloud."""
    name = args.name
    target = args.target
    print(f"[DEPLOY] {name} ← {target}")
    subprocess.run(["motus", "deploy", "--name", name, target])


def cmd_list(args):
    """List available agents."""
    if not AGENTS_DIR.exists():
        print("No agents directory found.")
        return

    agents = [d.name for d in AGENTS_DIR.iterdir() if d.is_dir() and (d / "agent.py").exists()]
    if agents:
        print(f"Available agents ({len(agents)}):")
        for a in agents:
            print(f"  {a}  →  motus serve start {a}.agent:agent")
    else:
        print("No agents found. Create one with: python tools/motus_agent.py build <name>")


def cmd_example(args):
    """Create an example agent from the motus examples."""
    name = args.name or "example"
    example_type = args.type

    src = MOTUS_DIR / "examples" / f"{example_type}.py"
    if not src.exists():
        print(f"[ERROR] Example not found: {src}")
        print("Available examples: agent, coding_agent, mcp_tools, memory")
        return

    agent_dir = AGENTS_DIR / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, agent_dir / "agent.py")
    (agent_dir / "__init__.py").write_text(f"from .agent import agent\n")
    print(f"[OK] Example agent created at {agent_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Motus Agent Builder & Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command")

    # build
    p_build = subparsers.add_parser("build", help="Build a new agent template")
    p_build.add_argument("name", help="Agent name")

    # serve
    p_serve = subparsers.add_parser("serve", help="Serve agent locally")
    p_serve.add_argument("target", help="Module:agent target (e.g., myagent.agent:agent)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    # chat
    p_chat = subparsers.add_parser("chat", help="Chat with agent")
    p_chat.add_argument("url", help="Agent URL")
    p_chat.add_argument("message", help="Message to send")

    # deploy
    p_deploy = subparsers.add_parser("deploy", help="Deploy to Motus Cloud")
    p_deploy.add_argument("name", help="Deployment name")
    p_deploy.add_argument("target", help="Module:agent target")

    # list
    subparsers.add_parser("list", help="List available agents")

    # example
    p_example = subparsers.add_parser("example", help="Create from example")
    p_example.add_argument("name", nargs="?", default="example", help="Agent name")
    p_example.add_argument("--type", default="agent", help="Example type")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "build": cmd_build,
        "serve": cmd_serve,
        "chat": cmd_chat,
        "deploy": cmd_deploy,
        "list": cmd_list,
        "example": cmd_example,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
