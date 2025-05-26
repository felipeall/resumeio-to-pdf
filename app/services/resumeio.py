import io
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import pytesseract
import requests
from fastapi import HTTPException
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import AnnotationBuilder

from app.schemas.resumeio import Extension

# Configure Tesseract path for Windows
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'D:\Git\Tes\tesseract.exe'

# Test Tesseract installation
try:
    version = pytesseract.get_tesseract_version()
    print(f"Tesseract version: {version}")
except Exception as e:
    print(f"Tesseract test failed: {e}")

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


    def __post_init__(self) -> None:
        """Set the cache date to the current time."""
        # Fix deprecated datetime.utcnow()
        self.cache_date = datetime.now(timezone.utc).isoformat()[:-4] + "Z"

    def generate_pdf(self) -> bytes:
        """
        Generate a PDF from the resume.io resume.

        Returns
        -------
        bytes
            PDF representation of the resume.
        """
        try:
            self.__get_resume_metadata()
            images = self.__download_images()
            pdf = PdfWriter()
            
            if not self.metadata:
                raise HTTPException(status_code=404, detail="No metadata found for resume")
            
            metadata_w, metadata_h = self.metadata[0].get("viewport", {}).get("width", 800), self.metadata[0].get("viewport", {}).get("height", 1200)

            for i, image in enumerate(images):
                page_pdf = pytesseract.image_to_pdf_or_hocr(Image.open(image), extension="pdf", config="--dpi 300")
                page = PdfReader(io.BytesIO(page_pdf)).pages[0]
                page_scale = max(page.mediabox.height / metadata_h, page.mediabox.width / metadata_w)
                pdf.add_page(page)

                # Add error handling for links
                if i < len(self.metadata) and self.metadata[i].get("links"):
                    for link in self.metadata[i].get("links", []):
                        try:
                            link_url = link.pop("url")
                            link.update((k, v * page_scale) for k, v in link.items())
                            x, y, w, h = link.values()

                            annotation = AnnotationBuilder.link(rect=(x, y, x + w, y + h), url=link_url)
                            pdf.add_annotation(page_number=i, annotation=annotation)
                        except (KeyError, ValueError) as e:
                            print(f"Warning: Could not process link on page {i}: {e}")
                            continue

            with io.BytesIO() as file:
                pdf.write(file)
                return file.getvalue()
        except Exception as e:
            print(f"Error generating PDF: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

    def __get_resume_metadata(self) -> None:
        """Download the metadata for the resume."""
        try:
            response = self.__get(
                self.METADATA_URL.format(rendering_token=self.rendering_token, cache_date=self.cache_date),
            )
            content: dict[str, list] = json.loads(response.text)
            self.metadata = content.get("pages", [])
            
            if not self.metadata:
                raise HTTPException(status_code=404, detail="No pages found in resume metadata")
                
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Invalid JSON response from metadata endpoint: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get resume metadata: {e}")

    def __download_images(self) -> list[io.BytesIO]:
        """Download the images for the resume.

        Returns
        -------
        list[io.BytesIO]
            List of image files.
        """
        images = []
        for page_id in range(1, 1 + len(self.metadata)):
            try:
                image_url = self.IMAGES_URL.format(
                    rendering_token=self.rendering_token,
                    page_id=page_id,
                    extension=self.extension.value,  # Use .value to get string
                    cache_date=self.cache_date,
                    image_size=self.image_size,
                )
                print(f"Downloading image: {image_url}")  # Debug logging
                response = self.__get(image_url)
                images.append(io.BytesIO(response.content))
            except Exception as e:
                print(f"Failed to download image for page {page_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to download image for page {page_id}")

        return images

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
        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/136.0.0.0 Safari/537.36",
                },
                timeout=30,  # Add timeout
            )
            
            print(f"Request to {url} returned status: {response.status_code}")  # Debug logging
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Unable to download resume (rendering token: {self.rendering_token}). "
                    f"Server returned: {response.status_code} - {response.text[:200]}"
                )
            return response
            
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=408, detail="Request timeout while downloading resume")
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="Connection error while downloading resume")
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")