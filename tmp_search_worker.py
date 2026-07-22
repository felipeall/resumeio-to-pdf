from pathlib import Path
import re
text = Path('app/renderer/.worker_cache/rendering.js').read_text(encoding='utf8', errors='ignore')
patterns = [r'\bresume\b', r'document', r'onmessage', r'taskId:\s*"render"', r'document\.resume', r'worker\.postMessage', r'function \(e\)', r'parse\(.*document']
for pat in patterns:
    print('PATTERN', pat)
    regex = re.compile(pat)
    for i, line in enumerate(text.splitlines(),1):
        if regex.search(line):
            print(i, line.strip())
            if i > 200:
                break
    print('---')
