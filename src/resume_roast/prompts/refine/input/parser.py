"""Pure parser for the refine chat session — no state, no side effects."""


class RefineParser:
    """Parse ``/replace``, ``/generate``, ``/exit``, ``/help``, and bare chat input.

    All methods are pure — no side effects.  Stateful side effects (e.g.
    updating the current bullet) belong in :class:`RefineState`.
    """

    def parse(self, raw: str) -> tuple[str, ...] | None:
        """See :meth:`SubcommandParser.parse` for return-value semantics."""
        if not raw:
            return None

        # ――― exit ―――
        if raw == "/exit":
            return ("exit",)

        # ――― subcommands with arguments ―――
        for prefix, cmd_name in (("/replace ", "replace"), ("/generate ", "generate")):
            if raw.startswith(prefix):
                arg = raw.removeprefix(prefix).strip()
                if not arg and cmd_name == "replace":
                    return None  # missing required argument
                if not arg:
                    break  # /generate with whitespace-only notes → fall through
                return (cmd_name, arg)

        # ――― bare /generate (no notes) ―――
        if raw == "/generate" or raw.startswith("/generate "):
            return ("generate",)

        # ――― bare /replace with no text ―――
        if raw == "/replace":
            return None

        # ――― help ―――
        if raw == "/help":
            return ("help",)

        # ――― unrecognised command (starts with / but we don't know it) ―――
        if raw.startswith("/"):
            return None

        # ――― plain chat ―――
        return ("chat", raw)
