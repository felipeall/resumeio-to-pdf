import re
from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.schemas.resumeio import Extension
from app.services.renderer import ResumeioRenderer
from app.services.resumeio import ResumeioDownloader

UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]")

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/render")
def render_resume(
    document: Annotated[dict, Body()],
    locale: Annotated[str, Query(pattern="^[a-z]{2}(-[a-zA-Z]{2})?$")] = "en",
):
    """
    Render every page of a resume.io document and return it as a PDF.

    Parameters
    ----------
    document : dict
        Resume document as served by https://resume.io/api/app/resumes/{id}.
    locale : str, optional
        Locale used to pick the renderer configuration, by default "en".

    Returns
    -------
    fastapi.responses.Response
        A PDF representation of the resume with appropriate headers for inline display.
    """
    renderer = ResumeioRenderer(document=document, locale=locale)
    name = pdf_filename(document)
    return Response(
        renderer.generate_pdf(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{name}.pdf"'},
    )


@router.post("/download/{rendering_token}")
def download_resume(
    rendering_token: Annotated[str, Path(min_length=24, max_length=24, pattern="^[a-zA-Z0-9]{24}$")],
    image_size: Annotated[int, Query(gt=0, le=2000)] = 2000,
    extension: Annotated[Extension, Query()] = Extension.jpeg,
):
    """
    Download a resume from resume.io and return it as a PDF.

    Parameters
    ----------
    rendering_token : str
        Rendering Token of the resume to download.
    image_size : int, optional
        Size of the images to download, by default 3000.
    extension : Extension, optional
        Image extension to download, by default "jpeg".

    Returns
    -------
    fastapi.responses.Response
        A PDF representation of the resume with appropriate headers for inline display.
    """
    resumeio = ResumeioDownloader(rendering_token=rendering_token, image_size=image_size, extension=extension)
    return Response(
        resumeio.generate_pdf(),
        headers={"Content-Disposition": f'inline; filename="{rendering_token}.pdf"'},
    )


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
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
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request},
    )


def pdf_filename(document: dict) -> str:
    """
    Build a filename that is safe to put in a Content-Disposition header.

    Parameters
    ----------
    document : dict
        Resume document, whose identifiers are supplied by the client.

    Returns
    -------
    str
        File name without an extension, stripped of quotes, separators and control characters.
    """
    name = str(document.get("renderingToken") or document.get("id") or "")
    return UNSAFE_FILENAME.sub("_", name) or "resume"
