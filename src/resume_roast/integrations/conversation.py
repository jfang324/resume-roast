"""A stateful chat session: holds the growing message list and appends turns."""

from collections.abc import Iterator
from dataclasses import dataclass, field

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message, Usage
from resume_roast.integrations.usage import total_usage


@dataclass
class Conversation:
    """A running conversation with an LLM, driven one user turn at a time.

    Wraps a stateless `LlmClient`: the message list *is* the history, and each
    `send_stream` appends the user turn, streams the reply, then appends the
    assistant turn. Usage accrues across turns so a session can report its cost.
    """

    _client: LlmClient
    messages: list[Message]
    temperature: float
    _usages: list[Usage] = field(default_factory=list[Usage])
    last_finish_reason: str | None = None

    @classmethod
    def start(cls, client: LlmClient, system: str, *, temperature: float) -> "Conversation":
        """Open a conversation seeded with a single system message."""
        return cls(client, [Message(role="system", content=system)], temperature)

    def send_stream(self, user_text: str) -> Iterator[str]:
        """Send a user turn and yield the reply's text chunks as they arrive.

        The assistant turn is recorded only once the stream is exhausted, since
        `usage` and `finish_reason` are unknown until then. If the client raises
        mid-stream, the just-appended user turn is rolled back so the caller can
        retry the same turn against an unchanged conversation.
        """
        self.messages.append(Message(role="user", content=user_text))
        chunks: list[str] = []
        try:
            stream = self._client.prompt_stream(self.messages, temperature=self.temperature)
            for chunk in stream:
                chunks.append(chunk)
                yield chunk
        except BaseException:
            self.messages.pop()
            raise
        self.messages.append(Message(role="assistant", content="".join(chunks)))
        if stream.usage is not None:
            self._usages.append(stream.usage)
        self.last_finish_reason = stream.finish_reason

    @property
    def total_usage(self) -> Usage | None:
        """Token usage summed across every turn that reported it, or None."""
        return total_usage(self._usages)
