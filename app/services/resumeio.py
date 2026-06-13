import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import requests
from fastapi import HTTPException
from PIL import Image

logger = logging.getLogger(__name__)

RESUMEIO_BASE = "https://resume.io"
WORKER_CACHE_DIR = Path(__file__).parent.parent / "renderer" / ".worker_cache"
RENDER_SCRIPT = Path(__file__).parent.parent / "renderer" / "render.mjs"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)


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
        Size of the images to download, by default 2000.
    """

    rendering_token: str
    extension: str = "jpeg"
    image_size: int = 2000
    max_pages: int = 5
    request_timeout: float = 15.0
    IMAGE_URL: str = (
        "https://ssr.resume.tools/to-image/{rendering_token}-{page}.{extension}?cache={cache_date}&size={image_size}"
    )

    def __post_init__(self) -> None:
        """Set the cache date to the current time."""
        self.cache_date = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()[:-10] + "Z"

    def generate_pdf(self) -> bytes:
        """
        Generate a PDF from the resume.io resume.

        Returns
        -------
        bytes
            PDF representation of the resume.
        """
        images = self.__download_images()
        if not images:
            raise HTTPException(status_code=500, detail="Unable to download any resume pages.")

        output = __import__("io").BytesIO()
        first_image, *other_images = images
        first_image.save(
            output,
            format="PDF",
            resolution=300,
            save_all=bool(other_images),
            append_images=other_images,
        )
        output.seek(0)
        return output.read()

    def __download_images(self) -> list[Image.Image]:
        """Download all available resume page images."""
        images = []
        page = 1

        while page <= self.max_pages:
            image_url = self.IMAGE_URL.format(
                rendering_token=self.rendering_token,
                page=page,
                extension=self.extension,
                cache_date=self.cache_date,
                image_size=self.image_size,
            )
            try:
                response = requests.get(
                    image_url,
                    headers={
                        "User-Agent": USER_AGENT,
                    },
                    timeout=self.request_timeout,
                )
            except requests.exceptions.RequestException as exc:
                raise HTTPException(
                    status_code=504,
                    detail=(
                        f"Timeout or network error while downloading resume page {page} "
                        f"(rendering token: {self.rendering_token}): {exc}"
                    ),
                ) from exc

            if response.status_code != 200:
                if page == 1:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Unable to download resume (rendering token: {self.rendering_token})",
                    )
                break

            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            expected_type = f"image/{self.extension}"
            if page > 1 and (content_type != expected_type or len(response.content) < 20000):
                break

            image = Image.open(__import__("io").BytesIO(response.content)).convert("RGB")
            images.append(image)
            page += 1

        return images


@dataclass
class ResumeioRenderer:
    """Render a resume.io document JSON as a multi-page PDF.

    Uses resume.io's own rendering Web Worker (run via Node.js) to produce
    a pixel-perfect PDF from the resume document JSON and renderer config.

    Parameters
    ----------
    document : dict
        The full resume document JSON from resume.io.
    """

    document: dict

    def generate_pdf(self) -> bytes:
        """Generate a PDF from the resume document."""
        locale = self.document.get("locale", "en")
        config = self._get_renderer_config(locale)
        self._ensure_worker_assets()
        return self._render(self.document, config)

    def _get_renderer_config(self, locale: str) -> dict:
        """Fetch the renderer configuration for the given locale."""
        response = requests.get(
            f"{RESUMEIO_BASE}/api/app/general/renderer-config/{locale}",
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch renderer config")
        return response.json()

    def _ensure_worker_assets(self) -> None:
        """Download and cache the rendering Web Worker and its vendor chunks."""
        if (WORKER_CACHE_DIR / "rendering.js").exists():
            return

        logger.info("Downloading Web Worker assets from resume.io...")
        WORKER_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        html = self._get_public(f"{RESUMEIO_BASE}/app/resumes")
        builder_match = re.search(r'/assets/js/builder-[^"\']+\.js', html)
        if not builder_match:
            raise HTTPException(status_code=502, detail="Could not find builder JS on resume.io")
        builder_url = f"{RESUMEIO_BASE}{builder_match.group()}"

        builder_js = self._get_public(builder_url)
        core_id_match = re.search(r'([0-9]+):"rendering-core"', builder_js)
        if not core_id_match:
            raise HTTPException(status_code=502, detail="Could not find rendering-core chunk ID")
        core_id = core_id_match.group(1)

        hash_match = re.search(rf'{core_id}:"([a-f0-9]+)"', builder_js)
        if not hash_match:
            raise HTTPException(status_code=502, detail="Could not find rendering-core chunk hash")
        core_hash = hash_match.group(1)

        core_url = f"{RESUMEIO_BASE}/assets/chunk/rendering-core.{core_hash}.js"
        core_js = self._get_public(core_url)
        worker_match = re.search(r"workers/rendering\.[a-f0-9]+\.js", core_js)
        if not worker_match:
            raise HTTPException(status_code=502, detail="Could not find rendering worker URL")
        worker_filename = worker_match.group()

        worker_url = f"{RESUMEIO_BASE}/assets/{worker_filename}"
        self._download(worker_url, WORKER_CACHE_DIR / "rendering.js")
        worker_code = (WORKER_CACHE_DIR / "rendering.js").read_text(encoding="utf-8", errors="ignore")

        # Download any explicit worker chunk filenames referenced in the worker code
        for chunk_ref in re.findall(r"workers/\d+\.[a-f0-9]+\.js", worker_code):
            filename = chunk_ref.split("/")[-1]
            self._download(f"{RESUMEIO_BASE}/assets/{chunk_ref}", WORKER_CACHE_DIR / filename)

        # Parse and download vendor bundles referenced via the 'workers/vendors' mapping
        vendors_pos = worker_code.find('workers/vendors.')
        if vendors_pos != -1:
            # find the mapping object that follows (a {...}) and extract its contents
            brace_start = worker_code.find('{', vendors_pos)
            if brace_start != -1:
                depth = 0
                brace_end = None
                for i in range(brace_start, len(worker_code)):
                    if worker_code[i] == '{':
                        depth += 1
                    elif worker_code[i] == '}':
                        depth -= 1
                        if depth == 0:
                            brace_end = i
                            break
                if brace_end:
                    block = worker_code[brace_start: brace_end + 1]
                    for match in re.finditer(r'(\d+):"([a-f0-9]{8,})"', block):
                        vendor_hash = match.group(2)
                        filename = f"vendors.{vendor_hash}.js"
                        if not (WORKER_CACHE_DIR / filename).exists():
                            try:
                                self._download(
                                    f"{RESUMEIO_BASE}/assets/workers/{filename}",
                                    WORKER_CACHE_DIR / filename,
                                )
                            except HTTPException:
                                pass

    def _get_public(self, url: str) -> str:
        """Fetch a public URL and return the text content."""
        response = requests.get(url, headers={"User-Agent": USER_AGENT})
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Failed to fetch {url}")
        return response.text

    def _download(self, url: str, path: Path) -> None:
        """Download a file preserving raw bytes."""
        logger.info("Downloading %s", path.name)
        response = requests.get(url, headers={"User-Agent": USER_AGENT})
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Failed to fetch {url}")
        path.write_bytes(response.content)

    def _render(self, document: dict, config: dict) -> bytes:
        """Run the rendering Web Worker via Node.js and return the PDF bytes."""
        print('PY_DOC_KEYS:', list(document.keys()))
        # Ensure the worker always receives a document object with a top-level `resume` key
        if isinstance(document, dict) and "resume" in document:
            resume_obj = document["resume"]
        else:
            resume_obj = document

        doc_for_worker = {"resume": resume_obj}
        for k in ("locale", "type", "templateConfig"):
            if isinstance(document, dict) and k in document:
                doc_for_worker[k] = document[k]

        payload = json.dumps({
            "document": doc_for_worker,
            "config": config,
            "workerDir": str(WORKER_CACHE_DIR),
        })
        # Write payload for debugging
        try:
            (WORKER_CACHE_DIR / "payload_debug.json").write_text(payload, encoding="utf-8")
        except Exception:
            pass

        result = subprocess.run(
            ["node", str(RENDER_SCRIPT)],
            input=payload.encode(),
            capture_output=True,
            timeout=120,
        )

        if result.returncode != 0:
            error_msg = result.stderr.decode().strip()
            raise HTTPException(status_code=500, detail=f"Rendering failed: {error_msg}")

        return result.stdout
