const http = require('http');
const os = require('os');
const fs = require('fs');

// Gateway check
const req = http.request({ hostname: 'localhost', port: 18790, path: '/health', method: 'GET', timeout: 5000 }, (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => {
    console.log('GATEWAY: ' + res.statusCode + ' ' + data);
    checkSystem();
  });
});
req.on('error', (e) => { console.log('GATEWAY: DOWN - ' + e.message); checkSystem(); });
req.on('timeout', () => { req.destroy(); console.log('GATEWAY: TIMEOUT'); checkSystem(); });
req.end();

function checkSystem() {
  const freemem = Math.round(os.freemem() / 1024 / 1024);
  const totalmem = Math.round(os.totalmem() / 1024 / 1024);
  const mempct = Math.round(((totalmem - freemem) / totalmem) * 100);
  console.log('RAM: ' + freemem + 'GB free / ' + totalmem + 'GB total (' + mempct + '% used)');
  
  // Check disk
  try {
    const drives = ['C:'];
    drives.forEach(d => {
      // Use wmic for disk space
      const { execSync } = require('child_process');
      const result = execSync('wmic logicaldisk where "DeviceID=\'' + d + '\'" get FreeSpace,Size /value 2>nul', { encoding: 'utf8', timeout: 5000 });
      const freeMatch = result.match(/FreeSpace=(\d+)/);
      const sizeMatch = result.match(/Size=(\d+)/);
      if (freeMatch && sizeMatch) {
        const freeGB = Math.round(parseInt(freeMatch[1]) / 1024 / 1024 / 1024);
        const totalGB = Math.round(parseInt(sizeMatch[1]) / 1024 / 1024 / 1024);
        console.log('DISK ' + d + ': ' + freeGB + 'GB free / ' + totalGB + 'GB total');
      }
    });
  } catch(e) {
    console.log('DISK: check failed - ' + e.message);
  }
}
