"""Protocols every LLM client implements; the CLI depends on these, not on providers."""

from collections.abc import Iterator, Sequence
from typing import Protocol

from resume_roast.integrations.types import Completion, Message, Usage


class CompletionStream(Protocol):
    """Iterable of response text chunks.

    ``usage`` and ``finish_reason`` hold None until the stream is exhausted,
    then whatever the API reported. Truncation is never raised here — by the
    time it is known, every chunk has already been delivered — callers
    inspect ``finish_reason`` instead.
    """

    usage: Usage | None
    finish_reason: str | None

    def __iter__(self) -> Iterator[str]:
        """Yield response text chunks in arrival order."""
        ...


class LlmClient(Protocol):
    """Any chat-completion client the CLI can drive."""

    def prompt(self, messages: Sequence[Message], *, temperature: float = 0.0) -> Completion:
        """Send `messages` and return the complete response.

        Raises:
            ApiError: for transport failures and for empty or truncated
                responses — callers need the full text.
        """
        ...

    def prompt_stream(
        self, messages: Sequence[Message], *, temperature: float = 0.0
    ) -> CompletionStream:
        """Send `messages` and return a stream of response text chunks.

        Raises:
            ApiError: when the request cannot be started; errors mid-stream
                surface from the returned iterator.
        """
        ...
