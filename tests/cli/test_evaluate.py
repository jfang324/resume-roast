"""Tests for the `evaluate` command."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from resume_roast.cli import cli
from tests.conftest import two_column_placements

PdfFactory = Callable[..., Path]

runner = CliRunner()


def test_evaluate_renders_node_tree(canonical_resume_pdf: Path) -> None:
    result = runner.invoke(cli, ["evaluate", str(canonical_resume_pdf)])

    assert result.exit_code == 0
    assert result.stdout == (
        "n1 [document] resume.pdf — 1 page(s), 2 section(s)\n"
        "  n2 [section] Jordan Diaz (p1)\n"
        "    n3 [entry] (untitled)\n"
        "      n4 [paragraph] jordan@example.com | 555-0100 (p1)\n"
        "  n5 [section] EXPERIENCE (p1)\n"
        "    n6 [entry] Software Engineer - Acme Corp (p1)\n"
        "      n7 [bullet] Shipped the roasting pipeline (p1)\n"
        "      n8 [bullet] Cut parse latency by 40% (p1)\n"
    )


def _missing_pdf(make_pdf: PdfFactory, tmp_path: Path) -> tuple[Path, str]:  # noqa: ARG001
    return tmp_path / "missing.pdf", "missing.pdf"


def _two_column_pdf(make_pdf: PdfFactory, tmp_path: Path) -> tuple[Path, str]:  # noqa: ARG001
    return make_pdf(two_column_placements()), "page 1"


def _docx_path(make_pdf: PdfFactory, tmp_path: Path) -> tuple[Path, str]:  # noqa: ARG001
    path = tmp_path / "resume.docx"
    path.write_bytes(b"whatever")
    return path, ".docx"


@pytest.mark.parametrize(
    "build",
    [_missing_pdf, _two_column_pdf, _docx_path],
    ids=["missing-file", "two-column-layout", "unsupported-extension"],
)
def test_evaluate_reports_error_for_unreadable_file(
    make_pdf: PdfFactory,
    tmp_path: Path,
    build: Callable[[PdfFactory, Path], tuple[Path, str]],
) -> None:
    path, expected_fragment = build(make_pdf, tmp_path)

    result = runner.invoke(cli, ["evaluate", str(path)])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("Error: ")
    assert result.stderr.count("\n") == 1
    assert expected_fragment in result.stderr


def test_root_help_lists_evaluate() -> None:
    result = runner.invoke(cli, [])

    assert "Parse a resume" in result.stdout
