from typing import Annotated

from fastapi import APIRouter, Path, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.schemas.resumeio import Extension
from app.services.resumeio import ResumeioDownloader

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/download/{rendering_token}")
def download_resume(
    rendering_token: Annotated[str, Path(min_length=24, max_length=24, pattern="^[a-zA-Z0-9]{24}$")],
    image_size: Annotated[int, Query(gt=0)] = 3000,
    extension: Annotated[Extension, Query(...)] = Extension.jpeg,
):
    """
    Download a resume from resume.io and return it as a PDF.

    Parameters
    ----------
    rendering_token : str
        Rendering Token of the resume to download.
    image_size : int, optional
        Size of the images to download, by default 3000.
    extension : str, optional
        Image extension to download, by default "jpg".

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
    return templates.TemplateResponse("index.html", {"request": request})
