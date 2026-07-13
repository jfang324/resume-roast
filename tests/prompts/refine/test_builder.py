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


# -- initial block -----------------------------------------------------------


def test_initial_block_shows_current_bullet() -> None:
    block = RefinePromptBuilder(_state("Led a team of 10")).build_initial_block()

    assert "<current bullet point>" in block
    assert "Led a team of 10" in block
    assert "</current bullet point>" in block


# -- chat block --------------------------------------------------------------


def test_chat_block_shows_current_bullet() -> None:
    builder = RefinePromptBuilder(_state("Managed sprints"))
    block = builder.build_turn_block(("chat", "what about the verb?"))

    assert "<current bullet point>" in block
    assert "Managed sprints" in block
    assert "what about the verb?" not in block


# -- replace block -----------------------------------------------------------


def test_replace_block_includes_new_bullet() -> None:
    builder = RefinePromptBuilder(_state("Old bullet"))
    block = builder.build_turn_block(("replace", "New and improved bullet"))

    assert "<current bullet point>" in block
    assert "New and improved bullet" in block
    assert "re-rate" in block.lower()


# -- generate block ----------------------------------------------------------


def test_generate_block_with_note() -> None:
    builder = RefinePromptBuilder(_state("Fixed bugs"))
    block = builder.build_turn_block(("generate", "I was the lead engineer"))

    assert "<current bullet point>" in block
    assert "Fixed bugs" in block
    assert "<note>" in block
    assert "I was the lead engineer" in block
    assert "explanation" in block.lower()


def test_generate_block_without_note() -> None:
    builder = RefinePromptBuilder(_state("Fixed bugs"))
    block = builder.build_turn_block(("generate",))

    assert "<current bullet point>" in block
    assert "Fixed bugs" in block
    assert "<note>" not in block
    assert "explanation" in block.lower()


# -- unknown command ---------------------------------------------------------


def test_unknown_command_raises_value_error() -> None:
    builder = RefinePromptBuilder(_state("Bullet"))

    with pytest.raises(ValueError, match="Unknown command"):
        builder.build_turn_block(("bogus",))
