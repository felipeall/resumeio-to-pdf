from resumeio_to_pdf import cli
from resumeio_to_pdf.services.errors import RenderError


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
