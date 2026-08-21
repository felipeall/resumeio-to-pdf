import os
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import requests
from fastapi import HTTPException

RESUMEIO_ORIGIN = "https://resume.io"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)
CACHE_DIR = Path(os.getenv("RESUMEIO_WORKER_CACHE", "/tmp/resumeio-worker"))
DISCOVERY_TTL_SECONDS = 3600

BUILDER_BUNDLE = re.compile(r"/assets/js/builder-[a-f0-9]+\.js")
CHUNK_NAMES = re.compile(r'(\d+):"([a-z-]+)"')
CHUNK_HASHES = re.compile(r'(\d+):"([a-f0-9]{16})"')
WORKER_FILE = re.compile(r'"workers/(rendering\.[a-f0-9]+\.js)"')
CHUNK_FILES = re.compile(r'"workers/([A-Za-z0-9_.-]+\.js)"')
VENDOR_HASHES = re.compile(r'"([a-f0-9]{20})"')

_discovered: tuple[float, str] | None = None


@dataclass
class WorkerBundle:
    """Location of the cached resume.io rendering worker.

    Parameters
    ----------
    directory : Path
        Directory holding the worker and every chunk it imports.
    entry : str
        File name of the worker itself.
    """

    directory: Path
    entry: str


def find_worker_name(rendering_core: str) -> str:
    """Read the worker file name out of the rendering-core chunk.

    Parameters
    ----------
    rendering_core : str
        Source of the rendering-core chunk, which names the worker.

    Returns
    -------
    str
        File name of the rendering worker.
    """
    match = WORKER_FILE.search(rendering_core)
    if not match:
        raise LookupError("rendering-core does not reference a worker")
    return match.group(1)


def find_rendering_core_url(builder_bundle: str) -> str:
    """Build the URL of the rendering-core chunk from the builder entry point.

    Parameters
    ----------
    builder_bundle : str
        Source of the builder entry point.

    Returns
    -------
    str
        Absolute URL of the rendering-core chunk.
    """
    names = dict(CHUNK_NAMES.findall(builder_bundle))
    hashes = dict(CHUNK_HASHES.findall(builder_bundle))
    chunk_ids = [chunk_id for chunk_id, name in names.items() if name == "rendering-core"]
    if not chunk_ids or chunk_ids[0] not in hashes:
        raise LookupError("builder bundle does not map a rendering-core chunk")
    return f"{RESUMEIO_ORIGIN}/assets/chunk/rendering-core.{hashes[chunk_ids[0]]}.js"


def find_chunk_names(worker: str) -> set[str]:
    """Collect every chunk the worker may import at runtime.

    Parameters
    ----------
    worker : str
        Source of the rendering worker.

    Returns
    -------
    set[str]
        File names of the named and vendor chunks.
    """
    names = set(CHUNK_FILES.findall(worker))
    marker = worker.find('"workers/vendors."')
    if marker != -1:
        table = worker[marker : marker + 6000]
        names |= {f"vendors.{chunk_hash}.js" for chunk_hash in VENDOR_HASHES.findall(table[: table.find("})")])}
    return names


def ensure_bundle() -> WorkerBundle:
    """Download the rendering worker and its chunks unless they are already cached.

    Returns
    -------
    WorkerBundle
        Cached worker ready to be executed by app/renderer/render.mjs.

    Raises
    ------
    HTTPException
        If resume.io does not serve the assets the worker is assembled from.
    """
    try:
        entry = _discover_worker_name()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        worker = _cache_asset(entry).read_text(encoding="utf-8")
        for name in find_chunk_names(worker):
            _cache_asset(name)
    except (LookupError, requests.RequestException) as error:
        raise HTTPException(status_code=502, detail=f"Unable to fetch the resume.io renderer: {error}") from error
    return WorkerBundle(directory=CACHE_DIR, entry=entry)


def fetch_renderer_config(locale: str) -> dict:
    """Fetch the renderer configuration the worker expects alongside a resume.

    Parameters
    ----------
    locale : str
        Locale of the resume, e.g. "en".

    Returns
    -------
    dict
        Renderer configuration.
    """
    try:
        response = _get(f"{RESUMEIO_ORIGIN}/api/app/general/renderer-config/{locale}")
        return response.json()
    except requests.RequestException as error:
        raise HTTPException(status_code=502, detail=f"Unable to fetch the renderer config: {error}") from error


def _discover_worker_name() -> str:
    global _discovered
    if _discovered and time.monotonic() - _discovered[0] < DISCOVERY_TTL_SECONDS:
        return _discovered[1]

    app_page = _get(f"{RESUMEIO_ORIGIN}/app/resumes").text
    bundle_path = BUILDER_BUNDLE.search(app_page)
    if not bundle_path:
        raise LookupError("resume.io does not serve a builder bundle")
    builder_bundle = _get(f"{RESUMEIO_ORIGIN}{bundle_path.group(0)}").text
    rendering_core = _get(find_rendering_core_url(builder_bundle)).text

    name = find_worker_name(rendering_core)
    _discovered = (time.monotonic(), name)
    return name


def _cache_asset(name: str) -> Path:
    path = CACHE_DIR / name
    if not path.exists():
        content = _get(f"{RESUMEIO_ORIGIN}/assets/workers/{name}").content
        with tempfile.NamedTemporaryFile(dir=CACHE_DIR, delete=False) as partial:
            partial.write(content)
        os.replace(partial.name, path)
    return path


def _get(url: str) -> requests.Response:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response
