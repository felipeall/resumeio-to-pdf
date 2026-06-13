import sys, json
from pathlib import Path
# Ensure repo root is on sys.path so `app` package imports correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.resumeio import ResumeioDownloader

p = Path('resume_24253312.json')
raw = json.loads(p.read_text(encoding='utf8'))
rt = raw.get('renderingToken') or (raw.get('resume') or {}).get('renderingToken')
if not rt:
    print('no renderingToken found')
    raise SystemExit(1)

print('using rendering token', rt)

d = ResumeioDownloader(rendering_token=rt)
pdf = d.generate_pdf()
Path('resume_24253312_downloader.pdf').write_bytes(pdf)
print('wrote resume_24253312_downloader.pdf')
