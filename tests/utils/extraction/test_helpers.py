"""Tests for shared document-format extraction helpers."""

from resume_roast.utils.extraction._helpers import none_when_blank


def testnone_when_blank_returns_none_for_none() -> None:
    assert none_when_blank(None) is None


def testnone_when_blank_returns_none_for_empty_string() -> None:
    assert none_when_blank("") is None


def testnone_when_blank_returns_none_for_whitespace() -> None:
    assert none_when_blank("   ") is None
    assert none_when_blank("\n") is None
    assert none_when_blank("\t  \n") is None


def testnone_when_blank_passes_through_real_strings() -> None:
    assert none_when_blank("hello") == "hello"
    assert none_when_blank("  hello  ") == "  hello  "
    assert none_when_blank("a") == "a"
