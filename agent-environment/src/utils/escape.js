/**
 * HTML Escape — XSS prevention for user-generated content.
 * Escapes characters that have special meaning in HTML so that
 * agent names, messages, room names, etc. can be safely rendered
 * via innerHTML on the frontend.
 */

const HTML_ENTITIES = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#x27;',
  '/': '&#x2F;',
  '`': '&#x60;',
  '=': '&#x3D;',
};

/**
 * Escape a string for safe HTML insertion.
 * @param {string} str - Raw user input
 * @returns {string} Escaped string safe for innerHTML
 */
function escapeHtml(str) {
  if (str == null) return '';
  return String(str).replace(/[&<>"'`=/]/g, (ch) => HTML_ENTITIES[ch] || ch);
}

/**
 * Deep-escape an object's string values (shallow — one level).
 * Useful for sanitizing API/WS response objects before sending.
 * @param {object} obj - Object with potentially unsafe string values
 * @param {string[]} keys - Keys to escape (if omitted, escapes all string values)
 * @returns {object} New object with escaped values
 */
function escapeObject(obj, keys = null) {
  if (!obj || typeof obj !== 'object') return obj;
  const result = { ...obj };
  for (const [key, val] of Object.entries(result)) {
    if (typeof val !== 'string') continue;
    if (keys && !keys.includes(key)) continue;
    result[key] = escapeHtml(val);
  }
  return result;
}

module.exports = { escapeHtml, escapeObject };
