# Resume.io to PDF

Download your resume from [resume.io](https://resume.io) as a PDF file. 

<div align="center"><a href="https://resumeio-to-pdf.fly.dev/"><img src="https://github.com/felipeall/resumeio-to-pdf/assets/20917430/b7edfda4-4768-4659-af68-561e1effe628" width="700" /></a></div>

Open the application, paste your resume JSON and click the download button. It renders every page with
resume.io's own rendering worker, so the PDF keeps selectable text instead of being an OCR'd image.

### How to find your resume JSON

Open https://resume.io/api/app/resumes while logged in, find the resume you want and note its `id`.
Then open `https://resume.io/api/app/resumes/{id}` and copy the whole payload.

### Downloading a single page instead

Entering a `renderingToken` still downloads the first page as an image, converts it to a PDF file and runs
OCR to extract the text. That path needs no login, but resume.io's image endpoint only ever renders page one
and caps the resolution at 2000px.

You will find the `renderingToken` in the same payload, and for cover letters under
https://resume.io/api/app/cover-letters/.

### How to run the application

Clone the repository
```bash
git clone https://github.com/felipeall/resumeio-to-pdf.git
```
    
Go to the project's root folder
```bash
cd resumeio-to-pdf
```

Build the image
```bash
docker build -t resumeio-to-pdf .
```

Run the container
```bash
docker run -p 8000:8000 resumeio-to-pdf
```

Open your browser and access http://localhost:8000

Running outside Docker additionally needs Node.js 18 or newer on the `PATH`, since the rendering worker
runs there. On the first render the worker and its chunks (~3.8 MB) are downloaded from resume.io into
`/tmp/resumeio-worker`, or into `$RESUMEIO_WORKER_CACHE` when set.

### Disclaimer

Please be advised that this application is designed for preview purposes only. 

By utilizing this tool, you explicitly agree to adhere to all applicable laws and regulations governing the use of such services. 
The creators of this application absolve themselves of any responsibility for potential damages or harm resulting from its utilization.

It is essential to visit the pricing page on Resume.io to explore fair and affordable options for accessing the resume downloading service directly through the official channels provided by Resume.io. 
The creators emphasize the importance of supporting the platform by subscribing to their services and discourage the use of this application as a substitute for legitimate and paid access.
