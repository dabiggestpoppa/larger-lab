const http = require('http');
const options = { hostname: 'localhost', port: 18790, path: '/health', method: 'GET', timeout: 5000 };
const req = http.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => console.log('STATUS:' + res.statusCode + '\n' + data));
});
req.on('error', (e) => console.log('DOWN:' + e.message));
req.on('timeout', () => { req.destroy(); console.log('TIMEOUT'); });
req.end();
