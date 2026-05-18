const os = require('os');
const freemem = Math.round(os.freemem() / 1024 / 1024);
const totalmem = Math.round(os.totalmem() / 1024 / 1024);
const usedmem = totalmem - freemem;
const mempct = Math.round((usedmem / totalmem) * 100);
console.log('RAM: ' + usedmem + 'GB / ' + totalmem + 'GB (' + mempct + '% used, ' + freemem + 'GB free)');
console.log('CPUs: ' + os.cpus().length + ' cores');
console.log('Uptime: ' + Math.round(os.uptime() / 3600) + ' hours');
