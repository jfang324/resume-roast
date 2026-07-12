"""Tests for `resume-roast evaluate`."""

# The fixture drives PyMuPDF's partially annotated document-building API.
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false

from pathlib import Path

import pymupdf
import pytest
from typer.testing import CliRunner

from resume_roast.cli.registry import build_subcommand_registry

app = build_subcommand_registry()
runner = CliRunner()

_LINK_URI = "https://github.com/janedoe"


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "sample.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 80), "Jane Doe", fontsize=20)
        page.insert_text((72, 120), "Roasted resumes at Acme Corp", fontsize=11)
        page.insert_link(
            {
                "kind": pymupdf.LINK_URI,
                "from": pymupdf.Rect(72, 200, 200, 215),
                "uri": _LINK_URI,
            }
        )
        doc.save(path)
    return path


def test_evaluate_prints_markdown_and_metadata(sample_pdf: Path) -> None:
    result = runner.invoke(app, ["evaluate", str(sample_pdf)])

    assert result.exit_code == 0
    assert "Jane Doe" in result.output
    assert "Roasted resumes at Acme Corp" in result.output
    assert "Pages: 1" in result.output
    assert f"Links: {_LINK_URI}" in result.output
    assert "Creator: (not set)" in result.output
    assert "words" in result.output


def test_evaluate_reports_unreadable_file(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"this is not a pdf")

    result = runner.invoke(app, ["evaluate", str(path)])

    assert result.exit_code == 1
    assert "Error" in result.output
    assert "Traceback" not in result.output


def test_evaluate_reports_missing_file(tmp_path: Path) -> None:
    result = runner.invoke(app, ["evaluate", str(tmp_path / "missing.pdf")])

    assert result.exit_code == 1
    assert "Error" in result.output
