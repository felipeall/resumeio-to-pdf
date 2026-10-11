import json
import os
import re
import time
from importlib.metadata import PackageNotFoundError, distribution

import requests

from resumeio_to_pdf.services.assets import CACHE_DIR

PACKAGE = "resumeio-to-pdf"
GITHUB_REPOSITORY = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")
CHECK_INTERVAL_SECONDS = 24 * 3600
REQUEST_TIMEOUT_SECONDS = 2
STATE_FILE = CACHE_DIR / "update-check.json"
OPT_OUT_VARIABLE = "RESUMEIO_NO_UPDATE_CHECK"
UPGRADE_COMMAND = f"uv tool upgrade {PACKAGE}"


def update_notice() -> str | None:
    """Tell the user when a newer commit of the tool is on the default branch.

    Only installs made from a GitHub repository (e.g. `uv tool install git+https://github.com/...`) are
    checked, at most once a day. Any failure is swallowed, so the check never gets in the way of rendering.

    Returns
    -------
    str | None
        Notice to show the user, or None when the tool is up to date or the check was skipped.
    """
    if os.getenv(OPT_OUT_VARIABLE):
        return None
    try:
        installed = installed_commit()
        if installed is None:
            return None
        repository, commit = installed
        behind_by = _cached_behind_by(commit)
        if behind_by is None:
            behind_by = _fetch_behind_by(repository, commit)
            _save_state(commit, behind_by)
    except Exception:  # an update check must never break the command
        return None
    if not behind_by:
        return None
    noun = "update" if behind_by == 1 else "updates"
    return f"A newer version of {PACKAGE} is available ({behind_by} {noun}). Update with:\n  {UPGRADE_COMMAND}"


def installed_commit() -> tuple[str, str] | None:
    """Read the GitHub repository and commit this package was installed from.

    Returns
    -------
    tuple[str, str] | None
        The "owner/name" repository and the commit SHA, or None for installs that are not from GitHub.
    """
    try:
        direct_url = distribution(PACKAGE).read_text("direct_url.json")
    except PackageNotFoundError:
        return None
    if not direct_url:
        return None
    origin = json.loads(direct_url)
    commit = origin.get("vcs_info", {}).get("commit_id")
    repository = GITHUB_REPOSITORY.match(origin.get("url", ""))
    if not commit or not repository:
        return None
    return f"{repository.group(1)}/{repository.group(2)}", commit


def _cached_behind_by(commit: str) -> int | None:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if state.get("commit") != commit or time.time() - state.get("checked_at", 0) > CHECK_INTERVAL_SECONDS:
        return None
    return state.get("behind_by")


def _fetch_behind_by(repository: str, commit: str) -> int:
    response = requests.get(
        f"https://api.github.com/repos/{repository}/compare/{commit}...HEAD",
        params={"per_page": 1},
        headers={"Accept": "application/vnd.github+json"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return int(response.json()["ahead_by"])


def _save_state(commit: str, behind_by: int) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"commit": commit, "behind_by": behind_by, "checked_at": time.time()}))
