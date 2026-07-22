const fs = require('fs');
try {
  const s = fs.readFileSync('resume_24253312.json','utf8');
  JSON.parse(s);
  console.log('valid');
} catch (e) {
  console.error(e.message);
  process.exit(1);
}