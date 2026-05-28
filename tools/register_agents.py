"""Register all agents with OCE command center."""
import requests
import json

agents = [
    {
        "session_key": "hermes",
        "label": "Hermes",
        "role": "On-the-go agent via Telegram. Scheduled jobs, quick tasks, voice, pocket agent.",
        "capabilities": ["telegram", "scheduling", "voice", "quick_tasks", "github_search"]
    },
    {
        "session_key": "oc2",
        "label": "OC2 (OWL)",
        "role": "Primary Operator / Orchestrator. Monitors, detects blockers, delegates tasks.",
        "capabilities": ["orchestration", "monitoring", "delegation", "chaos_testing", "repair"]
    },
    {
        "session_key": "pm1",
        "label": "PM1 (Polymorph)",
        "role": "Debugger / Tool Builder. Debugs tools, builds skills, fixes issues.",
        "capabilities": ["debugging", "tool_building", "skill_creation", "fixing"]
    },
    {
        "session_key": "as",
        "label": "AS (Assistant Manager)",
        "role": "Context Monitoring / Quality Checks / Documentation.",
        "capabilities": ["quality_review", "documentation", "context_monitoring", "testing"]
    },
    {
        "session_key": "rl",
        "label": "RL (Research Lead)",
        "role": "Research / DSP Integration. Workflow distiller, pattern memory, learning.",
        "capabilities": ["research", "dspy", "pattern_extraction", "workflow_analysis"]
    },
]

for agent in agents:
    r = requests.post('http://localhost:8000/command-center/agents/register', json=agent)
    print(f'{agent["label"]}: {r.status_code} - {r.json().get("status", r.json())}')

# Verify
r = requests.get('http://localhost:8000/command-center/agents')
print('\nAll registered agents:')
for key, agent in r.json()['agents'].items():
    print(f'  {key}: {agent["label"]} ({agent["status"]})')
