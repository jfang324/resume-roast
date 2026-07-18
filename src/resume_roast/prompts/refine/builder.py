"""Builds the refine feature's prompt text — static system prompt and per-turn messages.

All builders are pure functions of their inputs; session state (the current
bullet) lives with the refine service's executor and is passed in explicitly.
"""

from resume_roast.prompts.bullets import BULLET_PRINCIPLES

_SYSTEM = (
    """\
## Context

You are a resume-bullet coach working with a candidate to sharpen a single bullet
point, in a back-and-forth conversation. The candidate's first message is the
bullet they want to improve. Every message after that is their reply to you.
Stay on the one bullet under discussion — do not review or rewrite the rest of
their resume.

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


def build_system() -> str:
    """Three-section system prompt: Context / Bullet Writing Principles / Rules."""
    return _SYSTEM


def build_first_message(bullet: str) -> str:
    """Build the candidate's opening turn: the bullet to improve, tagged for the header.

    The ``<current bullet point>`` tag anchors the ``[current bullet point]``
    header the model maintains — the first message carries it so the header
    is well-defined from the very first reply.
    """
    return (
        f"This is the bullet I want to improve:\n\n"
        f"<current bullet point>\n{bullet}\n</current bullet point>"
    )


def build_chat_message(bullet: str, user_text: str) -> str:
    """Wrap a conversational turn with the current bullet as context.

    The per-turn context rides *inside the user turn* (the system prompt is
    set once and never re-sent), so the conversation stays a single system
    message followed by user/assistant turns — as do the other turn builders.
    """
    return f"<current bullet point>\n{bullet}\n</current bullet point>\n\n{user_text}"


def build_replace_message(new_bullet: str) -> str:
    """Announce the replacement bullet and ask for a re-rating."""
    return (
        f"I've updated my bullet to:\n\n"
        f"<current bullet point>\n{new_bullet}\n</current bullet point>\n\n"
        f"Update the current bullet in your [current bullet point] header "
        f"and re-rate it."
    )


def build_generate_message(bullet: str, note: str | None) -> str:
    """Request a candidate rewrite of the current bullet, honoring an optional note."""
    message = "Generate a new and improved bullet point based on the current bullet point"
    if note is not None:
        message += " and the note provided.\n\n"
    else:
        message += ".\n\n"

    message += f"<current bullet point>\n{bullet}\n</current bullet point>"

    if note is not None:
        message += f"\n\n<note>\n{note}\n</note>"
    message += (
        "\n\nOutput the candidate bullet on its own line, followed by a "
        "blank line, then a short explanation of what changed and why "
        "compared to the current bullet. Do NOT change the current "
        "bullet in your [current bullet point] header."
    )

    return message
