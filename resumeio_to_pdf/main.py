from fastapi import FastAPI

from resumeio_to_pdf.api.api import router

app = FastAPI(title="Resume.io to PDF")
app.include_router(router)
