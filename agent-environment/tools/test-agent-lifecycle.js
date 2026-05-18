/**
 * Test Agent Lifecycle — End-to-end test for the Agent Client SDK.
 *
 * Tests the full agent lifecycle:
 *   1. Check server health
 *   2. Register a test agent
 *   3. Move through 3 rooms
 *   4. Send messages in each room
 *   5. Update status and activity
 *   6. Verify world state reflects all changes
 *   7. Disconnect cleanly
 *   8. Report pass/fail for each step
 *
 * Run: node tools/test-agent-lifecycle.js
 *
 * Requires the environment server to be running on port 9000.
 */

const client = require('../src/agent-client');

const ROOMS = ['lobby', 'lab-room', 'meditation-room'];
const MESSAGES = [
  { room: 'lobby',          text: 'Hello from the Lobby!',       type: 'chat' },
  { room: 'lab-room',       text: 'Starting analysis...',         type: 'task' },
  { room: 'meditation-room', text: 'Reflecting on results...',    type: 'chat' },
];
const STATUSES = ['working', 'idle', 'meditating'];

let _results = [];
let _agent = null;

function report(step, passed, detail) {
  const status = passed ? '✅ PASS' : '❌ FAIL';
  _results.push({ step, passed, detail });
  console.log(`  ${status} — ${step}${detail ? ': ' + detail : ''}`);
}

async function main() {
  console.log('🧪 Agent Client SDK — E2E Test\n');
  console.log('═══════════════════════════════════════\n');

  // ── Step 1: Check server health ────────────────────────────────
  console.log('Step 1: Server health check');
  try {
    const world = await client.getWorld();
    // getWorld requires connection, so we test health via a raw require
    const http = require('http');
    await new Promise((resolve, reject) => {
      const req = http.get('http://localhost:9000/health', (res) => {
        let data = '';
        res.on('data', d => data += d);
        res.on('end', () => {
          try {
            const health = JSON.parse(data);
            if (health.status === 'ok') {
              report('Server health', true, `${health.agents} agents, ${health.rooms} rooms`);
            } else {
              report('Server health', false, `status: ${health.status}`);
            }
          } catch { report('Server health', false, 'Invalid JSON'); }
          resolve();
        });
      });
      req.on('error', (err) => {
        report('Server health', false, err.message);
        reject(err);
      });
      req.setTimeout(5000, () => {
        req.destroy();
        report('Server health', false, 'Timeout');
        reject(new Error('Timeout'));
      });
    });
  } catch {
    console.log('\n❌ Server is not running. Start it first:');
    console.log('   cd agent-environment && node src/server.js');
    process.exit(1);
  }

  // ── Step 2: Register agent ─────────────────────────────────────
  console.log('\nStep 2: Register test agent');
  try {
    _agent = await client.connect({
      name: 'TestAgent',
      role: 'tester',
      capabilities: ['communicate', 'test'],
      room: 'lobby',
    });
    report('Connect & register', !!_agent.id, `id=${_agent.id}, name=${_agent.name}`);
  } catch (err) {
    report('Connect & register', false, err.message);
    console.log('\n❌ Cannot proceed without registration.');
    process.exit(1);
  }

  // ── Step 3: Move through rooms ─────────────────────────────────
  console.log('\nStep 3: Move through rooms');
  for (const roomId of ROOMS) {
    try {
      const result = await client.moveTo(roomId);
      const me = client.whoami();
      const success = me.room === roomId;
      report(`Move to ${roomId}`, success, success ? `room=${me.room}` : `expected ${roomId}, got ${me.room}`);
    } catch (err) {
      report(`Move to ${roomId}`, false, err.message);
    }
  }

  // ── Step 4: Send messages ──────────────────────────────────────
  console.log('\nStep 4: Send messages in rooms');
  for (const msg of MESSAGES) {
    try {
      // Ensure we're in the right room
      await client.moveTo(msg.room);
      const result = await client.say(msg.text, msg.type);
      report(`Say in ${msg.room}`, !result.queued, `"${msg.text.slice(0, 30)}..."`);
    } catch (err) {
      report(`Say in ${msg.room}`, false, err.message);
    }
  }

  // ── Step 5: Update status and activity ─────────────────────────
  console.log('\nStep 5: Update status and activity');
  for (const status of STATUSES) {
    try {
      const result = await client.setStatus(status);
      const me = client.whoami();
      report(`Set status '${status}'`, me.status === status, `status=${me.status}`);
    } catch (err) {
      report(`Set status '${status}'`, false, err.message);
    }
  }

  try {
    await client.setActivity('Running E2E test suite', 0.9);
    report('Set activity', true, 'action="Running E2E test suite", level=0.9');
  } catch (err) {
    report('Set activity', false, err.message);
  }

  // ── Step 6: Verify world state ─────────────────────────────────
  console.log('\nStep 6: Verify world state');
  try {
    const world = await client.getWorld();
    const testAgent = world.agents?.find(a => a.id === _agent.id);

    report('World state fetched', !!world.agents, `${world.agents?.length} agents total`);
    report('Test agent in world', !!testAgent, testAgent ? `name=${testAgent.name}, room=${testAgent.currentRoom}` : 'not found');

    if (testAgent) {
      report('Agent status correct', testAgent.status === 'meditating', `status=${testAgent.status}`);
      report('Agent in meditation-room', testAgent.currentRoom === 'meditation-room', `room=${testAgent.currentRoom}`);
    }
  } catch (err) {
    report('World state verification', false, err.message);
  }

  // ── Step 7: Test event emitter ─────────────────────────────────
  console.log('\nStep 7: Event emitter');
  let eventFired = false;
  client.on('test-event', () => { eventFired = true; });
  client.emit('test-event');
  report('Event registration & emit', eventFired, 'custom event fired');

  // ── Step 8: Disconnect cleanly ─────────────────────────────────
  console.log('\nStep 8: Disconnect');
  try {
    await client.disconnect();
    const me = client.whoami();
    report('Disconnect', !me.connected, `connected=${me.connected}`);
  } catch (err) {
    report('Disconnect', false, err.message);
  }

  // ── Summary ────────────────────────────────────────────────────
  console.log('\n═══════════════════════════════════════');
  console.log('📊 Test Summary\n');

  const passed = _results.filter(r => r.passed).length;
  const failed = _results.filter(r => !r.passed).length;
  const total = _results.length;

  for (const r of _results) {
    console.log(`  ${r.passed ? '✅' : '❌'} ${r.step}${r.detail ? ': ' + r.detail : ''}`);
  }

  console.log(`\n${passed}/${total} passed, ${failed} failed`);

  if (failed > 0) {
    console.log('\n❌ SOME TESTS FAILED');
    process.exit(1);
  } else {
    console.log('\n✅ ALL TESTS PASSED');
    process.exit(0);
  }
}

main().catch(err => {
  console.error('\n❌ Unhandled error:', err.message);
  console.error(err.stack);
  process.exit(1);
});
