---
name: motus
description: >
  Build, serve, and deploy AI agents using the Motus framework (lithos-ai/motus).
  ReAct agents, task-graph workflows, MCP integration, multi-provider models,
  Docker sandboxes, guardrails, memory, and cloud deployment.
  Use when building agents, creating task workflows, serving agents locally,
  or deploying to Motus Cloud.
version: 1.0.0
source: https://github.com/lithos-ai/motus
---

# Motus — Agent Framework

> **Source**: [lithos-ai/motus](https://github.com/lithos-ai/motus) (Apache 2.0, v0.4.2)
> **Purpose**: Higher capability, lower cost, faster agents. No-framework approach.
> **Python**: 3.12+ | **Package**: `lithosai-motus`
> **Installed**: `C:\Users\wifik\Desktop\projects\motus\`

## What It Does

Motus provides the infrastructure for efficient agent serving:
- **ReActAgent** — Reasoning loop, tool dispatch, conversation state (under 10 lines)
- **Task graphs** — `@agent_task` turns functions into parallel, resilient workflow nodes
- **Multi-provider** — OpenAI, Anthropic, Gemini, Ollama, vLLM via unified client
- **MCP integration** — Connect any MCP server with `get_mcp()`
- **Docker sandboxes** — Run untrusted code in isolated containers
- **Guardrails** — Input/output validation on agents and tools
- **Memory** — Basic (append-only) and compact (auto-summarize) built in
- **Serving** — `motus serve` exposes agents as session-based HTTP API
- **Cloud deploy** — `motus deploy` to Motus Cloud
- **Observability** — Every LLM call, tool invocation, task dependency traced

## When to Use

| Scenario | Approach |
|----------|----------|
| Build a new agent | `ReActAgent` with tools |
| Parallel workflow | `@agent_task` decorator graph |
| Multi-agent system | `agent.as_tool()` composition |
| Need MCP tools | `get_mcp()` wrapper |
| Serve agent as API | `motus serve start` |
| Deploy to cloud | `motus deploy` |
| Untrusted code execution | Docker sandbox |
| Switch LLM provider | Change one line in client |

## Quick Start

### Build a ReAct Agent
```python
from motus.agent import ReActAgent
from motus.models import AnthropicChatClient, ChatMessage

agent = ReActAgent(
    client=AnthropicChatClient(),
    model_name="claude-haiku-4-5",
    system_prompt="You are a helpful assistant.",
)

# Run a turn
response, messages = await agent.run_turn(
    ChatMessage.user_message(content="Hello!"), []
)
```

### Build a Workflow (Task Graph)
```python
from motus.runtime import resolve
from motus.runtime.agent_task import agent_task

@agent_task
async def fetch(url): ...

@agent_task
async def summarize(article): ...

@agent_task
async def extract(article): ...

@agent_task(retries=3, timeout=10.0)
async def publish(summary, hashtags): ...

# Motus infers the dependency graph from data flow
article = fetch("https://example.com")
summary = summarize(article)      # Runs in parallel with extract
hashtags = extract(article)       # Both depend on article
post = publish(summary, hashtags) # Waits for both
print(resolve(post))
```

### Define Tools
```python
from motus.tools import tool

@tool
async def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

agent = ReActAgent(
    client=AnthropicChatClient(),
    model_name="claude-haiku-4-5",
    tools=[search],
)
```

### Serve Locally
```bash
# Start local server
motus serve start myapp:agent --port 8000

# Chat with local agent
motus serve chat http://localhost:8000 "Hello!"
```

### Deploy to Cloud
```bash
motus deploy --name myapp myapp:agent
motus serve chat https://myapp.lithosai.com "Hello!"
```

## Multi-Provider Models
```python
from motus.models import OpenAIChatClient, AnthropicChatClient, GeminiChatClient

# Switch providers by changing one line
agent = ReActAgent(client=OpenAIChatClient(), model_name="gpt-4o", tools=[search])
agent = ReActAgent(client=AnthropicChatClient(), model_name="claude-haiku-4-5", tools=[search])
agent = ReActAgent(client=GeminiChatClient(), model_name="gemini-2.0-flash", tools=[search])
```

## MCP Integration
```python
from motus.tools import get_mcp

# Connect any MCP server
mcp_tools = await get_mcp("npx", args=["-y", "@some/mcp-server"])
agent = ReActAgent(client=..., tools=[*mcp_tools, search])
```

## Multi-Agent Composition
```python
# Wrap any agent as a tool
specialist_agent = ReActAgent(client=..., tools=[...])
supervisor = ReActAgent(client=..., tools=[specialist_agent.as_tool()])

# Fork for independent conversation branches
branch = agent.fork()
```

## Memory
```python
from motus.memory import BasicMemory, CompactMemory

# Append-only memory
agent = ReActAgent(client=..., memory=BasicMemory())

# Auto-compacting memory (summarizes when token budget runs thin)
agent = ReActAgent(client=..., memory=CompactMemory(max_tokens=4000))
```

## Guardrails
```python
from motus.guardrails import input_guardrail, output_guardrail

@input_guardrail
async def validate_input(message: str) -> str:
    if "dangerous" in message:
        raise ValueError("Blocked: dangerous content")
    return message
```

## Docker Sandbox
```python
from motus.tools import DockerSandbox

sandbox = DockerSandbox(image="python:3.12", volumes={"/workspace": "/workspace"})
agent = ReActAgent(client=..., tools=[sandbox.as_tool()])
```

## Integration with larger-lab

### Agent Building Workflow
1. **CC** designs agent architecture
2. **PM** implements with Motus (`ReActAgent`, `@agent_task`, tools)
3. **AS** tests the agent locally (`motus serve start`)
4. **PM** debugs any issues
5. **All agents** can use the deployed agent via HTTP API

### Serving Infrastructure
- Local: `motus serve start <module>:<agent> --port 8000`
- Cloud: `motus deploy --name <name> <module>:<agent>`
- Health: `curl http://localhost:8000/health`
- Chat: `motus serve chat http://localhost:8000 "message"`

### Reference Files
- `C:\Users\wifik\Desktop\projects\motus\examples\agent.py` — Basic ReAct agent
- `C:\Users\wifik\Desktop\projects\motus\examples\runtime\task_graph_demo.py` — Task graph
- `C:\Users\wifik\Desktop\projects\motus\examples\skills\` — Skills example
- `C:\Users\wifik\Desktop\projects\motus\examples\mcp_tools.py` — MCP integration
- `C:\Users\wifik\Desktop\projects\motus\examples\memory.py` — Memory patterns
- `C:\Users\wifik\Desktop\projects\motus\plugins\motus\skills\motus\SKILL.md` — Plugin skill
- `https://docs.motus.lithosai.com/` — Full documentation
