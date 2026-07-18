"""Generate-block prompt builders: system prompt sections and the /generate message."""

from resume_roast.prompts.bullets import BULLET_PRINCIPLES
from resume_roast.prompts.generate_block.builder import build_generate_message, build_system

# -- system prompt -----------------------------------------------------------


def test_system_has_four_sections() -> None:
    system = build_system()

    assert "## Context" in system
    assert "## Process" in system
    assert "## Bullet Writing Principles" in system
    assert "## Rules" in system


def test_system_includes_bullet_principles() -> None:
    assert BULLET_PRINCIPLES in build_system()


def test_system_specifies_block_rating_format() -> None:
    assert "[block rating: X/10]" in build_system()


def test_system_forbids_drafting_in_gathering() -> None:
    system = build_system()

    assert "Do NOT propose, draft, or hint at bullet points" in system
    assert "Stay strictly in information-gathering" in system


def test_system_forces_generation_on_command() -> None:
    system = build_system()

    # /generate must always produce a block — the rating is feedback, not a gate.
    assert "always produce a complete resume block" in system
    assert "not a gate" in system


def test_system_defines_the_block_rating_scale() -> None:
    system = build_system()

    # The gate refers to a scale, so the scale itself must be defined.
    assert "## Block Rating Scale" in system
    assert "9-10" in system


def test_system_describes_three_phases() -> None:
    system = build_system()

    assert "GATHERING" in system
    assert "GENERATION" in system
    assert "REFINEMENT" in system


# -- generate message --------------------------------------------------------


def test_generate_message_triggers_block_creation() -> None:
    message = build_generate_message(None)

    assert "generate a complete resume entry" in message.lower()
    assert "this role or project" in message.lower()


def test_generate_message_includes_format_instructions() -> None:
    message = build_generate_message(None)

    assert "Format the block" in message
    assert "- " in message
    assert "header line" in message


def test_generate_message_forces_generation() -> None:
    message = build_generate_message(None)

    # /generate unconditionally produces a block rather than deferring to gather more.
    assert "Always produce a block" in message
    assert "do not ask for more details" in message


def test_generate_message_with_note() -> None:
    message = build_generate_message("Focus on the payment processing work")

    assert "generate a complete resume entry" in message.lower()
    assert "Additional note" in message
    assert "payment processing" in message


def test_generate_message_without_note_omits_additional_note() -> None:
    assert "Additional note" not in build_generate_message(None)
