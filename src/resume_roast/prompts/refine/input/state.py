"""Stateful wrapper around a :class:`SubcommandParser`.

Owns the current bullet for the refine session.  Parsing is pure and delegated
to the injected parser; a ``/replace`` only becomes the new current bullet once
the turn it drives has been sent successfully — see :meth:`commit`.
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
        """Parse *raw* — pure delegation, no state change.

        See :meth:`SubcommandParser.parse` for all return-value semantics.
        """
        return self._parser.parse(raw)

    def commit(self, parsed: tuple[str, ...]) -> None:
        """Apply a successfully-sent turn to the session state.

        Only ``/replace`` mutates state: its new text becomes
        :attr:`current_bullet`.  Called *after* the exchange succeeds, so a
        failed turn leaves the current bullet — and the transcript — untouched.
        """
        cmd, *args = parsed
        if cmd == "replace":
            self.current_bullet = args[0]
