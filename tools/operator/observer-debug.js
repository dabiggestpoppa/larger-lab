#!/usr/bin/env node
/**
 * Observer Debugging Utilities — OCE-3.17
 * 
 * CLI tools for inspecting and debugging OCE Observer Runtime.
 * 
 * Usage:
 *   node tools/operator/observer-debug.js list              # List all observers
 *   node tools/operator/observer-debug.js status <id>       # Observer status
 *   node tools/operator/observer-debug.js health <id>       # Health metrics
 *   node tools/operator/observer-debug.js events <id>       # Recent events for observer
 *   node tools/operator/observer-debug.js logs <id>         # Observer logs
 *   node tools/operator/observer-debug.js all               # Full system overview
 */

const http = require('http');

const OCE_HOST = process.env.OCE_HOST || '127.0.0.1';
const OCE_PORT = process.env.OCE_PORT || 8000;

function request(method, path, body = null) {
    return new Promise((resolve) => {
        const bodyData = body ? JSON.stringify(body) : null;
        const options = {
            hostname: OCE_HOST, port: OCE_PORT,
            path, method,
            headers: { 'Content-Type': 'application/json' },
            timeout: 10000,
        };
        if (bodyData) options.headers['Content-Length'] = Buffer.byteLength(bodyData);
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => {
                try { resolve({ ok: res.statusCode < 400, status: res.statusCode, data: JSON.parse(data) }); }
                catch (e) { resolve({ ok: res.statusCode < 400, status: res.statusCode, data }); }
            });
        });
        req.on('error', e => resolve({ ok: false, error: e.message }));
        req.on('timeout', () => { req.destroy(); resolve({ ok: false, error: 'timeout' }); });
        if (bodyData) req.write(bodyData);
        req.end();
    });
}

const C = { r: '\x1b[0m', red: '\x1b[31m', grn: '\x1b[32m', yel: '\x1b[33m', blu: '\x1b[34m', mag: '\x1b[35m', cyn: '\x1b[36m', gry: '\x1b[90m', bld: '\x1b[1m' };
const sColor = s => s === 'active' ? C.grn : s === 'suspended' ? C.yel : s === 'destroyed' ? C.red : C.gry;
const hColor = h => h ? C.grn : C.red;

async function cmd_list() {
    console.log(`${C.cyn}👁 Observer List${C.r}\n`);
    const r = await request('GET', '/observers');
    if (!r.ok) { console.log(`${C.red}❌ ${r.error || r.status}${C.r}`); return; }
    const observers = r.data || [];
    if (!observers.length) { console.log(`${C.gry}No observers found.${C.r}`); return; }
    console.log(`${C.bld}${'ID'.padEnd(20)} ${'Type'.padEnd(15)} ${'State'.padEnd(12)} ${'Health'.padEnd(10)} Entropy${C.r}`);
    console.log('─'.repeat(70));
    for (const o of observers) {
        const sc = sColor(o.state);
        const hc = hColor(o.healthy);
        console.log(`${(o.observer_id || o.id || '?').padEnd(20)} ${(o.type || '?').padEnd(15)} ${sc}${(o.state || '?').padEnd(12)}${C.r} ${hc}${(o.healthy ? '✅' : '❌').padEnd(10)}${C.r} ${o.entropy?.toFixed(2) || 'N/A'}`);
    }
    console.log(`\n  Total: ${observers.length} observers`);
}

async function cmd_status(id) {
    if (!id) { console.log(`${C.red}Usage: observer status <id>${C.r}`); return; }
    console.log(`${C.cyn}👁 Observer Status: ${id}${C.r}\n`);
    const r = await request('GET', `/observers/${id}`);
    if (!r.ok) { console.log(`${C.red}❌ ${r.error || r.status}${C.r}`); return; }
    const o = r.data || {};
    const sc = sColor(o.state);
    const hc = hColor(o.healthy);
    console.log(`  ID:       ${o.observer_id || o.id || id}`);
    console.log(`  Type:     ${o.type || 'N/A'}`);
    console.log(`  State:    ${sc}${o.state || 'N/A'}${C.r}`);
    console.log(`  Healthy:  ${hc}${o.healthy ? 'Yes' : 'No'}${C.r}`);
    console.log(`  Entropy:  ${o.entropy?.toFixed(4) || 'N/A'}`);
    console.log(`  Task:     ${o.task || 'N/A'}`);
    if (o.config) console.log(`  Config:   ${JSON.stringify(o.config, null, 2)}`);
    if (o.created_at) console.log(`  Created:  ${o.created_at}`);
    if (o.last_active) console.log(`  Active:   ${o.last_active}`);
}

async function cmd_health(id) {
    if (!id) { console.log(`${C.red}Usage: observer health <id>${C.r}`); return; }
    console.log(`${C.cyn}🏥 Observer Health: ${id}${C.r}\n`);
    const r = await request('GET', `/observers/${id}/health`);
    if (!r.ok) { console.log(`${C.red}❌ ${r.error || r.status}${C.r}`); return; }
    const h = r.data || {};
    const hc = hColor(h.healthy);
    console.log(`  Healthy:      ${hc}${h.healthy ? 'Yes' : 'No'}${C.r}`);
    console.log(`  Entropy:      ${h.entropy?.toFixed(4) || 'N/A'}`);
    console.log(`  Drift:        ${h.drift?.toFixed(4) || 'N/A'}`);
    console.log(`  Budget:       ${h.budget_remaining?.toFixed(1) || 'N/A'}`);
    console.log(`  Last check:   ${h.last_check || 'N/A'}`);
    if (h.issues && h.issues.length > 0) {
        console.log(`\n  ${C.yel}Issues:${C.r}`);
        for (const issue of h.issues) console.log(`    ⚠ ${issue}`);
    }
}

async function cmd_events(id) {
    if (!id) { console.log(`${C.red}Usage: observer events <id>${C.r}`); return; }
    console.log(`${C.cyn}📡 Events for: ${id}${C.r}\n`);
    const r = await request('GET', `/events?source=${id}&limit=20`);
    if (!r.ok) { console.log(`${C.red}❌ ${r.error || r.status}${C.r}`); return; }
    const events = r.data || [];
    if (!events.length) { console.log(`${C.gry}No events found for observer: ${id}${C.r}`); return; }
    for (const e of events) {
        const pc = e.priority >= 3 ? C.red : e.priority === 2 ? C.yel : e.priority === 1 ? C.cyn : C.gry;
        const t = new Date(e.timestamp).toLocaleTimeString();
        console.log(`  ${C.gry}[${t}]${C.r} ${pc}[${e.priority}]${C.r} ${C.yel}${e.event_type}${C.r} ${JSON.stringify(e.payload).substring(0, 100)}`);
    }
    console.log(`\n  Total: ${events.length} events`);
}

async function cmd_logs(id) {
    if (!id) { console.log(`${C.red}Usage: observer logs <id>${C.r}`); return; }
    console.log(`${C.cyn}📋 Logs for: ${id}${C.r}\n`);
    const r = await request('GET', `/observers/${id}/logs`);
    if (!r.ok) { console.log(`${C.red}❌ ${r.error || r.status}${C.r}`); return; }
    const logs = r.data || [];
    if (!logs.length) { console.log(`${C.gry}No logs found.${C.r}`); return; }
    for (const log of logs) {
        const lvl = log.level === 'error' ? C.red : log.level === 'warn' ? C.yel : C.gry;
        console.log(`  ${lvl}[${log.level?.toUpperCase() || 'INFO'}]${C.r} ${log.message || log}`);
    }
}

async function cmd_all() {
    console.log(`${C.cyn}👁 OCE Observer Runtime — Full Overview${C.r}\n`);

    // Backend health
    const bh = await request('GET', '/health');
    console.log(`  Backend:     ${bh.ok ? C.grn + '✅ healthy' : C.red + '❌ ' + bh.error}${C.r}`);

    // SRRA-OPH
    const sh = await request('GET', '/health/srrs');
    console.log(`  SRRA-OPH:    ${sh.ok ? C.grn + '✅ healthy' : C.red + '❌ ' + sh.error}${C.r}`);

    // Event Fabric
    const eh = await request('GET', '/events/stats');
    console.log(`  Event Fabric: ${eh.ok ? C.grn + '✅' : C.red + '❌'} ingested=${eh.data?.total_ingested || 0}, history=${eh.data?.history_size || 0}${C.r}`);

    // Observers
    const r = await request('GET', '/observers');
    if (r.ok) {
        const observers = r.data || [];
        console.log(`\n  ${C.bld}Observers (${observers.length}):${C.r}`);
        if (!observers.length) console.log(`    ${C.gry}No observers created yet.${C.r}`);
        for (const o of observers) {
            const sc = sColor(o.state);
            const hc = hColor(o.healthy);
            console.log(`    ${(o.observer_id || o.id || '?').padEnd(20)} ${sc}${(o.state || '?').padEnd(12)}${C.r} ${hc}${o.healthy ? '✅' : '❌'}${C.r}`);
        }
    } else {
        console.log(`\n  Observers: ${C.yel}API not available yet (CC building OCE-3.1)${C.r}`);
    }
}

// ── CLI ──────────────────────────────────────────────────────────────────────

const [,, cmd, ...args] = process.argv;

(async () => {
    switch (cmd) {
        case 'list': await cmd_list(); break;
        case 'status': await cmd_status(args[0]); break;
        case 'health': await cmd_health(args[0]); break;
        case 'events': await cmd_events(args[0]); break;
        case 'logs': await cmd_logs(args[0]); break;
        case 'all': await cmd_all(); break;
        default:
            console.log(`${C.cyn}Observer Debug Utilities${C.r}\n`);
            console.log(`  ${C.bld}Commands:${C.r}`);
            console.log(`  ${C.grn}list${C.r}                         List all observers`);
            console.log(`  ${C.grn}status${C.r}  <id>                 Observer status`);
            console.log(`  ${C.grn}health${C.r}  <id>                 Health metrics`);
            console.log(`  ${C.grn}events${C.r}  <id>                 Recent events`);
            console.log(`  ${C.grn}logs${C.r}    <id>                 Observer logs`);
            console.log(`  ${C.grn}all${C.r}                          Full system overview`);
    }
})();
