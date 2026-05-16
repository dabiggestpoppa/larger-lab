# OCE Testing Skill

## Purpose
Test the Operator Continuity Engine — Event Fabric, Observer Runtime, SRRA-OPH adapter, and API endpoints.

## Test Structure
```
oce/
├── backend/
│   ├── tests/
│   │   ├── test_event_fabric.py      # 32 tests (passing)
│   │   ├── test_oce_adapter.py       # 27 tests (passing)
│   │   ├── test_observer_runtime.py  # TODO: Phase 3
│   │   └── test_api_endpoints.py     # TODO: Phase 3
│   └── conftest.py
└── frontend/
    └── __tests__/                    # TODO: Jest tests
```

## Running Tests

```bash
# All OCE tests
cd oce
python -m pytest tests/ -v

# Specific test file
python -m pytest backend/tests/test_event_fabric.py -v

# With coverage
python -m pytest tests/ --cov=backend --cov-report=html

# Quick smoke test
python -m pytest tests/ -x -q  # Stop on first failure, quiet mode
```

## Event Fabric Tests (Phase 2)

### Test Categories
1. **Ingestion** — Events are validated, timestamped, classified
2. **Routing** — Events route to correct subscribers via topology
3. **Persistence** — Events stored in trajectory memory
4. **Streaming** — WebSocket delivers real-time events
5. **Filtering** — Query by type, source, priority, time range

### Example Test Pattern
```python
import pytest
from backend.event_fabric import EventFabric

@pytest.fixture
def fabric():
    return EventFabric()

@pytest.mark.asyncio
async def test_ingest_event(fabric):
    event = await fabric.ingest(
        event_type="observer.state_change",
        source="test-observer",
        payload={"state": "active"}
    )
    assert event.event_id is not None
    assert event.event_type == "observer.state_change"

@pytest.mark.asyncio
async def test_route_to_subscriber(fabric):
    received = []
    await fabric.subscribe("observer.state_change", lambda e: received.append(e))
    await fabric.ingest(event_type="observer.state_change", source="test", payload={})
    assert len(received) == 1
```

## Observer Runtime Tests (Phase 3)

### Test Categories
1. **Lifecycle** — create, activate, suspend, destroy
2. **Health** — entropy, drift, budget monitoring
3. **Event Subscription** — observers receive relevant events
4. **State Persistence** — snapshots, recovery anchors
5. **Multi-Observer** — concurrent observers, isolation

## API Endpoint Tests

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_get_observers():
    response = client.get("/observers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_post_event():
    response = client.post("/events/ingest", json={
        "event_type": "test.event",
        "source": "test",
        "payload": {"key": "value"}
    })
    assert response.status_code == 200
```

## Integration Tests

```bash
# Start backend, run end-to-end tests
cd oce/backend
uvicorn main:app --port 8000 &
sleep 2
python -m pytest tests/test_integration.py -v
kill %1
```

## Performance Tests

```bash
# Event throughput test
python tools/benchmark_events.py --count 10000 --rate 1000

# WebSocket latency test
python tools/benchmark_ws.py --connections 100 --duration 60
```

## Test Data Factories

```python
# tests/factories.py
from backend.event_fabric import Event

def make_event(**kwargs):
    defaults = {
        "event_type": "test.event",
        "source": "test",
        "priority": 1,
        "payload": {},
    }
    defaults.update(kwargs)
    return Event(**defaults)

def make_observer_config(**kwargs):
    defaults = {
        "observer_id": "test-observer",
        "observer_type": "system",
        "subscriptions": ["system.*"],
    }
    defaults.update(kwargs)
    return defaults
```
