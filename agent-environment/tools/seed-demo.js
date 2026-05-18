/**
 * Seed Demo — Creates real agents and simulates activity.
 * Uses the actual operational room registry and agent roster.
 *
 * Run: node tools/seed-demo.js
 *
 * Requires the environment server to be running on port 9000.
 * If the server is not running, the script will report and exit.
 */

const http = require('http');

const API = 'http://localhost:9000';

function api(method, path, body) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const req = http.request(`${API}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data ? Buffer.byteLength(data) : 0,
      },
    }, (res) => {
      let chunks = '';
      res.on('data', d => chunks += d);
      res.on('end', () => {
        try { resolve(JSON.parse(chunks)); }
        catch { resolve(chunks); }
      });
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

// Real agent roster matching AGENTS.md
const DEMO_AGENTS = [
  { name: 'OWL',  role: 'operator',   capabilities: ['communicate', 'read_files', 'write_files', 'orchestrate'] },
  { name: 'CC',   role: 'overseer',   capabilities: ['communicate', 'read_files', 'review'] },
  { name: 'AS',   role: 'assistant',  capabilities: ['communicate', 'read_files', 'write_files', 'monitor'] },
  { name: 'PM',   role: 'debugger',   capabilities: ['communicate', 'read_files', 'execute', 'debug'] },
  { name: 'RL',   role: 'researcher', capabilities: ['communicate', 'read_files', 'write_files', 'research'] },
];

// Real room assignments
const ROOM_ASSIGNMENTS = {
  'OWL': 'lobby',
  'CC':  'war-room',
  'AS':  'meditation-room',
  'PM':  'lab-room',
  'RL':  'lab-room',
};

const ROOM_NAMES = {
  'lobby':          'Lobby',
  'war-room':       'War Room',
  'meditation-room':'Meditation Room',
  'lab-room':       'Lab Room',
};

async function main() {
  console.log('🌱 Seeding real agent data...\n');

  // Check health
  let health;
  try {
    health = await api('GET', '/health');
  } catch (err) {
    console.error(`❌ Cannot connect to environment server at ${API}`);
    console.error(`   Start the server first: cd agent-environment && node src/server.js`);
    process.exit(1);
  }
  console.log(`✅ Server healthy — ${health.agents} agents, ${health.rooms} rooms\n`);

  // Register agents
  const agents = [];
  for (const agent of DEMO_AGENTS) {
    const result = await api('POST', '/api/agents', agent);
    if (result.success) {
      agents.push(result.agent);
      console.log(`✅ Registered: ${result.agent.name} (${result.agent.id})`);
    } else {
      console.log(`⚠️  ${agent.name}: ${result.error}`);
      // Try to find existing
      const existing = await api('GET', '/api/agents');
      const found = existing.agents?.find(a => a.name === agent.name);
      if (found) {
        agents.push(found);
        console.log(`   Found existing: ${found.name} (${found.id})`);
      }
    }
  }

  // Move agents to their assigned rooms
  console.log('');
  for (const agent of agents) {
    const roomId = ROOM_ASSIGNMENTS[agent.name];
    if (roomId) {
      const result = await api('POST', `/api/agents/${agent.id}/move`, { roomId });
      if (result.success) {
        console.log(`📍 ${agent.name} → ${ROOM_NAMES[roomId] || roomId}`);
      } else {
        console.log(`⚠️  ${agent.name} move failed: ${result.error}`);
      }
    }
  }

  // Post welcome messages
  console.log('');
  const messages = [
    { room: 'lobby', agent: 'OWL', text: 'Agent Environment operational. All agents registered.', type: 'system' },
    { room: 'lab-room', agent: 'RL', text: 'Lab Room ready. Awaiting strategy assignments.', type: 'system' },
    { room: 'war-room', agent: 'CC', text: 'War Room active. Standing by for operations.', type: 'system' },
  ];

  for (const msg of messages) {
    const roomAgent = agents.find(a => a.name === msg.agent);
    if (roomAgent) {
      await api('POST', `/api/rooms/${msg.room}/messages`, {
        agentId: roomAgent.id,
        text: msg.text,
        type: msg.type,
      });
      console.log(`💬 [${ROOM_NAMES[msg.room]}] ${msg.agent}: ${msg.text}`);
    }
  }

  // Set activity for each agent
  console.log('');
  const activities = {
    'OWL':  { action: 'Orchestrating the cognitive field', level: 0.9 },
    'CC':   { action: 'Reviewing architecture',             level: 0.6 },
    'AS':   { action: 'Monitoring context',                 level: 0.5 },
    'PM':   { action: 'Debugging strategy runner',          level: 0.7 },
    'RL':   { action: 'Researching market patterns',        level: 0.8 },
  };

  for (const agent of agents) {
    const act = activities[agent.name];
    if (act) {
      await api('POST', `/api/agents/${agent.id}/activity`, act);
      console.log(`⚡ ${agent.name}: ${act.action}`);
    }
  }

  // Print summary
  console.log('\n✅ Demo data seeded successfully!');
  console.log('🌐 Open http://localhost:9000 to view the dashboard');
  console.log('');
  console.log('Agent locations:');
  for (const agent of agents) {
    const roomId = ROOM_ASSIGNMENTS[agent.name];
    console.log(`  ${agent.name} (${agent.role}) → ${ROOM_NAMES[roomId] || roomId}`);
  }
}

main().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
