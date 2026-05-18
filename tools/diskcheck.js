const { execSync } = require('child_process');
try {
  const r = execSync('powershell -NoProfile -Command "Get-PSDrive -PSProvider FileSystem | ForEach-Object { $_.Name + \": \" + [math]::Round($_.Used/1GB,1) + \"GB used / \" + [math]::Round($_.Free/1GB,1) + \"GB free\" }"', { encoding: 'utf8', timeout: 5000 });
  console.log(r.trim());
} catch(e) { console.log('DISK: ' + e.message); }
