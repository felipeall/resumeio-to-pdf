import json
import time

import pytest

from resumeio_to_pdf import updates

COMMIT = "d06cfdbdae1d9251592d9aa70154cfffddaeda62"


class FakeDistribution:
    def __init__(self, direct_url):
        self.direct_url = direct_url

    def read_text(self, filename):
        assert filename == "direct_url.json"
        return self.direct_url


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.delenv(updates.OPT_OUT_VARIABLE, raising=False)
    monkeypatch.setattr(updates, "STATE_FILE", tmp_path / "update-check.json")


def install_from(monkeypatch, direct_url):
    payload = None if direct_url is None else json.dumps(direct_url)
    monkeypatch.setattr(updates, "distribution", lambda name: FakeDistribution(payload))


def github_install(monkeypatch, url="https://github.com/felipeall/resumeio-to-pdf"):
    install_from(monkeypatch, {"url": url, "vcs_info": {"vcs": "git", "commit_id": COMMIT}})


def behind_by(monkeypatch, value):
    calls = []

    def fetch(repository, commit):
        calls.append((repository, commit))
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(updates, "_fetch_behind_by", fetch)
    return calls


@pytest.mark.parametrize(
    "url",
    ["https://github.com/felipeall/resumeio-to-pdf", "https://github.com/felipeall/resumeio-to-pdf.git"],
)
def test_installed_commit_reads_repository_and_commit(monkeypatch, url):
    github_install(monkeypatch, url)
    assert updates.installed_commit() == ("felipeall/resumeio-to-pdf", COMMIT)


@pytest.mark.parametrize(
    "direct_url",
    [
        None,
        {"url": "file:///home/me/resumeio-to-pdf", "dir_info": {"editable": True}},
        {"url": "https://gitlab.com/someone/resumeio-to-pdf", "vcs_info": {"vcs": "git", "commit_id": COMMIT}},
    ],
)
def test_installs_not_from_github_are_skipped(monkeypatch, direct_url):
    install_from(monkeypatch, direct_url)
    calls = behind_by(monkeypatch, 3)
    assert updates.update_notice() is None
    assert calls == []


def test_notice_when_behind(monkeypatch):
    github_install(monkeypatch)
    calls = behind_by(monkeypatch, 3)
    notice = updates.update_notice()
    assert "(3 updates)" in notice
    assert updates.UPGRADE_COMMAND in notice
    assert calls == [("felipeall/resumeio-to-pdf", COMMIT)]


def test_no_notice_when_up_to_date(monkeypatch):
    github_install(monkeypatch)
    behind_by(monkeypatch, 0)
    assert updates.update_notice() is None


def test_result_is_cached_for_a_day(monkeypatch):
    github_install(monkeypatch)
    calls = behind_by(monkeypatch, 1)
    assert "(1 update)" in updates.update_notice()
    assert "(1 update)" in updates.update_notice()
    assert len(calls) == 1


def test_stale_cache_is_refreshed(monkeypatch):
    github_install(monkeypatch)
    updates.STATE_FILE.write_text(
        json.dumps({"commit": COMMIT, "behind_by": 5, "checked_at": time.time() - updates.CHECK_INTERVAL_SECONDS - 1}),
    )
    calls = behind_by(monkeypatch, 0)
    assert updates.update_notice() is None
    assert len(calls) == 1


def test_cache_of_another_commit_is_ignored(monkeypatch):
    github_install(monkeypatch)
    updates.STATE_FILE.write_text(json.dumps({"commit": "0" * 40, "behind_by": 5, "checked_at": time.time()}))
    calls = behind_by(monkeypatch, 0)
    assert updates.update_notice() is None
    assert len(calls) == 1


def test_failures_are_silent(monkeypatch):
    github_install(monkeypatch)
    behind_by(monkeypatch, OSError("offline"))
    assert updates.update_notice() is None


def test_opt_out(monkeypatch):
    github_install(monkeypatch)
    calls = behind_by(monkeypatch, 3)
    monkeypatch.setenv(updates.OPT_OUT_VARIABLE, "1")
    assert updates.update_notice() is None
    assert calls == []
