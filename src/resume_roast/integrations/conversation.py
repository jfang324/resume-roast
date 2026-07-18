"""A stateful chat session: holds the growing message list and appends turns."""

from collections.abc import Callable, Iterator

from resume_roast.integrations.llm_client import CompletionStream, LlmClient
from resume_roast.integrations.types import Message, Usage


class ConversationReply:
    """One streamed assistant reply, bundled with its post-stream metadata.

    Iterate for text chunks; ``usage`` and ``finish_reason`` are None until the
    stream is exhausted, then hold what the API reported — the same contract as
    `CompletionStream`, which this class satisfies. Single-use: the reply must
    be iterated exactly once, to exhaustion, for the assistant turn to be
    recorded in the conversation; ``exhausted`` reports whether that happened.
    """

    def __init__(
        self,
        stream: CompletionStream,
        on_complete: Callable[[str], None],
        on_error: Callable[[], None],
    ) -> None:
        self._stream = stream
        self._on_complete = on_complete
        self._on_error = on_error
        self._consumed = False
        self._exhausted = False

    def __iter__(self) -> Iterator[str]:
        """Yield reply chunks, then record the turn; roll back if the stream fails."""
        if self._consumed:
            msg = "A ConversationReply can only be iterated once."
            raise RuntimeError(msg)

        self._consumed = True
        chunks: list[str] = []

        try:
            for chunk in self._stream:
                chunks.append(chunk)

                yield chunk
        except BaseException:
            self._on_error()
            raise

        self._on_complete("".join(chunks))
        self._exhausted = True

    @property
    def exhausted(self) -> bool:
        """True once every chunk was yielded and the assistant turn recorded."""
        return self._exhausted

    @property
    def usage(self) -> Usage | None:
        """Token usage for this reply, None until the stream is exhausted."""
        return self._stream.usage

    @property
    def finish_reason(self) -> str | None:
        """Why the reply ended, None until the stream is exhausted."""
        return self._stream.finish_reason


class Conversation:
    """A running conversation with an LLM, driven one user turn at a time.

    Wraps a stateless `LlmClient`: the message list *is* the history, and each
    `send_stream` appends the user turn, streams the reply, then appends the
    assistant turn.

    Parameters
    ----------
    client
        The LLM client every turn is sent through.
    system_prompt
        Seeds the message list as its single system message.
    temperature
        Sampling temperature applied to every turn.
    """

    def __init__(
        self,
        client: LlmClient,
        system_prompt: str,
        temperature: float,
    ) -> None:
        self._client = client
        self.messages: list[Message] = [Message(role="system", content=system_prompt)]
        self.temperature = temperature

    def send_stream(self, user_text: str) -> ConversationReply:
        """Send a user turn and return the streamed reply.

        The user turn is appended and the request opened eagerly — a failure to
        open rolls the turn back and propagates. The assistant turn is recorded
        only once the reply is exhausted, since `usage` and `finish_reason` are
        unknown until then; if the stream fails mid-way, the user turn is rolled
        back so the caller can retry the same turn against an unchanged
        conversation.
        """
        self.messages.append(Message(role="user", content=user_text))
        try:
            stream = self._client.prompt_stream(
                self.messages,
                temperature=self.temperature,
            )
        except BaseException:
            self.messages.pop()
            raise

        return ConversationReply(
            stream,
            on_complete=self._record_assistant_turn,
            on_error=self._rollback_user_turn,
        )

    def _rollback_user_turn(self) -> None:
        self.messages.pop()

    def _record_assistant_turn(self, text: str) -> None:
        self.messages.append(Message(role="assistant", content=text))
