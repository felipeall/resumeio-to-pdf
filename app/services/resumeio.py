import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime

import requests
from fastapi import HTTPException
from fpdf import FPDF


@dataclass
class ResumeioDownloader:
    resume_id: str

    extension: str = "png"
    image_size: int = 1800
    cache_date: str = datetime.utcnow().isoformat()[:-4] + "Z"

    metadata: list = field(default_factory=lambda: [])
    images_urls: list = field(default_factory=lambda: [])

    IMAGE_URL: str = "https://ssr.resume.tools/to-image/ssid-{0}-{1}.{2}?cache={3}&size={4}"
    METADATA_URL: str = "https://ssr.resume.tools/meta/ssid-{0}?cache={1}"

    def __post_init__(self):
        pattern_id = re.compile(r"^[a-zA-Z0-9]{9}$")
        pattern_url = re.compile(r"(?<=resume.io/r/)([a-zA-Z0-9]){9}")

        if pattern_id.search(self.resume_id):
            pass

        elif pattern_url.search(self.resume_id):
            self.resume_id = pattern_url.search(self.resume_id).group(0)

        else:
            raise HTTPException(status_code=400, detail=f"Invalid resume id: {self.resume_id}")

    def run(self) -> bytearray:
        logging.info("")
        logging.info("Execution Parameters")
        logging.info("------------------------------------")
        logging.info(f"Resume ID: {self.resume_id}")
        logging.info(f"Images Extension: {self.extension}")
        logging.info(f"Images Size: {self.image_size}")
        logging.info(f"Date Cache: {self.cache_date}")
        logging.info("------------------------------------")
        logging.info("")

        logging.info("Resume Metadata")
        logging.info("------------------------------------")
        logging.info("Getting resume metadata...")
        self._get_resume_metadata()
        logging.info(self.metadata)
        logging.info("------------------------------------")
        logging.info("")

        logging.info("Resume Images")
        logging.info("------------------------------------")
        logging.info("Parsing resume images...")
        self._format_images_urls()
        logging.info(self.images_urls)
        logging.info("------------------------------------")
        logging.info("")

        logging.info("Resume PDF")
        logging.info("------------------------------------")
        logging.info("Generating pdf file...")
        self._generate_pdf()
        logging.info(f"PDF buffer loaded!")
        logging.info("------------------------------------")
        logging.info("")

        return self.buffer

    def _get_resume_metadata(self):
        request = requests.get(self.METADATA_URL.format(self.resume_id, self.cache_date))
        metadata = json.loads(request.text)
        metadata = metadata.get("pages")
        self.metadata = metadata

    def _format_images_urls(self):
        for page_id in range(1, 1 + len(self.metadata)):
            download_url = self.IMAGE_URL.format(
                self.resume_id,
                page_id,
                self.extension,
                self.cache_date,
                self.image_size,
            )
            self.images_urls.append(download_url)

    def _generate_pdf(self):
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
