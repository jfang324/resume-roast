"""Builds the generate-block feature's prompt blocks — static system and per-turn messages."""

from resume_roast.prompts.generate_block.input.state import GenerateBlockState
from resume_roast.prompts.system_prompt import BULLET_PRINCIPLES

_SYSTEM = (
    """\
## Context

You are a resume-block interviewer and writer. Your job is to guide the
user through crafting a compelling resume entry for a specific role or
project they've worked on.

## Process

The user will start by telling you about a role or project they've worked on.

PHASE 1 — GATHERING
Do NOT propose, draft, or hint at bullet points during this phase — no matter
how much information the user provides. Stay strictly in information-gathering
mode until the user types /generate.

Ask follow-up questions to gather details. Focus on:
- Responsibilities and contributions
- Technologies and tools used
- Key achievements and quantifiable impact
- Team size, scope, and outcomes
Ask one or two questions at a time — keep it conversational.

PHASE 2 — GENERATION
When the user types /generate, check whether you have enough specific,
quantifiable information to produce a high-quality block. Only generate if
the bullet points would score 8-10/10 on the [block rating] scale.

If the information is too vague or incomplete, explain what's missing and ask
targeted follow-up questions. Do not produce a weak block.

PHASE 3 — REFINEMENT
After generating the block, invite the user to refine it. On every subsequent
reply, reassess and re-rate the block, leading with: [block rating: X/10]

## Principles

"""
    + BULLET_PRINCIPLES
    + """\
## Rules

- Stay in the gathering phase until the user types /generate — do not propose,
  draft, or hint at bullet points during this phase
- Only include [block rating: X/10] in replies that come after the user types /generate
- After /generate, assess whether you have enough detail for an 8-10/10 block before producing it
- After /generate, lead every reply with [block rating: X/10] and re-rate the block each time
- Each bullet must start with a strong past-tense action verb
- No trailing period on bullet points
- When generating, output each bullet on its own line, starting with "- " and 3-6 bullets"""
)


class GenerateBlockPromptBuilder:
    """Assembles the static system prompt and per-turn messages.

    Parameters
    ----------
    state
        Session state (unused for now; reserved for future use).
    """

    def __init__(self, state: GenerateBlockState) -> None:
        self._state = state

    # ------------------------------------------------------------------
    # Static prompt (built once per session)
    # ------------------------------------------------------------------

    @staticmethod
    def build_system() -> str:
        """Full system prompt: Context / Process / Principles / Rules."""
        return _SYSTEM

    # ------------------------------------------------------------------
    # Per-turn user messages
    # ------------------------------------------------------------------

    def build_turn_message(self, parsed: tuple[str, ...]) -> str:
        """Return the user-turn text for the parsed command.

        Parameters
        ----------
        parsed
            The result of :meth:`GenerateBlockState.parse` — ``(cmd, *args)``.
        """
        cmd = parsed[0]
        if cmd == "chat":
            return parsed[1]
        if cmd == "generate":
            return self._generate_message(parsed[1] if len(parsed) > 1 else None)
        msg = f"Unknown command: {cmd!r}"
        raise ValueError(msg)

    # -- private message builders -------------------------------------

    @staticmethod
    def _generate_message(note: str | None) -> str:
        msg = (
            "Based on everything we've discussed, generate a complete resume entry "
            "for this role or project.\n"
            "Only proceed if you have enough detail for a high-quality block (8-10/10). "
            "If the information is insufficient, ask for more details instead.\n"
            "Format the block as follows:\n"
            '- Start with a header line describing the role (e.g. "Backend Engineer, Stripe")\n'
            '- Follow with 3-6 bullet points, each on its own line starting with "- "\n'
            "- Lead your reply with [block rating: X/10]\n"
            "- Follow the Bullet Writing Principles above"
        )
        if note is not None:
            msg += f"\n\nAdditional note: {note}"
        return msg
