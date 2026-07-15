"""ReAct utilities: parsing LLM actions from structured JSON responses."""

import json
import logging
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.tools.registry import ToolResult

logger = logging.getLogger(__name__)


def parse_action(text: str) -> dict[str, Any]:
    """Parse a JSON action from the LLM's response text."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise MalformedResponseError(f"response is not valid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise MalformedResponseError("response must be a JSON object")
    return cast(dict[str, Any], data)


def dispatch_tool(
    action_name: str,
    action: dict[str, Any],
    client: object,
    resume_markdown: str,
    competency_descriptions: str,
    answer_history: list[str],
    competency_ids: list[str] | None = None,
    current_question: str = "",
    verify_results: str = "",
) -> ToolResult:
    """Execute a tool from the registry and return the ToolResult."""
    from resume_roast.tools import REGISTRY

    return REGISTRY.execute(
        action_name,
        action,
        client=client,
        resume_md=resume_markdown,
        answer_history=answer_history,
        competency_text=competency_descriptions,
        competency_ids=competency_ids or [],
        current_question=current_question,
        verify_results=verify_results,
    )
