"""GenerateBlockCommandExecutor: passthrough chat and the /generate turn."""

from resume_roast.services.chat.types import ChatText, Command, SendTurn
from resume_roast.services.generate_block.executor import GenerateBlockCommandExecutor


def test_chat_passes_through_raw_text() -> None:
    outcome = GenerateBlockCommandExecutor().execute(ChatText("I was a backend engineer"))

    assert outcome == SendTurn("I was a backend engineer")


def test_chat_never_commits() -> None:
    outcome = GenerateBlockCommandExecutor().execute(ChatText("hello"))

    assert isinstance(outcome, SendTurn)
    assert outcome.commit is None


def test_generate_builds_the_block_request() -> None:
    outcome = GenerateBlockCommandExecutor().execute(Command("generate"))

    assert isinstance(outcome, SendTurn)
    assert "generate a complete resume entry" in outcome.text.lower()
    assert outcome.commit is None  # stateless — nothing to persist


def test_generate_with_notes_carries_the_note() -> None:
    outcome = GenerateBlockCommandExecutor().execute(Command("generate", "focus on payments"))

    assert isinstance(outcome, SendTurn)
    assert "focus on payments" in outcome.text


def test_help_documents_the_vocabulary_and_the_epilogue() -> None:
    text = GenerateBlockCommandExecutor().help_text

    assert "/generate <notes>" in text
    assert "Generate a resume block" in text
    assert "/exit" in text
    assert "/help" in text
    assert text.endswith("Or just type naturally and I'll ask questions.")
