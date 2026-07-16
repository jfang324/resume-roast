"""Evaluate service: build the prompt, drive structured_completion, return the report."""

import time
from dataclasses import dataclass

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.structured import structured_completion
from resume_roast.integrations.types import Message, Usage
from resume_roast.prompts.evaluate.builder import build_evaluate_prompt
from resume_roast.prompts.evaluate.output.parser import RoastReportParser
from resume_roast.prompts.evaluate.output.schema import RoastReport
from resume_roast.utils.extraction.types import ParsedResume


@dataclass(frozen=True)
class EvaluateResult:
    """What `run()` returns: the parsed report plus accounting."""

    report: RoastReport
    usage: Usage | None
    latency_seconds: float


def run(
    client: LlmClient,
    parsed: ParsedResume,
    persona: str,
    level: str,
) -> EvaluateResult:
    """Drive the LLM through the evaluate prompt and return the parsed report and metrics."""
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
