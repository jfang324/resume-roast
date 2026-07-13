"""Builds the refine feature's prompt blocks — static system and per-turn state blocks."""

from resume_roast.prompts.bullets import BULLET_PRINCIPLES
from resume_roast.prompts.refine.input.state import RefineState

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
    # Per-turn context blocks
    # ------------------------------------------------------------------

    def build_initial_block(self) -> str:
        """Context block injected before the first user turn."""
        return f"<current bullet point>\n{self._state.current_bullet}\n</current bullet point>"

    def build_turn_block(self, parsed: tuple[str, ...]) -> str:
        """Return a context block for the parsed command.

        Parameters
        ----------
        parsed
            The result of :meth:`RefineState.parse` — ``(cmd, *args)``.
        """
        cmd = parsed[0]
        if cmd == "chat":
            return self._block_chat()
        if cmd == "replace":
            return self._block_replace(parsed[1])
        if cmd == "generate":
            return self._block_generate(parsed[1] if len(parsed) > 1 else None)
        msg = f"Unknown command: {cmd!r}"
        raise ValueError(msg)

    # -- private block builders ---------------------------------------

    def _block_chat(self) -> str:
        return self.build_initial_block()

    def _block_replace(self, new_bullet: str) -> str:
        return (
            f"The candidate has updated their bullet point. "
            f"The new current bullet is:\n\n"
            f"<current bullet point>\n{new_bullet}\n</current bullet point>\n\n"
            f"Update the current bullet in your [current bullet point] header "
            f"and re-rate the new bullet."
        )

    def _block_generate(self, note: str | None) -> str:
        block = "Generate a new and improved bullet point based on the current bullet point"
        if note is not None:
            block += " and the note provided.\n\n"
        else:
            block += ".\n\n"
        block += f"<current bullet point>\n{self._state.current_bullet}\n</current bullet point>"
        if note is not None:
            block += f"\n\n<note>\n{note}\n</note>"
        block += (
            "\n\nOutput the candidate bullet on its own line, followed by a "
            "blank line, then a short explanation of what changed and why "
            "compared to the current bullet. Do NOT change the current "
            "bullet in your header."
        )
        return block
