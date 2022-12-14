import argparse
import json
import logging
import re
from datetime import datetime

import requests
from fpdf import FPDF


class ResumeioDownloader:
    IMAGE_URL: str = (
        "https://ssr.resume.tools/to-image/ssid-{0}-{1}.{2}?cache={3}&size={4}"
    )
    METADATA_URL: str = "https://ssr.resume.tools/meta/ssid-{0}?cache={1}"

    def __init__(self, resume_id: str) -> None:
        self.resume_id: str = resume_id
        self.extension: str = "png"
        self.image_size: int = 1800
        self.cache_date: str = datetime.utcnow().isoformat()[:-4] + "Z"

    def run(self) -> None:
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
        metadata = self._get_resume_metadata()
        logging.info(metadata)
        logging.info("------------------------------------")
        logging.info("")

        logging.info("Resume Images")
        logging.info("------------------------------------")
        logging.info("Parsing resume images...")
        images_urls = self._format_images_urls(metadata)
        logging.info(images_urls)
        logging.info("------------------------------------")
        logging.info("")

        logging.info("Resume PDF")
        logging.info("------------------------------------")
        logging.info("Generating pdf file...")
        pdf_file_name = self._generate_pdf(metadata, images_urls)
        logging.info(f"PDF file saved as: {pdf_file_name}")
        logging.info("------------------------------------")
        logging.info("")

    def _get_resume_metadata(self) -> list[dict]:
        request = requests.get(
            self.METADATA_URL.format(self.resume_id, self.cache_date)
        )
        metadata = json.loads(request.text)
        metadata = metadata.get("pages")

        return metadata

    def _format_images_urls(self, metadata: list[dict]) -> list[str]:
        images_urls = []

        for page_id in range(1, 1 + len(metadata)):
            download_url = self.IMAGE_URL.format(
                self.resume_id,
                page_id,
                self.extension,
                self.cache_date,
                self.image_size,
            )
            images_urls.append(download_url)

        return images_urls

    def _generate_pdf(self, metadata: list[dict], images_urls: list[str]) -> str:
        pdf_file_name = f"{self.resume_id}.pdf"
        w, h = metadata[0].get("viewport").values()

        pdf = FPDF(format=(w, h))
        pdf.set_auto_page_break(0)

        for i, image_url in enumerate(images_urls):
            pdf.add_page()
            pdf.image(image_url, w=w, h=h, type=self.extension)

            for link in metadata[i].get("links"):
                x = link["left"]
                y = h - link["top"]

                pdf.link(x=x, y=y, w=link["width"], h=link["height"], link=link["url"])

        pdf.output(name=pdf_file_name, dest="F")

        return pdf_file_name


class ResumeioParser(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None) -> None:
        pattern_id = re.compile(r"^[a-zA-Z0-9]{9}$")
        pattern_url = re.compile(r"(?<=resume.io/r/)([a-zA-Z0-9]){9}")

        if pattern_id.search(values):
            setattr(namespace, self.dest, values)

        elif pattern_url.search(values):
            setattr(namespace, self.dest, pattern_url.search(values).group(0))

        else:
            parser.error(f"`{values}` is an invalid Resume ID format!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("resume_id", nargs="?", action=ResumeioParser)
    parser.add_argument("-q", "--quiet", action="store_true", help="enable quiet mode")
    args = parser.parse_args()
    resume_id = args.resume_id
    quiet = args.quiet

    if not quiet:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    logging.info("Starting execution...")
    resumeio_downloader = ResumeioDownloader(resume_id)
    resumeio_downloader.run()
    logging.info("Finished execution!")


if __name__ == "__main__":
    main()
