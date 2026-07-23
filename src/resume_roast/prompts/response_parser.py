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
        unfenced = strip_code_fence(text.strip())
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


def parse_first_json_object(text: str, label: str = "output") -> dict[str, Any]:
    """Parse the first JSON object in `text`, tolerating trailing data.

    The tolerant counterpart to `ApiResponseParser.parse` for responses where
    the model may append prose after the object. ``label`` names the response
    in error messages, which retry loops send back to the model as feedback.

    Raises:
        MalformedResponseError: when `text` holds no leading JSON object.
    """
    cleaned = strip_code_fence(text.strip())
    try:
        data, _ = json.JSONDecoder().raw_decode(cleaned)
    except json.JSONDecodeError as exc:
        raise MalformedResponseError(f"{label} is not valid JSON ({exc})") from exc

    if not isinstance(data, dict):
        raise MalformedResponseError(f"{label} must be a JSON object")

    return cast("dict[str, Any]", data)


def string_list(value: object) -> list[str]:
    """Keep the non-blank strings of a JSON array; anything else is dropped.

    The lenient reading shared by parsers whose list fields are optional
    color, not contract — a malformed item loses itself, not the response.
    """
    if not isinstance(value, list):
        return []

    return [
        item.strip()
        for item in cast("list[object]", value)
        if isinstance(item, str) and item.strip()
    ]


def strip_code_fence(text: str) -> str:
    """Drop a surrounding Markdown code fence, a common extraction artifact."""
    if not text.startswith("```"):
        return text

    lines = text.splitlines()[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines)
