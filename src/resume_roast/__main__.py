"""Entry point for the console script and `python -m resume_roast`."""

import io
import sys

from resume_roast.cli.registry import build_subcommand_registry


def _force_utf8_output() -> None:
    """Reconfigure stdout/stderr to UTF-8.

    Windows consoles default to legacy code pages (cp1252) that crash on
    characters models routinely emit (e.g. the non-breaking hyphen);
    `errors="replace"` keeps even an unwritable character from killing a
    stream mid-roast.
    """
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    """Build the subcommand registry and run it."""
    _force_utf8_output()
    registry = build_subcommand_registry()
    registry()


if __name__ == "__main__":
    main()
