/**
 * TradeLocker Studio MCP Server.
 *
 * Provides tools for:
 * - Writing bot code into TradeLocker Studio's Monaco editor
 * - Running backtests via the Studio engine
 * - Reading backtest results
 * - Managing projects
 * - Configuring strategy parameters
 *
 * Architecture:
 *   Claude Code ←→ MCP (stdio) ←→ Studio Engine (localhost:53163)
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { registerProjectTools } from './tools/project.js';
import { registerCodeTools } from './tools/code.js';
import { registerBacktestTools } from './tools/backtest.js';
import { registerConfigTools } from './tools/config.js';
import { registerChatTools } from './tools/chat.js';
import { registerHealthTools } from './tools/health.js';

const server = new McpServer(
  {
    name: 'tradelocker-studio',
    version: '0.1.0',
    description: 'Write bot code, run backtests, and read results in TradeLocker Studio',
  },
  {
    instructions: `TradeLocker Studio MCP — Tools for bot development in TradeLocker Studio.

TOOL SELECTION GUIDE:
- "Create a new bot" → project_list to find existing, or tell user to create in Studio UI first
- "Write code for bot" → code_write with file_id and code
- "Run a backtest" → backtest_run with project_id
- "Check backtest results" → backtest_results with project_id and process_id
- "Configure backtest" → config_set with symbol, resolution, dates, margin
- "List projects" → project_list
- "Read bot code" → code_read with file_id

The Studio engine runs at http://127.0.0.1:53163 (TradeLocker Desktop spawns it).
Authentication uses JWT tokens from the TradeLocker REST API.`,
  },
);

// Register all tool groups
registerHealthTools(server);
registerProjectTools(server);
registerCodeTools(server);
registerBacktestTools(server);
registerConfigTools(server);
registerChatTools(server);

// Startup notice
process.stderr.write('⚠  tradelocker-studio MCP  |  TradeLocker Studio bot development tools\n');
process.stderr.write('   Requires TradeLocker Desktop running (spawns engine on :53163)\n\n');

// Start stdio transport
const transport = new StdioServerTransport();
await server.connect(transport);
