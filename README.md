# Resume.io to PDF

Download your resume from [resume.io](https://resume.io) as a PDF file. 

<div align="center"><a href="https://resumeio-to-pdf.fly.dev/"><img src="https://github.com/felipeall/resumeio-to-pdf/assets/20917430/b7edfda4-4768-4659-af68-561e1effe628" width="700" /></a></div>

Open the application, paste your resume document JSON, and click the download button.
It uses resume.io's own rendering engine to generate a pixel-perfect, full multi-page PDF of your resume.

> **Note:** Due to recent changes in resume.io's rendering service, only the first page of the resume can be downloaded and the maximum image resolution is capped at 2000px.

### How to find your resume document JSON

1. Log in to https://resume.io
2. Open your browser's developer tools (F12)
3. Go to the Network tab
4. Navigate to your resume editor or visit https://resume.io/api/app/resumes
5. Find the API response for your resume (e.g., https://resume.io/api/app/resumes/{id})
6. Copy the full JSON response — this is your resume document JSON

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

### Disclaimer

Please be advised that this application is designed for preview purposes only. 

By utilizing this tool, you explicitly agree to adhere to all applicable laws and regulations governing the use of such services. 
The creators of this application absolve themselves of any responsibility for potential damages or harm resulting from its utilization.

It is essential to visit the pricing page on Resume.io to explore fair and affordable options for accessing the resume downloading service directly through the official channels provided by Resume.io. 
The creators emphasize the importance of supporting the platform by subscribing to their services and discourage the use of this application as a substitute for legitimate and paid access.
