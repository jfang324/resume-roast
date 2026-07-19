"""Tool registration: defines action handlers and registers them with the registry."""

import logging
from typing import Any

from . import evaluate, verify
from .registry import Tool, ToolRegistry, ToolResult

logger = logging.getLogger(__name__)


def _verify_action(action: dict[str, Any], **context: Any) -> ToolResult:
    client = context["client"]
    resume_md = context["resume_md"]
    answer_history = context.get("answer_history", [""])
    claims = action.get("claims", [])
    if not claims:
        return ToolResult(success=False, data="No claims provided to verify.")
    answer = answer_history[-1] if answer_history else ""
    try:
        output, usage = verify.execute(client, claims, answer, resume_md)
        lines = ["Verify results:"]
        for c in output.claims:
            prob = f"{c.probability:.1%}"
            flags: list[str] = []
            if c.contradiction:
                flags.append("CONTRADICTION")
            if c.evidence:
                flags.append("evidence found")
            else:
                flags.append("no resume evidence")
            flag_str = f" ({', '.join(flags)})" if flags else ""
            lines.append(f'  - "{c.text}" probability={prob}{flag_str}')
        return ToolResult(
            success=True,
            data="\n".join(lines),
            result_type="verify_results",
            metadata={"usage": usage},
        )
    except Exception:
        logger.exception("verify tool failed")
        return ToolResult(success=False, data="Verification encountered an error.")


def _evaluate_action(action: dict[str, Any], **context: Any) -> ToolResult:
    client = context["client"]
    answer_history = context.get("answer_history", [""])
    competency_text = context.get("competency_text", "")
    competency_ids = context.get("competency_ids", [])
    original_question = action.get("original_question", context.get("current_question", ""))
    verify_results = action.get("verify_results", context.get("verify_results", ""))
    try:
        output, usage = evaluate.execute(
            client,
            original_question,
            answer_history,
            verify_results,
            competency_text,
            competency_ids,
        )
        lines = [
            "Evaluation complete.",
            f"Scores: {output.scores}",
            f"Critical failure: {output.critical_failure}",
        ]
        if output.strengths:
            lines.append(f"Strengths: {', '.join(output.strengths)}")
        if output.gaps:
            lines.append(f"Gaps: {', '.join(output.gaps)}")
        return ToolResult(
            success=True,
            data="\n".join(lines),
            result_type="evaluation",
            metadata={
                "usage": usage,
                "eval_output": output,
            },
        )
    except Exception:
        logger.exception("evaluate tool failed")
        return ToolResult(success=False, data="Evaluation encountered an error.")


def register_all(registry: ToolRegistry) -> None:
    registry.register(
        Tool(
            name="verify",
            description=(
                "Extract key factual claims from the candidate's last answer and "
                "verify each one against their resume. Call this after the user answers."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "claims": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Factual claims to verify against the resume",
                    },
                },
                "required": ["claims"],
            },
            required=["claims"],
            fn=_verify_action,
        )
    )

    registry.register(
        Tool(
            name="evaluate",
            description=(
                "Score the candidate's full answer cycle (including follow-ups) across "
                "all competencies. Call after verify and any follow-ups are complete."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "original_question": {
                        "type": "string",
                        "description": "The question that was asked",
                    },
                    "verify_results": {
                        "type": "string",
                        "description": "Results from the verify tool",
                    },
                },
                "required": [],
            },
            required=[],
            fn=_evaluate_action,
        )
    )
