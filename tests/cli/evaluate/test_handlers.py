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


@pytest.fixture(autouse=True)
def _isolated_storage_dir(  # pyright: ignore[reportUnusedFunction]
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.setattr("resume_roast.cli.evaluate.handlers.storage_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "sample.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 80), "Jane Doe", fontsize=20)
        page.insert_text((72, 120), "Roasted resumes at Acme Corp", fontsize=11)
        doc.save(path)
    return path


def test_evaluate_prints_system_and_user_prompt(sample_pdf: Path) -> None:
    result = runner.invoke(app, ["evaluate", str(sample_pdf)])

    assert result.exit_code == 0
    assert "=== system ===" in result.output
    assert "=== user ===" in result.output
    # Default settings select the recruiter persona and intern level.
    assert "## Persona: Recruiter" in result.output
    assert "Internship candidate" in result.output


def test_evaluate_embeds_resume_and_statistics_in_user_prompt(sample_pdf: Path) -> None:
    result = runner.invoke(app, ["evaluate", str(sample_pdf)])

    assert result.exit_code == 0
    user_section = result.output.split("=== user ===")[1]
    assert "<resume>" in user_section
    assert "Jane Doe" in user_section
    assert "- Pages: 1" in user_section


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
