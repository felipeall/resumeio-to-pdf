import asyncio
import subprocess
import sys
import os
from pathlib import Path

PORT = 8787
ROOT = Path(__file__).resolve().parent.parent / 'app' / 'renderer' / '.worker_cache'


async def run():
    proc = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT)], cwd=str(ROOT))
    try:
        # install pyppeteer if missing
        try:
            import pyppeteer
        except Exception:
            print('installing pyppeteer...')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyppeteer'])

        from pyppeteer import launch

        def find_local_chrome():
            from shutil import which
            candidates = []
            program_files = [
                Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')),
                Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')),
                Path(os.environ.get('LOCALAPPDATA', 'C:\\Users\\Default\\AppData\\Local')),
            ]
            for base in program_files:
                candidates += [
                    base / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
                    base / 'Microsoft' / 'Edge' / 'Application' / 'msedge.exe',
                ]
            for name in ('chrome', 'chrome.exe', 'msedge', 'msedge.exe'):
                p = which(name)
                if p:
                    candidates.append(Path(p))
            for p in candidates:
                try:
                    if p and p.exists():
                        return str(p)
                except Exception:
                    continue
            return None

        exe = find_local_chrome()
        launch_kwargs = {'headless': True, 'args': ['--no-sandbox']}
        if exe:
            launch_kwargs['executablePath'] = exe
            print('using local browser at', exe)

        browser = await launch(**launch_kwargs)
        page = await browser.newPage()
        url = f'http://localhost:{PORT}/preview.html'
        print('opening', url)
        await page.goto(url, {'waitUntil': 'networkidle0'})

        # wait until title changes to READY or ERROR
        for _ in range(60):
            title = await page.title()
            if title in ('READY', 'ERROR'):
                break
            await asyncio.sleep(0.5)
        title = await page.title()
        if title == 'READY':
            # try to read base64 PDF exposed by the preview page
            try:
                b64 = await page.evaluate('window.__PDF_BASE64__')
                if b64:
                    print('base64 length', len(b64))
                    # also read reported byte length from page
                    try:
                        reported = await page.evaluate('window.__PDF_BYTES__')
                    except Exception:
                        reported = None
                    print('reported bytes from page', reported)
                    data = b64.encode('ascii')
                    import base64
                    out = Path('resume_24253312_puppeteer_direct.pdf')
                    out.write_bytes(base64.b64decode(data))
                    print('wrote', out)
                else:
                    out = Path('resume_24253312_puppeteer.pdf')
                    await page.pdf({'path': str(out), 'printBackground': True, 'format': 'A4'})
                    print('wrote', out)
            except Exception:
                out = Path('resume_24253312_puppeteer.pdf')
                await page.pdf({'path': str(out), 'printBackground': True, 'format': 'A4'})
                print('wrote', out)
        else:
            content = await page.content()
            print('failed, page title', title)
            print(content[:1000])

        await browser.close()
    finally:
        proc.terminate()


if __name__ == '__main__':
    asyncio.run(run())
