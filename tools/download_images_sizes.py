import requests
from pathlib import Path
import json
p = Path('resume_24253312.json')
j = json.loads(p.read_text(encoding='utf8'))
rt = j.get('renderingToken') or (j.get('resume') or {}).get('renderingToken')
from datetime import datetime, timezone
cache_date = datetime.now(timezone.utc).isoformat()[:-10] + 'Z'
for size in (1000,2000,3000,4000,6000,8000):
    url = f"https://ssr.resume.tools/to-image/{rt}-2.jpeg?cache={cache_date}&size={size}"
    try:
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
        print('size',size,'status',r.status_code,'ct',r.headers.get('Content-Type'),'len',len(r.content))
    except Exception as e:
        print('error',e)
