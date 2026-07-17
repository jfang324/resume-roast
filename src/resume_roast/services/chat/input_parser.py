"""Lexical parsing of raw chat input — no vocabulary knowledge."""

from resume_roast.services.chat.types import ChatText, Command, UserInput


class InputParser:
    """Lexes raw user input — no vocabulary knowledge, no state."""

    def parse(self, raw: str) -> UserInput | None:
        """Split *raw* into a `Command` or `ChatText`; empty input is None.

        ``/name rest`` lexes to ``Command("name", "rest")`` with *rest*
        stripped and empty rest collapsed to None. Whether *name* exists —
        and whether it needs an argument — is the executor's call.
        """
        if not raw:
            return None
        if raw.startswith("/"):
            name, _, arg = raw[1:].partition(" ")
            return Command(name, arg.strip() or None)
        return ChatText(raw)
