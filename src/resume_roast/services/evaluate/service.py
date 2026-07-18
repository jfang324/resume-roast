"""Evaluate service: extract the resume, drive structured_completion, return the report."""

import time
from pathlib import Path

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.structured import structured_completion
from resume_roast.integrations.types import Message
from resume_roast.prompts.evaluate.builder import build_evaluate_prompt
from resume_roast.prompts.evaluate.output.parser import RoastReportParser
from resume_roast.services.evaluate.types import EvaluateResult
from resume_roast.utils.extraction.mappings import get_parser


def run(
    client: LlmClient,
    path: Path,
    persona: str,
    level: str,
) -> EvaluateResult:
    """Extract the resume at *path*, drive the evaluate prompt, and return the report.

    Raises:
        ExtractionError: when the document cannot be parsed.
        ApiError: transport and response failures, per `structured_completion`.
    """
    parsed = get_parser(path).parse(path)
    prompt = build_evaluate_prompt(parsed, persona, level)
    messages: list[Message] = [Message(role="system", content=prompt.system)]
    if prompt.user is not None:
        messages.append(Message(role="user", content=prompt.user))

    started = time.perf_counter()
    report, usage = structured_completion(client, messages, RoastReportParser().parse)

    return EvaluateResult(
        report=report,
        usage=usage,
        latency_seconds=time.perf_counter() - started,
    )
