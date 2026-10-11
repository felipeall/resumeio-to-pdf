import argparse
import json
import sys
from pathlib import Path

from resumeio_to_pdf.api.api import pdf_filename
from resumeio_to_pdf.services.errors import RenderError
from resumeio_to_pdf.services.renderer import ResumeioRenderer

REPOSITORY_URL = "https://github.com/felipeall/resumeio-to-pdf"
BUY_ME_A_COFFEE_URL = "https://www.buymeacoffee.com/felipeall"


def main(argv: list[str] | None = None) -> int:
    """Entry point of the `resumeio-to-pdf` command.

    Parameters
    ----------
    argv : list[str], optional
        Command line arguments, by default sys.argv[1:].

    Returns
    -------
    int
        Process exit code.
    """
    parser = argparse.ArgumentParser(prog="resumeio-to-pdf", description="Render a resume.io resume as a PDF.")
    commands = parser.add_subparsers(dest="command", required=True)

    render = commands.add_parser("render", help="render a resume JSON file into a multi-page PDF")
    render.add_argument("document", help="resume JSON from https://resume.io/api/app/resumes/{id}, or - for stdin")
    render.add_argument("-o", "--output", help="PDF path, by default <renderingToken>.pdf in the current folder")
    render.add_argument("--locale", help="renderer locale, by default the resume's own locale or en")

    serve = commands.add_parser("serve", help="start the web UI on this machine")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)
    if args.command == "serve":
        import uvicorn

        uvicorn.run("resumeio_to_pdf.main:app", host=args.host, port=args.port)
        return 0
    return _render(args)


def _render(args: argparse.Namespace) -> int:
    try:
        source = sys.stdin.read() if args.document == "-" else Path(args.document).read_text(encoding="utf-8")
        document = json.loads(source)
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: cannot read the resume JSON: {error}", file=sys.stderr)
        return 2
    if not isinstance(document, dict):
        print("error: expected a single resume object, not a list", file=sys.stderr)
        return 2

    locale = args.locale or document.get("locale") or "en"
    try:
        pdf = ResumeioRenderer(document=document, locale=locale).generate_pdf()
    except RenderError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    output = Path(args.output or f"{pdf_filename(document)}.pdf")
    output.write_bytes(pdf)
    print(
        f"Your resume is ready: {output.resolve()}\n"
        "\n"
        "If this tool helped you, please consider:\n"
        f"  - Starring the repository: {REPOSITORY_URL}\n"
        f"  - Buying me a coffee:       {BUY_ME_A_COFFEE_URL}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
