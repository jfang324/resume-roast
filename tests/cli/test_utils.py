"""Tests for shared CLI display helpers."""

import io
import re

from rich.console import Console
from rich.text import Text

from resume_roast.cli.utils import RotatingSpinner, display_value, print_highlighted_lines

_STYLES = {"  - ": "on #3a0000", "  + ": "on #003a00"}


def _rendered(text: str, *, terminal: bool, width: int = 20) -> list[str]:
    buf = io.StringIO()
    console = Console(
        file=buf,
        force_terminal=terminal,
        width=width,
        color_system="truecolor" if terminal else None,
    )
    print_highlighted_lines(text, console, _STYLES)
    return re.sub(r"\x1b\[[0-9;]*m", "", buf.getvalue()).splitlines()


def test_display_value_joins_tuples() -> None:
    assert display_value(("a", "b")) == "a, b"
    assert display_value("a") == "a"


def test_highlighted_lines_fill_the_full_terminal_width() -> None:
    lines = _rendered("  - short\nplain line\n  + also short", terminal=True)

    # Prefix-matched lines are padded out to the full width; other text is not.
    assert next(line for line in lines if line.startswith("  - ")) == "  - short".ljust(20)
    assert next(line for line in lines if line.startswith("  + ")) == "  + also short".ljust(20)
    assert "plain line" in lines


def test_highlighted_lines_stay_plain_off_a_terminal() -> None:
    lines = _rendered("  - short\nplain line\n  + also short", terminal=False)

    # No padding (no trailing whitespace) when the output is piped.
    assert lines == ["  - short", "plain line", "  + also short"]


def test_highlighted_lines_keep_bracketed_titles_intact() -> None:
    lines = _rendered("[Content — 5/10]", terminal=True)

    # Text, not markup: the brackets are not swallowed as Rich tags.
    assert lines[0].startswith("[Content — 5/10]")


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
