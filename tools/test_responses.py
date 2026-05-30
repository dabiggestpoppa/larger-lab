"""Test the fixed default handler."""
from core.spawn.agent_spawner import AgentSpawner
from core.consensus.observer_consensus import ConsensusResult
from core.spawn.spawn_blueprint import SpawnPlan
from datetime import datetime, timezone

spawner = AgentSpawner()

consensus = ConsensusResult(
    task_type='conversation',
    complexity='low',
    confidence=0.85,
    routing_path=['planner'],
    required_capabilities=['chat'],
    recommended_model='claude-haiku-4',
    spawn_required=False,
    timestamp=datetime.now(timezone.utc).isoformat(),
    voter_count=5,
    agreement_score=0.85,
)

blueprint = SpawnPlan(task_type='conversation', complexity='low')
context = {'conversation_history': []}
system_state = {'active_agents': 2, 'lifecycle_states': {'running': 1, 'complete': 3}}

tests = [
    'Hello there',
    'How are you doing today?',
    'What is SRRA?',
    'Tell me about yourself',
    'What can you do?',
    'I want to build a new feature',
    'Can you help me with this?',
    'What is the capital of France?',
    'How does the observer field work?',
    'Show me the topology',
    'I need to debug an issue',
    'What is the meaning of life?',
    'Explain quantum computing',
    'How tall is Mount Everest?',
    'Who wrote Hamlet?',
]

for msg in tests:
    result = spawner._build_dynamic_response(msg, context, system_state, consensus)
    preview = result.replace('\n', ' ')[:150]
    print(f'Input: {msg[:50]:50s}')
    print(f'Output: {preview}')
    print()
