const fs = require('fs');
const inputPath = process.argv[2] || '/dev/stdin';
let data;
try {
  data = fs.readFileSync(inputPath, 'utf8');
  console.log('READPATH', inputPath);
  console.log('LEN', data.length);
  console.log('HEAD', data.slice(0, 200));
  const parsed = JSON.parse(data);
  console.log('PARSED_KEYS', Object.keys(parsed));
  console.log('DOC_KEYS', Object.keys(parsed.document));
  console.log('DOC_STRING', JSON.stringify(parsed.document).slice(0,200));
} catch (e) {
  console.error('ERROR', e.stack || e.message);
  process.exit(1);
}
