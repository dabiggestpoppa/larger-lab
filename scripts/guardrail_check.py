import subprocess, json, os, sys
from pathlib import Path
from datetime import datetime

STATE_FILE = Path('scripts/guardrail_state.json')
STARTUP_DIR = Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'

IGNORED_TASKS = {
    'Microsoft', 'Mozilla', 'Adobe', 'SoftLanding',
    'OC2', 'OC3',
    'OneDrive', 'Google', 'GoogleUserPEH',
    'HP', 'Hewlett', 'RtkAudUService',
}

def get_tasks():
    try:
        r = subprocess.run(['schtasks', '/query', '/fo', 'LIST', '/v'], capture_output=True, text=True, timeout=30)
        tasks = []; cur = {}
        for line in r.stdout.splitlines():
            s = line.strip()
            if s.startswith('TaskName:'):
                if cur.get('task_name'): tasks.append(cur)
                cur = {'task_name': s.split(':', 1)[1].strip()}
            elif ':' in s and cur:
                k, v = s.split(':', 1); cur[k.strip().lower()] = v.strip()
        if cur.get('task_name'): tasks.append(cur)
        return tasks
    except Exception as e:
        return [{'error': str(e)}]

def get_startup():
    if not STARTUP_DIR.exists(): return []
    return [{'name': f.name, 'size': f.stat().st_size}
            for f in STARTUP_DIR.iterdir()
            if f.suffix.lower() not in ('.disabled', '.bak') and f.name.lower() != 'desktop.ini']

def check_acl(name):
    p = Path('C:/Windows/System32/Tasks') / name.lstrip('\\')
    if not p.exists(): return None
    try:
        r = subprocess.run(['icacls', str(p)], capture_output=True, text=True, timeout=10)
        u = os.environ.get('USERNAME', '')
        for line in r.stdout.splitlines():
            if u.lower() in line.lower():
                if '(F)' not in line and '(M)' not in line: return 'RESTRICTED'
        return 'OK'
    except: return 'ERROR'

def is_ignored(name):
    parts = [x.strip() for x in name.split('\\') if x.strip()]
    for part in parts:
        for ign in IGNORED_TASKS:
            if part.startswith(ign):
                return True
    return False

def main():
    print('=' * 60)
    print('SYSTEM GUARDRAIL CHECK')
    print('Time:', datetime.now().isoformat())
    print('=' * 60)
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {'known_tasks': {}, 'known_startup': [], 'last_check': None}
    alerts = []
    print()
    print('[1] Scheduled Tasks (non-Microsoft)')
    tasks = get_tasks(); cur_tasks = set(); shown = 0
    for t in tasks:
        n = t.get('task_name', '')
        if not n or is_ignored(n): continue
        cur_tasks.add(n); shown += 1
        st = t.get('status', '?'); ra = t.get('run as user', '?'); cmd = t.get('task to run', '?')[:80]
        if n not in state.get('known_tasks', {}):
            alerts.append('NEW TASK: ' + n)
            print('  WARN NEW:', n)
            print('    Status:', st, '  RunAs:', ra)
            print('    Command:', cmd)
        else: print('  OK', n, '(' + st + ')')
        acl = check_acl(n)
        if acl == 'RESTRICTED': alerts.append('RESTRICTED ACL: ' + n); print('    DANGER RESTRICTED ACL')
    for old in state.get('known_tasks', {}):
        if old not in cur_tasks: print('  INFO REMOVED:', old)
    if shown == 0: print('  (none)')
    print()
    print('[2] Startup Folder')
    su = get_startup(); cur_su = {e['name'] for e in su}
    for e in su:
        if e['name'] not in state.get('known_startup', []):
            alerts.append('NEW STARTUP: ' + e['name']); print('  WARN NEW:', e['name'], '(' + str(e['size']) + ' bytes)')
        else: print('  OK', e['name'])
    for old in state.get('known_startup', []):
        if old not in cur_su: print('  INFO REMOVED:', old)
    print()
    print('=' * 60)
    if alerts:
        print('DANGER', len(alerts), 'ALERT(S):')
        for a in alerts: print('  *', a)
    else: print('OK No new issues found.')
    state['known_tasks'] = {n: True for n in cur_tasks}
    state['known_startup'] = list(cur_su)
    state['last_check'] = datetime.now().isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print('State saved to', STATE_FILE)
    return len(alerts)

if __name__ == '__main__':
    sys.exit(main())
