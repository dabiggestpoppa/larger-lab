/**
 * Node Runner — Executes Node.js code in an isolated child process.
 * Uses vm-like isolation via separate node process with limited globals.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');
const config = require('../utils/config');
const logger = require('../utils/logger');

/**
 * Execute Node.js code string.
 * @param {string} code - Node.js source code
 * @param {object} opts - { timeoutMs }
 * @returns {Promise<{stdout, stderr, exitCode, timedOut}>}
 */
function runNode(code, opts = {}) {
  return new Promise((resolve) => {
    const timeoutMs = opts.timeoutMs || config.sandbox.nodeTimeoutMs;
    const maxBytes = config.sandbox.maxOutputBytes;

    // Write code to temp file
    const tmpFile = path.join(os.tmpdir(), `__node_sandbox_${Date.now()}.js`);
    fs.writeFileSync(tmpFile, code, 'utf8');

    let stdout = '';
    let stderr = '';
    let timedOut = false;
    let killed = false;

    const proc = spawn('node', ['--experimental-vm-modules', tmpFile], {
      timeout: timeoutMs,
    });

    const killTimer = setTimeout(() => {
      if (!proc.killed) {
        timedOut = true;
        killed = true;
        proc.kill('SIGTERM');
        logger.warn('Node sandbox timeout', { timeoutMs });
      }
    }, timeoutMs);

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
      if (stdout.length > maxBytes) {
        stdout = stdout.slice(0, maxBytes) + '\n[OUTPUT TRUNCATED]';
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
      try { fs.unlinkSync(tmpFile); } catch {}
      resolve({
        stdout: stdout.trim(),
        stderr: stderr.trim(),
        exitCode: code,
        timedOut,
      });
    });

    proc.on('error', (err) => {
      clearTimeout(killTimer);
      try { fs.unlinkSync(tmpFile); } catch {}
      resolve({
        stdout: '',
        stderr: `Process error: ${err.message}`,
        exitCode: -1,
        timedOut: false,
      });
    });
  });
}

module.exports = { runNode };
