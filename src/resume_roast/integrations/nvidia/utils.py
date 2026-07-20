"""Conversions between our boundary types and the OpenAI SDK's."""

import logging
from collections.abc import Sequence

import openai
from openai.types.chat import ChatCompletionMessageParam
from openai.types.completion_usage import CompletionUsage

from resume_roast.integrations.errors import (
    ApiError,
    AuthenticationError,
    TransientError,
)
from resume_roast.integrations.types import Message, Usage

logger = logging.getLogger(__name__)


def map_error(exc: openai.OpenAIError) -> ApiError:
    """Translate an SDK error into ours, split by what the user can do."""
    if isinstance(exc, openai.AuthenticationError | openai.PermissionDeniedError):
        return AuthenticationError(
            f"NVIDIA API rejected the key ({exc}). Run: resume-roast config credentials"
        )

    if isinstance(exc, openai.RateLimitError):
        # Logged here because map_error folds rate limits into TransientError
        # alongside connection/server errors; no downstream catch site can tell
        # a 429 from the rest. This 429 already survived the SDK's own retries.
        logger.error("NVIDIA API rate limit hit: %s", exc)

        return TransientError(
            f"NVIDIA API is unavailable ({exc}). Try again in a moment.",
        )

    if isinstance(exc, openai.APIConnectionError | openai.InternalServerError):
        return TransientError(
            f"NVIDIA API is unavailable ({exc}). Try again in a moment.",
        )

    return ApiError(str(exc))


def to_openai_messages(messages: Sequence[Message]) -> list[ChatCompletionMessageParam]:
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


def to_usage(usage: CompletionUsage) -> Usage:
    """Convert the SDK's usage object into ours."""
    return Usage(
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
    )
