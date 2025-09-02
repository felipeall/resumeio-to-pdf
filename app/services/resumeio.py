import io
import json
from dataclasses import dataclass
from datetime import datetime

import pytesseract
import requests
from fastapi import HTTPException
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import AnnotationBuilder

from app.schemas.resumeio import Extension


@dataclass
class ResumeioDownloader:
    """
    Class to download a resume from resume.io and convert it to a PDF.

    Parameters
    ----------
    rendering_token : str
        Rendering Token of the resume to download.
    extension : str, optional
        Image extension to download, by default "jpeg".
    image_size : int, optional
        Size of the images to download, by default 3000.
    """

    rendering_token: str
    extension: Extension = Extension.jpeg
    image_size: int = 3000
    METADATA_URL: str = "https://ssr.resume.tools/meta/{rendering_token}?cache={cache_date}"
    IMAGES_URL: str = (
        "https://ssr.resume.tools/to-image/{rendering_token}-{page_id}.{extension}?cache={cache_date}&size={image_size}"
    )

    # Fixed datetime compatibility
    def __post_init__(self) -> None:
        self.cache_date = datetime.utcnow().isoformat()[:-3] + "Z"
        print(f"DEBUG: Generated cache date: {self.cache_date}")

    def generate_pdf(self) -> bytes:
        """
        Generate a PDF from the resume.io resume.

        Returns
        -------
        bytes
            PDF representation of the resume.
        """
        self.__get_resume_metadata()
        images = self.__download_images()
        pdf = PdfWriter()
        metadata_w, metadata_h = self.metadata[0].get("viewport").values()

        for i, image in enumerate(images):
            page_pdf = pytesseract.image_to_pdf_or_hocr(Image.open(image), extension="pdf", config="--dpi 300")
            page = PdfReader(io.BytesIO(page_pdf)).pages[0]
            page_scale = max(page.mediabox.height / metadata_h, page.mediabox.width / metadata_w)
            pdf.add_page(page)

            for link in self.metadata[i].get("links"):
                link_url = link.pop("url")
                link.update((k, v * page_scale) for k, v in link.items())
                x, y, w, h = link.values()

                annotation = AnnotationBuilder.link(rect=(x, y, x + w, y + h), url=link_url)
                pdf.add_annotation(page_number=i, annotation=annotation)

        with io.BytesIO() as file:
            pdf.write(file)
            return file.getvalue()

    def __get_resume_metadata(self) -> None:
        """Download the metadata for the resume."""
        response = self.__get(
            self.METADATA_URL.format(rendering_token=self.rendering_token, cache_date=self.cache_date),
        )
        content: dict[str, list] = json.loads(response.text)
        self.metadata = content.get("pages")

    # Fixed enum value usage in URL construction
    def __download_images(self) -> list[io.BytesIO]:
        """Download the images for the resume.

        Returns
        -------
        list[io.BytesIO]
            List of image files.
        """
        images = []
        for page_id in range(1, 1 + len(self.metadata)):
            image_url = self.IMAGES_URL.format(
                rendering_token=self.rendering_token,
                page_id=page_id,
                extension=self.extension.value,  # Use .value instead of enum instance
                cache_date=self.cache_date,
                image_size=self.image_size,
            )
            response = self.__get(image_url)
            images.append(io.BytesIO(response.content))

        return images

    # Added debugging for troubleshooting
    def __get(self, url: str) -> requests.Response:
        """Get a response from a URL.

        Parameters
        ----------
        url : str
            URL to get.

        Returns
        -------
        requests.Response
            Response object.

        Raises
        ------
        HTTPException
            If the response status code is not 200.
        """
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36",
            },
        )
        if response.status_code != 200:
            print(f"DEBUG: URL: {url}")
            print(f"DEBUG: Status Code: {response.status_code}")
            print(f"DEBUG: Response Text: {response.text[:500]}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Unable to download resume (rendering token: {self.rendering_token})",
            )
        return response
