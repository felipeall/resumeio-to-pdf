import requests
from pathlib import Path
hash='4a4a6aee1b6a50afb962'
candidates = [
    f'https://resume.io/assets/vendors.{hash}.js',
    f'https://resume.io/assets/workers/vendors.{hash}.js',
    f'https://resume.io/assets/workers/vendors.{hash}.js',
]
out = Path('app/renderer/.worker_cache/vendors.'+hash+'.js')
for u in candidates:
    try:
        r = requests.get(u, headers={'User-Agent':'curl/7.79.1'}, timeout=10)
        print('try', u, r.status_code)
        if r.status_code == 200:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(r.content)
            print('saved', out)
            break
    except Exception as e:
        print('error', u, e)
else:
    print('none succeeded')
