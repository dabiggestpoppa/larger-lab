/**
 * Operator ↔ Event Fabric Integration
 * 
 * Connects System Operator and VS Code Controller tools to the OCE Event Fabric.
 * Every operator action emits a corresponding event into the fabric.
 * 
 * This is the bridge between PM's Operator tools and CC's Event Fabric.
 * 
 * Usage:
 *   const integration = require('./event-integration');
 *   await integration.init(); // Connect to running OCE backend
 *   const result = await integration.exec_and_emit('Get-Process | Select-Object -First 5');
 */

const http = require('http');
const { URL } = require('url');

// ── Configuration ────────────────────────────────────────────────────────────

const OCE_DEFAULT_HOST = '127.0.0.1';
const OCE_DEFAULT_PORT = 8000;
const OCE_API_PREFIX = '';

let _config = {
    host: OCE_DEFAULT_HOST,
    port: OCE_DEFAULT_PORT,
    enabled: true,
};

// ── HTTP Helper ──────────────────────────────────────────────────────────────

function http_request(method, path, body = null) {
    return new Promise((resolve, reject) => {
        const url = `http://${_config.host}:${_config.port}${OCE_API_PREFIX}${path}`;
        const bodyData = body ? JSON.stringify(body) : null;

        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 10000,
        };

        if (bodyData) {
            options.headers['Content-Length'] = Buffer.byteLength(bodyData);
        }

        const req = http.request(url, options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve({ success: res.statusCode < 400, status: res.statusCode, data: JSON.parse(data) });
                } catch (e) {
                    resolve({ success: res.statusCode < 400, status: res.statusCode, data });
                }
            });
        });

        req.on('error', (e) => resolve({ success: false, error: e.message }));
        req.on('timeout', () => { req.destroy(); resolve({ success: false, error: 'timeout' }); });

        if (bodyData) req.write(bodyData);
        req.end();
    });
}

// ── Event Emission ────────────────────────────────────────────────────────────

/**
 * Emit an event into the OCE Event Fabric.
 * @param {string} event_type - Event type (e.g., 'operator.command.executed')
 * @param {string} source - Source subsystem
 * @param {object} payload - Event payload
 * @param {number} priority - Event priority (0-3)
 * @returns {Promise<object>}
 */
async function emit_event(event_type, source, payload = {}, priority = null) {
    if (!_config.enabled) return { success: true, skipped: true };

    const body = {
        event_type,
        source,
        payload,
    };
    if (priority !== null) body.priority = priority;

    return http_request('POST', '/events/ingest', body);
}

// ── OCE-2.20: System Operator Integration ─────────────────────────────────────

/**
 * Execute a system command AND emit an event into the Event Fabric.
 * Wraps system-operator.js with event emission.
 */
async function exec_and_emit(command, timeout = 30000, cwd = null) {
    const { system_run_command } = require('./system-operator');
    const result = await system_run_command(command, timeout, cwd);

    await emit_event('operator.command.executed', 'system-operator', {
        command: command.substring(0, 500), // Truncate long commands
        success: result.success,
        exitCode: result.exitCode,
        outputLength: result.stdout ? result.stdout.length : 0,
        errorLength: result.stderr ? result.stderr.length : 0,
    }, result.success ? 1 : 3); // normal priority on success, critical on failure

    return result;
}

/**
 * Kill a process AND emit an event.
 */
async function kill_and_emit(target) {
    const { system_kill_process } = require('./system-operator');
    const result = await system_kill_process(target);

    await emit_event('operator.process.killed', 'system-operator', {
        target: String(target),
        success: result.success,
    }, 2); // high priority — process killed

    return result;
}

/**
 * Install a package AND emit an event.
 */
async function install_and_emit(packageName, manager = null) {
    const { system_install_package } = require('./system-operator');
    const result = await system_install_package(packageName, manager);

    await emit_event('operator.package.installed', 'system-operator', {
        package: packageName,
        manager: manager || 'auto-detect',
        success: result.success,
    }, result.success ? 1 : 3);

    return result;
}

// ── OCE-2.21: VS Code Controller Integration ──────────────────────────────────

/**
 * Open a file in VS Code AND emit an event.
 */
async function vscode_open_and_emit(filePath, line = null, column = null) {
    const { vscode_open_file } = require('./vscode-controller');
    const result = await vscode_open_file(filePath, line, column);

    await emit_event('operator.vscode.file_opened', 'vscode-controller', {
        file: filePath,
        line,
        column,
        success: result.success,
    }, 0); // low priority

    return result;
}

/**
 * Edit a file AND emit an event.
 */
async function vscode_edit_and_emit(filePath, action, options = {}) {
    const { vscode_edit_file } = require('./vscode-controller');
    const result = await vscode_edit_file(filePath, action, options);

    await emit_event('operator.vscode.file_edited', 'vscode-controller', {
        file: filePath,
        action,
        success: result.success,
    }, 0);

    return result;
}

/**
 * Run a VS Code command AND emit an event.
 */
async function vscode_command_and_emit(commandId, args = null) {
    const { vscode_run_command } = require('./vscode-controller');
    const result = await vscode_run_command(commandId, args);

    await emit_event('operator.vscode.command', 'vscode-controller', {
        command: commandId,
        success: result.success,
    }, 0);

    return result;
}

/**
 * Git commit AND emit an event.
 */
async function vscode_git_commit_and_emit(message, push = false, files = '.') {
    const { vscode_git_commit } = require('./vscode-controller');
    const result = await vscode_git_commit(message, push, files);

    await emit_event('operator.vscode.git_commit', 'vscode-controller', {
        message: message.substring(0, 200),
        push,
        success: result.success,
    }, 1);

    return result;
}

// ── OCE-2.23: Health Check ────────────────────────────────────────────────────

/**
 * Check OCE backend health and SRRA-OPH substrate status.
 * @returns {Promise<object>}
 */
async function check_oce_health() {
    const results = {
        timestamp: new Date().toISOString(),
        backend: null,
        srrs_substrate: null,
        event_fabric: null,
        issues: [],
    };

    // Check backend
    const backendHealth = await http_request('GET', '/health');
    results.backend = backendHealth.success ? 'healthy' : 'unhealthy';
    if (!backendHealth.success) {
        results.issues.push({ component: 'backend', error: backendHealth.error || backendHealth.data });
    }

    // Check SRRA-OPH substrate
    const srrsHealth = await http_request('GET', '/health/srrs');
    results.srrs_substrate = srrsHealth.success ? 'healthy' : 'unhealthy';
    if (!srrsHealth.success) {
        results.issues.push({ component: 'srrs_substrate', error: srrsHealth.error || srrsHealth.data });
    }

    // Check Event Fabric
    const fabricStats = await http_request('GET', '/events/stats');
    results.event_fabric = fabricStats.success ? 'healthy' : 'unhealthy';
    if (fabricStats.success && fabricStats.data) {
        results.event_fabric_stats = fabricStats.data;
    } else {
        results.issues.push({ component: 'event_fabric', error: fabricStats.error || 'No stats available' });
    }

    results.overall = results.issues.length === 0 ? 'healthy' : 'degraded';
    return results;
}

// ── Init ──────────────────────────────────────────────────────────────────────

function init(config = {}) {
    _config = { ..._config, ...config };
    return _config;
}

function disable() { _config.enabled = false; }
function enable() { _config.enabled = true; }

// ── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
    // Config
    init,
    enable,
    disable,
    emit_event,

    // OCE-2.20: System Operator integration
    exec_and_emit,
    kill_and_emit,
    install_and_emit,

    // OCE-2.21: VS Code Controller integration
    vscode_open_and_emit,
    vscode_edit_and_emit,
    vscode_command_and_emit,
    vscode_git_commit_and_emit,

    // OCE-2.23: Health check
    check_oce_health,

    // Raw HTTP
    http_request,
};
