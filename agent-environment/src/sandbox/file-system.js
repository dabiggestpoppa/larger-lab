/**
 * File System — Shared virtual filesystem for agents.
 * All paths are relative to the workspace root to prevent escape.
 */

const fs = require('fs');
const path = require('path');
const config = require('../utils/config');
const logger = require('../utils/logger');

const workspaceRoot = path.resolve(config.sandbox.workspaceRoot);

// Ensure workspace exists
fs.mkdirSync(workspaceRoot, { recursive: true });

/**
 * Resolve a relative path safely — prevents directory traversal.
 * Returns absolute path if safe, null if it escapes workspace.
 */
function safeResolve(relPath) {
  const resolved = path.resolve(workspaceRoot, relPath);
  if (!resolved.startsWith(workspaceRoot + path.sep) && resolved !== workspaceRoot) {
    logger.warn('Filesystem path escape attempt blocked', { path: relPath });
    return null;
  }
  return resolved;
}

function readFile(relPath) {
  const abs = safeResolve(relPath);
  if (!abs) return { success: false, error: 'Path escapes workspace root' };
  if (!fs.existsSync(abs)) return { success: false, error: 'File not found' };
  const stat = fs.statSync(abs);
  if (stat.size > config.sandbox.maxFileSizeBytes) {
    return { success: false, error: 'File exceeds maximum size' };
  }
  const content = fs.readFileSync(abs, 'utf8');
  return { success: true, content, size: stat.size };
}

function writeFile(relPath, content) {
  const abs = safeResolve(relPath);
  if (!abs) return { success: false, error: 'Path escapes workspace root' };
  if (typeof content !== 'string') {
    content = JSON.stringify(content, null, 2);
  }
  if (Buffer.byteLength(content, 'utf8') > config.sandbox.maxFileSizeBytes) {
    return { success: false, error: 'Content exceeds maximum file size' };
  }
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, content, 'utf8');
  logger.info('File written', { path: relPath, size: Buffer.byteLength(content, 'utf8') });
  return { success: true, path: relPath };
}

function listFiles(dirPath = '.') {
  const abs = safeResolve(dirPath);
  if (!abs) return { success: false, error: 'Path escapes workspace root' };
  if (!fs.existsSync(abs)) return { success: false, error: 'Directory not found' };
  const entries = fs.readdirSync(abs, { withFileTypes: true });
  const files = entries.map(e => ({
    name: e.name,
    path: path.join(dirPath, e.name).replace(/\\/g, '/'),
    isDirectory: e.isDirectory(),
    isFile: e.isFile(),
  }));
  return { success: true, files, count: files.length };
}

function deleteFile(relPath) {
  const abs = safeResolve(relPath);
  if (!abs) return { success: false, error: 'Path escapes workspace root' };
  if (!fs.existsSync(abs)) return { success: false, error: 'File not found' };
  fs.unlinkSync(abs);
  logger.info('File deleted', { path: relPath });
  return { success: true };
}

module.exports = { readFile, writeFile, listFiles, deleteFile, workspaceRoot };
