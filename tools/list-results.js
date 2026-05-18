const fs = require('fs');
const p = 'C:\\Users\\wifik\\Desktop\\projects\\larger-lab\\quant-lab\\results';
const f = fs.readdirSync(p).filter(x => x.includes('20260517'));
f.forEach(x => {
  const s = fs.statSync(p + '\\' + x);
  console.log(x, Math.round(s.size/1024) + 'KB', s.mtime.toISOString());
});
