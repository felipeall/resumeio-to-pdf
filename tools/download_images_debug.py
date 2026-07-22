import requests, sys
from pathlib import Path

p = Path('resume_24253312.json')
if not p.exists():
    print('resume_24253312.json not found', file=sys.stderr); sys.exit(1)
raw = p.read_text(encoding='utf8')
import json
j = json.loads(raw)
rt = j.get('renderingToken') or (j.get('resume') or {}).get('renderingToken')
if not rt:
    print('no rendering token', file=sys.stderr); sys.exit(1)

BASE = 'https://ssr.resume.tools/to-image/{rendering_token}-{page}.{extension}?cache={cache_date}&size={image_size}'
from datetime import datetime, timezone
cache_date = datetime.now(timezone.utc).isoformat()[:-10] + 'Z'

outdir = Path('tmp_images')
outdir.mkdir(exist_ok=True)

for ext in ('jpeg','png','webp'):
    print('\nTrying extension', ext)
    for page in range(1,7):
        url = BASE.format(rendering_token=rt,page=page,extension=ext,cache_date=cache_date,image_size=2000)
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        except Exception as e:
            print('page',page,'err',e)
            continue
        cl = len(r.content)
        ct = r.headers.get('Content-Type','')
        print('page',page,'status',r.status_code,'ct',ct,'len',cl)
        if r.status_code==200 and cl>20000 and 'image' in ct:
            fn = outdir / f'page_{page}.{ext}'
            fn.write_bytes(r.content)
            print('saved',fn)

print('\nDone')
