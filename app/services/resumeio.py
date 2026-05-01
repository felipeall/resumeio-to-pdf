import io
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests
from fastapi import HTTPException
from PIL import Image as PilImage
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link

from app.schemas.resumeio import Extension


@dataclass
class ResumeioDownloader:
    """
    Class to download a resume from resume.io and convert it to a PDF.

    Parameters
    ----------
    rendering_token : str
        Rendering Token of the resume to download.
    extension : Extension, optional
        Image extension to download, by default "jpeg".
    image_size : int, optional
        Size of the images to download, by default 2000.
    """

    rendering_token: str
    extension: Extension = Extension.jpeg
    image_size: int = 2000
    METADATA_URL: str = "https://ssr.resume.tools/meta/{rendering_token}?cache={cache_date}"
    IMAGES_URL: str = (
        "https://ssr.resume.tools/to-image/{rendering_token}-{page_id}.{extension}"
        "?cache={cache_date}&size={image_size}"
    )

    cache_date: str = field(init=False)
    metadata: list = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        """Set the cache date to the current time."""
        self.cache_date = datetime.now(timezone.utc).isoformat()[:-10] + "Z"

    def generate_pdf(self) -> bytes:
        """
        Generate a PDF from the resume.io resume.

        Returns
        -------
        bytes
            PDF representation of the resume.
        """
        self.__get_resume_metadata()

        if not self.metadata:
            raise HTTPException(status_code=502, detail="No pages found in resume metadata.")

        images = self.__download_images()
        pdf = PdfWriter()

        for i, image_bytes in enumerate(images):
            page_meta = self.metadata[i]
            viewport = page_meta.get("viewport") or {}
            metadata_w = viewport.get("width", 800)
            metadata_h = viewport.get("height", 1131)

            # Convert image to PDF page using Pillow (no extra dependencies)
            image_bytes.seek(0)
            try:
                pil_buf = io.BytesIO()
                PilImage.open(image_bytes).convert("RGB").save(pil_buf, format="PDF", resolution=150)
                page_pdf_bytes = pil_buf.getvalue()
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Failed to convert page {i + 1} image to PDF: {exc}")

            page = PdfReader(io.BytesIO(page_pdf_bytes)).pages[0]
            page_w = float(page.mediabox.width)
            page_h = float(page.mediabox.height)
            pdf.add_page(page)

            # Scale link coords from metadata viewport → PDF point dimensions
            scale_x = page_w / metadata_w
            scale_y = page_h / metadata_h

            for link in page_meta.get("links") or []:
                link_url = link.get("url")
                if not link_url:
                    continue

                x = link.get("left", link.get("x", 0)) * scale_x
                raw_y = link.get("top", link.get("y", 0))
                h = link.get("height", 0) * scale_y
                w = link.get("width", 0) * scale_x
                # Resume.io uses top-left origin; PDF uses bottom-left — flip y axis
                y = page_h - (raw_y * scale_y) - h

                link_annotation = Link(rect=(x, y, x + w, y + h), url=link_url)
                pdf.add_annotation(page_number=i, annotation=link_annotation)

        with io.BytesIO() as file:
            pdf.write(file)
            return file.getvalue()

    def __get_resume_metadata(self) -> None:
        """Download the metadata for the resume."""
        url = self.METADATA_URL.format(
            rendering_token=self.rendering_token,
            cache_date=self.cache_date,
        )
        response = self.__get(url)
        content: dict = json.loads(response.text)

        # Handle both {"pages": [...]} and a bare list response
        pages = content.get("pages")
        if not pages and isinstance(content, list):
            pages = content

        self.metadata = pages or []

    def __download_images(self) -> list[io.BytesIO]:
        """Download the images for all pages of the resume.

        Returns
        -------
        list[io.BytesIO]
            List of image byte streams, one per page.
        """
        images = []
        for page_id in range(1, len(self.metadata) + 1):
            image_url = self.IMAGES_URL.format(
                rendering_token=self.rendering_token,
                page_id=page_id,
                extension=self.extension.value,
                cache_date=self.cache_date,
                image_size=self.image_size,
            )
            response = self.__get(image_url)
            images.append(io.BytesIO(response.content))

        return images

    def __get(self, url: str) -> requests.Response:
        """Perform a GET request with a browser-like User-Agent.

        Parameters
        ----------
        url : str
            URL to fetch.

        Returns
        -------
        requests.Response
            Successful response object.

        Raises
        ------
        HTTPException
            If the response status code is not 200.
        """
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/136.0.0.0 Safari/537.36"
                ),
            },
            timeout=30,
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Unable to download resume (rendering token: {self.rendering_token}, url: {url})",
            )
        return response