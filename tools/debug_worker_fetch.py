import requests, re
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
url = "https://resume.io/app/resumes"
print('GET', url)
r = requests.get(url, headers={"User-Agent": UA})
print('status', r.status_code)
html = r.text
m = re.search(r'/assets/js/builder-[^"\']+\.js', html)
if m:
    print('builder match:', m.group())
else:
    print('no builder match; sample html prefix:')
    print(html[:2000])
