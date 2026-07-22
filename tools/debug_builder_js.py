import requests, re
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
base = "https://resume.io"
url = base + "/app/resumes"
r = requests.get(url, headers={"User-Agent": UA}, timeout=10)
html = r.text
m = re.search(r'/assets/js/builder-[^"\']+\.js', html)
print('builder:', m.group() if m else 'not found')
if not m:
    exit(1)
builder_url = base + m.group()
print('GET', builder_url)
b = requests.get(builder_url, headers={"User-Agent": UA}, timeout=10)
print('status', b.status_code)
js = b.text
cid = re.search(r'\{(\d+):"rendering-core"', js)
print('core id match:', cid.group(1) if cid else 'not found')
if cid:
    ch = re.search(rf'\{{{cid.group(1)}:"([a-f0-9]+)"', js)
    print('core hash match:', ch.group(1) if ch else 'not found')
print('\n--- occurrences of rendering-core in builder js ---\n')
for m in re.finditer(r'([0-9]+):"rendering-core"', js):
    i = m.start()
    print('match at', i, js[max(0, i-80): i+80])

print('\n--- builder js snippet ---\n')
print(js[:2000])
