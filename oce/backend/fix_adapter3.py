"""Fix event ID uniqueness and validate_contract signature."""
import os

target = os.path.join(os.path.dirname(__file__), 'srrs_adapter.py')
f = open(target, 'r')
content = f.read()
f.close()

# Fix 1: Add event counter for unique IDs
content = content.replace(
    '        self._topology_observer = None',
    '        self._topology_observer = None\n        self._event_counter = 0'
)

# Fix 2: Use counter-based event IDs
content = content.replace(
    'return f"event_{datetime.now().timestamp()}"',
    'self._event_counter += 1\n        return f"event_{datetime.now().timestamp()}_{self._event_counter}"'
)

# Fix 3: validate_contract needs actual values
content = content.replace(
    'result = self._contract_manager.validate_contract(contract_id)',
    'result = self._contract_manager.validate_contract(contract_id, actual_coherence_gain=0.0, actual_entropy_cost=0.0)'
)

f = open(target, 'w')
f.write(content)
f.close()
print('Fixed event IDs and validate_contract')
