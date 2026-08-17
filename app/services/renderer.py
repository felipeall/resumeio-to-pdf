import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException

from app.services.assets import RESUMEIO_ORIGIN, ensure_bundle, fetch_renderer_config

RENDER_SCRIPT = Path(__file__).parents[1] / "renderer" / "render.mjs"
NODE_BINARY = os.getenv("RESUMEIO_NODE_BINARY", "node")
RENDER_TIMEOUT_SECONDS = 120
ERROR_LINE = re.compile(r"^[A-Za-z]*Error(\[[^\]]+\])?: ")


@dataclass
class ResumeioRenderer:
    """Render a resume.io document into a PDF with resume.io's own rendering worker.

    Parameters
    ----------
    document : dict
        Resume document as served by https://resume.io/api/app/resumes/{id}.
    locale : str, optional
        Locale used to pick the renderer configuration, by default "en".
    """

    document: dict
    locale: str = "en"

    def generate_pdf(self) -> bytes:
        """Render every page of the resume into a single PDF.

        Returns
        -------
        bytes
            PDF representation of the resume.

        Raises
        ------
        HTTPException
            If the renderer is unavailable or fails to produce a PDF.
        """
        bundle = ensure_bundle()
        payload = json.dumps(
            {
                "document": self.document,
                "config": fetch_renderer_config(self.locale),
                "assetsDir": str(bundle.directory),
                "entry": bundle.entry,
                "host": RESUMEIO_ORIGIN,
            },
        )

        try:
            process = subprocess.run(
                [NODE_BINARY, str(RENDER_SCRIPT)],
                input=payload.encode(),
                capture_output=True,
                timeout=RENDER_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=500, detail=f"Node.js is required to render resumes: {error}") from error
        except subprocess.TimeoutExpired as error:
            raise HTTPException(status_code=504, detail="Rendering the resume timed out") from error

        if process.returncode != 0 or not process.stdout.startswith(b"%PDF"):
            raise HTTPException(status_code=502, detail=f"Unable to render the resume: {_last_error(process.stderr)}")

        return process.stdout


def _last_error(stderr: bytes) -> str:
    lines = [line.strip() for line in stderr.decode("utf-8", "replace").splitlines() if line.strip()]
    thrown = [line for line in lines if ERROR_LINE.match(line)]
    if thrown:
        return thrown[0]
    return lines[0] if lines else "the renderer produced no output"
