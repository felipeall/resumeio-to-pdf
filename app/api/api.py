from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import ResumeioDownloader

api_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@api_router.get("/download", response_class=HTMLResponse)
def main(resume_id: str):
    resumeio = ResumeioDownloader(resume_id=resume_id, image_size=3000, extension="jpg")
    buffer = resumeio.run()
    return Response(buffer, headers={"Content-Disposition": 'inline; filename="out.pdf"'}, media_type="application/pdf")


@api_router.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
