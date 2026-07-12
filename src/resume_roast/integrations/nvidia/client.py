"""Thin chat-completion client for the NVIDIA NIM API, via the OpenAI SDK."""

from collections.abc import Iterator, Sequence

import openai
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from openai.types.completion_usage import CompletionUsage

from resume_roast.integrations.errors import (
    ApiError,
    AuthenticationError,
    EmptyResponseError,
    TransientError,
    TruncatedResponseError,
)
from resume_roast.integrations.nvidia.types import Completion, Message, Usage

_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Reasoning models routinely spend 2500-4000 completion tokens on a
# full-resume evaluation; at 4096 responses truncated in practice.
_MAX_TOKENS = 8192

# Full-resume evaluations on nemotron-3-super regularly take 45-60+ seconds;
# a 60s limit produced timeouts on otherwise healthy calls.
_TIMEOUT_SECONDS = 180.0

# The SDK retries only retryable failures (connection errors, 429s, 5xx),
# honoring Retry-After; a bad API key fails immediately.
_MAX_TRANSPORT_RETRIES = 2


def _map_error(exc: openai.OpenAIError) -> ApiError:
    """Translate an SDK error into ours, split by what the user can do."""
    if isinstance(exc, openai.AuthenticationError | openai.PermissionDeniedError):
        return AuthenticationError(
            f"NVIDIA API rejected the key ({exc}). Run: resume-roast config credentials"
        )
    if isinstance(
        exc,
        openai.RateLimitError | openai.APIConnectionError | openai.InternalServerError,
    ):
        return TransientError(f"NVIDIA API is unavailable ({exc}). Try again in a moment.")
    return ApiError(str(exc))


def _to_openai_messages(messages: Sequence[Message]) -> list[ChatCompletionMessageParam]:
    """Convert our messages into the SDK's per-role param dicts."""
    converted: list[ChatCompletionMessageParam] = []
    for message in messages:
        if message.role == "system":
            converted.append({"role": "system", "content": message.content})
        elif message.role == "user":
            converted.append({"role": "user", "content": message.content})
        else:
            converted.append({"role": "assistant", "content": message.content})
    return converted


def _to_usage(usage: CompletionUsage) -> Usage:
    """Convert the SDK's usage object into ours."""
    return Usage(
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
    )


class CompletionStream:
    """Iterable of response text chunks.

    ``usage`` and ``finish_reason`` hold None until the stream is exhausted,
    then whatever the API reported (``usage`` requires the server to honor
    ``include_usage``). Truncation is never raised here — by the time it is
    known, every chunk has already been delivered — callers inspect
    ``finish_reason`` instead.
    """

    def __init__(self, stream: Stream[ChatCompletionChunk]) -> None:
        self._stream = stream
        self.usage: Usage | None = None
        self.finish_reason: str | None = None

    def __iter__(self) -> Iterator[str]:
        try:
            for chunk in self._stream:
                if chunk.usage is not None:
                    self.usage = _to_usage(chunk.usage)
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                if choice.finish_reason is not None:
                    self.finish_reason = choice.finish_reason
                if choice.delta.content:
                    yield choice.delta.content
        except openai.OpenAIError as exc:
            raise _map_error(exc) from exc


class NvidiaClient:
    """Sends chat completions to the NVIDIA NIM API; knows nothing else.

    Transport retries belong to the SDK (configured below); response parsing
    belongs to callers. ``model`` is required because settings own the model
    choice — a default here could silently drift from the catalog.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(
            base_url=_BASE_URL,
            api_key=api_key,
            timeout=_TIMEOUT_SECONDS,
            max_retries=_MAX_TRANSPORT_RETRIES,
        )
        self.model = model

    def prompt(self, messages: Sequence[Message], *, temperature: float = 0.0) -> Completion:
        """Send `messages` and return the complete response.

        Raises:
            ApiError: `AuthenticationError` for a rejected key,
                `TransientError` when retrying may help, `EmptyResponseError`
                for a contentless reply, and `TruncatedResponseError` when the
                model hit the completion-token limit — callers of this method
                need the full text, and a truncated response silently missing
                its tail is worse than a failure.
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=_to_openai_messages(messages),
                temperature=temperature,
                max_tokens=_MAX_TOKENS,
                stream=False,
            )
        except openai.OpenAIError as exc:
            raise _map_error(exc) from exc

        if not response.choices:
            raise EmptyResponseError("NVIDIA API returned no choices.")
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise TruncatedResponseError(
                f"Response hit the {_MAX_TOKENS}-token completion limit before finishing."
            )
        if not choice.message.content:
            raise EmptyResponseError(
                f"NVIDIA API returned no content (finish_reason: {choice.finish_reason})."
            )
        usage = _to_usage(response.usage) if response.usage is not None else None
        return Completion(
            text=choice.message.content,
            usage=usage,
            finish_reason=choice.finish_reason,
        )

    def prompt_stream(
        self, messages: Sequence[Message], *, temperature: float = 0.0
    ) -> CompletionStream:
        """Send `messages` and return a stream of response text chunks.

        Raises:
            ApiError: `AuthenticationError` or `TransientError` when the
                request cannot be started; errors mid-stream surface from the
                returned iterator.
        """
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=_to_openai_messages(messages),
                temperature=temperature,
                max_tokens=_MAX_TOKENS,
                stream=True,
                stream_options={"include_usage": True},
            )
        except openai.OpenAIError as exc:
            raise _map_error(exc) from exc
        return CompletionStream(stream)
