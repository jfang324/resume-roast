"""Tests for shared CLI display helpers."""

from rich.text import Text

from resume_roast.cli.utils import RotatingSpinner, display_value


def test_display_value_joins_tuples() -> None:
    assert display_value(("a", "b")) == "a, b"
    assert display_value("a") == "a"


def test_rotating_spinner_changes_message_every_five_seconds() -> None:
    spin = RotatingSpinner("dots", [Text("first"), Text("second")], style="dim")

    assert "first" in str(spin.render(100.0))
    assert "first" in str(spin.render(104.9))
    assert "second" in str(spin.render(105.1))


def test_rotating_spinner_wraps_around() -> None:
    spin = RotatingSpinner("dots", [Text("first"), Text("second")], style="dim")

    spin.render(100.0)

    assert "first" in str(spin.render(111.0))


def test_rotating_spinner_keeps_glyph_and_message_separated() -> None:
    spin = RotatingSpinner("dots", [Text("first")], style="dim")

    assert " first" in str(spin.render(0.0))
