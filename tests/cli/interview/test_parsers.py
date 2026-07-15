"""Tests for the interview document-parser registry."""

from pathlib import Path

import pytest

from resume_roast.cli.interview.parsers import PARSERS, parser_for
from resume_roast.utils.extraction.errors import UnreadableDocumentError


class TestParserFor:
    def test_pdf(self) -> None:
        result = parser_for("resume.pdf")
        assert result is PARSERS[".pdf"]

    def test_docx(self) -> None:
        result = parser_for("resume.docx")
        assert result is PARSERS[".docx"]

    def test_path_object(self) -> None:
        result = parser_for(Path("resume.pdf"))
        assert result is PARSERS[".pdf"]

    def test_uppercase_extension(self) -> None:
        result = parser_for("resume.PDF")
        assert result is PARSERS[".pdf"]

    def test_unsupported(self) -> None:
        with pytest.raises(UnreadableDocumentError):
            parser_for("resume.txt")

    def test_no_extension(self) -> None:
        with pytest.raises(UnreadableDocumentError):
            parser_for("resume")
