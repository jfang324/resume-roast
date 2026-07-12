"""Thin chat-completion client for the NVIDIA NIM API, via the OpenAI SDK."""

from collections.abc import Iterator, Sequence

import openai
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletionChunk

from resume_roast.integrations.errors import EmptyResponseError, TruncatedResponseError
from resume_roast.integrations.nvidia.constants import (
    BASE_URL,
    MAX_TOKENS,
    MAX_TRANSPORT_RETRIES,
    TIMEOUT_SECONDS,
)
from resume_roast.integrations.nvidia.utils import map_error, to_openai_messages, to_usage
from resume_roast.integrations.types import Completion, Message, Usage


class NvidiaCompletionStream:
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
                    self.usage = to_usage(chunk.usage)
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                if choice.finish_reason is not None:
                    self.finish_reason = choice.finish_reason
                if choice.delta.content:
                    yield choice.delta.content
        except openai.OpenAIError as exc:
            raise map_error(exc) from exc


class NvidiaClient:
    """Sends chat completions to the NVIDIA NIM API; knows nothing else.

    Transport retries belong to the SDK (configured below); response parsing
    belongs to callers. ``model`` is required because settings own the model
    choice — a default here could silently drift from the catalog.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(
            base_url=BASE_URL,
            api_key=api_key,
            timeout=TIMEOUT_SECONDS,
            max_retries=MAX_TRANSPORT_RETRIES,
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
                messages=to_openai_messages(messages),
                temperature=temperature,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
        except openai.OpenAIError as exc:
            raise map_error(exc) from exc

        if not response.choices:
            raise EmptyResponseError("NVIDIA API returned no choices.")
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise TruncatedResponseError(
                f"Response hit the {MAX_TOKENS}-token completion limit before finishing."
            )
        if not choice.message.content:
            raise EmptyResponseError(
                f"NVIDIA API returned no content (finish_reason: {choice.finish_reason})."
            )
        usage = to_usage(response.usage) if response.usage is not None else None
        return Completion(
            text=choice.message.content,
            usage=usage,
            finish_reason=choice.finish_reason,
        )

    def prompt_stream(
        self, messages: Sequence[Message], *, temperature: float = 0.0
    ) -> NvidiaCompletionStream:
        """Send `messages` and return a stream of response text chunks.

        Raises:
            ApiError: `AuthenticationError` or `TransientError` when the
                request cannot be started; errors mid-stream surface from the
                returned iterator.
        """
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=to_openai_messages(messages),
                temperature=temperature,
                max_tokens=MAX_TOKENS,
                stream=True,
                stream_options={"include_usage": True},
            )
        except openai.OpenAIError as exc:
            raise map_error(exc) from exc
        return NvidiaCompletionStream(stream)
