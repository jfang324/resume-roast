"""Tests for the ConsoleInputProvider."""

from resume_roast.cli.interview.input_provider import ConsoleInputProvider, make_input_provider


def test_make_input_provider() -> None:
    provider = make_input_provider()
    assert isinstance(provider, ConsoleInputProvider)


def test_console_protocol_conformance() -> None:
    """Verify the default provider satisfies the UserInputProvider protocol."""
    provider: object = make_input_provider()
    assert hasattr(provider, "get_input")
    assert callable(provider.get_input)
