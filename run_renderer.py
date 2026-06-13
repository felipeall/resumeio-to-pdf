import json
import sys
from pathlib import Path

from app.services.resumeio import ResumeioRenderer
import inspect

try:
    p = Path('resume_24253312.json')
    if not p.exists():
        print('resume_24253312.json not found', file=sys.stderr)
        sys.exit(1)
    raw = json.loads(p.read_text(encoding='utf8'))
    # The renderer expects a document object that contains a top-level `resume` key,
    # but also expects keys like `locale` and `type` at the document level.
    if isinstance(raw, dict) and "resume" in raw:
        doc = raw
    else:
        doc = {"resume": raw}
        for k in ("locale", "type", "templateConfig"):
            if k in raw:
                doc[k] = raw[k]
    print('document top-level keys:', list(doc.keys()))
    print('ResumeioRenderer loaded from:', inspect.getsourcefile(ResumeioRenderer))
    renderer = ResumeioRenderer(doc)
    pdf = renderer.generate_pdf()
    out = Path('resume_24253312.pdf')
    out.write_bytes(pdf)
    print('wrote', out.resolve())
except Exception as e:
    print('error:', e, file=sys.stderr)
    sys.exit(1)
