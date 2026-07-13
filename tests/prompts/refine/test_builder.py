"""RefinePromptBuilder: system prompt sections and per-turn context blocks."""

import pytest

from resume_roast.prompts.bullets import BULLET_PRINCIPLES
from resume_roast.prompts.refine.builder import RefinePromptBuilder
from resume_roast.prompts.refine.input.parser import RefineParser
from resume_roast.prompts.refine.input.state import RefineState


def _state(bullet: str) -> RefineState:
    return RefineState(RefineParser(), bullet)


# -- system prompt -----------------------------------------------------------


def test_system_has_three_sections() -> None:
    system = RefinePromptBuilder.build_system()

    assert "## Context" in system
    assert "## Principles" in system
    assert "## Rules" in system


def test_system_includes_bullet_principles() -> None:
    assert BULLET_PRINCIPLES in RefinePromptBuilder.build_system()


def test_system_specifies_header_format() -> None:
    system = RefinePromptBuilder.build_system()

    assert "[current rating: X/10]" in system
    assert "[current bullet point:" in system


def test_system_forbids_unsolicited_rewrites() -> None:
    system = RefinePromptBuilder.build_system()

    assert "Do not propose rewrites" in system


def test_system_keeps_replies_short() -> None:
    system = RefinePromptBuilder.build_system()

    assert "short and conversational" in system
    assert "no headings" in system


# -- first message -----------------------------------------------------------


def test_first_message_shows_current_bullet() -> None:
    message = RefinePromptBuilder(_state("Led a team of 10")).build_first_message()

    assert "<current bullet point>" in message
    assert "Led a team of 10" in message
    assert "</current bullet point>" in message


# -- chat message ------------------------------------------------------------


def test_chat_message_carries_the_bullet_and_the_user_text() -> None:
    builder = RefinePromptBuilder(_state("Managed sprints"))
    message = builder.build_turn_message(("chat", "what about the verb?"))

    assert "<current bullet point>" in message
    assert "Managed sprints" in message
    assert "what about the verb?" in message


# -- replace message ---------------------------------------------------------


def test_replace_message_includes_new_bullet() -> None:
    builder = RefinePromptBuilder(_state("Old bullet"))
    message = builder.build_turn_message(("replace", "New and improved bullet"))

    assert "<current bullet point>" in message
    assert "New and improved bullet" in message
    assert "re-rate" in message.lower()


# -- generate message --------------------------------------------------------


def test_generate_message_with_note() -> None:
    builder = RefinePromptBuilder(_state("Fixed bugs"))
    message = builder.build_turn_message(("generate", "I was the lead engineer"))

    assert "<current bullet point>" in message
    assert "Fixed bugs" in message
    assert "<note>" in message
    assert "I was the lead engineer" in message
    assert "explanation" in message.lower()


def test_generate_message_without_note() -> None:
    builder = RefinePromptBuilder(_state("Fixed bugs"))
    message = builder.build_turn_message(("generate",))

    assert "<current bullet point>" in message
    assert "Fixed bugs" in message
    assert "<note>" not in message
    assert "explanation" in message.lower()


# -- unknown command ---------------------------------------------------------


def test_unknown_command_raises_value_error() -> None:
    builder = RefinePromptBuilder(_state("Bullet"))

    with pytest.raises(ValueError, match="Unknown command"):
        builder.build_turn_message(("bogus",))
