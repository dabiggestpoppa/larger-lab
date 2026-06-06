"""
L3 — Autonomous Research Agents Layer

Detects knowledge gaps, spawns research agents, evaluates findings,
and feeds results back into the distillation layer.

Components:
    gap_detector.py     — Knowledge gap detector (AS)
    task_gen.py         — Research task generator (PM)
    research_agent.py   — LLM-driven research agent (CC)
    evaluator.py        — Finding confidence evaluator (PM2)
    router.py           — Research task → LLM router (PM2)
    lifecycle.py        — Agent lifecycle manager (AS)
    queue.py            — SQLite-backed task queue (CC)
    srra_adapter.py     — SRRA-OPH runtime adapter (CC)

Safety bounds:
    - Max 3 concurrent agents
    - Max 1 hour per task
    - Max 2 retries → abandoned
    - All actions logged to execution journal
"""

__all__ = []
