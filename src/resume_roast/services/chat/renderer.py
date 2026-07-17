"""Display port for chat sessions; the console implementation lives in the CLI layer."""

from collections.abc import Iterable
from typing import Protocol

from resume_roast.integrations.errors import TransientError
from resume_roast.integrations.types import Usage


class ChatRenderer(Protocol):
    """Renders session output; implementations own all display concerns."""

    def show_reply(self, chunks: Iterable[str]) -> None:
        """Stream one assistant reply to the user.

        Must drain *chunks* to exhaustion — the conversation records the
        assistant turn only once the reply stream is fully consumed.
        """
        ...

    def show_metrics(
        self, usage: Usage | None, finish_reason: str | None, latency_seconds: float
    ) -> None:
        """Print the metrics footprint of a completed exchange."""
        ...

    def show_transient_error(self, error: TransientError) -> None:
        """Report a retryable failure of the current turn."""
        ...

    def show_help(self, text: str) -> None:
        """Print the command help."""
        ...

    def show_usage_hint(self) -> None:
        """Point at ``/help`` after unrecognised input."""
        ...

    def show_interrupt(self) -> None:
        """Close the session's output after EOF or a keyboard interrupt."""
        ...
