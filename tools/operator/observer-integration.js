/**
 * Operator ↔ Observer Runtime Integration — OCE-3.16
 * 
 * Connects Operator tools to the OCE Observer Runtime.
 * - Operator actions emit observer lifecycle events
 * - Subscribes operator to observer health events
 * - Bridges system commands → observer actions
 * 
 * Usage:
 *   const oi = require('./observer-integration');
 *   await oi.init(); // Connect to OCE backend
 *   await oi.exec_and_emit('Get-Process'); // Run command + emit observer event
 *   await oi.subscribeToHealth(); // Subscribe to observer health events
 */

const http = require('http');
const { EventEmitter } = require('events');

const OCE_HOST = process.env.OCE_HOST || '127.0.0.1';
const OCE_PORT = process.env.OCE_PORT || 8000;

let _config = { host: OCE_HOST, port: OCE_PORT, enabled: true };
let _healthSubscribers = [];
let _eventEmitter = new EventEmitter();

// ── HTTP Helper ──────────────────────────────────────────────────────────────

function request(method, path, body = null) {
    return new Promise((resolve) => {
        const bodyData = body ? JSON.stringify(body) : null;
        const options = {
            hostname: _config.host, port: _config.port,
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

// ── Event Emission ────────────────────────────────────────────────────────────

async function emitEvent(eventType, source, payload = {}, priority = null) {
    if (!_config.enabled) return { success: true, skipped: true };
    const body = { event_type: eventType, source, payload };
    if (priority !== null) body.priority = priority;
    const result = await request('POST', '/events/ingest', body);
    if (result.ok) _eventEmitter.emit('emitted', { eventType, source, payload });
    return result;
}

// ── Observer Lifecycle Events ─────────────────────────────────────────────────

const OBSERVER_EVENTS = {
    COMMAND_EXECUTED: 'observer.command.executed',
    PROCESS_KILLED: 'observer.process.killed',
    FILE_MODIFIED: 'observer.file.modified',
    VSCODE_ACTION: 'observer.vscode.action',
    HEALTH_CHECK: 'observer.health.check',
    OBSERVER_CREATED: 'observer.lifecycle.created',
    OBSERVER_ACTIVATED: 'observer.lifecycle.activated',
    OBSERVER_SUSPENDED: 'observer.lifecycle.suspended',
    OBSERVER_DESTROYED: 'observer.lifecycle.destroyed',
};

// ── OCE-3.16: Operator ↔ Observer Integration ────────────────────────────────

/**
 * Execute system command AND emit observer event.
 */
async function execAndEmit(command, timeout = 30000, cwd = null) {
    const { system_run_command } = require('./system-operator');
    const startTime = Date.now();
    const result = await system_run_command(command, timeout, cwd);
    const duration = Date.now() - startTime;

    await emitEvent(OBSERVER_EVENTS.COMMAND_EXECUTED, 'operator', {
        command: command.substring(0, 500),
        success: result.success,
        exitCode: result.exitCode,
        durationMs: duration,
        outputLength: result.stdout ? result.stdout.length : 0,
    }, result.success ? 1 : 3);

    return { ...result, durationMs: duration };
}

/**
 * Kill process AND emit observer event.
 */
async function killAndEmit(target) {
    const { system_kill_process } = require('./system-operator');
    const result = await system_kill_process(target);

    await emitEvent(OBSERVER_EVENTS.PROCESS_KILLED, 'operator', {
        target: String(target),
        success: result.success,
    }, 2);

    return result;
}

/**
 * Edit file AND emit observer event.
 */
async function editAndEmit(filePath, action, options = {}) {
    const { vscode_edit_file } = require('./vscode-controller');
    const result = await vscode_edit_file(filePath, action, options);

    await emitEvent(OBSERVER_EVENTS.FILE_MODIFIED, 'operator', {
        file: filePath,
        action,
        success: result.success,
    }, 0);

    return result;
}

/**
 * VS Code action AND emit observer event.
 */
async function vscodeActionAndEmit(commandId, args = null) {
    const { vscode_run_command } = require('./vscode-controller');
    const result = await vscode_run_command(commandId, args);

    await emitEvent(OBSERVER_EVENTS.VSCODE_ACTION, 'operator', {
        command: commandId,
        success: result.success,
    }, 0);

    return result;
}

/**
 * Create an observer via OCE API.
 */
async function createObserver(observerType, config = {}) {
    const result = await request('POST', '/observers', { type: observerType, config });
    if (result.ok) {
        await emitEvent(OBSERVER_EVENTS.OBSERVER_CREATED, 'operator', {
            observerId: result.data?.observer_id,
            type: observerType,
        }, 2);
    }
    return result;
}

/**
 * Activate an observer.
 */
async function activateObserver(observerId) {
    const result = await request('POST', `/observers/${observerId}/activate`);
    if (result.ok) {
        await emitEvent(OBSERVER_EVENTS.OBSERVER_ACTIVATED, 'operator', { observerId }, 1);
    }
    return result;
}

/**
 * Suspend an observer.
 */
async function suspendObserver(observerId) {
    const result = await request('POST', `/observers/${observerId}/suspend`);
    if (result.ok) {
        await emitEvent(OBSERVER_EVENTS.OBSERVER_SUSPENDED, 'operator', { observerId }, 1);
    }
    return result;
}

/**
 * Destroy an observer.
 */
async function destroyObserver(observerId) {
    const result = await request('DELETE', `/observers/${observerId}`);
    if (result.ok) {
        await emitEvent(OBSERVER_EVENTS.OBSERVER_DESTROYED, 'operator', { observerId }, 2);
    }
    return result;
}

/**
 * Get observer health.
 */
async function getObserverHealth(observerId) {
    const result = await request('GET', `/observers/${observerId}/health`);
    await emitEvent(OBSERVER_EVENTS.HEALTH_CHECK, 'operator', {
        observerId,
        healthy: result.ok && result.data?.healthy,
    }, 0);
    return result;
}

/**
 * Subscribe to observer health events (polls for now, WebSocket later).
 */
async function subscribeToHealth(intervalMs = 30000) {
    const poll = async () => {
        const list = await request('GET', '/observers');
        if (list.ok && Array.isArray(list.data)) {
            for (const obs of list.data) {
                _eventEmitter.emit('observer:health', obs);
            }
        }
    };
    await poll();
    const interval = setInterval(poll, intervalMs);
    _healthSubscribers.push(interval);
    return interval;
}

function unsubscribeFromHealth() {
    for (const interval of _healthSubscribers) {
        clearInterval(interval);
    }
    _healthSubscribers = [];
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
    OBSERVER_EVENTS,

    // Operator → Observer actions
    execAndEmit,
    killAndEmit,
    editAndEmit,
    vscodeActionAndEmit,

    // Observer lifecycle
    createObserver,
    activateObserver,
    suspendObserver,
    destroyObserver,
    getObserverHealth,
    subscribeToHealth,
    unsubscribeFromHealth,

    // Event system
    on: (event, cb) => _eventEmitter.on(event, cb),
    off: (event, cb) => _eventEmitter.off(event, cb),
};
