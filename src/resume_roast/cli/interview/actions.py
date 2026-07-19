"""Typed action model for the interview ReAct loop.

Each dataclass represents one action the LLM can emit. Use `action_from_dict`
to parse the raw JSON response into the appropriate subtype, then dispatch with
``match/case``.
"""

from dataclasses import dataclass
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.response_parser import strip_code_fence


@dataclass(frozen=True)
class VerifyAction:
    name: str = "verify"
    claims: tuple[str, ...] = ()


@dataclass(frozen=True)
class FollowUpAction:
    name: str = "follow_up"


@dataclass(frozen=True)
class EvaluateAction:
    name: str = "evaluate"


@dataclass(frozen=True)
class AskFollowupAction:
    name: str = "ask_followup"
    question: str = ""


@dataclass(frozen=True)
class ConcludeAction:
    name: str = "conclude"


@dataclass(frozen=True)
class AskAction:
    name: str = "ask"


@dataclass(frozen=True)
class ParseFailure:
    name: str = "unknown"
    raw_text: str = ""


type InterviewAction = (
    VerifyAction
    | FollowUpAction
    | EvaluateAction
    | AskFollowupAction
    | ConcludeAction
    | AskAction
    | ParseFailure
)


def action_from_dict(raw: dict[str, Any]) -> InterviewAction:
    """Convert a parsed JSON dict into the matching Action subtype.

    Raises:
        MalformedResponseError: if the input is not a dict or has no ``action`` key.
    """
    name = raw.get("action", "")
    if name == "verify":
        claims = raw.get("claims", [])
        return VerifyAction(claims=tuple(claims))
    if name == "follow_up":
        return FollowUpAction()
    if name == "evaluate":
        return EvaluateAction()
    if name == "ask_followup":
        return AskFollowupAction(question=raw.get("question", ""))
    if name == "conclude":
        return ConcludeAction()
    if name == "ask":
        return AskAction()
    return ParseFailure(raw_text=str(raw))


def parse_llm_action(text: str) -> InterviewAction:
    """Parse the full LLM response *text* into a typed :obj:`InterviewAction`.

    Handles code-fence stripping, JSON decoding, and dict-to-Action conversion.
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
    return action_from_dict(cast("dict[str, Any]", data))
