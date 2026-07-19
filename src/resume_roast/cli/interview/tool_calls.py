"""Typed tool-call model for the interview ReAct loop.

Each dataclass represents one tool call the LLM can emit. Use `tool_call_from_dict`
to parse the raw JSON response into the appropriate subtype, then dispatch with
``match/case``.
"""

from dataclasses import dataclass
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.response_parser import strip_code_fence


@dataclass(frozen=True)
class VerifyCall:
    name: str = "verify"
    claims: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluateCall:
    name: str = "evaluate"


@dataclass(frozen=True)
class AskFollowupCall:
    name: str = "ask_followup"
    question: str = ""


@dataclass(frozen=True)
class ConcludeCall:
    name: str = "conclude"


@dataclass(frozen=True)
class UnknownTool:
    """A well-formed action whose name is not in the loop's vocabulary."""

    name: str


@dataclass(frozen=True)
class ParseFailure:
    name: str = "unknown"
    raw_text: str = ""


type ToolCall = (
    VerifyCall | EvaluateCall | AskFollowupCall | ConcludeCall | UnknownTool | ParseFailure
)


def tool_call_from_dict(raw: dict[str, Any]) -> ToolCall:
    """Convert a parsed JSON dict into the matching ToolCall subtype.

    Raises:
        MalformedResponseError: if the input is not a dict or has no ``action`` key.
    """
    name = raw.get("action", "")
    if name == "verify":
        claims = raw.get("claims", [])
        return VerifyCall(claims=tuple(claims))
    if name == "evaluate":
        return EvaluateCall()
    if name == "ask_followup":
        return AskFollowupCall(question=raw.get("question", ""))
    if name == "conclude":
        return ConcludeCall()
    if isinstance(name, str) and name:
        return UnknownTool(name=name)

    return ParseFailure(raw_text=str(raw))


def parse_tool_call(text: str) -> ToolCall:
    """Parse the full LLM response *text* into a typed :obj:`ToolCall`.

    Handles code-fence stripping, JSON decoding, and dict-to-ToolCall conversion.
    Malformed JSON raises :class:`MalformedResponseError` so callers can
    provide retry feedback.
    """
    cleaned = strip_code_fence(text.strip())
    try:
        import json

        data: object = json.loads(cleaned)
    except ValueError as exc:
        raise MalformedResponseError(f"response is not valid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise MalformedResponseError("response must be a JSON object")
    return tool_call_from_dict(cast("dict[str, Any]", data))
