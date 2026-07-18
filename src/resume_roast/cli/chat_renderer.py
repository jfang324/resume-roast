"""Rich-console implementation of the chat service's renderer protocol."""

from collections.abc import Iterable

from rich.console import Console

from resume_roast.cli.utils import USER_PROMPT, summary_line
from resume_roast.integrations.errors import TransientError
from resume_roast.integrations.types import Usage


class ConsoleRenderer:
    """Renders chat session output to a rich console.

    Parameters
    ----------
    console
        Destination for all output.
    label
        Short model name prefixed to every reply.
    model
        Full model id, for the per-exchange metrics line.
    """

    def __init__(self, console: Console, label: str, model: str) -> None:
        self._console = console
        self._label = label
        self._model = model

    def show_reply(self, chunks: Iterable[str]) -> None:
        """Print the reply label, stream the chunks, and close the line."""
        self._console.print(f"{self._label}{USER_PROMPT}", end="", style="bold")
        _stream_to_console(chunks, self._console)
        self._console.print()

    def show_metrics(
        self, usage: Usage | None, finish_reason: str | None, latency_seconds: float
    ) -> None:
        """Print the cut-off notice when truncated, then the metrics line."""
        if finish_reason == "length":
            self._console.print("(reply cut off at the length limit)", style="dim")

        self._console.print(
            summary_line(self._model, usage, latency_seconds),
            style="dim",
        )

    def show_transient_error(self, error: TransientError) -> None:
        """Break the reply line and invite a retry."""
        self._console.print(f"\n{error} — try again.", style="red")

    def show_help(self, text: str) -> None:
        """Print the command help, dimmed."""
        self._console.print(text, style="dim")

    def show_usage_hint(self) -> None:
        """Flag unrecognised input, dimmed."""
        self._console.print("(unrecognised command)", style="dim")

    def show_interrupt(self) -> None:
        """End the prompt line so the shell resumes cleanly."""
        self._console.print()


def _stream_to_console(chunks: Iterable[str], console: Console) -> None:
    for chunk in chunks:
        console.print(chunk, end="", markup=False, highlight=False, soft_wrap=True)
