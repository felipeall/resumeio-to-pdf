import re
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from resumeio_to_pdf.services.errors import RenderError
from resumeio_to_pdf.services.renderer import ResumeioRenderer

UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]")

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parents[1] / "templates")


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
    try:
        pdf = renderer.generate_pdf()
    except RenderError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{pdf_filename(document)}.pdf"'},
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
