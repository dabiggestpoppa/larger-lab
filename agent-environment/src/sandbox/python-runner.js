/**
 * Python Runner — Executes Python code in a child process with timeout.
 * Captures stdout, stderr, and return code. Enforces output limits.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const config = require('../utils/config');
const logger = require('../utils/logger');

// Ensure workspace exists
const workspaceRoot = path.resolve(config.sandbox.workspaceRoot);
fs.mkdirSync(workspaceRoot, { recursive: true });

/**
 * Execute Python code string.
 * @param {string} code - Python source code
 * @param {object} opts - { timeoutMs, filename }
 * @returns {Promise<{stdout, stderr, exitCode, timedOut}>}
 */
function runPython(code, opts = {}) {
  return new Promise((resolve) => {
    const timeoutMs = opts.timeoutMs || config.sandbox.pythonTimeoutMs;
    const maxBytes = config.sandbox.maxOutputBytes;

    // Write code to a temp file in workspace
    const tmpFile = opts.filename || `__sandbox_${Date.now()}.py`;
    const tmpPath = path.join(workspaceRoot, tmpFile);
    fs.writeFileSync(tmpPath, code, 'utf8');

    let stdout = '';
    let stderr = '';
    let timedOut = false;
    let killed = false;

    const proc = spawn('python', ['-u', tmpPath], {
      cwd: workspaceRoot,
      env: {
        ...process.env,
        PYTHONIOENCODING: 'utf-8',
      },
      timeout: timeoutMs,
    });

    const killTimer = setTimeout(() => {
      if (!proc.killed) {
        timedOut = true;
        killed = true;
        proc.kill('SIGTERM');
        logger.warn('Python sandbox timeout', { file: tmpFile, timeoutMs });
      }
    }, timeoutMs);

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
      if (stdout.length > maxBytes) {
        stdout = stdout.slice(0, maxBytes) + '\n[OUTPUT TRUNCATED — exceeded max size]';
        if (!killed) { killed = true; proc.kill('SIGTERM'); }
      }
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
      if (stderr.length > maxBytes) {
        stderr = stderr.slice(0, maxBytes) + '\n[ERROR OUTPUT TRUNCATED]';
      }
    });

    proc.on('close', (code) => {
      clearTimeout(killTimer);
      // Clean up temp file (unless it was a named file)
      if (!opts.filename) {
        try { fs.unlinkSync(tmpPath); } catch {}
      }
      resolve({
        stdout: stdout.trim(),
        stderr: stderr.trim(),
        exitCode: code,
        timedOut,
      });
    });

    proc.on('error', (err) => {
      clearTimeout(killTimer);
      resolve({
        stdout: '',
        stderr: `Process error: ${err.message}`,
        exitCode: -1,
        timedOut: false,
      });
    });
  });
}

module.exports = { runPython };
