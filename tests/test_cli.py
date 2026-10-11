import pytest

from resumeio_to_pdf import cli
from resumeio_to_pdf.services.errors import RenderError


@pytest.fixture(autouse=True)
def no_update_check(monkeypatch):
    monkeypatch.setattr(cli, "update_notice", lambda: None)


def test_render_writes_the_pdf_named_after_the_rendering_token(tmp_path, monkeypatch, capsys):
    document = tmp_path / "resume.json"
    document.write_text('{"renderingToken": "abc", "locale": "de"}')
    locales = []

    def generate_pdf(renderer):
        locales.append(renderer.locale)
        return b"%PDF-1.3"

    monkeypatch.setattr(cli.ResumeioRenderer, "generate_pdf", generate_pdf)
    monkeypatch.chdir(tmp_path)

    assert cli.main(["render", str(document)]) == 0
    assert (tmp_path / "abc.pdf").read_bytes() == b"%PDF-1.3"
    assert locales == ["de"]
    output = capsys.readouterr().out
    assert str(tmp_path / "abc.pdf") in output
    assert cli.REPOSITORY_URL in output
    assert cli.BUY_ME_A_COFFEE_URL in output


def test_render_reports_renderer_failures(tmp_path, monkeypatch, capsys):
    document = tmp_path / "resume.json"
    document.write_text("{}")

    def generate_pdf(renderer):
        raise RenderError("worker exploded")

    monkeypatch.setattr(cli.ResumeioRenderer, "generate_pdf", generate_pdf)

    assert cli.main(["render", str(document), "-o", str(tmp_path / "out.pdf")]) == 1
    assert "worker exploded" in capsys.readouterr().err
    assert not (tmp_path / "out.pdf").exists()


def test_render_rejects_invalid_json(tmp_path, capsys):
    document = tmp_path / "resume.json"
    document.write_text("not json")

    assert cli.main(["render", str(document)]) == 2
    assert "cannot read the resume JSON" in capsys.readouterr().err


def test_render_rejects_the_resume_list(tmp_path, capsys):
    document = tmp_path / "resumes.json"
    document.write_text("[]")

    assert cli.main(["render", str(document)]) == 2
    assert "single resume object" in capsys.readouterr().err


def test_render_prints_the_update_notice(tmp_path, monkeypatch, capsys):
    document = tmp_path / "resume.json"
    document.write_text("{}")
    monkeypatch.setattr(cli.ResumeioRenderer, "generate_pdf", lambda renderer: b"%PDF-1.3")
    monkeypatch.setattr(cli, "update_notice", lambda: "A newer version is available")

    assert cli.main(["render", str(document), "-o", str(tmp_path / "out.pdf")]) == 0
    assert "A newer version is available" in capsys.readouterr().err


def test_help_prints_the_update_notice(monkeypatch, capsys):
    monkeypatch.setattr(cli, "update_notice", lambda: "A newer version is available")

    with pytest.raises(SystemExit):
        cli.main(["--help"])
    assert "A newer version is available" in capsys.readouterr().err


def test_serve_prints_the_update_notice_once_before_starting(monkeypatch, capsys):
    import uvicorn

    events = []
    monkeypatch.setattr(cli, "update_notice", lambda: events.append("notice") or "A newer version is available")
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: events.append("server"))

    assert cli.main(["serve"]) == 0
    assert events == ["notice", "server"]
    assert capsys.readouterr().err.count("A newer version is available") == 1
