"""Fix remaining adapter issues."""
import os

target = os.path.join(os.path.dirname(__file__), 'srrs_adapter.py')
f = open(target, 'r')
content = f.read()
f.close()

# Fix 1: TopologyObserver.record_event -> record_edge
content = content.replace(
    'self._topology_observer.record_event(event_type, payload)',
    'self._topology_observer.record_edge("planner", "execution", event_type)'
)

# Fix 2: created_at is already a string, don't call isoformat()
content = content.replace(
    '"created_at": contract.created_at.isoformat(),',
    '"created_at": contract.created_at,'
)

f = open(target, 'w')
f.write(content)
f.close()
print('Fixed adapter issues')
