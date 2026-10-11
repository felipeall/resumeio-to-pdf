import uvicorn
from fastapi import FastAPI

from resumeio_to_pdf.api.api import router

app = FastAPI(title="Resume.io to PDF")
app.include_router(router)


if __name__ == "__main__":
    """Instantiate the application webserver"""
    uvicorn.run("resumeio_to_pdf.main:app", host="0.0.0.0", port=8000)
