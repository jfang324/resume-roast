"""Stateful wrapper around a :class:`SubcommandParser`.

Owns the current bullet for the refine session and updates it on
``/replace``.  Delegates pure parsing to the injected parser.
"""

from resume_roast.prompts.subcommand_parser import SubcommandParser


class RefineState:
    """Tracks the current bullet and delegates command parsing.

    Parameters
    ----------
    parser
        A :class:`RefineParser` (or any :class:`SubcommandParser`).
    initial_bullet
        The bullet the user provided on the CLI — becomes
        :attr:`current_bullet` immediately.
    """

    def __init__(self, parser: SubcommandParser, initial_bullet: str) -> None:
        self._parser = parser
        self.current_bullet = initial_bullet

    def parse(self, raw: str) -> tuple[str, ...] | None:
        """Parse *raw* and, if it is a ``/replace``, update ``current_bullet``.

        See :meth:`SubcommandParser.parse` for all return-value semantics.
        """
        result = self._parser.parse(raw)
        if result is None:
            return None
        cmd, *args = result
        if cmd == "replace":
            self.current_bullet = args[0]
        return result
