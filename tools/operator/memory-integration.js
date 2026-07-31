/**
 * Operator ↔ Structural Memory Integration — OCE-4.17
 *
 * Connects Operator tools to OCE Structural Memory layer.
 * - Operator actions stored in memory for continuity
 * - Operator can query memory for historical context
 * - Bridges system commands → memory snapshots
 * - Reconstructs operator state from memory anchors
 *
 * Endpoints used:
 *   GET  /memory                     — Full memory view (trajectory + structural)
 *   GET  /memory/observers/{id}/timeline  — Observer timeline
 *   GET  /memory/observers/{id}/snapshot  — State at time
 *   POST /memory/observers/{id}/compress  — Trigger compression
 *   POST /memory/observers/{id}/reconstruct — Rebuild state
 *   GET  /memory/search              — Search across memory layers
 *   GET  /memory/stats               — Memory usage statistics
 *
 * Usage:
 *   const mi = require('./memory-integration');
 *   await mi.init();
 *   await mi.storeAction('exec', { command: 'Get-Process' });  // Store operator action
 *   const ctx = await mi.getContext('recent', 10);              // Get recent context
 *   const timeline = await mi.getTimeline(observerId);          // Get observer timeline
 *   const state = await mi.reconstruct(observerId);             // Rebuild observer state
 */

const http = require('http');
const { EventEmitter } = require('events');
const fs = require('fs');
const path = require('path');

const OCE_HOST = process.env.OCE_HOST || '127.0.0.1';
const OCE_PORT = process.env.OCE_PORT || 8000;

let _config = { host: OCE_HOST, port: OCE_PORT, enabled: true };
let _eventEmitter = new EventEmitter();
let _actionLog = [];           // Local action buffer (pre-persistence)
let _actionLogMax = 500;       // Max local entries before flush

// ── HTTP Helper ──────────────────────────────────────────────────────────────

function request(method, path, body = null) {
    return new Promise((resolve) => {
        const bodyData = body ? JSON.stringify(body) : null;
        const options = {
            hostname: _config.host, port: _config.port,
            path, method,
            headers: { 'Content-Type': 'application/json' },
            timeout: 15000,
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

// ── Event Emission ────────────────────────────────────────────────────────────

async function emitEvent(eventType, source, payload = {}, priority = null) {
    if (!_config.enabled) return { success: true, skipped: true };
    const body = { event_type: eventType, source, payload };
    if (priority !== null) body.priority = priority;
    const result = await request('POST', '/events/ingest', body);
    if (result.ok) _eventEmitter.emit('emitted', { eventType, source, payload });
    return result;
}

// ── Memory Event Types ───────────────────────────────────────────────────────

const MEMORY_EVENTS = {
    ACTION_STORED:     'memory.action.stored',
    ACTION_REPLAYED:   'memory.action.replayed',
    SNAPSHOT_CREATED:  'memory.snapshot.created',
    COMPRESSION_RUN:   'memory.compression.run',
    RECONSTRUCTED:     'memory.reconstructed',
    CONTEXT_LOADED:    'memory.context.loaded',
    TIMELINE_QUERIED:  'memory.timeline.queried',
    SEARCH_PERFORMED:  'memory.search.performed',
};

// ── OCE-4.17: Operator ↔ Memory Integration ─────────────────────────────────

/**
 * Store an operator action in memory.
 * Buffers locally and emits event for persistence.
 *
 * @param {string} actionType  — 'exec', 'kill', 'edit', 'vscode', 'observer', 'system'
 * @param {object} details     — Action-specific details
 * @returns {object}           — { logged: true, entry: {...} }
 */
async function storeAction(actionType, details = {}) {
    const entry = {
        id: `action_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`,
        action_type: actionType,
        details,
        timestamp: new Date().toISOString(),
        source: 'operator',
    };

    // Buffer locally
    _actionLog.push(entry);
    if (_actionLog.length > _actionLogMax) {
        _actionLog = _actionLog.slice(-_actionLogMax);
    }

    // Emit event for OCE persistence
    await emitEvent(MEMORY_EVENTS.ACTION_STORED, 'operator', {
        action_id: entry.id,
        action_type: actionType,
        summary: JSON.stringify(details).substring(0, 200),
    }, 0);

    _eventEmitter.emit('action:stored', entry);
    return { logged: true, entry };
}

/**
 * Get recent operator context from local buffer + OCE memory.
 *
 * @param {string} scope   — 'recent' | 'session' | 'full'
 * @param {number} limit   — Max entries to return
 * @returns {object}       — { actions: [...], trajectory: [...], structural: {...} }
 */
async function getContext(scope = 'recent', limit = 20) {
    const result = {
        actions: [],
        trajectory: [],
        structural: {},
        scope,
        timestamp: new Date().toISOString(),
    };

    // Local action buffer
    if (scope === 'recent') {
        result.actions = _actionLog.slice(-limit);
    } else if (scope === 'session') {
        result.actions = _actionLog;
    } else {
        result.actions = _actionLog;
    }

    // Query OCE memory for trajectory + structural
    const memRes = await request('GET', '/memory');
    if (memRes.ok && memRes.data) {
        result.trajectory = memRes.data.trajectory_memory || [];
        result.structural = memRes.data.structural_memory || {};
    }

    await emitEvent(MEMORY_EVENTS.CONTEXT_LOADED, 'operator', {
        scope,
        action_count: result.actions.length,
        trajectory_count: result.trajectory.length,
    }, 0);

    return result;
}

/**
 * Get observer timeline from Structural Memory.
 *
 * @param {string} observerId  — Observer ID
 * @param {object} options     — { since, until, limit }
 * @returns {object}           — Timeline data
 */
async function getTimeline(observerId, options = {}) {
    const params = new URLSearchParams();
    if (options.since) params.set('since', options.since);
    if (options.until) params.set('until', options.until);
    if (options.limit) params.set('limit', String(options.limit));
    const qs = params.toString() ? `?${params.toString()}` : '';

    const res = await request('GET', `/memory/observers/${observerId}/timeline${qs}`);

    await emitEvent(MEMORY_EVENTS.TIMELINE_QUERIED, 'operator', {
        observer_id: observerId,
        found: res.ok,
    }, 0);

    return res;
}

/**
 * Get observer state snapshot at a point in time.
 *
 * @param {string} observerId  — Observer ID
 * @param {string} timestamp   — ISO timestamp (optional, default: now)
 * @returns {object}           — Snapshot data
 */
async function getSnapshot(observerId, timestamp = null) {
    const qs = timestamp ? `?timestamp=${encodeURIComponent(timestamp)}` : '';
    const res = await request('GET', `/memory/observers/${observerId}/snapshot${qs}`);

    if (res.ok) {
        await emitEvent(MEMORY_EVENTS.SNAPSHOT_CREATED, 'operator', {
            observer_id: observerId,
            timestamp: timestamp || 'latest',
        }, 0);
    }

    return res;
}

/**
 * Trigger memory compression for an observer.
 *
 * @param {string} observerId  — Observer ID
 * @param {object} options     — { max_age, ratio }
 * @returns {object}           — Compression result
 */
async function compressMemory(observerId, options = {}) {
    const res = await request('POST', `/memory/observers/${observerId}/compress`, options);

    await emitEvent(MEMORY_EVENTS.COMPRESSION_RUN, 'operator', {
        observer_id: observerId,
        success: res.ok,
        options,
    }, res.ok ? 0 : 2);

    return res;
}

/**
 * Reconstruct observer state from memory anchors.
 *
 * @param {string} observerId  — Observer ID
 * @param {string} timestamp   — Target timestamp (optional)
 * @returns {object}           — Reconstructed state
 */
async function reconstructState(observerId, timestamp = null) {
    const body = timestamp ? { timestamp } : {};
    const res = await request('POST', `/memory/observers/${observerId}/reconstruct`, body);

    await emitEvent(MEMORY_EVENTS.RECONSTRUCTED, 'operator', {
        observer_id: observerId,
        timestamp: timestamp || 'latest',
        success: res.ok,
    }, res.ok ? 1 : 3);

    return res;
}

/**
 * Search across memory layers.
 *
 * @param {string} query       — Search query
 * @param {object} options     — { layers, limit, since, until }
 * @returns {object}           — Search results grouped by layer
 */
async function searchMemory(query, options = {}) {
    const params = new URLSearchParams({ q: query });
    if (options.layers) params.set('layers', options.layers.join(','));
    if (options.limit) params.set('limit', String(options.limit));
    if (options.since) params.set('since', options.since);
    if (options.until) params.set('until', options.until);

    const res = await request('GET', `/memory/search?${params.toString()}`);

    await emitEvent(MEMORY_EVENTS.SEARCH_PERFORMED, 'operator', {
        query: query.substring(0, 100),
        found: res.ok,
        result_count: res.data ? (Array.isArray(res.data) ? res.data.length : Object.keys(res.data).length) : 0,
    }, 0);

    return res;
}

/**
 * Get memory usage statistics.
 *
 * @returns {object} — Memory stats (usage by layer, compression ratios, etc.)
 */
async function getMemoryStats() {
    return await request('GET', '/memory/stats');
}

/**
 * Replay a stored action by ID.
 *
 * @param {string} actionId  — Action ID from storeAction
 * @returns {object}         — { found: boolean, entry: {...} }
 */
async function replayAction(actionId) {
    const entry = _actionLog.find(a => a.id === actionId);
    if (!entry) {
        return { found: false, error: `Action not found: ${actionId}` };
    }

    await emitEvent(MEMORY_EVENTS.ACTION_REPLAYED, 'operator', {
        action_id: actionId,
        action_type: entry.action_type,
    }, 1);

    return { found: true, entry };
}

/**
 * Flush local action log to disk (survives restart).
 *
 * @param {string} filePath  — Override path (optional)
 * @returns {object}         — { flushed: number, path: string }
 */
function flushActionLog(filePath = null) {
    const logPath = filePath || path.join(
        process.env.TEMP || '/tmp',
        'operator-action-log.json'
    );
    fs.writeFileSync(logPath, JSON.stringify(_actionLog, null, 2), 'utf-8');
    return { flushed: _actionLog.length, path: logPath };
}

/**
 * Load action log from disk.
 *
 * @param {string} filePath  — Override path (optional)
 * @returns {object}         — { loaded: number, path: string }
 */
function loadActionLog(filePath = null) {
    const logPath = filePath || path.join(
        process.env.TEMP || '/tmp',
        'operator-action-log.json'
    );
    if (!fs.existsSync(logPath)) {
        return { loaded: 0, path: logPath, note: 'File not found' };
    }
    const data = JSON.parse(fs.readFileSync(logPath, 'utf-8'));
    _actionLog = Array.isArray(data) ? data : [];
    return { loaded: _actionLog.length, path: logPath };
}

// ── Init ──────────────────────────────────────────────────────────────────────

function init(config = {}) {
    _config = { ..._config, ...config };
    return _config;
}

// ── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
    init,
    emitEvent,
    request,
    MEMORY_EVENTS,

    // Operator → Memory actions
    storeAction,
    getContext,
    replayAction,
    flushActionLog,
    loadActionLog,

    // Memory queries
    getTimeline,
    getSnapshot,
    compressMemory,
    reconstructState,
    searchMemory,
    getMemoryStats,

    // Event system
    on: (event, cb) => _eventEmitter.on(event, cb),
    off: (event, cb) => _eventEmitter.off(event, cb),

    // Internal (for testing)
    _getActionLog: () => [..._actionLog],
    _clearActionLog: () => { _actionLog = []; },
};
