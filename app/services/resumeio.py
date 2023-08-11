import json
import re
from dataclasses import dataclass, field
from datetime import datetime

import requests
from fastapi import HTTPException
from fpdf import FPDF


@dataclass
class ResumeioDownloader:
    """
    A utility class to download and generate PDF from resume.io URLs.

    Parameters
    ----------
    resume_id : str
        ID or URL of the resume to download.
    extension : str, optional
        The format of images. Default is 'png'.
    image_size : int, optional
        The size of the images. Default is 1800.
    cache_date : str
        The timestamp of the cache. Default is the current UTC time.
    images_urls : list
        List to store formatted image URLs. Default is an empty list.
    """

    resume_id: str

    extension: str = "png"
    image_size: int = 1800
    cache_date: str = datetime.utcnow().isoformat()[:-4] + "Z"

    images_urls: list = field(default_factory=lambda: [])

    IMAGE_URL: str = (
        "https://ssr.resume.tools/to-image/ssid-{resume_id}-{page_id}.{extension}?cache={cache_date}&size={image_size}"
    )
    METADATA_URL: str = "https://ssr.resume.tools/meta/ssid-{resume_id}?cache={cache_date}"

    def __post_init__(self) -> None:
        """Post initialization to validate and format resume_id."""
        pattern_id = re.compile(r"^[a-zA-Z0-9]{9}$")
        pattern_url = re.compile(r"(?<=resume.io/r/)([a-zA-Z0-9]){9}")

        if pattern_id.search(self.resume_id):
            pass

        elif pattern_url.search(self.resume_id):
            self.resume_id = pattern_url.search(self.resume_id).group(0)

        else:
            raise HTTPException(status_code=400, detail=f"Invalid resume id: {self.resume_id}")

    def run(self) -> bytearray:
        """
        Main method to download and generate PDF from resume.io.

        Returns
        -------
        bytearray
            The generated PDF content.
        """
        self._get_resume_metadata()
        self._format_images_urls()
        self._generate_pdf()

        return self.buffer

    def _get_resume_metadata(self) -> None:
        """Fetch and store metadata of the resume."""
        request = requests.get(self.METADATA_URL.format(resume_id=self.resume_id, cache_date=self.cache_date))
        metadata = json.loads(request.text)
        metadata = metadata.get("pages")
        self.metadata = metadata

    def _format_images_urls(self) -> None:
        """Format and store image download URLs for each page of the resume."""
        for page_id in range(1, 1 + len(self.metadata)):
            download_url = self.IMAGE_URL.format(
                resume_id=self.resume_id,
                page_id=page_id,
                extension=self.extension,
                cache_date=self.cache_date,
                image_size=self.image_size,
            )
            self.images_urls.append(download_url)

    def _generate_pdf(self) -> None:
        """Generate a PDF using the FPDF library from fetched images and metadata."""
        w, h = self.metadata[0].get("viewport").values()

        pdf = FPDF(format=(w, h))
        pdf.set_auto_page_break(0)

        for i, image_url in enumerate(self.images_urls):
            pdf.add_page()
            pdf.image(image_url, w=w, h=h, type=self.extension)

            for link in self.metadata[i].get("links"):
                x = link["left"]
                y = h - link["top"]

                pdf.link(x=x, y=y, w=link["width"], h=link["height"], link=link["url"])

        self.buffer = pdf.output(dest="S")
