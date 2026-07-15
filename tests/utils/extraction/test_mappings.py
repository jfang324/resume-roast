"""Tests for the suffix-to-parser registry."""

from pathlib import Path

import pytest

from resume_roast.utils.extraction.errors import UnreadableDocumentError
from resume_roast.utils.extraction.mappings import PARSERS, get_parser


class TestGetParser:
    def test_pdf(self) -> None:
        result = get_parser("resume.pdf")
        assert result is PARSERS[".pdf"]

    def test_docx(self) -> None:
        result = get_parser("resume.docx")
        assert result is PARSERS[".docx"]

    def test_path_object(self) -> None:
        result = get_parser(Path("resume.pdf"))
        assert result is PARSERS[".pdf"]

    def test_uppercase_extension(self) -> None:
        result = get_parser("resume.PDF")
        assert result is PARSERS[".pdf"]

    def test_unsupported(self) -> None:
        with pytest.raises(UnreadableDocumentError):
            get_parser("resume.txt")

    def test_no_extension(self) -> None:
        with pytest.raises(UnreadableDocumentError):
            get_parser("resume")
