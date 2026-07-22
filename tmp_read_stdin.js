const fs = require('fs');
const input = fs.readFileSync('/dev/stdin', 'utf8');
console.log('INPUT_LENGTH', input.length);
console.log('HEAD', input.slice(0, 200));
try {
  const obj = JSON.parse(input);
  console.log('HAS_DOCUMENT', obj.hasOwnProperty('document'));
  console.log('DOC_KEYS', Object.keys(obj.document));
  console.log('DOC_HEAD', JSON.stringify(obj.document).slice(0,200));
} catch (e) {
  console.error('PARSE_ERR', e.message);
  process.exit(1);
}
