from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.resumeio import ResumeioDownloader

api_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@api_router.get("/download", response_class=HTMLResponse)
def download_resume(resume_id: str):
    """
    Download a resume from resume.io and return it as a PDF.

    Parameters
    ----------
    resume_id : str
        ID or URL of the resume to download.

    Returns
    -------
    fastapi.responses.Response
        A PDF representation of the resume with appropriate headers for inline display.
    """
    resumeio = ResumeioDownloader(resume_id=resume_id, image_size=3000, extension="jpg")
    buffer = resumeio.run()
    return Response(
        buffer, headers={"Content-Disposition": 'inline; filename="resume.pdf"'}, media_type="application/pdf"
    )


@api_router.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    Render the main index page.

    Parameters
    ----------
    request : fastapi.Request
        The request instance.

    Returns
    -------
    fastapi.templating.Jinja2Templates.TemplateResponse
        Rendered template of the main index page.
    """
    return templates.TemplateResponse("index.html", {"request": request})
