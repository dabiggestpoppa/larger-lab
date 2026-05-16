"""Fix event routing pipeline."""
import os

target = os.path.join(os.path.dirname(__file__), 'dspy_pipelines.py')
f = open(target, 'r')
content = f.read()
f.close()

# Fix should_sync call
old = '''should_sync = self._sync_optimizer.should_sync(
            obs_a="planner",
            obs_b="execution",
            entropy_delta=entropy_level
        )'''

new = '''should_sync = self._sync_optimizer.should_sync(
            obs_a="planner",
            obs_b="execution",
            coherence_gain=1.0 - entropy_level,
            entropy_cost=entropy_level
        )'''

content = content.replace(old, new)

f = open(target, 'w')
f.write(content)
f.close()
print('Fixed event routing pipeline')
