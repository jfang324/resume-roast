"""Pure parser for the generate-block chat session — no state, no side effects."""


class GenerateBlockParser:
    """Parse ``/generate``, ``/exit``, and bare chat input.

    All methods are pure — no state, no side effects.
    """

    def parse(self, raw: str) -> tuple[str, ...] | None:
        """See :meth:`SubcommandParser.parse` for return-value semantics."""
        if not raw:
            return None

        if raw == "/exit":
            return ("exit",)

        if raw == "/generate":
            return ("generate",)

        if raw.startswith("/generate "):
            arg = raw.removeprefix("/generate ").strip()
            return ("generate", arg) if arg else ("generate",)

        if raw.startswith("/"):
            return None

        return ("chat", raw)
