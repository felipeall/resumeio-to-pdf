const fs = require('fs');
const path = require('path');
const inPath = path.join(__dirname, 'resume_24253312.json');
const outDir = 'E:/dev';
const outPath = path.join(outDir, 'stdin');
const d = fs.readFileSync(inPath, 'utf8');
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(outPath, '{"document":' + d + ',"config":{}}', 'utf8');
console.log('wrote', outPath);