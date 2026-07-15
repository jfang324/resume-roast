"""User-input abstraction for the interview session.

Replaces bare ``input(USER_PROMPT)`` calls so the test harness can inject
canned answers without mocking ``builtins.input``.
"""

from typing import Protocol


class UserInputProvider(Protocol):
    """Anything that can yield one line of user input."""

    def get_input(self, prompt: str = "") -> str:
        """Return a single line of user input."""
        ...


class ConsoleInputProvider:
    """Default implementation that delegates to ``builtins.input``."""

    def get_input(self, prompt: str = "") -> str:
        return input(prompt)


def make_input_provider() -> UserInputProvider:
    """Build the default input provider for production use."""
    return ConsoleInputProvider()
