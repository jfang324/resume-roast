"""RefineCommandExecutor: vocabulary outcomes and current-bullet commits."""

from resume_roast.services.chat.types import ChatText, Command, SendTurn
from resume_roast.services.refine.executor import RefineCommandExecutor


def test_chat_wraps_the_current_bullet_around_the_text() -> None:
    executor = RefineCommandExecutor("Managed a team")

    outcome = executor.execute(ChatText("what about the verb?"))

    assert isinstance(outcome, SendTurn)
    assert "Managed a team" in outcome.text
    assert "what about the verb?" in outcome.text
    assert outcome.commit is None  # chatting never moves the bullet


def test_generate_carries_the_bullet_and_the_note_without_committing() -> None:
    executor = RefineCommandExecutor("Managed a team")

    outcome = executor.execute(Command("generate", "add metrics"))

    assert isinstance(outcome, SendTurn)
    assert "Managed a team" in outcome.text
    assert "add metrics" in outcome.text
    assert outcome.commit is None  # a candidate is not an adoption


def test_generate_without_note_omits_the_note_tag() -> None:
    executor = RefineCommandExecutor("Managed a team")

    outcome = executor.execute(Command("generate"))

    assert isinstance(outcome, SendTurn)
    assert "<note>" not in outcome.text


def test_replace_commits_the_new_bullet_only_when_called() -> None:
    executor = RefineCommandExecutor("Old bullet")

    outcome = executor.execute(Command("replace", "New bullet"))

    assert isinstance(outcome, SendTurn)
    assert "New bullet" in outcome.text
    assert outcome.commit is not None

    # Until the session reports the exchange landed, nothing changed.
    assert executor.current_bullet == "Old bullet"

    outcome.commit()
    assert executor.current_bullet == "New bullet"


def test_turns_after_a_committed_replace_use_the_new_bullet() -> None:
    executor = RefineCommandExecutor("Old bullet")

    replace = executor.execute(Command("replace", "New bullet"))
    assert isinstance(replace, SendTurn)
    assert replace.commit is not None
    replace.commit()

    follow_up = executor.execute(ChatText("better?"))

    assert isinstance(follow_up, SendTurn)
    assert "New bullet" in follow_up.text
    assert "Old bullet" not in follow_up.text


def test_help_documents_the_full_vocabulary() -> None:
    for command in ("/replace", "/generate", "/exit", "/help"):
        assert command in RefineCommandExecutor("bullet").help_text
