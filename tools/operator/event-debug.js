#!/usr/bin/env node
/**
 * Event Fabric Debugging Utilities — OCE-2.22
 * 
 * CLI tools for inspecting and debugging the OCE Event Fabric.
 * 
 * Usage:
 *   node tools/operator/event-debug.js tail [type] [min_priority]
 *   node tools/operator/event-debug.js stats
 *   node tools/operator/event-debug.js replay <type> [limit]
 *   node tools/operator/event-debug.js health
 *   node tools/operator/event-debug.js emit <type> <source> <json_payload>
 *   node tools/operator/event-debug.js types
 */

const http = require('http');

const OCE_HOST = process.env.OCE_HOST || '127.0.0.1';
const OCE_PORT = process.env.OCE_PORT || 8000;
const API = '';

function request(method, path, body = null) {
    return new Promise((resolve) => {
        const bodyData = body ? JSON.stringify(body) : null;
        const options = {
            hostname: OCE_HOST, port: OCE_PORT,
            path: `${API}${path}`, method,
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
const pColor = p => p >= 3 ? C.red : p === 2 ? C.yel : p === 1 ? C.cyn : C.gry;
const pLabel = p => ['LOW', 'NORM', 'HIGH', 'CRIT'][p] || '????';

async function cmd_tail(filterType, minPri) {
    console.log(`${C.cyn}📡 Event Tail${C.r} — ${filterType || 'all'} (min_pri: ${minPri})${C.gry} | Ctrl+C to stop${C.r}\n`);
    let lastId = null;
    while (true) {
        const q = `/events?limit=20${filterType ? '&event_type=' + filterType : ''}&min_priority=${minPri}`;
        const r = await request('GET', q);
        if (!r.ok) { console.log(`${C.red}Error: ${r.error}${C.r}`); await sleep(5000); continue; }
        const evts = r.data?.events || r.data || [];
        for (const e of evts) {
            if (e.event_id === lastId) break;
            const pc = pColor(e.priority || 0);
            const t = new Date(e.timestamp).toLocaleTimeString();
            console.log(`${C.gry}[${t}]${C.r} ${pc}[${pLabel(e.priority || 0)}]${C.r} ${C.yel}${e.event_type}${C.r} ${C.gry}src:${e.source}${C.r} ${JSON.stringify(e.payload || {}).substring(0, 120)}`);
        }
        if (evts.length > 0) lastId = evts[0].event_id;
        await sleep(2000);
    }
}

async function cmd_stats() {
    console.log(`${C.cyn}📊 Event Fabric Statistics${C.r}\n`);
    const r = await request('GET', '/events/stats');
    if (!r.ok) { console.log(`${C.red}❌ ${r.error || r.status}${C.r}`); return; }
    const s = r.data || {};
    console.log(`${C.bld}Throughput:${C.r}`);
    console.log(`  Ingested: ${s.total_ingested || 0} | Routed: ${s.total_routed || 0} | Persisted: ${s.total_persisted || 0}`);
    console.log(`  Subscribers: ${s.active_subscribers || 0} | Streams: ${s.active_streams || 0} | History: ${s.history_size || 0}`);
    if (s.events_by_type && Object.keys(s.events_by_type).length > 0) {
        console.log(`\n${C.bld}By Type:${C.r}`);
        for (const [t, n] of Object.entries(s.events_by_type).sort((a, b) => b[1] - a[1]))
            console.log(`  ${C.yel}${t.padEnd(35)}${C.r} ${String(n).padStart(6)} ${C.cyn}${'█'.repeat(Math.min(n, 40))}${C.r}`);
    }
    if (s.events_by_source && Object.keys(s.events_by_source).length > 0) {
        console.log(`\n${C.bld}By Source:${C.r}`);
        for (const [s2, n] of Object.entries(s.events_by_source).sort((a, b) => b[1] - a[1]))
            console.log(`  ${C.grn}${s2.padEnd(20)}${C.r} ${String(n).padStart(6)} ${C.cyn}${'█'.repeat(Math.min(n, 40))}${C.r}`);
    }
}

async function cmd_replay(type, limit = 20) {
    console.log(`${C.cyn}🔄 Replay: ${type} (last ${limit})${C.r}\n`);
    const r = await request('GET', `/events?event_type=${type}&limit=${limit}`);
    if (!r.ok) { console.log(`${C.red}❌ ${r.error}${C.r}`); return; }
    const evts = (r.data?.events || r.data || []).reverse();
    if (!evts.length) { console.log(`${C.yel}No events for: ${type}${C.r}`); return; }
    for (const e of evts) {
        const pc = pColor(e.priority || 0);
        console.log(`${C.gry}[${new Date(e.timestamp).toLocaleString()}]${C.r} ${pc}[${pLabel(e.priority || 0)}]${C.r} ${C.yel}${e.event_type}${C.r}`);
        console.log(`  Source: ${e.source} | Payload: ${JSON.stringify(e.payload, null, 2).substring(0, 400)}`);
    }
    console.log(`\n${C.grn}✅ ${evts.length} events replayed${C.r}`);
}

async function cmd_health() {
    console.log(`${C.cyn}🏥 OCE Health Check${C.r}\n`);
    const checks = [
        { name: 'Backend', path: '/health' },
        { name: 'SRRA-OPH', path: '/health/srrs' },
        { name: 'Event Fabric', path: '/events/stats' },
    ];
    let allOk = true;
    for (const chk of checks) {
        const r = await request('GET', chk.path);
        const status = r.ok ? `${C.grn}✅ healthy${C.r}` : `${C.red}❌ ${r.error || 'unhealthy'}${C.r}`;
        console.log(`  ${chk.name.padEnd(15)} ${status}`);
        if (!r.ok) allOk = false;
    }
    console.log(`\n${allOk ? C.grn + '✅ All systems healthy' : C.yel + '⚠️  Some components degraded'}${C.r}`);
}

async function cmd_emit(type, source, payloadStr) {
    let payload = {};
    try { payload = JSON.parse(payloadStr || '{}'); } catch (e) { payload = { raw: payloadStr }; }
    const r = await request('POST', '/events/ingest', { event_type: type, source, payload });
    if (r.ok) console.log(`${C.grn}✅ Emitted: ${type} from ${source}${C.r}`);
    else console.log(`${C.red}❌ Failed: ${r.error}${C.r}`);
}

async function cmd_types() {
    console.log(`${C.cyn}📋 Registered Event Types${C.r}\n`);
    const r = await request('GET', '/events/types');
    if (!r.ok) { console.log(`${C.red}❌ ${r.error}${C.r}`); return; }
    const types = r.data?.event_types || r.data || [];
    for (const t of types) {
        const pc = pColor(t.priority || 0);
        console.log(`  ${pc}[${pLabel(t.priority || 0)}]${C.r} ${C.yel}${t.type}${C.r}`);
        console.log(`         ${C.gry}${t.description}${C.r}`);
    }
    console.log(`\n  Total: ${types.length} event types`);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── CLI ──────────────────────────────────────────────────────────────────────

const [,, cmd, ...args] = process.argv;

(async () => {
    switch (cmd) {
        case 'tail': await cmd_tail(args[0] || null, parseInt(args[1]) || 0); break;
        case 'stats': await cmd_stats(); break;
        case 'replay': await cmd_replay(args[0] || 'observer.state_change', parseInt(args[1]) || 20); break;
        case 'health': await cmd_health(); break;
        case 'emit': await cmd_emit(args[0] || 'operator.command.executed', args[1] || 'event-debug', args[2] || '{}'); break;
        case 'types': await cmd_types(); break;
        default:
            console.log(`${C.cyan}Event Fabric Debug Utilities${C.r}\n`);
            console.log(`  ${C.bld}Commands:${C.r}`);
            console.log(`  ${C.grn}tail${C.r}   [type] [min_priority]  Live tail of events`);
            console.log(`  ${C.grn}stats${C.r}                       Event statistics`);
            console.log(`  ${C.grn}replay${C.r} <type> [limit]       Replay events from history`);
            console.log(`  ${C.grn}health${C.r}                      OCE health check`);
            console.log(`  ${C.grn}emit${C.r}   <type> <src> [json]  Emit test event`);
            console.log(`  ${C.grn}types${C.r}                       List registered event types`);
            console.log(`\n  ${C.gry}Env: OCE_HOST, OCE_PORT (default: 127.0.0.1:8000)${C.r}`);
    }
})();
