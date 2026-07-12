"""Dataclasses crossing the NVIDIA client boundary."""

from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class Message:
    """One turn of a chat-completion conversation."""

    role: Role
    content: str


@dataclass(frozen=True)
class Usage:
    """Token counts reported by the API for one completion."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class Completion:
    """A finished, non-streamed model response.

    ``usage`` is None when the API reports no token counts; ``finish_reason``
    is None when the API omits it.
    """

    text: str
    usage: Usage | None
    finish_reason: str | None
