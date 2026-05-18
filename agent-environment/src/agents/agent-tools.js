/**
 * Agent Tools — Tools available to agents within the environment.
 * Each tool is a function agents can invoke via the message bus.
 */

const { runPython } = require('../sandbox/python-runner');
const { runNode } = require('../sandbox/node-runner');
const { readFile, writeFile, listFiles, deleteFile } = require('../sandbox/file-system');
const logger = require('../utils/logger');

/**
 * Execute Python code.
 */
async function toolExecutePython(agentId, { code, timeoutMs }) {
  logger.info('Agent executing python', { agentId, codeLength: code?.length });
  const result = await runPython(code || '', { timeoutMs });
  return { type: 'python-result', agentId, ...result };
}

/**
 * Execute Node.js code.
 */
async function toolExecuteNode(agentId, { code, timeoutMs }) {
  logger.info('Agent executing node', { agentId, codeLength: code?.length });
  const result = await runNode(code || '', { timeoutMs });
  return { type: 'node-result', agentId, ...result };
}

/**
 * Read a file from the workspace.
 */
function toolReadFile(agentId, { path }) {
  logger.info('Agent reading file', { agentId, path });
  return { type: 'file-read-result', agentId, ...readFile(path) };
}

/**
 * Write a file to the workspace.
 */
function toolWriteFile(agentId, { path, content }) {
  logger.info('Agent writing file', { agentId, path });
  return { type: 'file-write-result', agentId, ...writeFile(path, content) };
}

/**
 * List files in a directory.
 */
function toolListFiles(agentId, { path = '.' }) {
  return { type: 'file-list-result', agentId, ...listFiles(path) };
}

/**
 * Delete a file.
 */
function toolDeleteFile(agentId, { path }) {
  logger.info('Agent deleting file', { agentId, path });
  return { type: 'file-delete-result', agentId, ...deleteFile(path) };
}

// Tool registry — maps tool name to handler
const tools = {
  'execute-python': toolExecutePython,
  'execute-node': toolExecuteNode,
  'read-file': toolReadFile,
  'write-file': toolWriteFile,
  'list-files': toolListFiles,
  'delete-file': toolDeleteFile,
};

/**
 * Invoke a tool by name.
 */
async function invokeTool(toolName, agentId, params = {}) {
  const tool = tools[toolName];
  if (!tool) return { success: false, error: `Unknown tool: ${toolName}` };
  try {
    const result = await tool(agentId, params);
    return { success: true, result };
  } catch (err) {
    logger.error('Tool invocation failed', { toolName, agentId, error: err.message });
    return { success: false, error: err.message };
  }
}

function listTools() {
  return Object.keys(tools).map(name => ({
    name,
    description: getToolDescription(name),
  }));
}

function getToolDescription(name) {
  const descriptions = {
    'execute-python': 'Execute Python code in the sandbox',
    'execute-node': 'Execute Node.js code in the sandbox',
    'read-file': 'Read a file from the workspace',
    'write-file': 'Write a file to the workspace',
    'list-files': 'List files in a workspace directory',
    'delete-file': 'Delete a file from the workspace',
  };
  return descriptions[name] || 'No description';
}

module.exports = { invokeTool, listTools };
