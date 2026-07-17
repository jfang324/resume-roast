"""Input port for chat sessions; the console implementation lives in the CLI layer."""

from typing import Protocol


class InputProvider(Protocol):
    """Yields one line of raw user input per call; implementations own the prompt."""

    def get_input(self) -> str:
        """Return the next line of user input.

        Raises:
            EOFError: when the input source is closed.
            KeyboardInterrupt: when the user interrupts the session.
        """
        ...
