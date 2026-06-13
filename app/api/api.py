import json
from typing import Annotated

from fastapi import APIRouter, Form, Path, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.resumeio import ResumeioDownloader, ResumeioRenderer

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/download")
def download_resume(document: Annotated[str, Form()]):
    """Download a resume from a document JSON payload and return it as a PDF."""
    document_dict = json.loads(document)
    rendering_token = document_dict.get("renderingToken", "resume")
    renderer = ResumeioRenderer(document=document_dict)
    return Response(
        renderer.generate_pdf(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{rendering_token}.pdf"'},
    )


@router.post("/download/{rendering_token}")
def download_resume_by_token(
    rendering_token: Annotated[str, Path(min_length=24, max_length=24, pattern="^[a-zA-Z0-9]{24}$")],
    image_size: Annotated[int, Query(gt=0, le=2000)] = 2000,
    extension: Annotated[str, Query()] = "jpeg",
):
    """Download a resume from a rendering token and return it as a PDF."""
    resumeio = ResumeioDownloader(
        rendering_token=rendering_token,
        image_size=image_size,
        extension=extension,
    )
    return Response(
        resumeio.generate_pdf(),
        headers={"Content-Disposition": f'inline; filename="{rendering_token}.pdf"'},
    )


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    """Render the main index page."""
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request},
    )
