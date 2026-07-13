"""Protocol for parsing raw user input into structured chat subcommands."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SubcommandParser(Protocol):
    """Parse raw user input into (cmd_name, *args).

    Every chat feature module (refine, etc.) implements this protocol so
    that the handler can dispatch without knowing the command syntax.
    """

    def parse(self, raw: str) -> tuple[str, ...] | None:
        """Parse *raw* user input (no leading/trailing whitespace expected).

        Return value semantics:

        ``None``
            Empty input, unrecognised command, missing required argument.
            The handler should print a usage hint and skip the turn.

        ``("exit",)``
            End the session.
            The handler should break the interactive loop.

        ``("chat", user_text)``
            A plain conversational turn.
            The handler should pass the user_text to the LLM as-is.

        ``(cmd, *args)``
            A recognised subcommand with zero or more arguments.
            The handler should construct the appropriate prompt block and
            send a synthetic user message to the LLM.
        """
        ...
