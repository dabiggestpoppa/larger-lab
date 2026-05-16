"""Add _event_counter to adapter __init__."""
import os

target = os.path.join(os.path.dirname(__file__), 'srrs_adapter.py')
f = open(target, 'r')
content = f.read()
f.close()

# Add _event_counter after _topology_observer
old = '        self._topology_observer: Optional[TopologyObserver] = None\n'
new = '        self._topology_observer: Optional[TopologyObserver] = None\n        self._event_counter = 0\n'
content = content.replace(old, new)

f = open(target, 'w')
f.write(content)
f.close()
print('Added _event_counter')
