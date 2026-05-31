# Observer Core — O-1 through O-7

TYPE: observer
SUMMARY: The 7-phase Observer Core system that orchestrates the cognitive field above the SRRA-OPH substrate.
CAUSE: The Observer Core is the intelligence layer that manages consensus, spawning, learning, and field stabilization.
FUNCTION: Reference for all Observer Core phases, their components, and test status.

## Architecture

The Observer Core sits between the Agent Network and SRRA-OPH:
```
Agent Network → Observer Core (O-1→O-7) → SRRA-OPH → OCE V3
```

## Phase Status

| Phase | Name | Backend | Frontend | Tests | Status |
|-------|------|---------|----------|-------|--------|
| O-1 | Consensus Engine | 9/9 | 10/10 | 42/42 | ✅ Complete |
| O-2 | Spawn Engine | 10/10 | 7/7 | needs alignment | ✅ Complete |
| O-3 | Learning Loop | 10/10 | 8/8 | needs alignment | ✅ Complete |
| O-4 | Field Stabilizer | 11/11 | 9/9 | 14/14 | ✅ Complete |
| O-5 | Topology Manager | 12/12 | 12/12 | — | ✅ Complete |
| O-6 | Local Substrate | 11/11 | 8/8 | 52/52 | ✅ Complete |
| O-7 | Persistent Field | 12/12 | 8/8 | 35/35 | ✅ Complete |

## O-1: Consensus Engine
- Manages agreement between observers on field state
- 42/42 tests passing
- Backend: consensus_engine.py, consensus_api.py
- Frontend: ConsensusPanel.tsx

## O-2: Spawn Engine
- Manages agent spawning with context injection
- Backend: spawn_engine.py, spawn_api.py
- Frontend: SpawnPanel.tsx

## O-3: Learning Loop
- Extracts patterns from execution history
- Backend: learning_loop.py, learning_api.py
- Frontend: LearningPanel.tsx

## O-4: Field Stabilizer
- Monitors and stabilizes field coherence
- 14/14 tests passing
- Backend: field_stabilizer.py, field_api.py
- Frontend: FieldPanel.tsx

## O-5: Topology Manager
- Manages observer network topology
- Backend: topology_manager.py, topology_api.py
- Frontend: TopologyPanel.tsx

## O-6: Local Substrate
- Provides local computation substrate for observers
- 52/52 tests passing
- Backend: substrate_api.py
- Frontend: SubstratePanel.tsx

## O-7: Persistent Field
- Maintains persistent field state across sessions
- 35/35 tests passing
- Backend: persistent_field_api.py
- Frontend: PersistentPanel.tsx

## Key Files

| File | Purpose |
|------|---------|
| oce/backend/observer_runtime.py | Observer runtime engine |
| oce/backend/consensus_engine.py | O-1 consensus |
| oce/backend/spawn_engine.py | O-2 spawning |
| oce/backend/phase4_api.py | O-4 field API |
| oce/backend/substrate_api.py | O-6 substrate |
| oce/backend/persistent_field_api.py | O-7 persistent field |

RELATIONSHIPS: [[System Architecture]] [[V3 Cognitive Field]] [[SRRA-OPH]]

STATUS: active
SOURCE: AGENTS.md, team-chat.md
