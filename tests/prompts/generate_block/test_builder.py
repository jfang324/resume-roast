"""GenerateBlockPromptBuilder: system prompt sections and per-turn messages."""

import pytest

from resume_roast.prompts.generate_block.builder import GenerateBlockPromptBuilder
from resume_roast.prompts.generate_block.input.parser import GenerateBlockParser
from resume_roast.prompts.generate_block.input.state import GenerateBlockState
from resume_roast.prompts.system_prompt import BULLET_PRINCIPLES


def _state() -> GenerateBlockState:
    return GenerateBlockState(GenerateBlockParser())


# -- system prompt -----------------------------------------------------------


def test_system_has_four_sections() -> None:
    system = GenerateBlockPromptBuilder.build_system()

    assert "## Context" in system
    assert "## Process" in system
    assert "## Principles" in system
    assert "## Rules" in system


def test_system_includes_bullet_principles() -> None:
    assert BULLET_PRINCIPLES in GenerateBlockPromptBuilder.build_system()


def test_system_specifies_block_rating_format() -> None:
    system = GenerateBlockPromptBuilder.build_system()

    assert "[block rating: X/10]" in system


def test_system_forbids_drafting_in_gathering() -> None:
    system = GenerateBlockPromptBuilder.build_system()

    assert "Do NOT propose, draft, or hint at bullet points" in system
    assert "Stay strictly in information-gathering" in system


def test_system_requires_quality_gate_before_generation() -> None:
    system = GenerateBlockPromptBuilder.build_system()

    assert "8-10/10" in system


def test_system_describes_three_phases() -> None:
    system = GenerateBlockPromptBuilder.build_system()

    assert "GATHERING" in system
    assert "GENERATION" in system
    assert "REFINEMENT" in system


# -- chat message ------------------------------------------------------------


def test_chat_message_passes_through_raw_text() -> None:
    builder = GenerateBlockPromptBuilder(_state())
    message = builder.build_turn_message(("chat", "I was a backend engineer at Stripe"))

    assert message == "I was a backend engineer at Stripe"


# -- generate message --------------------------------------------------------


def test_generate_message_triggers_block_creation() -> None:
    builder = GenerateBlockPromptBuilder(_state())
    message = builder.build_turn_message(("generate",))

    assert "generate a complete resume entry" in message.lower()
    assert "this role or project" in message.lower()


def test_generate_message_includes_format_instructions() -> None:
    builder = GenerateBlockPromptBuilder(_state())
    message = builder.build_turn_message(("generate",))

    assert "Format the block" in message
    assert "- " in message
    assert "header line" in message


def test_generate_message_includes_quality_check() -> None:
    builder = GenerateBlockPromptBuilder(_state())
    message = builder.build_turn_message(("generate",))

    assert "Only proceed if" in message
    assert "8-10/10" in message


def test_generate_message_with_note() -> None:
    builder = GenerateBlockPromptBuilder(_state())
    message = builder.build_turn_message(("generate", "Focus on the payment processing work"))

    assert "generate a complete resume entry" in message.lower()
    assert "Additional note" in message
    assert "payment processing" in message


def test_generate_message_without_note_omits_additional_note() -> None:
    builder = GenerateBlockPromptBuilder(_state())
    message = builder.build_turn_message(("generate",))

    assert "Additional note" not in message


# -- unknown command ---------------------------------------------------------


def test_unknown_command_raises_value_error() -> None:
    builder = GenerateBlockPromptBuilder(_state())

    with pytest.raises(ValueError, match="Unknown command"):
        builder.build_turn_message(("bogus",))
