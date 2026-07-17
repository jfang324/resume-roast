"""Console implementation of the chat service's input port."""

from resume_roast.cli.utils import USER_PROMPT


class ConsoleInputProvider:
    """Reads one line from stdin, displaying the standard prompt."""

    def __init__(self, prompt: str = USER_PROMPT) -> None:
        self._prompt = prompt

    def get_input(self) -> str:
        """Return the next line of user input."""
        return input(self._prompt)
