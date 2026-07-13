"""Stateful wrapper around a :class:`SubcommandParser`.

No mutable state to track (unlike refine's current_bullet) — the full
conversation history serves as context.  State exists for consistency with the
:class:`SubcommandParser` protocol and as a future extension point.
"""

from resume_roast.prompts.subcommand_parser import SubcommandParser


class GenerateBlockState:
    """Tracks session state and delegates command parsing.

    Parameters
    ----------
    parser
        A :class:`GenerateBlockParser` (or any :class:`SubcommandParser`).
    """

    def __init__(self, parser: SubcommandParser) -> None:
        self._parser = parser

    def parse(self, raw: str) -> tuple[str, ...] | None:
        """Parse *raw* — pure delegation, no state change."""
        return self._parser.parse(raw)

    def commit(self, parsed: tuple[str, ...]) -> None:
        """Apply a successfully-sent turn to the session state.

        Currently a no-op — no mutable state to update.
        """
        _ = parsed
