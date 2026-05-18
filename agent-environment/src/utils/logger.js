/**
 * Logger — Simple timestamped console logger.
 * Writes to console with level prefixes. No external deps.
 */

const LOG_LEVELS = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 };
const CURRENT_LEVEL = LOG_LEVELS[process.env.LOG_LEVEL || 'INFO'] ?? 1;

function format(level, msg, meta) {
  const ts = new Date().toISOString();
  const base = `[${ts}] [${level}]`;
  if (meta) return `${base} ${msg} ${JSON.stringify(meta)}`;
  return `${base} ${msg}`;
}

module.exports = {
  debug(msg, meta) { if (CURRENT_LEVEL <= 0) console.log(format('DEBUG', msg, meta)); },
  info(msg, meta)  { if (CURRENT_LEVEL <= 1) console.log(format('INFO', msg, meta)); },
  warn(msg, meta)  { if (CURRENT_LEVEL <= 2) console.warn(format('WARN', msg, meta)); },
  error(msg, meta) { if (CURRENT_LEVEL <= 3) console.error(format('ERROR', msg, meta)); },
};
