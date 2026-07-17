"""CommandExecutor validation and dispatch: built-ins, vocabulary, argument policy."""

from collections.abc import Mapping
from enum import Enum

from resume_roast.services.chat.command_executor import CommandExecutor
from resume_roast.services.chat.enums import ArgPolicy
from resume_roast.services.chat.types import (
    ChatText,
    Command,
    CommandSpec,
    EndSession,
    Invalid,
    Outcome,
    SendTurn,
    ShowHelp,
)


class _EchoCommand(Enum):
    ECHO = "echo"
    NEED = "need"


class _EchoExecutor(CommandExecutor[_EchoCommand]):
    """Minimal concrete executor: one optional-arg and one required-arg command."""

    @property
    def commands(self) -> Mapping[_EchoCommand, CommandSpec]:
        return {
            _EchoCommand.ECHO: CommandSpec(ArgPolicy.OPTIONAL, "Echo the argument", "<text>"),
            _EchoCommand.NEED: CommandSpec(ArgPolicy.REQUIRED, "Needs an argument", "<value>"),
        }

    def chat(self, text: str) -> Outcome:
        return SendTurn(f"chat:{text}")

    def command(self, command: _EchoCommand, arg: str | None) -> Outcome:
        return SendTurn(f"{command.value}:{arg}")


def test_none_input_is_invalid() -> None:
    assert _EchoExecutor().execute(None) == Invalid()


def test_chat_text_reaches_the_chat_hook() -> None:
    assert _EchoExecutor().execute(ChatText("hi")) == SendTurn("chat:hi")


def test_exit_ends_the_session() -> None:
    assert _EchoExecutor().execute(Command("exit")) == EndSession()


def test_help_carries_the_generated_help_text() -> None:
    assert _EchoExecutor().execute(Command("help")) == ShowHelp(_EchoExecutor().help_text)


def test_help_is_generated_from_the_vocabulary() -> None:
    text = _EchoExecutor().help_text

    assert text.startswith("Available commands:")
    assert "/echo <text>" in text
    assert "Echo the argument" in text
    assert "/need <value>" in text
    assert "Needs an argument" in text
    # The built-ins are documented alongside the feature commands.
    assert "/exit" in text
    assert "End the session" in text
    assert "/help" in text
    assert "Show this message" in text


def test_help_epilogue_is_appended_after_a_blank_line() -> None:
    class _WithEpilogue(_EchoExecutor):
        @property
        def help_epilogue(self) -> str:
            return "Or just type naturally."

    assert _WithEpilogue().help_text.endswith("\n\nOr just type naturally.")
    assert _EchoExecutor().help_text.endswith("Show this message")  # none by default


def test_exit_with_an_argument_is_invalid() -> None:
    # "/exit now" was never a command; it must not end the session.
    assert _EchoExecutor().execute(Command("exit", "now")) == Invalid()


def test_unknown_command_is_invalid() -> None:
    assert _EchoExecutor().execute(Command("bogus")) == Invalid()


def test_known_command_reaches_the_command_hook() -> None:
    assert _EchoExecutor().execute(Command("echo", "hello")) == SendTurn("echo:hello")


def test_optional_argument_may_be_absent() -> None:
    assert _EchoExecutor().execute(Command("echo")) == SendTurn("echo:None")


def test_missing_required_argument_is_invalid() -> None:
    assert _EchoExecutor().execute(Command("need")) == Invalid()


def test_required_argument_present_dispatches() -> None:
    assert _EchoExecutor().execute(Command("need", "this")) == SendTurn("need:this")
