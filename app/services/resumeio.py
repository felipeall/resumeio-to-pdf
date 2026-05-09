import io
from dataclasses import dataclass
from datetime import datetime, timezone

import pytesseract
import requests
from fastapi import HTTPException
from PIL import Image

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
    IMAGE_URL: str = (
        "https://ssr.resume.tools/to-image/{rendering_token}-1.{extension}?cache={cache_date}&size={image_size}"
    )

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
        image = self.__download_image()
        page_pdf = pytesseract.image_to_pdf_or_hocr(Image.open(image), extension="pdf", config="--dpi 300")
        return page_pdf

    def __download_image(self) -> io.BytesIO:
        """Download the first page image of the resume.

        Returns
        -------
        io.BytesIO
            Image file.
        """
        image_url = self.IMAGE_URL.format(
            rendering_token=self.rendering_token,
            extension=self.extension.value,
            cache_date=self.cache_date,
            image_size=self.image_size,
        )
        response = self.__get(image_url)
        return io.BytesIO(response.content)

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
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Unable to download resume (rendering token: {self.rendering_token})",
            )
        return response
