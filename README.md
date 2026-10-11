# Resume.io to PDF

Turn your [resume.io](https://resume.io) resume into a multi-page PDF on your own machine.

It renders every page with resume.io's own rendering worker, the same one the resume.io editor runs in your
browser, so the PDF keeps the original layout and selectable, vector text.

> **Note:** there is no hosted version anymore. The tool runs only locally, so your resume never leaves your
> computer except to talk to resume.io itself.

### Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Node.js](https://nodejs.org/) 18 or newer on the `PATH` (the rendering worker runs there)

### 1. Install

```bash
uv tool install git+https://github.com/felipeall/resumeio-to-pdf
```

This puts the `resumeio-to-pdf` command on your `PATH`. Upgrade it later with
`uv tool upgrade resumeio-to-pdf` and remove it with `uv tool uninstall resumeio-to-pdf`.

### 2. Get your resume JSON

1. Log in to [resume.io](https://resume.io).
2. Open https://resume.io/api/app/resumes in the same browser and note the `id` of the resume you want.
3. Open `https://resume.io/api/app/resumes/{id}` and save the page as `resume.json`.

The rendering token alone is no longer enough: resume.io's image endpoint only ever serves the first page.

### 3. Render it

From the command line:

```bash
resumeio-to-pdf render resume.json
```

This writes `<renderingToken>.pdf` to the current folder. Use `-o my-resume.pdf` to pick the file name,
`--locale` to override the resume's language, and `-` instead of a path to read the JSON from stdin.

Or with the web UI on http://127.0.0.1:8000:

```bash
resumeio-to-pdf serve
```

Or with Docker, which bundles Node.js:

```bash
git clone https://github.com/felipeall/resumeio-to-pdf.git
cd resumeio-to-pdf
docker build -t resumeio-to-pdf .
docker run -p 127.0.0.1:8000:8000 resumeio-to-pdf
```

On the first render the worker and its chunks (~3.8 MB) are downloaded from resume.io into
`~/.cache/resumeio-to-pdf`, or into `$RESUMEIO_WORKER_CACHE` when set. Nothing from resume.io is stored in this
repository.

### Development

```bash
uv sync
uv run pytest
uv run ruff check .
```

### Disclaimer

Please be advised that this application is designed for preview purposes only. 

By utilizing this tool, you explicitly agree to adhere to all applicable laws and regulations governing the use of such services. 
The creators of this application absolve themselves of any responsibility for potential damages or harm resulting from its utilization.

It is essential to visit the pricing page on Resume.io to explore fair and affordable options for accessing the resume downloading service directly through the official channels provided by Resume.io. 
The creators emphasize the importance of supporting the platform by subscribing to their services and discourage the use of this application as a substitute for legitimate and paid access.
