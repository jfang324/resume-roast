"""Builds the refine feature's prompt blocks — static system and per-turn state blocks."""

from resume_roast.prompts.refine.input.state import RefineState
from resume_roast.prompts.system_prompt import BULLET_PRINCIPLES

_SYSTEM = (
    """\
## Context

You are a resume-bullet coach working with a candidate to sharpen a single bullet
point, in a back-and-forth conversation. The candidate's first message is the
bullet they want to improve. Every message after that is their reply to you.
Stay on the one bullet under discussion — do not review or rewrite the rest of
their resume.

## Principles

"""
    + BULLET_PRINCIPLES
    + """\
## Rules

- Lead every reply with the current state on one line:
  `[current rating: X/10][current bullet point: "..."]`
- Re-rate the bullet on every reply. The [current bullet point] in your header
  reflects the value inside the most recent <current bullet point> block. Only
  update it when that block's value changes.
- Do not propose rewrites unless the candidate provides a revised bullet or
  explicitly requests a generation via "Generate a candidate."
- Keep replies short and conversational. Plain sentences, no headings or
  markdown beyond the state line."""
)


class RefinePromptBuilder:
    """Assembles the static system prompt and per-turn context blocks.

    Parameters
    ----------
    state
        Session state used to read the current bullet for turn blocks.
    """

    def __init__(self, state: RefineState) -> None:
        self._state = state

    # ------------------------------------------------------------------
    # Static prompt (built once per session)
    # ------------------------------------------------------------------

    @staticmethod
    def build_system() -> str:
        """Three-section system prompt: Context / Principles / Rules."""
        return _SYSTEM

    # ------------------------------------------------------------------
    # Per-turn user messages
    # ------------------------------------------------------------------

    def build_first_message(self) -> str:
        """Build the candidate's opening turn: the bullet to improve, tagged for the header.

        The ``<current bullet point>`` tag anchors the ``[current bullet point]``
        header the model maintains — the first message carries it so the header
        is well-defined from the very first reply.
        """
        return (
            f"This is the bullet I want to improve:\n\n"
            f"<current bullet point>\n{self._state.current_bullet}\n</current bullet point>"
        )

    def build_turn_message(self, parsed: tuple[str, ...]) -> str:
        """Return the user-turn text for the parsed command.

        The per-turn context rides *inside the user turn* (the system prompt is
        set once and never re-sent), so the conversation stays a single system
        message followed by user/assistant turns.

        Parameters
        ----------
        parsed
            The result of :meth:`RefineState.parse` — ``(cmd, *args)``.
        """
        cmd = parsed[0]
        if cmd == "chat":
            return self._chat_message(parsed[1])
        if cmd == "replace":
            return self._replace_message(parsed[1])
        if cmd == "generate":
            return self._generate_message(parsed[1] if len(parsed) > 1 else None)
        msg = f"Unknown command: {cmd!r}"
        raise ValueError(msg)

    # -- private message builders -------------------------------------

    def _chat_message(self, user_text: str) -> str:
        return (
            f"<current bullet point>\n{self._state.current_bullet}\n</current bullet point>\n\n"
            f"{user_text}"
        )

    def _replace_message(self, new_bullet: str) -> str:
        return (
            f"I've updated my bullet to:\n\n"
            f"<current bullet point>\n{new_bullet}\n</current bullet point>\n\n"
            f"Update the current bullet in your [current bullet point] header "
            f"and re-rate it."
        )

    def _generate_message(self, note: str | None) -> str:
        message = "Generate a new and improved bullet point based on the current bullet point"
        if note is not None:
            message += " and the note provided.\n\n"
        else:
            message += ".\n\n"
        message += f"<current bullet point>\n{self._state.current_bullet}\n</current bullet point>"
        if note is not None:
            message += f"\n\n<note>\n{note}\n</note>"
        message += (
            "\n\nOutput the candidate bullet on its own line, followed by a "
            "blank line, then a short explanation of what changed and why "
            "compared to the current bullet. Do NOT change the current "
            "bullet in your [current bullet point] header."
        )
        return message
