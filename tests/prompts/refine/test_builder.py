"""Refine prompt builders: system prompt sections and per-turn context blocks."""

from resume_roast.prompts.refine.builder import (
    build_chat_message,
    build_first_message,
    build_generate_message,
    build_replace_message,
    build_system,
)
from resume_roast.prompts.system_prompt import BULLET_PRINCIPLES

# -- system prompt -----------------------------------------------------------


def test_system_has_three_sections() -> None:
    system = build_system()

    assert "## Context" in system
    assert "## Principles" in system
    assert "## Rules" in system


def test_system_includes_bullet_principles() -> None:
    assert BULLET_PRINCIPLES in build_system()


def test_system_specifies_header_format() -> None:
    system = build_system()

    assert "[current rating: X/10]" in system
    assert "[current bullet point:" in system


def test_system_forbids_unsolicited_rewrites() -> None:
    assert "Do not propose rewrites" in build_system()


def test_system_keeps_replies_short() -> None:
    system = build_system()

    assert "short and conversational" in system
    assert "no headings" in system


# -- first message -----------------------------------------------------------


def test_first_message_shows_current_bullet() -> None:
    message = build_first_message("Led a team of 10")

    assert "<current bullet point>" in message
    assert "Led a team of 10" in message
    assert "</current bullet point>" in message


# -- chat message ------------------------------------------------------------


def test_chat_message_carries_the_bullet_and_the_user_text() -> None:
    message = build_chat_message("Managed sprints", "what about the verb?")

    assert "<current bullet point>" in message
    assert "Managed sprints" in message
    assert "what about the verb?" in message


# -- replace message ---------------------------------------------------------


def test_replace_message_includes_new_bullet() -> None:
    message = build_replace_message("New and improved bullet")

    assert "<current bullet point>" in message
    assert "New and improved bullet" in message
    assert "re-rate" in message.lower()


# -- generate message --------------------------------------------------------


def test_generate_message_with_note() -> None:
    message = build_generate_message("Fixed bugs", "I was the lead engineer")

    assert "<current bullet point>" in message
    assert "Fixed bugs" in message
    assert "<note>" in message
    assert "I was the lead engineer" in message
    assert "explanation" in message.lower()


def test_generate_message_without_note() -> None:
    message = build_generate_message("Fixed bugs", None)

    assert "<current bullet point>" in message
    assert "Fixed bugs" in message
    assert "<note>" not in message
    assert "explanation" in message.lower()
