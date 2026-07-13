"""Shared parsing of structured LLM responses into feature types."""

import json
from abc import ABC, abstractmethod
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError


class ApiResponseParser[T](ABC):
    """Parses an LLM's text response into a validated ``T``.

    ``parse`` owns what every JSON response needs — code-fence stripping and
    decoding — while subclasses validate the decoded object against their
    schema in ``_parse_object``. Every failure raises
    `MalformedResponseError` with a message written for the model, since
    retry loops send it back verbatim as feedback.
    """

    def parse(self, text: str) -> T:
        """Parse the response `text` into a validated ``T``.

        Raises:
            MalformedResponseError: when `text` is not valid JSON, is not a
                JSON object, or fails the subclass's schema validation.
        """
        unfenced = _strip_code_fence(text.strip())
        try:
            data = json.loads(unfenced)
        except json.JSONDecodeError as exc:
            raise MalformedResponseError(f"the response is not valid JSON ({exc})") from exc
        if not isinstance(data, dict):
            raise MalformedResponseError("the response must be a single JSON object")
        return self._parse_object(cast(dict[str, Any], data))

    @abstractmethod
    def _parse_object(self, data: dict[str, Any]) -> T:
        """Validate the decoded JSON object against the feature's schema."""


def _strip_code_fence(text: str) -> str:
    """Drop a surrounding Markdown code fence, a common extraction artifact."""
    if not text.startswith("```"):
        return text
    lines = text.splitlines()[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)
