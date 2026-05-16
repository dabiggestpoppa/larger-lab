/**
 * VS Code Controller — Phase 2
 * 
 * Gives OpenClaw direct control over VS Code through its CLI.
 * All tools return { success: boolean, ...data }
 * 
 * Usage:
 *   const vscode = require('./vscode-controller');
 *   const result = await vscode.vscode_open_file('src/main.ts', 10, 5);
 */

const { exec, execSync } = require('child_process');
const { promisify } = require('util');
const path = require('path');
const fs = require('fs');
const os = require('os');

const execAsync = promisify(exec);

const IS_WINDOWS = os.platform() === 'win32';

// ── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Find the VS Code CLI path.
 * @returns {string} Path to code command
 */
function find_vscode_cli() {
    const candidates = IS_WINDOWS
        ? [
            path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Microsoft VS Code', 'bin', 'code.cmd'),
            path.join(process.env.ProgramFiles || '', 'Microsoft VS Code', 'bin', 'code.cmd'),
            'code',
        ]
        : [
            '/usr/local/bin/code',
            '/usr/bin/code',
            'code',
        ];

    for (const candidate of candidates) {
        try {
            if (candidate === 'code' || fs.existsSync(candidate)) {
                execSync(`${candidate} --version`, { stdio: 'pipe' });
                return candidate;
            }
        } catch (e) { /* try next */ }
    }
    return 'code'; // fallback
}

let _vscodePath = null;
function get_vscode_path() {
    if (!_vscodePath) _vscodePath = find_vscode_cli();
    return _vscodePath;
}

async function run_vscode(args, timeout = 15000) {
    const cmd = `${get_vscode_path()} ${args}`;
    try {
        const { stdout, stderr } = await execAsync(cmd, {
            timeout,
            maxBuffer: 5 * 1024 * 1024,
            encoding: 'utf-8',
        });
        return { success: true, stdout: stdout.trim(), stderr: stderr.trim() };
    } catch (error) {
        return {
            success: false,
            stdout: (error.stdout || '').trim(),
            stderr: (error.stderr || '').trim(),
            error: error.message,
        };
    }
}

// ── Tool: vscode_open_file ───────────────────────────────────────────────────

/**
 * Open a file in VS Code with optional line/column navigation.
 * @param {string} filePath - Path to file
 * @param {number} line - Line number (optional)
 * @param {number} column - Column number (optional)
 * @returns {Promise<object>}
 */
async function vscode_open_file(filePath, line = null, column = null) {
    let args = `--goto "${filePath}"`;
    if (line !== null) {
        args = `--goto "${filePath}:${line}${column ? ':' + column : ''}"`;
    }
    return run_vscode(args);
}

// ── Tool: vscode_run_command ──────────────────────────────────────────────────

/**
 * Execute a VS Code command by ID.
 * @param {string} commandId - VS Code command ID (e.g., 'editor.action.formatDocument')
 * @param {string} args - JSON string of arguments (optional)
 * @returns {Promise<object>}
 */
async function vscode_run_command(commandId, args = null) {
    // Use the CLI to run commands via the workbench action
    const cmdArgs = args
        ? `--command "${commandId}" --args '${args}'`
        : `--command "${commandId}"`;
    return run_vscode(cmdArgs);
}

// ── Tool: vscode_run_in_terminal ──────────────────────────────────────────────

/**
 * Run a command in VS Code's integrated terminal.
 * @param {string} command - Command to run
 * @param {string} terminalName - Optional terminal name
 * @returns {Promise<object>}
 */
async function vscode_run_in_terminal(command, terminalName = null) {
    const nameArg = terminalName ? `--terminal-name "${terminalName}"` : '';
    return run_vscode(`--command "workbench.action.terminal.sendSequence" --args '{"text": "${command}\\r"}' ${nameArg}`);
}

// ── Tool: vscode_search_workspace ─────────────────────────────────────────────

/**
 * Search across workspace using ripgrep.
 * @param {string} pattern - Search pattern
 * @param {string} path - Path to search in (default: workspace root)
 * @param {boolean} caseSensitive - Case sensitive search
 * @param {string} filePattern - File glob pattern (e.g., "*.ts")
 * @returns {Promise<object>}
 */
async function vscode_search_workspace(pattern, path = null, caseSensitive = false, filePattern = null) {
    let args = `--search "${pattern}"`;
    if (path) args += ` --folder "${path}"`;
    if (caseSensitive) args += ' --case-sensitive';
    if (filePattern) args += ` --glob "${filePattern}"`;
    return run_vscode(args);
}

// ── Tool: vscode_edit_file ────────────────────────────────────────────────────

/**
 * Insert, replace, or delete text in a file.
 * @param {string} filePath - Path to file
 * @param {string} action - 'insert', 'replace', 'delete'
 * @param {object} options - { line, column, text, startLine, endLine }
 * @returns {Promise<object>}
 */
async function vscode_edit_file(filePath, action, options = {}) {
    try {
        const absPath = path.resolve(filePath);
        if (!fs.existsSync(absPath)) {
            return { success: false, error: `File not found: ${absPath}` };
        }

        const content = fs.readFileSync(absPath, 'utf-8');
        const lines = content.split('\n');

        switch (action) {
            case 'insert': {
                const lineNum = options.line || lines.length;
                const text = options.text || '';
                lines.splice(lineNum - 1, 0, text);
                fs.writeFileSync(absPath, lines.join('\n'), 'utf-8');
                return { success: true, action: 'insert', line: lineNum, file: absPath };
            }
            case 'replace': {
                const startLine = options.startLine || 1;
                const endLine = options.endLine || startLine;
                const newText = options.text || '';
                lines.splice(startLine - 1, endLine - startLine + 1, newText);
                fs.writeFileSync(absPath, lines.join('\n'), 'utf-8');
                return { success: true, action: 'replace', startLine, endLine, file: absPath };
            }
            case 'delete': {
                const startLine = options.startLine || 1;
                const endLine = options.endLine || startLine;
                lines.splice(startLine - 1, endLine - startLine + 1);
                fs.writeFileSync(absPath, lines.join('\n'), 'utf-8');
                return { success: true, action: 'delete', startLine, endLine, file: absPath };
            }
            default:
                return { success: false, error: `Unknown action: ${action}. Use: insert, replace, delete` };
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ── Tool: vscode_install_extension ────────────────────────────────────────────

/**
 * Install a VS Code extension.
 * @param {string} extensionId - Extension ID (e.g., 'ms-python.python')
 * @returns {Promise<object>}
 */
async function vscode_install_extension(extensionId) {
    return run_vscode(`--install-extension ${extensionId} --force`, 60000);
}

// ── Tool: vscode_git_commit ───────────────────────────────────────────────────

/**
 * Stage, commit, and optionally push.
 * @param {string} message - Commit message
 * @param {boolean} push - Whether to push after commit
 * @param {string} files - Files to stage (default: all)
 * @returns {Promise<object>}
 */
async function vscode_git_commit(message, push = false, files = '.') {
    const results = {};

    // Stage files
    const stageResult = await run_vscode(`add "${files}"`);
    if (!stageResult.success) return { success: false, stage: stageResult, error: 'Stage failed' };
    results.stage = stageResult;

    // Commit
    const commitResult = await run_vscode(`commit -m "${message}"`);
    if (!commitResult.success) return { success: false, commit: commitResult, error: 'Commit failed' };
    results.commit = commitResult;

    // Push
    if (push) {
        const pushResult = await run_vscode('push');
        results.push = pushResult;
    }

    return { success: true, ...results };
}

// ── Tool: vscode_get_problems ─────────────────────────────────────────────────

/**
 * Read problems (errors/warnings) from VS Code.
 * @param {string} filePath - Optional file to filter by
 * @returns {Promise<object>}
 */
async function vscode_get_problems(filePath = null) {
    // VS Code doesn't expose problems via CLI directly
    // We use the problems.json from the workspace storage as a workaround
    const args = filePath
        ? `--command "workbench.actions.view.problems" --args '{"filter": "${filePath}"}`
        : `--command "workbench.actions.view.problems"`;
    return run_vscode(args);
}

// ── Tool: vscode_list_extensions ──────────────────────────────────────────────

/**
 * List installed VS Code extensions.
 * @param {boolean} showVersions - Show version numbers
 * @returns {Promise<object>}
 */
async function vscode_list_extensions(showVersions = true) {
    const args = showVersions
        ? '--list-extensions --show-versions'
        : '--list-extensions';
    const result = await run_vscode(args);
    if (result.success && result.stdout) {
        const extensions = result.stdout.split('\n')
            .filter(l => l.trim())
            .map(l => {
                const parts = l.split('@');
                return { id: parts[0], version: parts[1] || 'unknown' };
            });
        return { success: true, extensions, count: extensions.length };
    }
    return result;
}

// ── Tool: vscode_get_workspace ────────────────────────────────────────────────

/**
 * Get current workspace information.
 * @returns {Promise<object>}
 */
async function vscode_get_workspace() {
    const result = await run_vscode('--status');
    if (result.success) {
        return { success: true, status: result.stdout };
    }
    return result;
}

// ── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
    // File operations
    vscode_open_file,
    vscode_edit_file,

    // Command execution
    vscode_run_command,
    vscode_run_in_terminal,

    // Search
    vscode_search_workspace,

    // Extensions
    vscode_install_extension,
    vscode_list_extensions,

    // Git
    vscode_git_commit,

    // Problems
    vscode_get_problems,

    // Workspace
    vscode_get_workspace,

    // Helpers
    find_vscode_cli,
    get_vscode_path,
};
