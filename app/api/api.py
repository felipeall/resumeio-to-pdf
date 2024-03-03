import re

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.resumeio import ResumeioDownloader

api_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@api_router.get("/download", response_class=HTMLResponse)
def download_resume(resume: str, image_size: int = 3000, extension: str = "jpg"):
    """
    Download a resume from resume.io and return it as a PDF.

    Parameters
    ----------
    resume : str
        ID or URL of the resume to download.
    image_size : int, optional
        Size of the images to download, by default 3000.
    extension : str, optional
        Image extension to download, by default "jpg".

    Returns
    -------
    fastapi.responses.Response
        A PDF representation of the resume with appropriate headers for inline display.
    """
    resume_id = parse_resume_id(resume)
    resumeio = ResumeioDownloader(resume_id=resume_id, image_size=image_size, extension=extension)
    buffer = resumeio.generate_pdf()
    return Response(
        buffer, headers={"Content-Disposition": f'inline; filename="{resume_id}.pdf"'}, media_type="application/pdf",
    )


@api_router.get("/", response_class=HTMLResponse, include_in_schema=False)
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


def parse_resume_id(resume_input: str) -> str:
    """
    Parse a resume.io ID or URL.

    Parameters
    ----------
    resume_input : str
        ID or URL of the resume to parse.

    Returns
    -------
    str
        The resume ID.

    """
    match = re.search(r"^(.+resume\.io/r/)?(?P<id>[a-zA-Z0-9]+)$", resume_input)
    if not match:
        raise HTTPException(status_code=400, detail=f"Invalid resumeio.io ID or URL: {resume_input}")

    return match.groupdict().get("id")
