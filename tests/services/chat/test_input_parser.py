"""InputParser lexing: purely lexical, no vocabulary knowledge."""

from resume_roast.services.chat.input_parser import InputParser
from resume_roast.services.chat.types import ChatText, Command


def test_empty_input_is_none() -> None:
    assert InputParser().parse("") is None


def test_plain_text_is_a_chat_turn() -> None:
    assert InputParser().parse("what about the verb?") == ChatText("what about the verb?")


def test_bare_slash_command_has_no_arg() -> None:
    assert InputParser().parse("/exit") == Command("exit", None)


def test_command_argument_is_stripped() -> None:
    assert InputParser().parse("/replace  Led a team  ") == Command("replace", "Led a team")


def test_whitespace_only_argument_collapses_to_none() -> None:
    assert InputParser().parse("/generate   ") == Command("generate", None)


def test_unknown_names_still_lex_as_commands() -> None:
    # Vocabulary is the executor's business, not the lexer's.
    assert InputParser().parse("/bogus stuff") == Command("bogus", "stuff")


def test_a_lone_slash_is_a_nameless_command() -> None:
    assert InputParser().parse("/") == Command("", None)
