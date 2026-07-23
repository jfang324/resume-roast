"""Typed tool-call model for the interview ReAct loop.

Each dataclass represents one tool call the LLM can emit, carrying the
``thought`` the model attached to it. Use `parse_tool_call` to parse the
raw response text into the appropriate subtype, then dispatch with
``match/case``.
"""

import json
from dataclasses import dataclass
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.response_parser import strip_code_fence


@dataclass(frozen=True)
class VerifyCall:
    name: str = "verify"
    claims: tuple[str, ...] = ()
    thought: str | None = None


@dataclass(frozen=True)
class EvaluateCall:
    name: str = "evaluate"
    thought: str | None = None


@dataclass(frozen=True)
class AskFollowupCall:
    name: str = "ask_followup"
    question: str = ""
    thought: str | None = None


@dataclass(frozen=True)
class ConcludeCall:
    name: str = "conclude"
    thought: str | None = None


@dataclass(frozen=True)
class UnknownTool:
    """A well-formed action whose name is not in the loop's vocabulary."""

    name: str
    thought: str | None = None


@dataclass(frozen=True)
class ParseFailure:
    name: str = "unknown"
    raw_text: str = ""
    thought: str | None = None


type ToolCall = (
    VerifyCall | EvaluateCall | AskFollowupCall | ConcludeCall | UnknownTool | ParseFailure
)


def tool_call_from_dict(raw: dict[str, Any]) -> ToolCall:
    """Convert a parsed JSON dict into the matching ToolCall subtype."""
    thought = raw.get("thought")
    if not isinstance(thought, str) or not thought.strip():
        thought = None

    name = raw.get("tool", "")
    if name == "verify":
        claims = raw.get("claims", [])
        if not isinstance(claims, list) or not all(
            isinstance(claim, str) for claim in cast("list[object]", claims)
        ):
            return ParseFailure(raw_text=str(raw), thought=thought)

        return VerifyCall(claims=tuple(cast("list[str]", claims)), thought=thought)

    if name == "evaluate":
        return EvaluateCall(thought=thought)

    if name == "ask_followup":
        question = raw.get("question", "")
        if not isinstance(question, str):
            return ParseFailure(raw_text=str(raw), thought=thought)

        return AskFollowupCall(question=question, thought=thought)

    if name == "conclude":
        return ConcludeCall(thought=thought)

    if isinstance(name, str) and name:
        return UnknownTool(name=name, thought=thought)

    return ParseFailure(raw_text=str(raw), thought=thought)


def parse_tool_call(text: str) -> ToolCall:
    """Parse the full LLM response *text* into a typed :obj:`ToolCall`.

    Handles code-fence stripping, JSON decoding, and dict-to-ToolCall conversion.
    Malformed JSON raises :class:`MalformedResponseError` so callers can
    provide retry feedback.
    """
    cleaned = strip_code_fence(text.strip())
    try:
        data: object = json.loads(cleaned)
    except ValueError as exc:
        raise MalformedResponseError(f"response is not valid JSON ({exc})") from exc

    if not isinstance(data, dict):
        raise MalformedResponseError("response must be a JSON object")

    return tool_call_from_dict(cast("dict[str, Any]", data))
