"""Tests for shared document-format extraction helpers."""

import pytest

from resume_roast.utils.extraction._helpers import none_when_blank


@pytest.mark.parametrize("value", [None, "", "   ", "\n", "\t  \n"])
def test_none_when_blank_returns_none_for_blank_values(value: str | None) -> None:
    assert none_when_blank(value) is None


@pytest.mark.parametrize("value", ["hello", "  hello  ", "a"])
def test_none_when_blank_passes_real_strings_through_unstripped(value: str) -> None:
    """Padding is preserved: the helper decides blankness, it does not normalize."""
    assert none_when_blank(value) == value
