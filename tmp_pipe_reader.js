let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  console.log('INPUT_HEAD', input.slice(0, 200));
  try {
    const obj = JSON.parse(input);
    console.log('DOCUMENT_KEYS', Object.keys(obj.document));
    console.log('HAS_RESUME', Object.prototype.hasOwnProperty.call(obj.document, 'resume'));
  } catch (err) {
    console.error('PARSE_ERROR', err.message);
    console.error(input.slice(0, 200));
    process.exit(1);
  }
});
