const fs = require('fs');
const readStdIn = async () => {
  if (!process.stdin.isTTY) {
    let data = '';
    for await (const chunk of process.stdin) {
      data += chunk;
    }
    return data;
  } else if (fs.existsSync('/dev/stdin')) {
    return fs.readFileSync('/dev/stdin', 'utf8');
  }
  let data = '';
  for await (const chunk of process.stdin) {
    data += chunk;
  }
  return data;
};
(async () => {
  const input = await readStdIn();
  console.log('INPUT_LEN', input.length);
  try {
    const payload = JSON.parse(input);
    console.log('PAYLOAD_KEYS', Object.keys(payload));
    console.log('DOC_KEYS', Object.keys(payload.document));
    console.log('HEAD', JSON.stringify(payload).slice(0,200));
  } catch (err) {
    console.error('PARSE_ERR', err.message);
    console.error(input.slice(0,200));
  }
})();
